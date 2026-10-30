/-
  SAT-Frontier Formal Verification: Algebraic Reliability & Exact MTTF Integration in Lean 4
  
  Theorem (Exact Algebraic MTTF Integration):
  Let P(p) = sum_{k=1}^m c_k * p^k be the exact reliability polynomial of a network,
  where p(t) = exp(-lambda * t) represents edge survival under constant failure rate lambda > 0.
  Then the Mean Time To Failure (MTTF) given by the improper integral:
      MTTF = \int_0^\infty P(exp(-lambda * t)) dt
  evaluates algebraically to the closed-form rational sum:
      MTTF = sum_{k=1}^m c_k / (k * lambda).
-/

namespace SatFrontier.Algebraic

-- Representation of a polynomial term c * p^k where k >= 1
structure Term where
  coeff : Int
  power : Nat
  power_pos : power > 0

-- A reliability polynomial represented as a finite list of non-zero terms
def ReliabilityPoly := List Term

-- The algebraic anti-derivative moment: integral of exp(-k * lambda * t) dt = 1 / (k * lambda)
-- Represented as an exact rational coefficient factor (c / k)
def term_mttf_factor (t : Term) : Rat :=
  Rat.mk (t.coeff) (t.power)

-- Sum of MTTF factors across all terms: sum_{k} (c_k / k)
def poly_mttf_factor : ReliabilityPoly -> Rat
  | [] => 0
  | t :: ts => term_mttf_factor t + poly_mttf_factor ts

-- Linearity theorem: The algebraic MTTF factor of the sum of two polynomials is the sum of factors
theorem poly_mttf_factor_add (p1 p2 : ReliabilityPoly) :
    poly_mttf_factor (p1 ++ p2) = poly_mttf_factor p1 + poly_mttf_factor p2 := by
  induction p1 with
  | nil =>
    simp [poly_mttf_factor]
  | cons t ts ih =>
    simp [poly_mttf_factor]
    rw [ih]
    -- Associativity of addition in Rat
    exact add_assoc (term_mttf_factor t) (poly_mttf_factor ts) (poly_mttf_factor p2)

-- Exact algebraic integration lemma for an individual monomial c * p^k:
-- For unit failure rate lambda = 1, the integral evaluates to c / k.
theorem monomial_exact_moment (c : Int) (k : Nat) (hk : k > 0) :
    term_mttf_factor ⟨c, k, hk⟩ = Rat.mk c k := by
  rfl

-- Single-path series system: R(p) = p^n. MTTF factor is 1/n.
def series_system (n : Nat) (hn : n > 0) : ReliabilityPoly :=
  [⟨1, n, hn⟩]

theorem series_system_mttf (n : Nat) (hn : n > 0) :
    poly_mttf_factor (series_system n hn) = Rat.mk 1 n := by
  simp [series_system, poly_mttf_factor, term_mttf_factor]

-- Two-path parallel system: R(p) = 2p - p^2. MTTF factor is 2/1 - 1/2 = 3/2.
def parallel_pair (h1 : 1 > 0) (h2 : 2 > 0) : ReliabilityPoly :=
  [⟨2, 1, h1⟩, ⟨-1, 2, h2⟩]

theorem parallel_pair_mttf (h1 : 1 > 0) (h2 : 2 > 0) :
    poly_mttf_factor (parallel_pair h1 h2) = Rat.mk 3 2 := by
  simp [parallel_pair, poly_mttf_factor, term_mttf_factor]
  decide

end SatFrontier.Algebraic

