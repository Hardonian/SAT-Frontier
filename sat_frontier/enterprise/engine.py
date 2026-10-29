"""High-Level Enterprise Reliability Engine for SLA audit and network resilience analysis."""
from dataclasses import dataclass
from fractions import Fraction
import time
from typing import Dict, List, Optional, Tuple, Union

from .metrics import (
    ComponentImportance,
    CutVulnerability,
    DowntimeMetrics,
    calculate_downtime_metrics,
    compute_birnbaum_importance,
    rank_cut_vulnerabilities,
)
from .topology import EnterpriseTopology
from ..cut_compiler import find_all_minimal_cuts, to_cut_cnf
from ..wmc import WeightedFormula, wmc_solve


@dataclass
class EnterpriseAuditResult:
    topology_name: str
    source_terminal: str
    target_terminal: str
    status: str
    availability_fraction: Fraction
    metrics: DowntimeMetrics
    minimal_cuts_count: int
    single_points_of_failure: List[CutVulnerability]
    top_vulnerabilities: List[CutVulnerability]
    component_criticality: List[ComponentImportance]
    compilation_seconds: float
    solving_seconds: float
    total_seconds: float
    search_nodes: int


class EnterpriseReliabilityEngine:
    """Production reliability quantification engine for mission-critical enterprise systems."""

    def __init__(self, topology: EnterpriseTopology):
        self.topology = topology
        self.net, self.edge_attr_map = topology.to_network_graph()

    def audit_terminal_pair(
        self,
        source: Union[int, str],
        target: Union[int, str],
        timeout_seconds: float = 30.0,
        max_search_nodes: int = 200000,
        compute_sensitivity: bool = True,
    ) -> EnterpriseAuditResult:
        """Run an exhaustive SLA reliability and vulnerability audit between two terminals."""
        t_start = time.perf_counter()

        s_id = self.topology.node_to_id.get(source)
        t_id = self.topology.node_to_id.get(target)
        if s_id is None:
            raise ValueError(f"Source terminal '{source}' not found in topology.")
        if t_id is None:
            raise ValueError(f"Target terminal '{target}' not found in topology.")

        # 1. Compile Dual Cut CNF
        t0 = time.perf_counter()
        cuts = find_all_minimal_cuts(self.net, s_id, t_id)
        wf = to_cut_cnf(self.net, s_id, t_id)
        t_compilation = time.perf_counter() - t0

        # 2. Solve Exact Reliability
        t0 = time.perf_counter()
        res = wmc_solve(
            wf,
            algorithm="combined_wmc",
            seconds=timeout_seconds,
            max_nodes=max_search_nodes,
        )
        t_solving = time.perf_counter() - t0

        if res["status"] != "exact":
            raise RuntimeError(f"Solver failed to achieve exact count: {res['status']}")

        avail_frac = Fraction(res["weight_fraction"])
        downtime = calculate_downtime_metrics(avail_frac)

        # 3. Cut Vulnerability Analysis
        edge_labels = {
            eid: f"{attr.u}<->{attr.v}" for eid, attr in self.edge_attr_map.items()
        }
        all_vulns = rank_cut_vulnerabilities(
            cuts,
            edge_probs=self.net.edge_probs,
            edge_labels=edge_labels,
            limit=20,
        )
        spofs = [v for v in all_vulns if v.is_single_point_of_failure]

        # 4. Component Sensitivity (Birnbaum Importance)
        criticality = []
        if compute_sensitivity:
            def fast_eval(probs_dict: Dict[int, Fraction]) -> Fraction:
                w_dict = {}
                for e, p in probs_dict.items():
                    w_dict[e] = p
                    w_dict[-e] = Fraction(1) - p
                wf_temp = WeightedFormula(
                    wf.clauses, n_vars=wf.n_vars, weights=w_dict
                )
                r_temp = wmc_solve(
                    wf_temp,
                    algorithm="combined_wmc",
                    seconds=5.0,
                    max_nodes=max_search_nodes,
                )
                return (
                    Fraction(r_temp["weight_fraction"])
                    if r_temp["status"] == "exact"
                    else Fraction(0)
                )

            all_edge_ids = list(range(1, len(self.net.edges) + 1))
            criticality = compute_birnbaum_importance(
                eval_func=fast_eval,
                all_edge_ids=all_edge_ids,
                edge_probs=self.net.edge_probs,
                edge_labels=edge_labels,
            )

        t_total = time.perf_counter() - t_start

        return EnterpriseAuditResult(
            topology_name=self.topology.name,
            source_terminal=str(source),
            target_terminal=str(target),
            status=res["status"],
            availability_fraction=avail_frac,
            metrics=downtime,
            minimal_cuts_count=len(cuts),
            single_points_of_failure=spofs,
            top_vulnerabilities=all_vulns,
            component_criticality=criticality,
            compilation_seconds=t_compilation,
            solving_seconds=t_solving,
            total_seconds=t_total,
            search_nodes=res["nodes"],
        )

