# Preregistration: Hypothesis H19 — Continuous Weibull Aging & Wear-Out Reliability via Generalized Algebraic MTTF Integration

## 1. Background & Scientific Motivation

In mission-critical infrastructure, components rarely exhibit memoryless exponential failure rates throughout their operational lifecycle. Under mechanical stress, thermal cycling, and chemical degradation (e.g. undersea fiber optic repeaters, turbine blades, high-voltage transformers, and satellite solar arrays), physical failure rates increase over time due to wear-out and fatigue.

Such systems are rigorously modeled by the **Weibull distribution** with shape parameter $\beta > 0$ and scale parameter $\lambda > 0$:

$$h(t) = \beta \lambda (\lambda t)^{\beta - 1} \implies R_e(t) = \exp\left(-(\lambda t)^\beta\right)$$

- For $\beta = 1$: Constant failure rate (memoryless exponential baseline).
- For $\beta > 1$: Increasing failure rate (wear-out, fatigue, mechanical aging). Specifically, $\beta = 2$ corresponds to the Rayleigh linear wear-out distribution.
- For $\beta < 1$: Decreasing failure rate (early-life infant mortality).

Prior to this work, evaluating exact continuous MTTF on arbitrary meshed networks under non-exponential aging distributions was deemed intractable without extensive Monte Carlo lifetime simulations or discretization approximations.

## 2. Hypothesis Formulation

**Hypothesis H19**:
Algebraic model counting over $\mathbb{Z}[x]$ evaluates exact closed-form reliability polynomials whose algebraic integration under Weibull aging evaluates closed-form continuous Mean Time To Failure (MTTF), raw lifetime moments, and quantile $B_{10}$ lifetimes without Monte Carlo simulation:

$$\text{MTTF}_{\text{Weibull}} = \frac{\Gamma(1 + 1/\beta)}{\lambda} \sum_{j=1}^m \frac{a_j}{j^{1/\beta}}$$

where $a_j \in \mathbb{Z}$ are standard monomial coefficients of the exact reliability polynomial $P(x) = \sum_{j=1}^m a_j x^j$.

**Falsification Criteria**:

1. Any relative discrepancy greater than $10^{-4}$ between the closed-form algebraic Weibull MTTF and an independent composite numerical quadrature oracle (Simpson's composite rule).
2. Failure to compute closed-form MTTF and variance across cyclic meshes, ladders, barbells, and planar grids in sub-1-second CPU latency.

## 3. Mathematical Theorem & Proof

### Theorem 11 (Generalized Weibull MTTF Integration)

Let $G = (V, E)$ be a coherent network whose physical components experience Weibull aging with scale parameter $\lambda > 0$ and shape parameter $\beta > 0$.
The component survivability function is:

$$R_e(t) = \exp\left(-(\lambda t)^\beta\right)$$

Let $P(x) = \sum_{j=1}^m a_j x^j \in \mathbb{Z}[x]$ be the standard monomial expansion of the exact network reliability polynomial evaluated via Algebraic Dual Cut WMC over $\mathbb{Z}[x]$.
Then:

1. The continuous network reliability function is:

   $$R(t) = \sum_{j=1}^m a_j \exp\left(-j (\lambda t)^\beta\right)$$

2. The exact $r$-th raw failure moment is:

   $$\mathbb{E}[T^r] = \frac{\Gamma(1 + r/\beta)}{\lambda^r} \sum_{j=1}^m \frac{a_j}{j^{r/\beta}}$$

3. In particular, the Mean Time To Failure ($r = 1$) is:

   $$\text{MTTF}_{\text{Weibull}} = \frac{\Gamma(1 + 1/\beta)}{\lambda} \sum_{j=1}^m \frac{a_j}{j^{1/\beta}}$$

4. The exact failure variance is:

   $$\operatorname{Var}(T) = \mathbb{E}[T^2] - (\text{MTTF}_{\text{Weibull}})^2$$

*Proof*:
At operational time $t \ge 0$, component survival is $x(t) = \exp(-(\lambda t)^\beta)$. By definition of the reliability polynomial:

$$R(t) = P(x(t)) = \sum_{j=1}^m a_j (x(t))^j = \sum_{j=1}^m a_j \exp\left(-j (\lambda t)^\beta\right)$$

The $r$-th raw lifetime moment is defined by:

$$\mathbb{E}[T^r] = \int_0^\infty r t^{r-1} R(t) \, dt = \sum_{j=1}^m a_j \int_0^\infty r t^{r-1} \exp\left(-j (\lambda t)^\beta\right) \, dt$$

Apply substitution $u = j (\lambda t)^\beta$. Then $t = \frac{u^{1/\beta}}{j^{1/\beta} \lambda}$ and $dt = \frac{1}{\beta j^{1/\beta} \lambda} u^{1/\beta - 1} \, du$.
Substituting into the integral:

$$\int_0^\infty r t^{r-1} \exp\left(-j (\lambda t)^\beta\right) \, dt = \int_0^\infty r \left( \frac{u^{1/\beta}}{j^{1/\beta} \lambda} \right)^{r-1} e^{-u} \frac{1}{\beta j^{1/\beta} \lambda} u^{1/\beta - 1} \, du$$

$$= \frac{r}{\beta \lambda^r j^{r/\beta}} \int_0^\infty u^{(r-1)/\beta + 1/\beta - 1} e^{-u} \, du = \frac{r}{\beta \lambda^r j^{r/\beta}} \int_0^\infty u^{r/\beta - 1} e^{-u} \, du$$

$$= \frac{r}{\beta \lambda^r j^{r/\beta}} \Gamma(r/\beta) = \frac{\frac{r}{\beta} \Gamma(r/\beta)}{\lambda^r j^{r/\beta}} = \frac{\Gamma(1 + r/\beta)}{\lambda^r j^{r/\beta}}$$

Summing across all terms $j = 1, \dots, m$ yields:

$$\mathbb{E}[T^r] = \frac{\Gamma(1 + r/\beta)}{\lambda^r} \sum_{j=1}^m \frac{a_j}{j^{r/\beta}}$$

Setting $r = 1$ gives $\text{MTTF}_{\text{Weibull}} = \frac{\Gamma(1 + 1/\beta)}{\lambda} \sum_{j=1}^m \frac{a_j}{j^{1/\beta}}$.
Setting $r = 2$ gives $\mathbb{E}[T^2] = \frac{\Gamma(1 + 2/\beta)}{\lambda^2} \sum_{j=1}^m \frac{a_j}{j^{2/\beta}}$.
The variance follows by $\operatorname{Var}(T) = \mathbb{E}[T^2] - (\mathbb{E}[T])^2$. $\blacksquare$

## 4. Benchmark Topologies & Evaluation Suite

The empirical evaluation executes 24 benchmark instances spanning diverse topological families and aging regimes:

1. **Serial & Parallel Backbones**: Single-path, two-channel, quad-channel paths.
2. **Meshes & Bridges**: Wheatstone bridge, diamond meshes, complete $K_4$ backbones.
3. **Planar Grids**: $2 \times 3$, $2 \times 4$, $3 \times 3$ grids.
4. **Aging Parameter Gradients**: Shape parameter $\beta \in \{1.0, 1.5, 2.0, 2.5, 3.0\}$.
5. **Independent Oracle Checks**: Composite Simpson rule numerical quadrature with 20,000 subintervals across all 24 instances.

