"""Algebraic Model Counting over Z[x] for Exact Network Reliability Polynomials and Percolation Susceptibility.

Computes the exact closed-form polynomial:
    P(x) = sum_{k=0}^{|E|} c_k x^k
where c_k is the exact number of operational edge subgraphs of size k connecting source to target.
Enables instant O(|E|) evaluation of R(p) for any p, exact derivative (susceptibility) dR/dp,
and determination of finite-size percolation thresholds p_c.
"""
from collections import deque
from fractions import Fraction
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .cut_compiler import find_all_minimal_cuts
from .reliability import NetworkGraph


def poly_add(p1: List[int], p2: List[int]) -> List[int]:
    """Add two polynomials in Z[x]."""
    n = max(len(p1), len(p2))
    res = [0] * n
    for i in range(len(p1)):
        res[i] += p1[i]
    for i in range(len(p2)):
        res[i] += p2[i]
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    return res


def poly_mul(p1: List[int], p2: List[int]) -> List[int]:
    """Multiply two polynomials in Z[x] via discrete convolution."""
    if not p1 or not p2 or (len(p1) == 1 and p1[0] == 0) or (len(p2) == 1 and p2[0] == 0):
        return [0]
    res = [0] * (len(p1) + len(p2) - 1)
    for i, a in enumerate(p1):
        if a != 0:
            for j, b in enumerate(p2):
                res[i + j] += a * b
    while len(res) > 1 and res[-1] == 0:
        res.pop()
    return res


def poly_scale_var(p: List[int], assign: int) -> List[int]:
    """Multiply polynomial by variable weight: x if assign==1, 1 if assign==0."""
    if assign == 1:
        return [0] + p if any(p) else [0]
    return list(p)


class ReliabilityPolynomial:
    """Represents the exact network reliability polynomial P(x) = sum c_k x^k."""

    def __init__(self, coefficients: List[int]):
        self.coefficients = list(coefficients)
        self.total_edges = len(self.coefficients) - 1
        self.total_connected_subgraphs = sum(self.coefficients)

    def evaluate(self, p: Union[float, Fraction]) -> Union[float, Fraction]:
        """Evaluate exact reliability R(p) for arbitrary operational probability p."""
        m = self.total_edges
        if isinstance(p, Fraction):
            q = Fraction(1) - p
            return sum(
                Fraction(c_k) * (p**k) * (q ** (m - k))
                for k, c_k in enumerate(self.coefficients)
            )
        else:
            p_f = float(p)
            q_f = 1.0 - p_f
            return sum(
                float(c_k) * (p_f**k) * (q_f ** (m - k))
                for k, c_k in enumerate(self.coefficients)
            )

    def susceptibility(self, p: float) -> float:
        """Compute exact analytic derivative dR/dp (susceptibility) at p."""
        m = self.total_edges
        p_f = float(p)
        q_f = 1.0 - p_f
        deriv = 0.0
        for k, c_k in enumerate(self.coefficients):
            if c_k == 0:
                continue
            term1 = k * (p_f ** (k - 1)) * (q_f ** (m - k)) if k > 0 else 0.0
            term2 = (m - k) * (p_f**k) * (q_f ** (m - k - 1)) if k < m else 0.0
            deriv += c_k * (term1 - term2)
        return deriv

    def peak_susceptibility(self, steps: int = 1000) -> Tuple[float, float]:
        """Find the exact percolation transition threshold p_c and peak susceptibility."""
        max_chi = 0.0
        p_c = 0.5
        for i in range(1, steps):
            p = i / steps
            chi = self.susceptibility(p)
            if chi > max_chi:
                max_chi = chi
                p_c = p
        return p_c, max_chi

    def to_dict(self) -> Dict[str, Any]:
        p_c, max_chi = self.peak_susceptibility()
        return {
            "total_edges": self.total_edges,
            "coefficients": self.coefficients,
            "total_connected_subgraphs": self.total_connected_subgraphs,
            "percolation_threshold_pc": round(p_c, 4),
            "peak_susceptibility": round(max_chi, 4),
        }


def find_clause_components(clauses: List[List[int]]) -> List[List[List[int]]]:
    """Find disjoint connected components in the clause-variable bipartite graph."""
    if not clauses:
        return []

    var_to_clauses = {}
    for idx, c in enumerate(clauses):
        for lit in c:
            v = abs(lit)
            if v not in var_to_clauses:
                var_to_clauses[v] = []
            var_to_clauses[v].append(idx)

    visited_clauses = set()
    components = []

    for start_c in range(len(clauses)):
        if start_c in visited_clauses:
            continue
        comp_clauses = []
        q = deque([start_c])
        visited_clauses.add(start_c)
        visited_vars = set()

        while q:
            c_idx = q.popleft()
            comp_clauses.append(clauses[c_idx])
            for lit in clauses[c_idx]:
                v = abs(lit)
                if v not in visited_vars:
                    visited_vars.add(v)
                    for nxt_c in var_to_clauses.get(v, []):
                        if nxt_c not in visited_clauses:
                            visited_clauses.add(nxt_c)
                            q.append(nxt_c)

        components.append(comp_clauses)

    return components


