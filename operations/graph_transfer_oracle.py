"""Graph Connectivity Frontier Transfer Matrix DP and Exhaustive Oracle.

Provides:
- brute(edges, source, target, probabilities):
    Exhaustive 2^|E| state space evaluation of exact network reliability
    under rational or signed edge weights in exact rational arithmetic (Fraction).
- transfer(edges, source, target, probabilities):
    Frontier transfer matrix dynamic programming over cut-boundaries.
    Evaluates exact network reliability in O(2^{pw} * |E|) time where pw
    is the pathwidth of the edge-ordered graph.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any, Iterable, List, Sequence, Set, Tuple


def canonical(groups: Iterable[Iterable[Any]]) -> Tuple[Tuple[Any, ...], ...]:
    """Return canonical immutable sorted tuple-of-tuples representation of a vertex partition."""
    return tuple(sorted(tuple(sorted(g)) for g in groups if g))


def brute(
    edges: Sequence[Tuple[Any, Any]],
    source: Any,
    target: Any,
    probabilities: Sequence[Fraction | int | float],
) -> Fraction:
    """Exhaustive truth-table oracle evaluating exact network reliability."""
    m = len(edges)
    probs = [Fraction(p) for p in probabilities]
    total = Fraction(0, 1)

    for mask in range(1 << m):
        # Build adjacency for active edges in this mask
        adj = defaultdict(list)
        for i, (u, v) in enumerate(edges):
            if (mask >> i) & 1:
                adj[u].append(v)
                adj[v].append(u)

        # BFS connectivity from source
        visited: Set[Any] = {source}
        queue = [source]
        while queue:
            curr = queue.pop(0)
            if curr == target:
                break
            for nbr in adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)

        if target in visited:
            weight = Fraction(1, 1)
            for i in range(m):
                if (mask >> i) & 1:
                    weight *= probs[i]
                else:
                    weight *= (Fraction(1, 1) - probs[i])
            total += weight

    return total


def transfer(
    edges: Sequence[Tuple[Any, Any]],
    source: Any,
    target: Any,
    probabilities: Sequence[Fraction | int | float],
) -> Tuple[Fraction, int]:
    """Frontier transfer matrix dynamic programming evaluation.

    Returns:
        (exact_reliability, max_frontier_states)
    """
    if not edges:
        return (Fraction(1, 1) if source == target else Fraction(0, 1), 1)

    probs = [Fraction(p) for p in probabilities]
    s, t = source, target
    last = {v: i for i, (u, v) in enumerate(edges) for v in (u, v)}

    # Initial state: s and t in their own singleton components
    init_groups = [{s}, {t}] if s != t else [{s}]
    states: dict[Tuple[Tuple[Any, ...], ...], Fraction] = {
        canonical(init_groups): Fraction(1, 1)
    }
    max_states = 1

    for i, (u, v) in enumerate(edges):
        p = probs[i]
        nxt: dict[Tuple[Tuple[Any, ...], ...], Fraction] = defaultdict(Fraction)

        for state, mass in states.items():
            groups = [set(g) for g in state]
            known = set().union(*groups)
            for x in (u, v):
                if x not in known:
                    groups.append({x})
                    known.add(x)

            # Inactive edge branch: multiplier (1 - p)
            w_inactive = Fraction(1, 1) - p
            if w_inactive != 0:
                gs0 = [g.copy() for g in groups]
                for g in gs0:
                    g.difference_update(
                        x for x in list(g) if x not in (s, t) and last[x] == i
                    )
                c0 = canonical(g for g in gs0 if g)
                nxt[c0] += mass * w_inactive

            # Active edge branch: multiplier p
            if p != 0:
                gs1 = [g.copy() for g in groups]
                a = next(j for j, g in enumerate(gs1) if u in g)
                b = next(j for j, g in enumerate(gs1) if v in g)
                if a != b:
                    gs1[a].update(gs1[b])
                    gs1.pop(b)
                for g in gs1:
                    g.difference_update(
                        x for x in list(g) if x not in (s, t) and last[x] == i
                    )
                c1 = canonical(g for g in gs1 if g)
                nxt[c1] += mass * p

        states = nxt
        max_states = max(max_states, len(states))

    total = sum(
        m for state, m in states.items() if any(s in g and t in g for g in state)
    )
    return (total, max_states)

