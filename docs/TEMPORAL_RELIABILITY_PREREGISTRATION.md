# Preregistration: Hypothesis H15 — Continuous Temporal Network Reliability & Exact Closed-Form MTTF via Algebraic Polynomial Integration over $\mathbb{Z}[x]$

## 1. Background & Scientific Motivation
In aerospace (FAA/DO-178C, NASA), telecommunications (Telcordia SR-332), power grids (IEEE 1366), and mission-critical cloud computing, infrastructure availability is fundamentally time-dependent. Operators require continuous lifetime metrics over decades of service:
- Continuous availability function $R(t) = \mathbb{P}(\text{system operational at time } t)$.
- Mean Time To Failure: $\text{MTTF} = \mathbb{E}[T] = \int_0^\infty R(t) \, dt$.
- Variance and standard deviation of lifetime $\operatorname{Var}(T)$.
- Quantile metrics such as $B_{10}$ lifetime (the operational time until $10\%$ of systems experience failure).

Prior to this work, evaluating exact continuous MTTF on arbitrary meshed networks required either:
1. Monte Carlo lifetime simulation with high variance and intractable sample requirements for high-nines components;
2. Numerical integration of black-box state probabilities; or
3. Approximations limited to simple series-parallel graphs.

## 2. Hypothesis Formulation
**Hypothesis H15**:
Algebraic model counting over $\mathbb{Z}[x]$ evaluates exact closed-form reliability polynomials whose algebraic integration yields exact rational Mean Time To Failure (MTTF), failure variance, and $B_{10}$ lifetimes in a single search pass without numerical simulation:
$$\text{MTTF} = \sum_{j=1}^m \frac{a_j}{j \lambda}$$
where $a_j \in \mathbb{Z}$ are standard monomial coefficients of the exact reliability polynomial $P(x) = \sum_{j=1}^m a_j x^j$.

**Falsification Criteria**:
1. Any relative discrepancy greater than $10^{-4}$ between the closed-form algebraic MTTF and an independent composite numerical quadrature oracle (Simpson's composite rule).
2. Failure to compute exact rational MTTF and variance across cyclic meshes, ladders, barbells, and planar grids in sub-3-second CPU latency.

## 3. Mathematical Theorem & Proof

### Theorem (Exact Algebraic MTTF Integration)
Let $G = (V, E)$ be a network where components experience exponential failure with hazard rate $\lambda > 0$. Let $P(x) = \sum_{k=0}^m c_k x^k (1 - x)^{m - k}$ be the exact reliability polynomial evaluated over survivability parameter $x \in [0, 1]$.
Expanding $P(x)$ into standard monomial basis:
$$P(x) = \sum_{j=1}^m a_j x^j, \quad a_j \in \mathbb{Z}$$
where:
$$a_j = \sum_{k=0}^j c_k \binom{m - k}{j - k} (-1)^{j - k}$$
Then:
1. The exact continuous network reliability function is:
   $$R(t) = \sum_{j=1}^m a_j e^{-j \lambda t}$$
2. The exact Mean Time To Failure is:
   $$\text{MTTF} = \int_0^\infty R(t) \, dt = \sum_{j=1}^m \frac{a_j}{j \lambda}$$
3. The exact second raw failure moment is:
   $$\mathbb{E}[T^2] = 2 \int_0^\infty t R(t) \, dt = 2 \sum_{j=1}^m \frac{a_j}{(j \lambda)^2}$$
4. The exact failure variance is:
   $$\operatorname{Var}(T) = \mathbb{E}[T^2] - (\text{MTTF})^2$$

*Proof*:
At time $t \ge 0$, independent component survival is $x(t) = e^{-\lambda t}$. By the definition of the reliability polynomial, $R(t) = P(x(t)) = \sum_{j=1}^m a_j (e^{-\lambda t})^j = \sum_{j=1}^m a_j e^{-j \lambda t}$.
Since $j \ge 1$ and $\lambda > 0$, each term $e^{-j \lambda t}$ is Lebesgue-integrable on $[0, \infty)$.
By linearity of the integral:
$$\int_0^\infty R(t) \, dt = \sum_{j=1}^m a_j \int_0^\infty e^{-j \lambda t} \, dt = \sum_{j=1}^m a_j \left[ -\frac{e^{-j \lambda t}}{j \lambda} \right]_0^\infty = \sum_{j=1}^m \frac{a_j}{j \lambda}$$
Similarly, integrating by parts for $\mathbb{E}[T^2] = \int_0^\infty 2t R(t) \, dt$:
$$\int_0^\infty t e^{-j \lambda t} \, dt = \frac{1}{(j \lambda)^2} \int_0^\infty u e^{-u} \, du = \frac{1}{(j \lambda)^2} \Gamma(2) = \frac{1}{(j \lambda)^2}$$
Multiplying by 2 gives $\mathbb{E}[T^2] = 2 \sum_{j=1}^m \frac{a_j}{(j \lambda)^2}$. The variance follows by definition. $\blacksquare$

