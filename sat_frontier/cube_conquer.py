"""Parallel Cube-and-Conquer lookahead solver for high-core CPU execution (e.g. AMD EPYC)."""
import hashlib
import json
import os
import resource
import statistics
from collections import defaultdict
from fractions import Fraction
from multiprocessing import Pool, get_context
from time import perf_counter
from pathlib import Path

from .core import Formula, parse_dimacs, solve
from .wmc import WeightedFormula, wmc_solve


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def select_cube_variables(clauses, n_vars, depth=3, priority_vars=None):
    """Select the top branching variables for lookahead cube generation."""
    active_vars = set(abs(lit) for c in clauses for lit in c)
    if not active_vars:
        return []

    selected = []
    if priority_vars:
        for v in priority_vars:
            if v in active_vars and len(selected) < depth:
                selected.append(v)

    while len(selected) < depth:
        remaining = active_vars - set(selected)
        if not remaining:
            break
        counts = defaultdict(int)
        for c in clauses:
            for lit in c:
                if abs(lit) in remaining:
                    counts[abs(lit)] += 1
        best_v = max(remaining, key=lambda v: (counts[v], v))
        selected.append(best_v)

    return selected


def generate_cubes(clauses, n_vars, depth=3, priority_vars=None):
    """Generate independent, disjoint assumption cubes (partial assignments)."""
    vars_to_branch = select_cube_variables(clauses, n_vars, depth=depth, priority_vars=priority_vars)
    if not vars_to_branch:
        return [()]

    cubes = [()]
    for v in vars_to_branch:
        nxt_cubes = []
        for cube in cubes:
            nxt_cubes.append(cube + (v,))
            nxt_cubes.append(cube + (-v,))
        cubes = nxt_cubes

    return cubes


def _cube_signature(dimacs_text: str, cube: tuple, algo: str, seconds: float, max_nodes: int) -> str:
    payload = json.dumps({
        "dimacs_sha256": _sha(dimacs_text),
        "cube": list(cube),
        "algo": algo,
        "seconds": seconds,
        "max_nodes": max_nodes,
    }, sort_keys=True)
    return _sha(payload)


def _eval_cube_unweighted(args):
    """Worker function for unweighted model count of a single cube."""
    dimacs_text, cube, algo, seconds, max_nodes = args
    f = parse_dimacs(dimacs_text)
    conditioned_clauses = [list(c) for c in f.clauses] + [[lit] for lit in cube]
    cond_f = Formula(f.n, conditioned_clauses)
    res = solve(cond_f, algorithm=algo, seconds=seconds, max_nodes=max_nodes)
    return {
        'cube': cube,
        'status': res['status'],
        'count': res.get('count'),
        'nodes': res.get('nodes', 0),
        'elapsed': res.get('elapsed_seconds', 0.0),
    }


def _eval_cube_weighted(args):
    """Worker function for Weighted Model Count of a single cube."""
    dimacs_text, cube, algo, seconds, max_nodes = args
    clauses = []
    weights = {}
    n_vars = 0
    for line in dimacs_text.splitlines():
        line = line.strip()
        if not line or line.startswith('c'):
            if line.startswith('c p weight'):
                parts = line.split()
                lit = int(parts[3])
                w = Fraction(parts[4])
                weights[lit] = w
            continue
        if line.startswith('p cnf'):
            parts = line.split()
            n_vars = int(parts[2])
            continue
        lits = [int(x) for x in line.split() if x != '0']
        if lits:
            clauses.append(lits)

    conditioned_clauses = clauses + [[lit] for lit in cube]
    wf = WeightedFormula(conditioned_clauses, n_vars=n_vars, weights=weights)
    res = wmc_solve(wf, algorithm=algo, seconds=seconds, max_nodes=max_nodes)
    return {
        'cube': cube,
        'status': res['status'],
        'weight_fraction': res.get('weight_fraction'),
        'nodes': res.get('nodes', 0),
        'elapsed': res.get('elapsed_seconds', 0.0),
    }


