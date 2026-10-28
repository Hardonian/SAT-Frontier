"""Bounded sharpSAT-TD exact-counter subprocess; never interpret decision SAT as #SAT."""
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .core import Formula


def count(binary, formula, seconds=5.0, memory_bytes=None):
    """Run sharpSAT-TD on an unweighted DIMACS formula. Outputs are retained in result.

    Linux wait4 yields direct child maximum RSS in KiB. Memory limit is address
    space (RLIMIT_AS), not RSS. Unsupported platforms report null measurements.
    """
    if seconds <= 0 or (memory_bytes is not None and memory_bytes <= 0):
        raise ValueError("invalid resource budget")
    binary = str(Path(binary).resolve())
    result = {"status": "error", "count": None, "peak_rss_kib": None,
              "memory_limit": "unsupported" if memory_bytes is not None else "not_requested"}
    if not Path(binary).is_file() or not os.access(binary, os.X_OK):
        return dict(result, reason="missing_binary")
    linux = sys.platform.startswith("linux") and hasattr(os, "wait4")
    if memory_bytes is not None and not linux:
        return dict(result, reason="memory_limit_unsupported")
    with tempfile.TemporaryDirectory(prefix="sat-counter-") as d:
        input_path = Path(d) / "input.cnf"
        input_path.write_text(formula.dimacs())
        solver_args = ["-decot", "0", "-decow", "100", "-tmpdir", d, "-cs", "64", str(input_path)]
        if linux:
            cmd = [sys.executable, str(Path(__file__).with_name("process_exec.py")),
                   str(memory_bytes or 0), binary] + solver_args
        else:
            shebang = None
            try:
                with open(binary, "rb") as bf:
                    hdr = bf.read(256)
                if hdr.startswith(b"#!"):
                    shebang = hdr.split(b"\n")[0][2:].decode().strip()
            except OSError:
                pass
            if shebang:
                cmd = [shebang, binary] + solver_args
            else:
                cmd = [binary] + solver_args
        with (Path(d)/"stdout").open("w+b") as out, (Path(d)/"stderr").open("w+b") as err:
            try:
                proc = subprocess.Popen(cmd, stdout=out, stderr=err, start_new_session=True, cwd=d)
            except OSError as exc:
                return dict(result, reason="launch_error", detail=str(exc))
            start = time.monotonic()
            timed_out = False
            if linux:
                while True:
                    pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
                    if pid:
                        proc.returncode = os.waitstatus_to_exitcode(status)
                        result["peak_rss_kib"] = usage.ru_maxrss
                        break
                    if time.monotonic() - start >= seconds:
                        timed_out = True
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass  # Child exited between wait4 and killpg.
                        _, status, usage = os.wait4(proc.pid, 0)
                        proc.returncode = os.waitstatus_to_exitcode(status)
                        result["peak_rss_kib"] = usage.ru_maxrss
                        break
                    time.sleep(0.005)
            else:
                try:
                    proc.wait(timeout=seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    proc.kill()
                    proc.wait()
            result.update(wall_seconds=time.monotonic()-start, returncode=proc.returncode,
                          memory_limit="rlimit_as" if memory_bytes is not None else "not_requested")
            out.seek(0); err.seek(0)
            result.update(stdout=out.read().decode("utf-8", "replace"),
                          stderr=err.read().decode("utf-8", "replace"))
    if timed_out:
        return dict(result, status="unknown", reason="timeout")
    if proc.returncode != 0:
        return dict(result, reason="process_exit")
    matches = re.findall(r"(?m)^c s exact arb int ([0-9]+)\s*$", result["stdout"])
    if len(matches) != 1:
        return dict(result, reason="malformed_output")
    return dict(result, status="exact", count=int(matches[0]))


def minimize(formula, disagrees):
    """Deterministically delete clauses then literals while discrepancy survives.

    Predicate must raise on inconclusive runs; n stays fixed to preserve semantics
    of free variables. Returns a 1-minimal result for this ordered deletion pass.
    """
    clauses = list(formula.clauses)
    if not disagrees(formula):
        raise ValueError("formula does not disagree")
    changed = True
    while changed:
        changed = False
        for i in range(len(clauses)):
            trial = clauses[:i] + clauses[i+1:]
            if disagrees(Formula(formula.n, tuple(trial))):
                clauses = trial; changed = True; break
        if changed:
            continue
        for i, clause in enumerate(clauses):
            for j in range(len(clause)):
                trial = clauses.copy()
                trial[i] = clause[:j] + clause[j+1:]
                if disagrees(Formula(formula.n, tuple(trial))):
                    clauses = trial; changed = True; break
            if changed:
                break
    return Formula(formula.n, tuple(clauses))
