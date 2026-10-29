"""Enterprise reliability metrics, downtime quantification, and component criticality."""
from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Dict, List, Optional, Tuple


MINUTES_PER_YEAR = 525600.0
HOURS_PER_YEAR = 8760.0
SECONDS_PER_YEAR = 31536000.0


@dataclass
class DowntimeMetrics:
    availability: float
    unavailability: float
    availability_fraction: str
    downtime_minutes_per_year: float
    downtime_hours_per_year: float
    downtime_seconds_per_year: float
    downtime_minutes_per_month: float
    n_nines: str


@dataclass
class CutVulnerability:
    cut_edges: Tuple[int, ...]
    edge_names: List[str]
    order: int
    unavailability_probability: float
    unavailability_fraction: str
    is_single_point_of_failure: bool


@dataclass
class ComponentImportance:
    edge_id: int
    edge_label: str
    birnbaum_importance: float
    availability: float
    sensitivity_rank: int


def calculate_downtime_metrics(availability_fraction: Fraction) -> DowntimeMetrics:
    """Calculate exact SLA availability and annualized downtime metrics."""
    R_frac = availability_fraction
    Q_frac = Fraction(1) - R_frac
    R = float(R_frac)
    Q = float(Q_frac)

    # N-nines classification
    if R >= 0.999999:
        nines = "Six Nines (>= 99.9999%)"
    elif R >= 0.99999:
        nines = "Five Nines (>= 99.999%)"
    elif R >= 0.9999:
        nines = "Four Nines (>= 99.99%)"
    elif R >= 0.999:
        nines = "Three Nines (>= 99.9%)"
    elif R >= 0.99:
        nines = "Two Nines (>= 99.0%)"
    elif R >= 0.9:
        nines = "One Nine (>= 90.0%)"
    else:
        nines = "< 90% (Sub-Standard)"

    return DowntimeMetrics(
        availability=R,
        unavailability=Q,
        availability_fraction=str(R_frac),
        downtime_minutes_per_year=Q * MINUTES_PER_YEAR,
        downtime_hours_per_year=Q * HOURS_PER_YEAR,
        downtime_seconds_per_year=Q * SECONDS_PER_YEAR,
        downtime_minutes_per_month=(Q * MINUTES_PER_YEAR) / 12.0,
        n_nines=nines,
    )


def rank_cut_vulnerabilities(
    cuts: List[Tuple[int, ...]],
    edge_probs: Dict[int, Fraction],
    edge_labels: Optional[Dict[int, str]] = None,
    limit: int = 15,
) -> List[CutVulnerability]:
    """Rank minimal cuts by vulnerability (single points of failure first, then highest failure prob)."""
    vulns = []
    labels = edge_labels or {}

    for c in cuts:
        # Failure probability of this cut: all edges in the cut must fail simultaneously
        p_cut_fail = Fraction(1)
        for eid in c:
            p_edge = edge_probs[eid]
            p_cut_fail *= (Fraction(1) - p_edge)

        order = len(c)
        edge_names = [labels.get(eid, f"Edge_{eid}") for eid in c]
        vulns.append(
            CutVulnerability(
                cut_edges=c,
                edge_names=edge_names,
                order=order,
                unavailability_probability=float(p_cut_fail),
                unavailability_fraction=str(p_cut_fail),
                is_single_point_of_failure=(order == 1),
            )
        )

    # Sort: single points of failure first (smallest order), then highest failure probability descending
    vulns.sort(key=lambda v: (v.order, -v.unavailability_probability))
    return vulns[:limit]


def compute_birnbaum_importance(
    eval_func,
    all_edge_ids: List[int],
    edge_probs: Dict[int, Fraction],
    edge_labels: Optional[Dict[int, str]] = None,
) -> List[ComponentImportance]:
    """Compute exact Birnbaum importance measure I_B(e) = R(p_e=1) - R(p_e=0).

    eval_func: Callable[[Dict[int, Fraction]], Fraction] evaluating system reliability given edge probs.
    """
    labels = edge_labels or {}
    importances = []

    for eid in all_edge_ids:
        # Evaluate with e forced operational (p_e = 1)
        probs_up = dict(edge_probs)
        probs_up[eid] = Fraction(1)
        r_up = eval_func(probs_up)

        # Evaluate with e forced failed (p_e = 0)
        probs_down = dict(edge_probs)
        probs_down[eid] = Fraction(0)
        r_down = eval_func(probs_down)

        i_b = float(r_up - r_down)
        importances.append(
            ComponentImportance(
                edge_id=eid,
                edge_label=labels.get(eid, f"Link_{eid}"),
                birnbaum_importance=max(0.0, i_b),
                availability=float(edge_probs[eid]),
                sensitivity_rank=0,  # to be assigned
            )
        )

    # Sort descending by Birnbaum importance
    importances.sort(key=lambda ci: -ci.birnbaum_importance)
    for rank, ci in enumerate(importances, 1):
        ci.sensitivity_rank = rank

    return importances
