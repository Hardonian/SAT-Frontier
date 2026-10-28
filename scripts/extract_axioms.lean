import Lean

open Lean

def main : IO Unit := do
  IO.println "=== SAT-Frontier Formal Theorem Axiom Inspection ==="
  let targets := [
    `OAI.Algorithms.SubexponentialSAT.SqrtLogSpace.compiled_exact_count_and_sat,
    `OAI.Algorithms.SubexponentialSAT.SqrtLogSpace.exact_count_and_sat,
    `OAI.Algorithms.SubexponentialSAT.SqrtLogSpace.exact_count_eth,
    `OAI.Algorithms.SubexponentialSAT.SqrtLogSpace.sat_polynomial_space,
    `OAI.Algorithms.SubexponentialSAT.SqrtLogSpace.original_sat_main
  ]
  for target in targets do
    IO.println s!"Inspecting axioms for: {target}"
