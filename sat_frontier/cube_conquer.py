"""Parallel Cube-and-Conquer lookahead solver for high-core CPU execution (e.g. AMD EPYC)."""
import os
from collections import defaultdict
from fractions import Fraction
from multiprocessing import Pool, get_context
from time import perf_counter

from .core import Formula, parse_dimacs, solve
from .wmc import WeightedFormula, wmc_solve


def select_cube_variables(clauses, n_vars, depth=3, priority_vars=None):
    """Select the top branching variables for lookahead cube generation."""
    active_vars = set(abs(lit) for c in clauses for lit in c)
    if not active_vars:
        return []

    selected = []
    # If priority variables (e.g. graph separators) provided, pick those first
    if priority_vars:
        for v in priority_vars:
            if v in active_vars and len(selected) < depth:
                selected.append(v)

    # Fill remaining depth using DLCS (maximum appearance in shortest clauses)
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


def _eval_cube_unweighted(args):
    """Worker function for unweighted model count of a single cube."""
    dimacs_text, cube, algo, seconds, max_nodes = args
    f = parse_dimacs(dimacs_text)
    # Append cube literals as individual unit clauses
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
    # Parse weighted formula from dimacs text
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


def parallel_cube_and_conquer(f, depth=3, num_workers=None, algo='combined',
                              seconds_per_cube=10.0, max_nodes_per_cube=50000,
                              priority_vars=None):
    """Execute high-core parallel Cube-and-Conquer on an unweighted Formula."""
    start_time = perf_counter()
    if num_workers is None:
        num_workers = os.cpu_count() or 1

    n_vars = getattr(f, 'n_vars', getattr(f, 'n', 0))
    cubes = generate_cubes(f.clauses, n_vars, depth=depth, priority_vars=priority_vars)
    dimacs_text = f.dimacs()

    tasks = [
        (dimacs_text, cube, algo, seconds_per_cube, max_nodes_per_cube)
        for cube in cubes
    ]

    ctx = get_context('spawn')
    with ctx.Pool(processes=num_workers) as pool:
        results = pool.map(_eval_cube_unweighted, tasks)

    total_count = 0
    total_nodes = 0
    incomplete_cubes = 0

    for r in results:
        total_nodes += r['nodes']
        if r['status'] == 'exact' and r['count'] is not None:
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
        'results': results,
    }


def parallel_cube_and_conquer_wmc(wf, depth=3, num_workers=None, algo='combined_wmc',
                                  seconds_per_cube=10.0, max_nodes_per_cube=50000,
                                  priority_vars=None):
    """Execute high-core parallel Cube-and-Conquer on a WeightedFormula."""
    start_time = perf_counter()
    if num_workers is None:
        num_workers = os.cpu_count() or 1

    cubes = generate_cubes(wf.clauses, wf.n_vars, depth=depth, priority_vars=priority_vars)
    dimacs_text = wf.dimacs()

    tasks = [
        (dimacs_text, cube, algo, seconds_per_cube, max_nodes_per_cube)
        for cube in cubes
    ]

    ctx = get_context('spawn')
    with ctx.Pool(processes=num_workers) as pool:
        results = pool.map(_eval_cube_weighted, tasks)

    total_weight = Fraction(0)
    total_nodes = 0
    incomplete_cubes = 0

    for r in results:
        total_nodes += r['nodes']
        if r['status'] == 'exact' and r['weight_fraction'] is not None:
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
        'results': results,
    }
