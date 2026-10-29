"""Production CLI for SAT-Frontier Enterprise Reliability & SLA Compliance Audit."""
import argparse
import json
import sys
from pathlib import Path

from .engine import EnterpriseReliabilityEngine
from .report import generate_json_audit_summary, generate_markdown_audit_report
from .topology import EnterpriseTopology


def main():
    parser = argparse.ArgumentParser(
        description="SAT-Frontier Enterprise: SLA Reliability & Vulnerability Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m sat_frontier.enterprise.cli --topology network.json --source VPC_East --target VPC_West
  python -m sat_frontier.enterprise.cli --demo-cloud --out-report cloud_audit.md --out-json cloud_audit.json
        """,
    )
    parser.add_argument("--topology", help="Path to JSON network topology file")
    parser.add_argument("--source", help="Source terminal name or node ID")
    parser.add_argument("--target", help="Target terminal name or node ID")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-analysis timeout budget in seconds")
    parser.add_argument("--demo-cloud", action="store_true", help="Run built-in multi-region cloud VPC benchmark")
    parser.add_argument("--out-report", help="Output path for Markdown compliance audit report")
    parser.add_argument("--out-json", help="Output path for machine-readable JSON summary")
    parser.add_argument("--no-sensitivity", action="store_true", help="Skip Birnbaum component importance calculations")

    args = parser.parse_args()

    if args.demo_cloud:
        topo = EnterpriseTopology("EnterpriseCloudVPC")
        topo.add_link("Client_App", "Edge_Ingress_1", availability=0.9995)
        topo.add_link("Client_App", "Edge_Ingress_2", availability=0.9995)
        topo.add_link("Edge_Ingress_1", "TransitGateway_East", availability=0.9999)
        topo.add_link("Edge_Ingress_2", "TransitGateway_Central", availability=0.9999)
        topo.add_link("TransitGateway_East", "TransitGateway_Central", availability=0.999)  # Cross-region interconnect
        topo.add_link("TransitGateway_East", "DB_Cluster_Primary", availability=0.9999)
        topo.add_link("TransitGateway_Central", "DB_Cluster_Replica", availability=0.9999)
        topo.add_link("DB_Cluster_Primary", "DB_Cluster_Replica", availability=0.9995)  # Replication link
        source = "Client_App"
        target = "DB_Cluster_Primary"
    elif args.topology:
        p = Path(args.topology)
        if not p.exists():
            print(f"Error: File '{args.topology}' does not exist.")
            sys.exit(1)
        data = json.loads(p.read_text(encoding="utf-8"))
        topo = EnterpriseTopology.from_dict(data)
        source = args.source
        target = args.target
        if not source or not target:
            print("Error: --source and --target are required when specifying a topology file.")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    print(f"Auditing system: {topo.name}")
    print(f"Terminals: {source} <--> {target}")
    print(f"Compiling and evaluating exact reliability...")

    engine = EnterpriseReliabilityEngine(topo)
    result = engine.audit_terminal_pair(
        source=source,
        target=target,
        timeout_seconds=args.timeout,
        compute_sensitivity=not args.no_sensitivity,
    )

    m = result.metrics
    print("\n" + "=" * 65)
    print(" SAT-Frontier Enterprise Audit Summary")
    print("=" * 65)
    print(f"Availability Status   : {result.status.upper()}")
    print(f"System Availability   : {m.availability * 100:.6f}% ({m.n_nines})")
    print(f"Exact Probability     : {result.availability_fraction}")
    print(f"Annual Downtime       : {m.downtime_minutes_per_year:.2f} minutes/year ({m.downtime_hours_per_year:.2f} hours)")
    print(f"Single Points Failure : {len(result.single_points_of_failure)}")
    print(f"Total Minimal Cuts    : {result.minimal_cuts_count}")
    print(f"Total Audit Latency   : {result.total_seconds * 1000:.2f} ms")
    print("=" * 65)

    if result.single_points_of_failure:
        print("\n[CRITICAL WARNING] Single Points of Failure Detected:")
        for spof in result.single_points_of_failure:
            print(f"  * Cut {spof.cut_edges}: {' , '.join(spof.edge_names)} (Prob: {spof.unavailability_probability:.6e})")

    if result.component_criticality:
        print("\nTop 5 Most Critical Components (Birnbaum Sensitivity Index):")
        for ci in result.component_criticality[:5]:
            print(f"  #{ci.sensitivity_rank} {ci.edge_label:<20} : {ci.birnbaum_importance:.6f} (Avail: {ci.availability * 100:.2f}%)")

    md_report = generate_markdown_audit_report(result)
    if args.out_report:
        Path(args.out_report).write_text(md_report, encoding="utf-8")
        print(f"\nExecutive Markdown report saved: {args.out_report}")

    json_summary = generate_json_audit_summary(result)
    if args.out_json:
        Path(args.out_json).write_text(json_summary, encoding="utf-8")
        print(f"Machine-readable JSON summary saved: {args.out_json}")


if __name__ == "__main__":
    main()

