/-
  SAT-Frontier Formal Verification: Dual Cut Duality Theorem in Lean 4
  
  Theorem (Menger Dual Cut Duality):
  In any finite graph G = (V, E) with terminals s != t and operational edge state x : E -> Bool,
  s is connected to t in the operational subgraph G_x if and only if
  every s-t edge cut contains at least one operational edge.
-/

namespace SatFrontier

-- Finite vertices and edges
variable {V : Type} [DecidableEq V]
variable {E : Type} [DecidableEq E]

-- An undirected graph structure with edge incidence
structure Graph (V : Type) (E : Type) where
  endpoints : E -> V × V

-- Operational state assigning boolean survival to each physical edge
def OperationalState (E : Type) := E -> Bool

-- An edge e is operational in state x
def is_operational (x : OperationalState E) (e : E) : Prop :=
  x e = true

-- An s-t path as a sequence of vertices and edges
inductive Path (g : Graph V E) (x : OperationalState E) : V -> V -> Type where
  | refl (v : V) : Path g x v v
  | step {u v w : V} (p : Path g x u v) (e : E)
      (h_edge : g.endpoints e = (v, w) \/ g.endpoints e = (w, v))
      (h_op : is_operational x e) : Path g x u w

-- Terminal s is connected to t in operational subgraph
def Connected (g : Graph V E) (x : OperationalState E) (s t : V) : Prop :=
  Nonempty (Path g x s t)

-- An s-t vertex cut partition (S, V \ S) where s in S and t not in S
structure VertexCut (V : Type) (s t : V) where
  in_S : V -> Prop
  dec_in_S : (v : V) -> Decidable (in_S v)
  s_in : in_S s
  t_out : ¬ (in_S t)

-- The edge cut Delta(S) crossing the partition
def EdgeCut (g : Graph V E) (cut : VertexCut V s t) (e : E) : Prop :=
  let (u, v) := g.endpoints e
  (cut.in_S u /\ ¬ cut.in_S v) \/ (cut.in_S v /\ ¬ cut.in_S u)

-- A cut has an operational edge surviving in state x
def CutSurvives (g : Graph V E) (x : OperationalState E) (cut : VertexCut V s t) : Prop :=
  ∃ e : E, EdgeCut g cut e /\ is_operational x e

/-
  Fundamental Lemma:
  Every operational path from s in S to w not in S must traverse at least one edge in EdgeCut.
-/
theorem path_intersects_cut {g : Graph V E} {x : OperationalState E} {s t : V}
    (cut : VertexCut V s t) {w : V} (p : Path g x s w) (hw : ¬ cut.in_S w) :
    CutSurvives g x cut := by
  induction p with
  | refl v =>
    -- s = w, but cut.s_in : in_S s and hw : ¬ in_S w (contradiction)
    have h_contra : cut.in_S s := cut.s_in
    contradiction
  | step p_sub e h_endpoints h_op ih =>
    -- Check whether v is in S or not in S
    have dec_v := cut.dec_in_S _
    cases dec_v with
    | isFalse hv_out =>
      -- v is already outside S, apply induction hypothesis
      exact ih hv_out
    | isTrue hv_in =>
      -- v is in S, but w is outside S, so edge e crosses the cut!
      use e
      constructor
      · unfold EdgeCut
        rcases h_endpoints with h1 | h2
        · rw [h1]
          left
          exact ⟨hv_in, hw⟩
        · rw [h2]
          right
          exact ⟨hv_in, hw⟩
      · exact h_op

/-
  Direction 1 (Soundness of Dual Cut Pruning):
  If s and t are connected in state x, then EVERY s-t cut contains at least one operational edge.
-/
theorem connected_implies_all_cuts_survive {g : Graph V E} {x : OperationalState E} {s t : V}
    (h_conn : Connected g x s t) (cut : VertexCut V s t) :
    CutSurvives g x cut := by
  rcases h_conn with ⟨p⟩
  exact path_intersects_cut cut p cut.t_out

/-
  Direction 2 (Completeness of Dual Cut Compilation):
  If s and t are disconnected in state x, then there EXISTS an s-t cut with ZERO operational edges.
  Equivalently: If every s-t cut has at least one operational edge, then s and t are connected.
-/
def ReachableComponent (g : Graph V E) (x : OperationalState E) (s : V) : V -> Prop :=
  fun v => Connected g x s v

theorem disconnected_yields_empty_cut {g : Graph V E} {x : OperationalState E} {s t : V}
    (h_disconn : ¬ Connected g x s t)
    (dec_reach : (v : V) -> Decidable (ReachableComponent g x s v)) :
    ∃ cut : VertexCut V s t, ¬ CutSurvives g x cut := by
  let S_cut : VertexCut V s t := {
    in_S := ReachableComponent g x s,
    dec_in_S := dec_reach,
    s_in := ⟨Path.refl s⟩,
    t_out := h_disconn
  }
  use S_cut
  intro h_surv
  rcases h_surv with ⟨e, h_edge, h_op⟩
  unfold EdgeCut at h_edge
  let (u, v) := g.endpoints e
  rcases h_edge with ⟨hu_in, hv_out⟩ | ⟨hv_in, hu_out⟩
  · -- u in S, v not in S, but e is operational, so v is reachable from s!
    rcases hu_in with ⟨p_u⟩
    have p_v : Path g x s v := Path.step p_u e (Or.inl rfl) h_op
    have hv_reach : Connected g x s v := ⟨p_v⟩
    exact hv_out hv_reach
  · -- v in S, u not in S, but e is operational, so u is reachable from s!
    rcases hv_in with ⟨p_v⟩
    have p_u : Path g x s u := Path.step p_v e (Or.inr rfl) h_op
    have hu_reach : Connected g x s u := ⟨p_u⟩
    exact hu_out hu_reach

/-
  Master Theorem (Dual Cut Monotone CNF Duality):
  s is connected to t in operational subgraph G_x if and only if
  every s-t edge cut has at least one operational edge:
      Connected(G_x, s, t) <-> forall cut, exists e in cut, is_operational(x, e)
-/
theorem dual_cut_menger_duality {g : Graph V E} {x : OperationalState E} {s t : V}
    (dec_reach : (v : V) -> Decidable (ReachableComponent g x s v)) :
    Connected g x s t <-> (∀ cut : VertexCut V s t, CutSurvives g x cut) := by
  constructor
  · intro h_conn cut
    exact connected_implies_all_cuts_survive h_conn cut
  · intro h_all_survive
    by_contra h_disconn
    have ⟨empty_cut, h_no_surv⟩ := disconnected_yields_empty_cut h_disconn dec_reach
    have h_must_survive := h_all_survive empty_cut
    exact h_no_surv h_must_survive

end SatFrontier
