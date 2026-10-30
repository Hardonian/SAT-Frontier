"""Graph separator decomposition and articulation-point branching for exact #SAT."""
import math
from dataclasses import asdict
from time import perf_counter

from .core import BudgetExceeded, Formula, Stats, canonical, components


def find_separator_variable(cnf, active):
    """Find the best articulation or vertex separator variable in the residual formula.

    Constructs the variable-adjacency graph from active clauses. If any variable's
    removal partitions the active variables into multiple connected components,
    selects the cut vertex that minimizes the maximum component size (balanced split).
    Ties broken by component count, occurrence count, then variable index.
    """
    if len(active) <= 1:
        return next(iter(active))

    # Map each variable to the clause indices containing it
    var_clauses = {v: [] for v in active}
    for i, c in enumerate(cnf):
        for x in c:
            v = abs(x)
            if v in var_clauses:
                var_clauses[v].append(i)

    best_v = None
    best_score = (-1, 0, 0, 0, 0)

    for v in sorted(active):
        remaining = active - {v}
        if not remaining:
            return v
        seen = set()
        comp_sizes = []
        for start in remaining:
            if start not in seen:
                comp_size = 0
                q = [start]
                seen.add(start)
                while q:
                    curr = q.pop()
                    comp_size += 1
                    for ci in var_clauses[curr]:
                        for lit in cnf[ci]:
                            nxt = abs(lit)
                            if nxt in remaining and nxt not in seen:
                                seen.add(nxt)
                                q.append(nxt)
                comp_sizes.append(comp_size)

        num_comps = len(comp_sizes)
        is_cut = 1 if num_comps > 1 else 0
        max_comp = max(comp_sizes) if comp_sizes else 0
        balance = -max_comp if is_cut else 0
        occ = len(var_clauses[v])

        # Preference: cut vertex > balanced split > more components > higher occurrences > lower var index
        score = (is_cut, balance, num_comps, occ, -v)
        if score > best_score:
            best_score = score
            best_v = v

    return best_v if best_v is not None else min(active)


def solve_separator(f, seconds=5.0, max_nodes=1_000_000, cache_limit=100_000,
                    *, memo=True, decompose=True):
    """Exact model counter with graph separator branching.

    Preserves exact count semantics, unit propagation, memoization, and component
    decomposition. When residual formula is connected, branches on the best
    articulation point to force early graph factorization.
    """
    if not math.isfinite(seconds) or seconds <= 0 or max_nodes <= 0 or cache_limit < 0:
        raise ValueError("invalid resource budget")

    start = perf_counter()
    stats, cache = Stats(), {}

    def check():
        if perf_counter() - start >= seconds:
            raise BudgetExceeded("wall_limit")
        if stats.nodes >= max_nodes:
            raise BudgetExceeded("node_limit")

    def restrict(cnf, literal):
        out = []
        for c in cnf:
            check()
            if literal not in c:
                out.append(tuple(x for x in c if x != -literal))
        return canonical(out)

    def visit(cnf, remaining, depth=0):
        check()
        if depth >= 400:
            raise BudgetExceeded("depth_limit")
        stats.nodes += 1

        while True:
            if () in cnf:
                return 0
            if not cnf:
                return 1 << len(remaining)
            unit = next((c[0] for c in cnf if len(c) == 1), None)
            if unit is None:
                break
            remaining = remaining - {abs(unit)}
            stats.unit_assignments += 1
            cnf = restrict(cnf, unit)

        active = frozenset(abs(x) for c in cnf for x in c)
        free_factor = 1 << len(remaining - active)
        key = cnf

        if memo and key in cache:
            stats.cache_hits += 1
            return free_factor * cache[key]

        groups = components(cnf) if decompose else []
        if len(groups) > 1:
            stats.component_splits += 1
            result = 1
            for sub, variables in groups:
                result *= visit(sub, variables, depth + 1)
                if result == 0:
                    break
        else:
            v = find_separator_variable(cnf, active)
            result = (visit(restrict(cnf, v), active - {v}, depth + 1)
                      + visit(restrict(cnf, -v), active - {v}, depth + 1))

        if memo and len(cache) < cache_limit:
            cache[key] = result
        return free_factor * result

    try:
        count = visit(canonical(f.clauses), frozenset(range(1, f.n + 1)))
        status, reason = "exact", None
    except BudgetExceeded as exc:
        count, status, reason = None, "unknown", str(exc)
    except RecursionError:
        count, status, reason = None, "unknown", "recursion_limit"

    stats.cache_entries = len(cache)
    return dict(status=status, count=count, algorithm="separator", reason=reason,
                elapsed_seconds=perf_counter() - start, **asdict(stats))


def generate_barbell(n_cluster, bridge_len, seed=42):
    """Deterministically generate a barbell graph CNF with a known cut vertex bridge."""
    import random
    rng = random.Random(seed)
    # Left cluster: variables 1..n_cluster
    # Bridge: variables (n_cluster + 1) .. (n_cluster + bridge_len)
    # Right cluster: variables (n_cluster + bridge_len + 1) .. (2 * n_cluster + bridge_len)
    total_n = 2 * n_cluster + bridge_len
    left_vars = list(range(1, n_cluster + 1))
    bridge_vars = list(range(n_cluster + 1, n_cluster + bridge_len + 1))
    right_vars = list(range(n_cluster + bridge_len + 1, total_n + 1))

    clauses = []
    # Dense 3-SAT on left cluster
    for _ in range(n_cluster * 3):
        vs = rng.sample(left_vars, 3)
        clauses.append(tuple(v if rng.random() > 0.5 else -v for v in vs))

    # Dense 3-SAT on right cluster
    for _ in range(n_cluster * 3):
        vs = rng.sample(right_vars, 3)
        clauses.append(tuple(v if rng.random() > 0.5 else -v for v in vs))

    # Path bridge connecting left to right:
    # left anchor: left_vars[-1] -> bridge_vars[0] -> ... -> right_vars[0]
    path = [left_vars[-1]] + bridge_vars + [right_vars[0]]
    for i in range(len(path) - 1):
        u, w = path[i], path[i + 1]
        clauses.append((u, -w))
        clauses.append((-u, w))

    return Formula(total_n, tuple(clauses))

