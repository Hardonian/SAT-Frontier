"""All-Pairs SLA Reliability Matrix, Topological Centrality, and Heatmap Generator.

Computes exact pairwise availability for all (u, v) in an enterprise network topology,
measures network diameter reliability, computes failure-aware node centrality,
and renders interactive terminal and markdown SLA compliance heatmaps.
"""
from dataclasses import dataclass
from fractions import Fraction
import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from .metrics import DowntimeMetrics, calculate_downtime_metrics
from .topology import EnterpriseTopology
from ..cut_compiler import find_all_minimal_cuts, to_cut_cnf
from ..wmc import WeightedFormula, wmc_solve


@dataclass
class AllPairsSlaResult:
    """Complete all-pairs SLA evaluation and topological resilience profile."""
    topology_name: str
    nodes: List[str]
    matrix: Dict[Tuple[str, str], Fraction]
    float_matrix: Dict[Tuple[str, str], float]
    diameter_reliability: Fraction
    diameter_pair: Tuple[str, str]
    average_availability: float
    node_centrality: Dict[str, float]
    vulnerable_pairs: List[Dict[str, Any]]
    total_pairs_evaluated: int
    elapsed_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topology_name": self.topology_name,
            "nodes_count": len(self.nodes),
            "nodes": self.nodes,
            "diameter_reliability": str(self.diameter_reliability),
            "diameter_reliability_float": float(self.diameter_reliability),
            "diameter_pair": list(self.diameter_pair),
            "average_availability": round(self.average_availability, 6),
            "node_centrality": {k: round(v, 6) for k, v in self.node_centrality.items()},
            "vulnerable_pairs": self.vulnerable_pairs,
            "total_pairs_evaluated": self.total_pairs_evaluated,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
        }


def compute_all_pairs_sla(
    topology: EnterpriseTopology,
    timeout_per_pair: float = 10.0,
    max_search_nodes: int = 100000,
) -> AllPairsSlaResult:
    """Compute exact all-pairs SLA availability across all node pairs in topology."""
    t_start = time.perf_counter()
    net, edge_attr_map = topology.to_network_graph()
    node_names = sorted(topology.node_to_id.keys(), key=str)
    n = len(node_names)

    matrix: Dict[Tuple[str, str], Fraction] = {}
    float_matrix: Dict[Tuple[str, str], float] = {}

    pairs_evaluated = 0
    worst_avail = Fraction(1, 1)
    worst_pair = (node_names[0], node_names[0]) if n > 0 else ("", "")

    # For undirected graphs, R(u, v) == R(v, u)
    for i in range(n):
        u_name = node_names[i]
        u_id = topology.node_to_id[u_name]
        matrix[(u_name, u_name)] = Fraction(1, 1)
        float_matrix[(u_name, u_name)] = 1.0

        for j in range(i + 1, n):
            v_name = node_names[j]
            v_id = topology.node_to_id[v_name]

            cuts = find_all_minimal_cuts(net, u_id, v_id)
            if not cuts:
                avail = Fraction(0, 1)
            else:
                wf = to_cut_cnf(net, u_id, v_id)
                res = wmc_solve(
                    wf,
                    algorithm="combined_wmc",
                    seconds=timeout_per_pair,
                    max_nodes=max_search_nodes,
                )
                avail = Fraction(res["weight_fraction"]) if res["status"] == "exact" else Fraction(0, 1)

            pairs_evaluated += 1
            matrix[(u_name, v_name)] = avail
            matrix[(v_name, u_name)] = avail
            float_val = float(avail)
            float_matrix[(u_name, v_name)] = float_val
            float_matrix[(v_name, u_name)] = float_val

            if avail < worst_avail:
                worst_avail = avail
                worst_pair = (u_name, v_name)

    # Compute node centrality: average availability to all other nodes
    node_centrality: Dict[str, float] = {}
    total_avail_sum = 0.0
    total_distinct_pairs = n * (n - 1) // 2 if n > 1 else 1

    for u_name in node_names:
        others_sum = sum(float_matrix[(u_name, v_name)] for v_name in node_names if v_name != u_name)
        node_centrality[u_name] = others_sum / (n - 1) if n > 1 else 1.0

    for i in range(n):
        for j in range(i + 1, n):
            total_avail_sum += float_matrix[(node_names[i], node_names[j])]

    avg_availability = total_avail_sum / total_distinct_pairs if n > 1 else 1.0

    # Rank most vulnerable pairs
    sorted_pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            u_name = node_names[i]
            v_name = node_names[j]
            avail = matrix[(u_name, v_name)]
            dt = calculate_downtime_metrics(avail)
            sorted_pairs.append({
                "source": u_name,
                "target": v_name,
                "availability": str(avail),
                "availability_float": float(avail),
                "n_nines": dt.n_nines,
                "downtime_hours_year": dt.downtime_hours_per_year,
                "downtime_minutes_year": dt.downtime_minutes_per_year,
            })

    sorted_pairs.sort(key=lambda x: x["availability_float"])

    elapsed = time.perf_counter() - t_start

    return AllPairsSlaResult(
        topology_name=topology.name,
        nodes=node_names,
        matrix=matrix,
        float_matrix=float_matrix,
        diameter_reliability=worst_avail,
        diameter_pair=worst_pair,
        average_availability=avg_availability,
        node_centrality=node_centrality,
        vulnerable_pairs=sorted_pairs,
        total_pairs_evaluated=pairs_evaluated,
        elapsed_seconds=elapsed,
    )


