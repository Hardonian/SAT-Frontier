"""Repairable Systems Network Reliability & Exact Failure Frequency Engine.

Hypothesis H20 (Theorem 12):
Exact Markov Renewal Duality evaluates the asymptotic network failure frequency,
steady-state availability, MTBF, and MTTR of complex repairable networks in
exact rational arithmetic (Q) via Birnbaum sensitivity index contraction:
    omega_sys = sum_{e in E} I_B(e) * lambda_e * A_e
    MTBF_sys = A_sys / omega_sys
    MTTR_sys = (1 - A_sys) / omega_sys.

Theorem 12 (Repairable System Renewal Duality):
Let G = (V, E) be a network where physical edges alternate between operational
and failed states under constant failure rates lambda_e > 0 and repair rates mu_e > 0.
The operational availability of edge e is A_e = mu_e / (lambda_e + mu_e) in Q.
Let R(p) be the multilinear network reliability polynomial.
Then:
1. The steady-state network availability is A_sys = R(A_1, ..., A_m) in Q.
2. The exact asymptotic network failure frequency (expected system failures per unit time) is:
       omega_sys = sum_{e in E} frac{partial R}{partial p_e}(A) * lambda_e * A_e in Q.
3. The exact system Mean Time Between Failures is:
       MTBF_sys = A_sys / omega_sys in Q.
4. The exact system Mean Time To Repair is:
       MTTR_sys = (1 - A_sys) / omega_sys in Q.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, NamedTuple, Tuple

from sat_frontier.cut_compiler import to_cut_cnf
from sat_frontier.wmc import WeightedFormula, wmc_solve


class RepairableAuditResult(NamedTuple):
    """Complete repairable network audit metrics in exact rational arithmetic."""
    availability_exact: Fraction
    unavailability_exact: Fraction
    failure_frequency_exact: Fraction
    mtbf_hours_exact: Fraction
    mttr_hours_exact: Fraction
    availability_float: float
    mtbf_hours_float: float
    mttr_hours_float: float
    nines: float
    birnbaum_criticalities: Dict[Tuple[int, int], Fraction]
    cuts_count: int


def audit_repairable_network(
    net: Any,
    source: Any,
    target: Any,
    failure_rates: Dict[Tuple[int, int], Fraction],
    repair_rates: Dict[Tuple[int, int], Fraction],
) -> RepairableAuditResult:
    """Evaluate exact repairable network metrics (A_sys, omega_sys, MTBF, MTTR) via Birnbaum contraction."""
    edges = list(net.edges)
    edge_avail: Dict[Tuple[int, int], Fraction] = {}
    edge_lambda: Dict[Tuple[int, int], Fraction] = {}

    for u, v in edges:
        e = (u, v) if (u, v) in failure_rates else (v, u)
        lam = failure_rates.get(e, Fraction(1, 10000))
        mu = repair_rates.get(e, Fraction(1, 10))  # default 10-hour MTTR
        avail = mu / (lam + mu)
        edge_avail[(u, v)] = avail
        edge_lambda[(u, v)] = lam

    # Compile Dual Cut CNF
    wf = to_cut_cnf(net, source, target)
    m = len(edges)

    # Base availability weights
    base_weights: Dict[int, Fraction] = {}
    for idx, (u, v) in enumerate(edges, start=1):
        p = edge_avail[(u, v)]
        base_weights[idx] = p
        base_weights[-idx] = Fraction(1) - p

    wf_base = WeightedFormula(wf.clauses, n_vars=m, weights=base_weights)
    res_base = wmc_solve(wf_base, algorithm="combined")
    a_sys = Fraction(res_base["weight_fraction"])

    # Compute Birnbaum index for each edge: I_B(e) = R(1_e) - R(0_e)
    # Using unit propagation on cut clauses:
    # Setting edge e to 1 eliminates clauses containing x_e.
    # Setting edge e to 0 simplifies clauses containing x_e.
    birnbaum: Dict[Tuple[int, int], Fraction] = {}
    omega_sys = Fraction(0, 1)

    for idx, (u, v) in enumerate(edges, start=1):
        # R(1_e): e is guaranteed operational (weight 1 = 1, weight -1 = 0)
        w_pos = dict(base_weights)
        w_pos[idx] = Fraction(1)
        w_pos[-idx] = Fraction(0)
        wf_pos = WeightedFormula(wf.clauses, n_vars=m, weights=w_pos)
        r_pos = Fraction(wmc_solve(wf_pos, algorithm="combined")["weight_fraction"])

        # R(0_e): e is guaranteed failed (weight 1 = 0, weight -1 = 1)
        w_neg = dict(base_weights)
        w_neg[idx] = Fraction(0)
        w_neg[-idx] = Fraction(1)
        wf_neg = WeightedFormula(wf.clauses, n_vars=m, weights=w_neg)
        r_neg = Fraction(wmc_solve(wf_neg, algorithm="combined")["weight_fraction"])

        i_b = r_pos - r_neg
        birnbaum[(u, v)] = i_b

        # Contribution to failure frequency: I_B(e) * lambda_e * A_e
        omega_sys += i_b * edge_lambda[(u, v)] * edge_avail[(u, v)]

    u_sys = Fraction(1) - a_sys
    mtbf = (a_sys / omega_sys) if omega_sys > 0 else Fraction(10**12, 1)
    mttr = (u_sys / omega_sys) if omega_sys > 0 else Fraction(0, 1)

    # N-nines availability
    import math
    u_float = float(u_sys)
    nines = -math.log10(u_float) if u_float > 0 else 12.0

    return RepairableAuditResult(
        availability_exact=a_sys,
        unavailability_exact=u_sys,
        failure_frequency_exact=omega_sys,
        mtbf_hours_exact=mtbf,
        mttr_hours_exact=mttr,
        availability_float=float(a_sys),
        mtbf_hours_float=float(mtbf),
        mttr_hours_float=float(mttr),
        nines=round(nines, 4),
        birnbaum_criticalities=birnbaum,
        cuts_count=len(wf.clauses),
    )


def brute_force_repairable_oracle(
    net: Any,
    source: Any,
    target: Any,
    failure_rates: Dict[Tuple[int, int], Fraction],
    repair_rates: Dict[Tuple[int, int], Fraction],
) -> Tuple[Fraction, Fraction, Fraction, Fraction]:
    """Exhaustive truth-table oracle verifying A_sys, omega_sys, MTBF, MTTR over 2^|E| states."""
    edges = list(net.edges)
    m = len(edges)
    if m > 16:
        raise ValueError(f"Oracle limit exceeded: {m} > 16")

    edge_avail: List[Fraction] = []
    edge_lam: List[Fraction] = []
    for u, v in edges:
        e = (u, v) if (u, v) in failure_rates else (v, u)
        lam = failure_rates.get(e, Fraction(1, 10000))
        mu = repair_rates.get(e, Fraction(1, 10))
        edge_avail.append(mu / (lam + mu))
        edge_lam.append(lam)

    # Determine connectivity for each state mask
    from collections import deque
    def is_connected(mask: int) -> bool:
        visited = {source}
        queue = deque([source])
        while queue:
            curr = queue.popleft()
            if curr == target:
                return True
            for i, (u, v) in enumerate(edges):
                if (mask & (1 << i)):
                    nbr = v if u == curr else (u if v == curr else None)
                    if nbr is not None and nbr not in visited:
                        visited.add(nbr)
                        queue.append(nbr)
        return False

    state_up = [is_connected(mask) for mask in range(1 << m)]

    a_sys = Fraction(0, 1)
    omega_sys = Fraction(0, 1)

    for mask in range(1 << m):
        # State steady-state probability pi(mask)
        p_state = Fraction(1, 1)
        for i in range(m):
            if mask & (1 << i):
                p_state *= edge_avail[i]
            else:
                p_state *= (Fraction(1) - edge_avail[i])

        if state_up[mask]:
            a_sys += p_state
            # Check edge transitions causing system failure
            for i in range(m):
                if mask & (1 << i):
                    mask_fail = mask ^ (1 << i)
                    if not state_up[mask_fail]:
                        omega_sys += p_state * edge_lam[i]

    u_sys = Fraction(1) - a_sys
    mtbf = (a_sys / omega_sys) if omega_sys > 0 else Fraction(10**12, 1)
    mttr = (u_sys / omega_sys) if omega_sys > 0 else Fraction(0, 1)

    return a_sys, omega_sys, mtbf, mttr

