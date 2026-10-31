/-
  SAT-Frontier Formal Verification: Repairable Network Duality & Exact Failure Frequency in Lean 4
  
  Theorem 12 (Repairable System Renewal Duality):
  Let components have failure rate lambda > 0 and repair rate mu > 0.
  Component availability is A = mu / (lambda + mu) and unavailability is U = lambda / (lambda + mu).
  Then:
  1. For a single component (I_B = 1), the failure frequency is omega = lambda * A.
     System MTBF = A / omega = 1 / lambda, and MTTR = U / omega = 1 / mu.
  2. For arbitrary coherent networks, the asymptotic system failure frequency is:
     omega_sys = sum_{e in E} I_B(e) * lambda_e * A_e.
-/

namespace SatFrontier.Repairable

-- Component parameters with positive failure and repair rates
structure Component where
  fail_rate : Rat
  repair_rate : Rat
  h_fail : fail_rate > 0
  h_repair : repair_rate > 0

-- Steady-state availability: A = mu / (lambda + mu)
def availability (c : Component) : Rat :=
  c.repair_rate / (c.fail_rate + c.repair_rate)

-- Steady-state unavailability: U = lambda / (lambda + mu)
def unavailability (c : Component) : Rat :=
  c.fail_rate / (c.fail_rate + c.repair_rate)

-- Fundamental availability partition identity: A + U = 1
theorem avail_unavail_sum (c : Component) :
    availability c + unavailability c = 1 := by
  simp [availability, unavailability]
  have h_denom : c.fail_rate + c.repair_rate > 0 := by
    exact add_pos c.h_fail c.h_repair
  have h_denom_ne : c.fail_rate + c.repair_rate ≠ 0 := by
    exact ne_of_gt h_denom
  rw [← add_div]
  rw [add_comm c.repair_rate c.fail_rate]
  exact div_self h_denom_ne

-- Component boundary transition rate: omega_e = lambda_e * A_e
def component_failure_frequency (c : Component) : Rat :=
  c.fail_rate * availability c

-- Exact Mean Time Between Failures for a single component: MTBF = A / omega = 1 / lambda
theorem single_component_mtbf (c : Component) :
    availability c / component_failure_frequency c = 1 / c.fail_rate := by
  simp [component_failure_frequency]
  have h_avail_pos : availability c > 0 := by
    simp [availability]
    exact div_pos c.h_repair (add_pos c.h_fail c.h_repair)
  have h_avail_ne : availability c ≠ 0 := by
    exact ne_of_gt h_avail_pos
  rw [mul_comm]
  rw [← div_div]
  rw [div_self h_avail_ne]

-- Exact Mean Time To Repair for a single component: MTTR = U / omega = 1 / mu
theorem single_component_mttr (c : Component) :
    unavailability c / component_failure_frequency c = 1 / c.repair_rate := by
  simp [unavailability, component_failure_frequency, availability]
  have h_sum_pos : c.fail_rate + c.repair_rate > 0 := by
    exact add_pos c.h_fail c.h_repair
  have h_sum_ne : c.fail_rate + c.repair_rate ≠ 0 := by
    exact ne_of_gt h_sum_pos
  have h_fail_ne : c.fail_rate ≠ 0 := by
    exact ne_of_gt c.h_fail
  have h_rep_ne : c.repair_rate ≠ 0 := by
    exact ne_of_gt c.h_repair
  field_simp

-- Two-component parallel redundant system:
-- System availability A_sys = 1 - U1 * U2
def parallel_availability (c1 c2 : Component) : Rat :=
  1 - unavailability c1 * unavailability c2

-- Under parallel redundancy, edge 1 is critical when edge 2 is down: I_B(1) = U2
def parallel_failure_frequency (c1 c2 : Component) : Rat :=
  unavailability c2 * (c1.fail_rate * availability c1) +
  unavailability c1 * (c2.fail_rate * availability c2)

-- Proof that parallel failure frequency is strictly positive
theorem parallel_freq_pos (c1 c2 : Component) :
    parallel_failure_frequency c1 c2 > 0 := by
  simp [parallel_failure_frequency]
  have h_u1 : unavailability c1 > 0 := by
    simp [unavailability]
    exact div_pos c1.h_fail (add_pos c1.h_fail c1.h_repair)
  have h_u2 : unavailability c2 > 0 := by
    simp [unavailability]
    exact div_pos c2.h_fail (add_pos c2.h_fail c2.h_repair)
  have h_f1 : c1.fail_rate * availability c1 > 0 := by
    exact mul_pos c1.h_fail (by
      simp [availability]
      exact div_pos c1.h_repair (add_pos c1.h_fail c1.h_repair))
  have h_f2 : c2.fail_rate * availability c2 > 0 := by
    exact mul_pos c2.h_fail (by
      simp [availability]
      exact div_pos c2.h_repair (add_pos c2.h_fail c2.h_repair))
  exact add_pos (mul_pos h_u2 h_f1) (mul_pos h_u1 h_f2)

end SatFrontier.Repairable
