"""High-Level Enterprise Reliability Engine for SLA audit and network resilience analysis."""
from dataclasses import dataclass
from fractions import Fraction
import time
from typing import Any, Dict, List, Optional, Tuple, Union

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
from ..dicut_compiler import DirectedNetworkGraph, find_all_minimal_dicuts, to_dicut_cnf
from ..k_cut_compiler import find_all_minimal_k_cuts, to_k_cut_cnf
from ..poly_wmc import ReliabilityPolynomial, solve_poly_wmc
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

    def audit_multi_terminal(
        self,
        terminals: List[Union[int, str]],
        timeout_seconds: float = 30.0,
        max_search_nodes: int = 200000,
        compute_sensitivity: bool = True,
    ) -> EnterpriseAuditResult:
        """Run an exhaustive SLA reliability and vulnerability audit across multi-terminal set K."""
        t_start = time.perf_counter()

        term_ids = []
        for term in terminals:
            tid = self.topology.node_to_id.get(term)
            if tid is None:
                raise ValueError(f"Terminal '{term}' not found in topology.")
            term_ids.append(tid)

        if len(term_ids) < 2:
            raise ValueError("Multi-terminal audit requires at least 2 terminals.")

        # 1. Dual K-Cut Compilation
        t0 = time.perf_counter()
        cuts = find_all_minimal_k_cuts(self.net, term_ids)
        wf = to_k_cut_cnf(self.net, term_ids)
        t_compilation = time.perf_counter() - t0

        # 2. Exact #WMC Solving
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
            source_terminal=f"K_terminals[{','.join(str(t) for t in terminals[:3])}{'...' if len(terminals)>3 else ''}]",
            target_terminal="mutual_connectivity",
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

    def audit_parametric_curve(
        self,
        source: Union[int, str],
        target: Union[int, str],
        timeout_seconds: float = 30.0,
        max_search_nodes: int = 100000,
    ) -> Dict[str, Any]:
        """Compute closed-form reliability polynomial over Z[x] and percolation phase transition."""
        t_start = time.perf_counter()
        s_id = self.topology.node_to_id.get(source)
        t_id = self.topology.node_to_id.get(target)
        if s_id is None:
            raise ValueError(f"Source terminal '{source}' not found in topology.")
        if t_id is None:
            raise ValueError(f"Target terminal '{target}' not found in topology.")

        cuts = find_all_minimal_cuts(self.net, s_id, t_id)
        if not cuts:
            return {
                "status": "unsat",
                "coefficients": [0] * (len(self.net.edges) + 1),
                "percolation_threshold_pc": 0.0,
                "peak_susceptibility": 0.0,
                "evaluations": {},
                "elapsed_seconds": time.perf_counter() - t_start,
            }

        clauses = [list(c) for c in cuts]
        active_vars = set(range(1, len(self.net.edges) + 1))
        coeffs, status, nodes = solve_poly_wmc(
            clauses, active_vars, timeout_seconds=timeout_seconds, max_nodes=max_search_nodes
        )
        poly = ReliabilityPolynomial(coeffs)
        p_c, max_chi = poly.peak_susceptibility()

        evals = {
            "p=0.90": poly.evaluate(0.90),
            "p=0.95": poly.evaluate(0.95),
            "p=0.99": poly.evaluate(0.99),
            "p=0.999": poly.evaluate(0.999),
        }

        return {
            "status": status,
            "coefficients": coeffs,
            "total_edges": poly.total_edges,
            "total_connected_subgraphs": poly.total_connected_subgraphs,
            "percolation_threshold_pc": round(p_c, 4),
            "peak_susceptibility": round(max_chi, 4),
            "evaluations": evals,
            "search_nodes": nodes,
            "elapsed_seconds": time.perf_counter() - t_start,
        }

    @staticmethod
    def audit_directed_network(
        dnet: DirectedNetworkGraph,
        source: Any,
        target: Any,
        timeout_seconds: float = 30.0,
        max_search_nodes: int = 100000,
    ) -> Dict[str, Any]:
        """Audit directed two-terminal reachability via dual dicut compilation."""
        t_start = time.perf_counter()
        cuts = find_all_minimal_dicuts(dnet, source, target)
        wf = to_dicut_cnf(dnet, source, target)
        comp_s = time.perf_counter() - t_start

        t0 = time.perf_counter()
        res = wmc_solve(
            wf,
            algorithm="combined_wmc",
            seconds=timeout_seconds,
            max_nodes=max_search_nodes,
        )
        solv_s = time.perf_counter() - t0

        avail_frac = Fraction(res["weight_fraction"]) if res["status"] == "exact" else Fraction(0)
        downtime = calculate_downtime_metrics(avail_frac)

        return {
            "status": res["status"],
            "source": str(source),
            "target": str(target),
            "availability_fraction": str(avail_frac),
            "availability_float": float(avail_frac),
            "metrics": downtime,
            "minimal_dicuts_count": len(cuts),
            "search_nodes": res["nodes"],
            "compilation_seconds": comp_s,
            "solving_seconds": solv_s,
            "total_seconds": time.perf_counter() - t_start,
        }

    def audit_all_pairs(
        self,
        timeout_per_pair: float = 10.0,
        max_search_nodes: int = 100000,
    ):
        """Compute complete pairwise availability matrix, diameter SLA, and node centrality."""
        from .all_pairs import compute_all_pairs_sla
        return compute_all_pairs_sla(
            self.topology,
            timeout_per_pair=timeout_per_pair,
            max_search_nodes=max_search_nodes,
        )

    @staticmethod
    def audit_srrg_reliability(
        srrg_net: Any,
        source: int,
        target: int,
    ) -> Dict[str, Any]:
        """Audit network reliability under Shared-Risk Resource Groups (SRRG / Fate-Sharing)."""
        from sat_frontier.srrg_compiler import find_minimal_srrg_cuts, solve_srrg_reliability
        t_start = time.perf_counter()
        cuts = find_minimal_srrg_cuts(srrg_net, source, target)
        rel_frac, nodes, solve_time = solve_srrg_reliability(srrg_net, source, target)
        metrics = calculate_downtime_metrics(rel_frac)
        return {
            "status": "exact",
            "source": source,
            "target": target,
            "availability_fraction": str(rel_frac),
            "availability_float": float(rel_frac),
            "metrics": metrics,
            "srrg_cuts_count": len(cuts),
            "search_nodes": nodes,
            "solve_time_seconds": solve_time,
            "total_seconds": time.perf_counter() - t_start,
        }