def render_terminal_heatmap(result: AllPairsSlaResult, col_width: int = 10) -> str:
    """Render an ASCII / ANSI formatted terminal heatmap table of the SLA matrix."""
    nodes = result.nodes
    lines = []
    lines.append("=" * 85)
    lines.append(f" SAT-Frontier All-Pairs SLA Availability Matrix & Resilience Profile")
    lines.append(f" System: {result.topology_name} ({len(nodes)} nodes, {result.total_pairs_evaluated} distinct pairs)")
    lines.append("=" * 85)

    # Truncate node names for compact column headers
    headers = [n[:col_width - 1].center(col_width) for n in nodes]
    row_hdr_width = max(len(n) for n in nodes) + 2
    row_hdr_width = max(row_hdr_width, 18)

    header_line = f"{'Node':<{row_hdr_width}}|" + "|".join(headers) + "|"
    lines.append(header_line)
    lines.append("-" * len(header_line))

    for u in nodes:
        cells = []
        for v in nodes:
            if u == v:
                cells.append("  --  ".center(col_width))
            else:
                p = result.float_matrix.get((u, v), 0.0)
                pct = p * 100.0
                if pct >= 99.9999:
                    s_pct = "99.9999%"
                elif pct >= 99.99:
                    s_pct = f"{pct:.4f}%"
                elif pct >= 99.0:
                    s_pct = f"{pct:.3f}%"
                else:
                    s_pct = f"{pct:.2f}%"
                cells.append(s_pct.center(col_width))
        lines.append(f"{u:<{row_hdr_width}}|" + "|".join(cells) + "|")

    lines.append("=" * 85)
    lines.append(f"Network Diameter Reliability : {float(result.diameter_reliability)*100:.6f}%")
    lines.append(f"Bottleneck SLA Pair          : {result.diameter_pair[0]} <---> {result.diameter_pair[1]}")
    lines.append(f"Mean Network Availability    : {result.average_availability*100:.6f}%")
    lines.append(f"All-Pairs Evaluation Latency : {result.elapsed_seconds*1000:.2f} ms")
    lines.append("-" * 85)
    lines.append("Top 3 Most Vulnerable SLA Pairs:")
    for idx, p in enumerate(result.vulnerable_pairs[:3], 1):
        lines.append(f"  #{idx} {p['source']} <--> {p['target']:<18} : {p['availability_float']*100:.6f}% ({p['n_nines']}, {p['downtime_minutes_year']:.2f} min/yr downtime)")
    lines.append("=" * 85)
    return "\n".join(lines)


def generate_all_pairs_markdown_report(result: AllPairsSlaResult) -> str:
    """Generate a GitHub-flavored Markdown audit report for all-pairs network resilience."""
    lines = [
        f"# All-Pairs SLA Availability Matrix & Vulnerability Audit",
        f"",
        f"**Topology**: `{result.topology_name}`  ",
        f"**Node Count**: {len(result.nodes)}  ",
        f"**Total Pairwise Paths**: {result.total_pairs_evaluated}  ",
        f"**Network Diameter Availability**: `{float(result.diameter_reliability)*100:.5f}%` (Worst-Case Pair: `{result.diameter_pair[0]}` $\\leftrightarrow$ `{result.diameter_pair[1]}`)  ",
        f"**Mean Network Availability**: `{result.average_availability*100:.5f}%`  ",
        f"**Audit Latency**: `{result.elapsed_seconds*1000:.2f} ms`  ",
        f"",
        f"---",
        f"",
        f"## 1. Top 5 Most Vulnerable SLA Pairs",
        f"",
        f"| Rank | Terminal Pair | Exact Availability | N-Nines SLA Tier | Annual Downtime |",
        f"| :---: | :--- | :--- | :--- | :--- |",
    ]
    for idx, p in enumerate(result.vulnerable_pairs[:5], 1):
        rel_pct = f"{p['availability_float']*100:.5f}%"
        lines.append(
            f"| **{idx}** | `{p['source']}` $\\leftrightarrow$ `{p['target']}` | `{rel_pct}` | {p['n_nines']} | {p['downtime_minutes_year']:.2f} min/yr ({p['downtime_hours_year']:.2f} hr/yr) |"
        )

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 2. Node Resilience Centrality Ranking",
        f"",
        f"Node centrality $C_R(v)$ measures the mean availability from node $v$ to all other nodes in the network:",
        f"",
        f"| Node Name | Mean Reachability $C_R(v)$ | Vulnerability Tier |",
        f"| :--- | :--- | :--- |",
    ])
    sorted_centrality = sorted(result.node_centrality.items(), key=lambda x: x[1])
    for name, c_val in sorted_centrality:
        c_pct = f"{c_val*100:.4f}%"
        tier = "Critical Vulnerability (<95%)" if c_val < 0.95 else ("Moderate Risk (<99%)" if c_val < 0.99 else "High Resilience (>=99%)")
        lines.append(f"| `{name}` | `{c_pct}` | {tier} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. Complete Pairwise Availability Matrix",
        f"",
    ])
    headers = ["Node"] + [f"`{n}`" for n in result.nodes]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join([":---"] * len(headers)) + " |")
    for u in result.nodes:
        row = [f"`{u}`"]
        for v in result.nodes:
            if u == v:
                row.append("--")
            else:
                p = result.float_matrix.get((u, v), 0.0)
                row.append(f"{p*100:.2f}%")
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines) + "\n"