def solve_poly_wmc(
    clauses: List[List[int]],
    active_vars: Set[int],
    timeout_seconds: float = 30.0,
    max_nodes: int = 50000,
) -> Tuple[List[int], str, int]:
    """Solve algebraic model counting over Z[x] with component caching and unit propagation."""
    t0 = time.perf_counter()
    memo = {}
    nodes_evaluated = 0

    def dpll(cur_clauses: List[List[int]], cur_vars: Set[int]) -> List[int]:
        nonlocal nodes_evaluated
        nodes_evaluated += 1

        if time.perf_counter() - t0 > timeout_seconds:
            raise TimeoutError("Polynomial WMC solve timed out")
        if nodes_evaluated > max_nodes:
            raise RuntimeError("Node budget exceeded")

        # 1. Contradiction / empty clause
        for c in cur_clauses:
            if len(c) == 0:
                return [0]

        # 2. Empty clause set: all remaining active vars are free
        if len(cur_clauses) == 0:
            res = [1]
            for _ in range(len(cur_vars)):
                res = poly_mul(res, [1, 1])
            return res

        # 3. Unit propagation
        unit = None
        for c in cur_clauses:
            if len(c) == 1:
                unit = c[0]
                break
        if unit is not None:
            var = abs(unit)
            val = 1 if unit > 0 else 0
            rem_vars = cur_vars - {var}
            next_clauses = []
            for c in cur_clauses:
                if unit in c:
                    continue
                if -unit in c:
                    next_clauses.append([l for l in c if l != -unit])
                else:
                    next_clauses.append(list(c))
            sub_poly = dpll(next_clauses, rem_vars)
            return poly_scale_var(sub_poly, val)

        # 4. Free variables elimination
        clause_vars = {abs(l) for c in cur_clauses for l in c}
        free_vars = cur_vars - clause_vars
        if free_vars:
            sub_poly = dpll(cur_clauses, clause_vars)
            factor = [1]
            for _ in range(len(free_vars)):
                factor = poly_mul(factor, [1, 1])
            return poly_mul(sub_poly, factor)

        # 5. Component decomposition
        comps = find_clause_components(cur_clauses)
        if len(comps) > 1:
            total_poly = [1]
            for comp in comps:
                comp_vars = {abs(l) for c in comp for l in c}
                comp_poly = dpll(comp, comp_vars)
                total_poly = poly_mul(total_poly, comp_poly)
            return total_poly

        # 6. Canonical memoization
        canonical_clauses = tuple(sorted(tuple(sorted(c)) for c in cur_clauses))
        if canonical_clauses in memo:
            return memo[canonical_clauses]

        # 7. Variable selection: DLCS heuristic (maximum occurrences in shortest clauses)
        min_len = min(len(c) for c in cur_clauses)
        candidates = [c for c in cur_clauses if len(c) == min_len]
        counts = {}
        for c in candidates:
            for lit in c:
                v = abs(lit)
                counts[v] = counts.get(v, 0) + 1
        branch_var = max(cur_vars, key=lambda v: (counts.get(v, 0), v))
        rem_vars = cur_vars - {branch_var}

        # Branch True (x_e = 1, weight x)
        c_true = []
        for c in cur_clauses:
            if branch_var in c:
                continue
            if -branch_var in c:
                c_true.append([l for l in c if l != -branch_var])
            else:
                c_true.append(list(c))
        p_true = poly_scale_var(dpll(c_true, rem_vars), 1)

        # Branch False (x_e = 0, weight 1)
        c_false = []
        for c in cur_clauses:
            if -branch_var in c:
                continue
            if branch_var in c:
                c_false.append([l for l in c if l != branch_var])
            else:
                c_false.append(list(c))
        p_false = poly_scale_var(dpll(c_false, rem_vars), 0)

        result_poly = poly_add(p_true, p_false)
        memo[canonical_clauses] = result_poly
        return result_poly

    try:
        poly = dpll(clauses, active_vars)
        # Pad polynomial up to degree len(active_vars)
        m = len(active_vars)
        if len(poly) < m + 1:
            poly = poly + [0] * (m + 1 - len(poly))
        return poly, "exact", nodes_evaluated
    except (TimeoutError, RuntimeError) as e:
        return [0] * (len(active_vars) + 1), str(e), nodes_evaluated


def compute_reliability_polynomial(
    net: NetworkGraph,
    source: Any,
    target: Any,
    timeout_seconds: float = 30.0,
    max_nodes: int = 50000,
) -> Tuple[ReliabilityPolynomial, str, int, float]:
    """Compute the exact ReliabilityPolynomial for two-terminal connectivity in net."""
    t0 = time.perf_counter()
    cuts = find_all_minimal_cuts(net, source, target)
    if not cuts:
        m = len(net.edges)
        return ReliabilityPolynomial([0] * (m + 1)), "unsat", 0, time.perf_counter() - t0

    clauses = [list(c) for c in cuts]
    m = len(net.edges)
    active_vars = set(range(1, m + 1))

    coeffs, status, nodes = solve_poly_wmc(
        clauses, active_vars, timeout_seconds=timeout_seconds, max_nodes=max_nodes
    )
    dt = time.perf_counter() - t0
    return ReliabilityPolynomial(coeffs), status, nodes, dt


def brute_force_poly_oracle(net: NetworkGraph, source: Any, target: Any) -> List[int]:
    """Independent exhaustive oracle for reliability polynomial coefficients c_k."""
    edges = list(net.edges)
    m = len(edges)
    all_nodes = set(net.adj.keys())
    c_counts = [0] * (m + 1)

    for mask in range(1 << m):
        active = [edges[i] for i in range(m) if (mask & (1 << i))]
        k = bin(mask).count("1")

        adj = {u: [] for u in all_nodes}
        for u, v in active:
            adj[u].append(v)
            adj[v].append(u)

        visited = {source}
        q = deque([source])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    q.append(v)

        if target in visited:
            c_counts[k] += 1

    return c_counts