def _load_checkpoint(checkpoint_dir: Path):
    """Load existing checkpoint results keyed by cube signature."""
    if not checkpoint_dir.exists():
        return {}
    out = {}
    for p in checkpoint_dir.glob('*.json'):
        try:
            data = json.loads(p.read_text())
            sig = data.get('signature')
            if sig:
                out[sig] = data
        except Exception:
            continue
    return out


def _save_checkpoint(checkpoint_dir: Path, sig: str, result: dict):
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / f"{sig}.json"
    path.write_text(json.dumps({"signature": sig, **result}, indent=2) + "\n")


def parallel_cube_and_conquer(f, depth=3, num_workers=None, algo='combined',
                              seconds_per_cube=10.0, max_nodes_per_cube=50000,
                              priority_vars=None, checkpoint_dir=None):
    """Execute high-core parallel Cube-and-Conquer on an unweighted Formula."""
    start_time = perf_counter()
    if num_workers is None:
        num_workers = os.cpu_count() or 1

    n_vars = getattr(f, 'n_vars', getattr(f, 'n', 0))
    cubes = generate_cubes(f.clauses, n_vars, depth=depth, priority_vars=priority_vars)
    dimacs_text = f.dimacs()

    checkpoint_path = Path(checkpoint_dir) if checkpoint_dir else None
    existing = _load_checkpoint(checkpoint_path) if checkpoint_path else {}

    tasks = []
    for cube in cubes:
        sig = _cube_signature(dimacs_text, cube, algo, seconds_per_cube, max_nodes_per_cube)
        if sig in existing:
            continue
        tasks.append((dimacs_text, cube, algo, seconds_per_cube, max_nodes_per_cube, sig, checkpoint_path))

    ctx = get_context('spawn')
    results = []
    if tasks:
        # Flatten for pool: drop checkpoint args for worker
        worker_tasks = [(t[0], t[1], t[2], t[3], t[4]) for t in tasks]
        with ctx.Pool(processes=num_workers) as pool:
            worker_results = pool.map(_eval_cube_unweighted, worker_tasks)

        for task_args, worker_res in zip(tasks, worker_results):
            sig = task_args[5]
            ck = task_args[6]
            if ck:
                _save_checkpoint(ck, sig, worker_res)
            results.append(worker_res)

    # Merge existing + new
    all_results = list(existing.values()) + results

    total_count = 0
    total_nodes = 0
    incomplete_cubes = 0
    cube_elapsed = []

    for r in all_results:
        total_nodes += r.get('nodes', 0)
        cube_elapsed.append(r.get('elapsed', 0.0))
        if r.get('status') == 'exact' and r.get('count') is not None:
            total_count += r['count']
        else:
            incomplete_cubes += 1

    elapsed = perf_counter() - start_time
    status = 'exact' if incomplete_cubes == 0 else 'unknown'

    return {
        'status': status,
        'count': total_count if status == 'exact' else None,
        'cubes_total': len(cubes),
        'cubes_incomplete': incomplete_cubes,
        'workers': num_workers,
        'total_nodes': total_nodes,
        'elapsed_seconds': elapsed,
        'partitioning_seconds': None,
        'results': all_results,
        'cube_time_median': statistics.median(cube_elapsed) if cube_elapsed else None,
        'cube_time_max': max(cube_elapsed) if cube_elapsed else None,
        'checkpoint_dir': str(checkpoint_path) if checkpoint_path else None,
    }


