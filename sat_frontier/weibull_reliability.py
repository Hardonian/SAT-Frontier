"""Weibull Aging, Fatigue, and Wear-Out Network Reliability Engine.

Hypothesis H19 (Theorem 11):
Exact Algebraic Weibull MTTF Integration over Z[x] evaluates closed-form continuous
Mean Time To Failure (MTTF), raw lifetime moments, and quantile B-life metrics
under aging and wear-out hazard rates (Weibull shape parameter beta > 0)
without Monte Carlo simulation.

Theorem 11 (Generalized Weibull MTTF Integration):
Let G = (V, E) be a network whose physical components experience Weibull aging
with scale parameter lambda > 0 and shape parameter beta > 0.
The individual edge survivability function is:
    R_e(t) = exp(-(lambda * t)^beta).
Let P(x) = sum_{j=1}^m a_j x^j in Z[x] be the standard monomial expansion of the
exact network reliability polynomial evaluated via Algebraic Dual Cut WMC over Z[x].
The continuous network reliability function is:
    R(t) = sum_{j=1}^m a_j exp(-j * (lambda * t)^beta).
The exact r-th raw failure moment is:
    E[T^r] = int_0^infty r * t^{r-1} * R(t) dt
           = frac{Gamma(1 + r / beta)}{lambda^r} * sum_{j=1}^m frac{a_j}{j^{r / beta}}.
In particular, the Mean Time To Failure (r = 1) is:
    MTTF_Weibull = frac{Gamma(1 + 1 / beta)}{lambda} * sum_{j=1}^m frac{a_j}{j^{1 / beta}}.
The failure variance is:
    Var(T) = E[T^2] - (MTTF_Weibull)^2.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, NamedTuple, Tuple

from sat_frontier.poly_wmc import ReliabilityPolynomial, compute_reliability_polynomial
from sat_frontier.temporal_reliability import polynomial_to_monomial_basis


class WeibullReliabilityResult(NamedTuple):
    """Complete Weibull aging and wear-out reliability audit metrics."""
    mttf_hours: float
    variance_hours2: float
    std_dev_hours: float
    b10_life_hours: float
    b1_life_hours: float
    beta_shape: float
    lambda_scale_per_hour: float
    gamma_factor: float
    monomial_coefficients: Dict[int, int]
    polynomial: ReliabilityPolynomial


def compute_weibull_mttf(
    poly: ReliabilityPolynomial,
    beta: float,
    lambda_per_hour: float,
) -> Tuple[float, float]:
    """Compute (MTTF, Var(T)) under Weibull wear-out hazard (shape beta, scale lambda).

    Uses exact monomial summation scaled by Gamma(1 + 1/beta) and Gamma(1 + 2/beta).
    """
    if beta <= 0:
        raise ValueError(f"Weibull shape beta must be strictly positive, got {beta}")
    if lambda_per_hour <= 0:
        raise ValueError(f"Weibull scale lambda must be strictly positive, got {lambda_per_hour}")

    monomials = polynomial_to_monomial_basis(poly)

    # Gamma factors: Gamma(1 + 1/beta) and Gamma(1 + 2/beta)
    gamma_1 = math.gamma(1.0 + 1.0 / beta)
    gamma_2 = math.gamma(1.0 + 2.0 / beta)

    # MTTF = (Gamma(1 + 1/beta) / lambda) * sum_{j=1}^m (a_j / j^{1/beta})
    sum_1 = 0.0
    for j, a_j in monomials.items():
        sum_1 += float(a_j) / (float(j) ** (1.0 / beta))
    mttf = (gamma_1 / lambda_per_hour) * sum_1

    # E[T^2] = (Gamma(1 + 2/beta) / lambda^2) * sum_{j=1}^m (a_j / j^{2/beta})
    sum_2 = 0.0
    for j, a_j in monomials.items():
        sum_2 += float(a_j) / (float(j) ** (2.0 / beta))
    e_t2 = (gamma_2 / (lambda_per_hour ** 2)) * sum_2

    variance = max(0.0, e_t2 - (mttf ** 2))
    return mttf, variance


def compute_weibull_b_life(
    poly: ReliabilityPolynomial,
    beta: float,
    lambda_per_hour: float,
    target_unreliability: float = 0.10,
) -> float:
    """Compute B-life (time until unreliability reaches target_unreliability, e.g. B10 -> 0.10).

    Inverts P(x) = 1 - target_unreliability on [0, 1] via bisection, then applies:
        t = (-ln(x))^{1/beta} / lambda.
    """
    target_r = 1.0 - target_unreliability
    low = 0.0
    high = 1.0

    # P(0) = 0, P(1) = 1 for any coherent network
    for _ in range(64):
        mid = (low + high) / 2.0
        r_mid = poly.evaluate(mid)
        if r_mid < target_r:
            low = mid
        else:
            high = mid

    x_star = (low + high) / 2.0
    if x_star >= 1.0:
        return 0.0
    if x_star <= 0.0:
        return float("inf")

    # t = (-ln(x))^{1/beta} / lambda
    return ((-math.log(x_star)) ** (1.0 / beta)) / lambda_per_hour


def audit_weibull_reliability(
    topology: Any,
    source: int = 1,
    target: int = 2,
    beta: float = 2.0,
    lambda_per_hour: float = 1e-4,
) -> WeibullReliabilityResult:
    """Full Weibull reliability audit of network topology between source and target."""
    poly, _, _, _ = compute_reliability_polynomial(topology, source, target)
    monomials = polynomial_to_monomial_basis(poly)
    mttf, var = compute_weibull_mttf(poly, beta, lambda_per_hour)
    std_dev = math.sqrt(var)
    b10 = compute_weibull_b_life(poly, beta, lambda_per_hour, 0.10)
    b1 = compute_weibull_b_life(poly, beta, lambda_per_hour, 0.01)

    return WeibullReliabilityResult(
        mttf_hours=mttf,
        variance_hours2=var,
        std_dev_hours=std_dev,
        b10_life_hours=b10,
        b1_life_hours=b1,
        beta_shape=beta,
        lambda_scale_per_hour=lambda_per_hour,
        gamma_factor=math.gamma(1.0 + 1.0 / beta),
        monomial_coefficients=monomials,
        polynomial=poly,
    )


def weibull_quadrature_oracle(
    poly: ReliabilityPolynomial,
    beta: float,
    lambda_per_hour: float,
    n_steps: int = 20_000,
) -> float:
    """Independent composite Simpson rule numerical quadrature oracle for Weibull MTTF."""
    # Find t_max where R(t_max) < 1e-9
    # For a single edge, R(t) = exp(-(lambda*t)^beta) = 1e-9 => (lambda*t)^beta = 9*ln(10)
    t_max = ((9.0 * math.log(10.0)) ** (1.0 / beta)) / lambda_per_hour * 2.0

    if n_steps % 2 != 0:
        n_steps += 1
    h = t_max / n_steps

    def r_eval(t: float) -> float:
        if t <= 0.0:
            return 1.0
        arg = (lambda_per_hour * t) ** beta
        if arg > 700.0:
            return 0.0
        x = math.exp(-arg)
        return poly.evaluate(x)

    integral = r_eval(0.0) + r_eval(t_max)
    for i in range(1, n_steps):
        weight = 4.0 if i % 2 == 1 else 2.0
        integral += weight * r_eval(i * h)

    return (h / 3.0) * integral
