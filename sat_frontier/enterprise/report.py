"""Executive and technical compliance report generators for enterprise SLA audits."""
import json
from .engine import EnterpriseAuditResult


def generate_markdown_audit_report(result: EnterpriseAuditResult) -> str:
    """Generate publication-ready executive Markdown compliance audit report."""
    m = result.metrics

    lines = [
        f"# Infrastructure Reliability & SLA Compliance Audit Report",
        f"",
        f"**System**: `{result.topology_name}`  ",
        f"**Terminal Pair**: `{result.source_terminal}` $\\longleftrightarrow$ `{result.target_terminal}`  ",
        f"**Audit Status**: **{result.status.upper()} (Exact Closed-Form Solution)**  ",
        f"**Solver Technology**: SAT-Frontier Dual Cut Compilation & Weighted Model Counting  ",
        f"",
        f"---",
        f"",
        f"## 1. Executive Summary & SLA Metrics",
        f"",
        f"| Metric | Exact Value | Description |",
        f"| :--- | :--- | :--- |",
        f"| **Availability ($R$)** | **`{m.availability * 100:.6f}%`** | Steady-state operational probability |",
        f"| **Unavailability ($Q$)** | **`{m.unavailability * 100:.6f}%`** | Failure probability ($1 - R$) |",
        f"| **Exact Rational Fraction** | `{result.availability_fraction}` | Exact mathematical reliability |",
        f"| **SLA Classification** | **{m.n_nines}** | Industry standard classification |",
        f"| **Annual Downtime** | **`{m.downtime_minutes_per_year:.2f} minutes`** (`{m.downtime_hours_per_year:.2f} hours`) | Expected outage duration per year |",
        f"| **Monthly Downtime** | **`{m.downtime_minutes_per_month:.2f} minutes`** | Expected outage duration per month |",
        f"",
        f"---",
        f"",
        f"## 2. Infrastructure Vulnerability & Single Points of Failure",
        f"",
        f"- **Total Inclusion-Minimal Cuts**: `{result.minimal_cuts_count}`  ",
        f"- **Single Points of Failure (SPOFs)**: **`{len(result.single_points_of_failure)}`**  ",
        f"",
    ]

    if result.single_points_of_failure:
        lines.append(f"> [!CAUTION]")
        lines.append(f"> **Critical Warning**: {len(result.single_points_of_failure)} Single Point(s) of Failure detected! A single component outage will sever terminal connectivity.")
        lines.append(f"")
        lines.append(f"| SPOF Cut | Disconnected Edges | Failure Probability |")
        lines.append(f"| :--- | :--- | :--- |")
        for spof in result.single_points_of_failure:
            lines.append(f"| Cut {spof.cut_edges} | `{' , '.join(spof.edge_names)}` | `{spof.unavailability_probability:.6e}` |")
        lines.append(f"")
    else:
        lines.append(f"> [!TIP]")
        lines.append(f"> **Resilient Design**: Zero Single Points of Failure detected. All minimal cuts require $\\ge 2$ simultaneous link failures.")
        lines.append(f"")

    lines.extend([
        f"### Top Critical Cut Vulnerabilities",
        f"",
        f"| Cut Order | Vulnerable Components | Failure Probability | Mode |",
        f"| :--- | :--- | :--- | :--- |",
    ])
    for v in result.top_vulnerabilities[:10]:
        mode_str = "Single Point of Failure" if v.is_single_point_of_failure else f"{v.order}-Link Cut"
        lines.append(f"| {v.order} | `{' + '.join(v.edge_names)}` | `{v.unavailability_probability:.6e}` | {mode_str} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. Component Criticality & Sensitivity Ranking (Birnbaum Index)",
        f"",
        f"The Birnbaum Importance Index $I_B(e) = \\frac{{\\partial R}}{{\\partial p_e}}$ measures the marginal improvement in overall system availability gained by reinforcing each individual link.",
        f"",
        f"| Rank | Component Link | Component Availability | Birnbaum Criticality Index | Upgrade Priority |",
        f"| :--- | :--- | :--- | :--- | :--- |",
    ])

    for ci in result.component_criticality[:10]:
        priority = "CRITICAL" if ci.birnbaum_importance > 0.1 else ("HIGH" if ci.birnbaum_importance > 0.01 else "MODERATE")
        lines.append(f"| #{ci.sensitivity_rank} | `{ci.edge_label}` | `{ci.availability * 100:.2f}%` | **`{ci.birnbaum_importance:.6f}`** | {priority} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 4. Computational Performance & Audit Provenance",
        f"",
        f"- **Dual Cut Compilation Time**: `{result.compilation_seconds * 1000:.2f} ms`",
        f"- **Exact WMC Solving Time**: `{result.solving_seconds * 1000:.2f} ms`",
        f"- **Total Audit Latency**: `{result.total_seconds * 1000:.2f} ms`",
        f"- **Search Tree Explored**: `{result.search_nodes:,} nodes`",
        f"",
        f"*Audited by SAT-Frontier Enterprise Engine v0.2.3. Zero Monte Carlo sampling or approximation error.*",
    ])

    return "\n".join(lines) + "\n"


def generate_json_audit_summary(result: EnterpriseAuditResult) -> str:
    """Generate clean machine-readable JSON summary for CI/CD integration."""
    m = result.metrics
    data = {
        "system": result.topology_name,
        "terminals": {
            "source": result.source_terminal,
            "target": result.target_terminal,
        },
        "status": result.status,
        "availability": {
            "fraction": str(result.availability_fraction),
            "percentage": m.availability * 100.0,
            "n_nines": m.n_nines,
            "downtime_minutes_per_year": m.downtime_minutes_per_year,
            "downtime_hours_per_year": m.downtime_hours_per_year,
        },
        "vulnerabilities": {
            "total_minimal_cuts": result.minimal_cuts_count,
            "single_points_of_failure_count": len(result.single_points_of_failure),
            "single_points_of_failure": [
                {"cut": v.cut_edges, "edges": v.edge_names, "probability": v.unavailability_probability}
                for v in result.single_points_of_failure
            ],
            "top_cuts": [
                {"order": v.order, "edges": v.edge_names, "probability": v.unavailability_probability}
                for v in result.top_vulnerabilities[:10]
            ],
        },
        "component_criticality": [
            {
                "rank": ci.sensitivity_rank,
                "label": ci.edge_label,
                "birnbaum_index": ci.birnbaum_importance,
                "availability": ci.availability,
            }
            for ci in result.component_criticality[:10]
        ],
        "performance": {
            "compilation_seconds": result.compilation_seconds,
            "solving_seconds": result.solving_seconds,
            "total_seconds": result.total_seconds,
            "search_nodes": result.search_nodes,
        },
    }
    return json.dumps(data, indent=2) + "\n"