def parallel_cube_and_conquer_wmc(wf, depth=3, num_workers=None, algo='combined_wmc',
                                  seconds_per_cube=10.0, max_nodes_per_cube=50000,
                                  priority_vars=None, checkpoint_dir=None):
    """Execute high-core parallel Cube-and-Conquer on a WeightedFormula."""
    start_time = perf_counter()
    if num_workers is None:
        num_workers = os.cpu_count() or 1

    cubes = generate_cubes(wf.clauses, wf.n_vars, depth=depth, priority_vars=priority_vars)
    dimacs_text = wf.dimacs()

    checkpoint_path = Path(checkpoint_dir) if checkpoint_dir else None
    existing = _load_checkpoint(checkpoint_path) if checkpoint_path else {}

    tasks = []
    for cube in cubes:
        sig = _cube_signature(dimacs_text, cube, algo, seconds_per_cube, max_nodes_per_cube)
        if sig in existing:
            continue
        tasks.append((dimacs_text, cube, algo, seconds_per_cube, max_nodes_per_cube, sig, checkpoint_path))

    ctx = get_context('spawn')
    results = []
    if tasks:
        worker_tasks = [(t[0], t[1], t[2], t[3], t[4]) for t in tasks]
        with ctx.Pool(processes=num_workers) as pool:
            worker_results = pool.map(_eval_cube_weighted, worker_tasks)

        for task_args, worker_res in zip(tasks, worker_results):
            sig = task_args[5]
            ck = task_args[6]
            if ck:
                _save_checkpoint(ck, sig, worker_res)
            results.append(worker_res)

    all_results = list(existing.values()) + results

    total_weight = Fraction(0)
    total_nodes = 0
    incomplete_cubes = 0
    cube_elapsed = []

    for r in all_results:
        total_nodes += r.get('nodes', 0)
        cube_elapsed.append(r.get('elapsed', 0.0))
        if r.get('status') == 'exact' and r.get('weight_fraction') is not None:
            total_weight += Fraction(r['weight_fraction'])
        else:
            incomplete_cubes += 1

    elapsed = perf_counter() - start_time
    status = 'exact' if incomplete_cubes == 0 else 'unknown'

    return {
        'status': status,
        'weight_fraction': str(total_weight) if status == 'exact' else None,
        'weight_float': float(total_weight) if status == 'exact' else None,
        'cubes_total': len(cubes),
        'cubes_incomplete': incomplete_cubes,
        'workers': num_workers,
        'total_nodes': total_nodes,
        'elapsed_seconds': elapsed,
        'partitioning_seconds': None,
        'results': all_results,
        'cube_time_median': statistics.median(cube_elapsed) if cube_elapsed else None,
        'cube_time_max': max(cube_elapsed) if cube_elapsed else None,
        'checkpoint_dir': str(checkpoint_path) if checkpoint_path else None,
    }


def _discover_resources():
    """Discover CPU, NUMA, and memory topology."""
    info = {
        "cpu_count": os.cpu_count() or 1,
        "numa_nodes": 0,
        "cpus_per_node": [],
        "total_memory_mb": 0,
        "available_memory_mb": 0,
        "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0),
    }

    # NUMA topology
    try:
        with open('/sys/devices/system/node/possible') as f:
            txt = f.read().strip()
        parts = txt.split('-')
        if len(parts) == 2:
            start, end = int(parts[0]), int(parts[1])
            info["numa_nodes"] = end - start + 1
            for node in range(start, end + 1):
                try:
                    with open(f'/sys/devices/system/node/node{node}/cpulist') as f:
                        cpus = f.read().strip()
                    info["cpus_per_node"].append(cpus)
                except Exception:
                    info["cpus_per_node"].append("")
    except Exception:
        pass

    # Memory
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    info["total_memory_mb"] = int(line.split()[1]) // 1024
                elif line.startswith('MemAvailable:'):
                    info["available_memory_mb"] = int(line.split()[1]) // 1024
    except Exception:
        pass

    return info


def recommend_workers(instance_bytes: int, per_cube_memory_mb: int = 50, max_workers: int = None):
    """Conservative worker sizing based on available memory and CPU."""
    resources = _discover_resources()
    cpu_max = resources["cpu_count"]
    mem_max = max(1, resources.get("available_memory_mb", 0) // max(1, per_cube_memory_mb))

    if max_workers is None:
        max_workers = min(cpu_max, mem_max)
    else:
        max_workers = min(max_workers, cpu_max, mem_max)

    return {
        "recommended_workers": max(1, max_workers),
        "cpu_count": cpu_max,
        "numa_nodes": resources["numa_nodes"],
        "available_memory_mb": resources.get("available_memory_mb", 0),
        "load_avg_1m": resources["load_avg"][0],
        "reason": f"cpu={cpu_max}, mem_limited={mem_max}, chosen=min({max_workers})",
    }
