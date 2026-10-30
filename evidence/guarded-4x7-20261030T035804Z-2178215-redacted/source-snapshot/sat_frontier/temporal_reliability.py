"""Continuous Temporal Network Reliability and Exact Closed-Form MTTF Engine.

Hypothesis H15:
Algebraic Polynomial Integration over Z[x] evaluates exact continuous Mean Time
To Failure (MTTF), higher failure moments, hazard rates, and B10 lifetime metrics
in closed form without numerical simulation.

Theorem (Exact Algebraic MTTF Integration):
Let G = (V, E) be a network where components experience exponential failure with
hazard rate lambda > 0 (MTBF = 1 / lambda).
Let P(x) = sum_{k=0}^m c_k x^k (1 - x)^{m - k} be the exact network reliability
polynomial evaluated over survivability parameter x in [0, 1].
Expanding P(x) into its standard monomial basis:
    P(x) = sum_{j=1}^m a_j x^j,   where a_j in Z.
At operational time t >= 0, component survivability is x(t) = exp(-lambda * t).
The continuous time-dependent network reliability function is:
    R(t) = sum_{j=1}^m a_j exp(-j * lambda * t).
The exact Mean Time To Failure (MTTF) is the continuous integral of R(t):
    MTTF = int_0^infty R(t) dt = sum_{j=1}^m frac{a_j}{j * lambda}.
The second raw failure moment is:
    E[T^2] = 2 * sum_{j=1}^m frac{a_j}{(j * lambda)^2}.
The exact failure variance is:
    Var(T) = E[T^2] - (MTTF)^2.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Callable, Dict, List, NamedTuple, Tuple

from sat_frontier.poly_wmc import ReliabilityPolynomial, compute_reliability_polynomial


class TemporalReliabilityResult(NamedTuple):
    """Complete continuous temporal reliability and lifetime audit metrics."""
    mttf_exact: Fraction
    mttf_hours: float
    variance_exact: Fraction
    variance_hours2: float
    std_dev_hours: float
    b10_life_hours: float
    b1_life_hours: float
    lambda_per_hour: float
    monomial_coefficients: Dict[int, int]
    polynomial: ReliabilityPolynomial


def polynomial_to_monomial_basis(poly: ReliabilityPolynomial) -> Dict[int, int]:
    """Convert Bernstein-like reliability coefficients c_k into standard monomial basis sum a_j x^j.

    P(x) = sum_{k=0}^m c_k x^k (1 - x)^{m - k}
         = sum_{k=0}^m c_k x^k sum_{i=0}^{m-k} binom(m-k, i) (-1)^i x^i
         = sum_{j=0}^m [ sum_{k=0}^j c_k binom(m-k, j-k) (-1)^{j-k} ] x^j
    """
    m = poly.total_edges
    c = poly.coefficients
    a: Dict[int, int] = {}

    for j in range(1, m + 1):
        coeff_j = 0
        for k in range(j + 1):
            if k < len(c) and c[k] != 0:
                comb = math.comb(m - k, j - k)
                sign = (-1) ** (j - k)
                coeff_j += c[k] * comb * sign
        if coeff_j != 0:
            a[j] = coeff_j

    return a


def compute_exact_mttf(
    poly: ReliabilityPolynomial,
    hazard_rate_per_hour: float,
) -> Tuple[Fraction, Fraction]:
    """Compute exact rational (MTTF, Var(T)) from reliability polynomial.

    Returns:
        (mttf_exact, variance_exact) scaled by 1/lambda and 1/lambda^2.
    """
    monomials = polynomial_to_monomial_basis(poly)
    lambda_frac = Fraction(hazard_rate_per_hour).limit_denominator(1_000_000)

    # MTTF = sum_{j=1}^m a_j / (j * lambda)
    mttf_norm = Fraction(0, 1)
    for j, a_j in monomials.items():
        mttf_norm += Fraction(a_j, j)

    mttf = mttf_norm / lambda_frac

    # E[T^2] = 2 * sum_{j=1}^m a_j / (j^2 * lambda^2)
    e_t2_norm = Fraction(0, 1)
    for j, a_j in monomials.items():
        e_t2_norm += Fraction(2 * a_j, j * j)

    e_t2 = e_t2_norm / (lambda_frac * lambda_frac)
    variance = e_t2 - (mttf * mttf)

    return mttf, variance


def compute_quantile_life(
    poly: ReliabilityPolynomial,
    hazard_rate_per_hour: float,
    target_unreliability: float = 0.10,
) -> float:
    """Find the exact operational time t such that 1 - R(t) = target_unreliability (e.g. B10 life).

    Solves P(x) = 1 - target_unreliability for x in (0, 1) via Newton-Raphson, then t = -ln(x) / lambda.
    """
    target_r = 1.0 - target_unreliability
    # Newton-Raphson on f(x) = P(x) - target_r = 0
    x = 0.95
    for _ in range(50):
        val = float(poly.evaluate(x)) - target_r
        dval = poly.susceptibility(x)
        if abs(dval) < 1e-14:
            break
        dx = val / dval
        x = x - dx
        x = max(1e-12, min(1.0 - 1e-12, x))
        if abs(dx) < 1e-12:
            break

    if x <= 0.0 or x >= 1.0:
        return 0.0

    return -math.log(x) / hazard_rate_per_hour


def evaluate_temporal_reliability(
    net: Any,
    s: int,
    t: int,
    hazard_rate_per_hour: float = 1e-5,  # e.g. 1 failure per 100,000 hours (~11.4 years MTBF)
) -> TemporalReliabilityResult:
    """Evaluate complete continuous temporal reliability metrics for network net between s and t."""
    poly, status, nodes, solve_time = compute_reliability_polynomial(net, s, t)
    monomials = polynomial_to_monomial_basis(poly)

    mttf_exact, var_exact = compute_exact_mttf(poly, hazard_rate_per_hour)
    mttf_h = float(mttf_exact)
    var_h2 = float(var_exact)
    std_dev_h = math.sqrt(max(0.0, var_h2))

    b10_h = compute_quantile_life(poly, hazard_rate_per_hour, 0.10)
    b1_h = compute_quantile_life(poly, hazard_rate_per_hour, 0.01)

    return TemporalReliabilityResult(
        mttf_exact=mttf_exact,
        mttf_hours=mttf_h,
        variance_exact=var_exact,
        variance_hours2=var_h2,
        std_dev_hours=std_dev_h,
        b10_life_hours=b10_h,
        b1_life_hours=b1_h,
        lambda_per_hour=hazard_rate_per_hour,
        monomial_coefficients=monomials,
        polynomial=poly,
    )


def numerical_quadrature_mttf_oracle(
    poly: ReliabilityPolynomial,
    hazard_rate_per_hour: float,
    t_max_factor: float = 20.0,
    steps: int = 20000,
) -> float:
    """Independent numerical quadrature oracle computing MTTF via Simpson's composite rule.

    Used to cross-verify the algebraic integration theorem.
    """
    # Rough estimate of upper limit of integration
    t_max = t_max_factor / hazard_rate_per_hour
    h = t_max / steps

    def r_of_t(t_val: float) -> float:
        x_val = math.exp(-hazard_rate_per_hour * t_val)
        return poly.evaluate(x_val)

    # Simpson's composite rule: (h/3) * (f0 + 4f1 + 2f2 + 4f3 + ... + fn)
    integral = r_of_t(0.0) + r_of_t(t_max)
    for i in range(1, steps):
        t_i = i * h
        weight = 4.0 if i % 2 == 1 else 2.0
        integral += weight * r_of_t(t_i)

    return (h / 3.0) * integral
