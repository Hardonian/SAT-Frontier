"""Production CLI for SAT-Frontier Enterprise Reliability & SLA Compliance Audit."""
import argparse
import json
import sys
from pathlib import Path

from .all_pairs import (
    compute_all_pairs_sla,
    generate_all_pairs_markdown_report,
    render_terminal_heatmap,
)
from .engine import EnterpriseReliabilityEngine
from .importers import load_topology
from .report import generate_json_audit_summary, generate_markdown_audit_report
from .topology import EnterpriseTopology


def main():
    parser = argparse.ArgumentParser(
        description="SAT-Frontier Enterprise: SLA Reliability & Vulnerability Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m sat_frontier.enterprise.cli --topology network.json --source VPC_East --target VPC_West
  python -m sat_frontier.enterprise.cli --demo-cloud --all-pairs
  python -m sat_frontier.enterprise.cli --demo-cloud --out-report cloud_audit.md --out-json cloud_audit.json
        """,
    )
    parser.add_argument("--topology", help="Path to network topology file (.graphml, .gml, .json, .csv, .tsv)")
    parser.add_argument("--default-availability", default="0.99", help="Default link availability if unspecified in topology (default: 0.99)")
    parser.add_argument("--source", help="Source terminal name or node ID")
    parser.add_argument("--target", help="Target terminal name or node ID")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-analysis timeout budget in seconds")
    parser.add_argument("--demo-cloud", action="store_true", help="Run built-in multi-region cloud VPC benchmark")
    parser.add_argument("--demo-subsea", action="store_true", help="Run built-in transatlantic subsea optical mesh benchmark")
    parser.add_argument("--all-pairs", action="store_true", help="Run exhaustive all-pairs pairwise SLA matrix and heatmap")
    parser.add_argument("--weibull", action="store_true", help="Run continuous Weibull aging and wear-out MTTF integration")
    parser.add_argument("--weibull-beta", type=float, default=2.0, help="Weibull shape parameter (default: 2.0 / Rayleigh)")
    parser.add_argument("--hazard-rate", type=float, default=1e-4, help="Component failure rate lambda per hour (default: 1e-4)")
    parser.add_argument("--repairable", action="store_true", help="Run Markov renewal repairable duality audit (frequency, MTBF, MTTR)")
    parser.add_argument("--repair-rate", type=float, default=1e-2, help="Component repair rate mu per hour (default: 1e-2)")
    parser.add_argument("--enclosure", action="store_true", help="Run any-time monotone dual enclosure bounding")
    parser.add_argument("--max-paths", type=int, default=5, help="Maximum minimal paths for lower bound (default: 5)")
    parser.add_argument("--max-cuts", type=int, default=5, help="Maximum minimal cuts for upper bound (default: 5)")
    parser.add_argument("--dashboard", action="store_true", help="Launch interactive web dashboard and desktop runner")
    parser.add_argument("--out-report", help="Output path for Markdown compliance audit report")
    parser.add_argument("--out-json", help="Output path for machine-readable JSON summary")
    parser.add_argument("--no-sensitivity", action="store_true", help="Skip Birnbaum component importance calculations")

    args = parser.parse_args()

    if args.dashboard:
        from .desktop import DesktopApp
        app = DesktopApp()
        app.run()
        sys.exit(0)

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
    elif args.demo_subsea:
        topo = EnterpriseTopology("SubseaOpticalMesh")
        topo.add_link("NYC_Landing", "Halifax_Station", availability=0.9999)
        topo.add_link("NYC_Landing", "Bermuda_Repeater", availability=0.9995)
        topo.add_link("Halifax_Station", "North_Atlantic_Cable", availability=0.999)
        topo.add_link("Bermuda_Repeater", "Azores_Landing", availability=0.998)
        topo.add_link("North_Atlantic_Cable", "London_Telehouse", availability=0.9999)
        topo.add_link("Azores_Landing", "London_Telehouse", availability=0.999)
        topo.add_link("North_Atlantic_Cable", "Azores_Landing", availability=0.995)
        source = "NYC_Landing"
        target = "London_Telehouse"
    elif args.topology:
        p = Path(args.topology)
        if not p.exists():
            print(f"Error: File '{args.topology}' does not exist.")
            sys.exit(1)
        topo = load_topology(p, default_availability=args.default_availability)
        source = args.source
        target = args.target
        if not args.all_pairs and (not source or not target):
            print("Error: --source and --target are required when specifying a topology file without --all-pairs.")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    engine = EnterpriseReliabilityEngine(topo)

    # All-Pairs Evaluation Branch
    if args.all_pairs:
        print(f"Executing All-Pairs SLA Matrix Analysis on: {topo.name}")
        nodes_list = sorted(topo.node_to_id.keys(), key=str)
        print(f"Nodes ({len(nodes_list)}): {', '.join(nodes_list)}")
        all_pairs_res = engine.audit_all_pairs(timeout_per_pair=args.timeout)

        # Print Terminal Heatmap
        print("\n" + render_terminal_heatmap(all_pairs_res))

        if args.out_report:
            md_content = generate_all_pairs_markdown_report(all_pairs_res)
            Path(args.out_report).write_text(md_content, encoding="utf-8")
            print(f"\nAll-Pairs Markdown compliance report saved: {args.out_report}")

        if args.out_json:
            json_content = json.dumps(all_pairs_res.to_dict(), indent=2)
            Path(args.out_json).write_text(json_content, encoding="utf-8")
            print(f"All-Pairs JSON data saved: {args.out_json}")
        return

    # Weibull Analysis Branch
    if args.weibull:
        print(f"Auditing Weibull Wear-Out Reliability: {topo.name}")
        print(f"Terminals: {source} <--> {target} | Beta: {args.weibull_beta} | Lambda: {args.hazard_rate}/hr")
        res_weibull = engine.audit_weibull_reliability(
            source=source,
            target=target,
            beta=args.weibull_beta,
            lambda_per_hour=args.hazard_rate,
        )
        print("\n" + "=" * 65)
        print(" SAT-Frontier Weibull Aging & Fatigue Audit Summary")
        print("=" * 65)
        print(f"Status               : {res_weibull['status'].upper()}")
        print(f"MTTF (Mean Life)     : {res_weibull['mttf_hours']:.2f} hours")
        print(f"Standard Deviation   : {res_weibull['std_dev_hours']:.2f} hours")
        print(f"B10 Useful Life      : {res_weibull['b10_life_hours']:.2f} hours (10% failure)")
        print(f"B1 High-Rel Life     : {res_weibull['b1_life_hours']:.2f} hours (1% failure)")
        print(f"Shape Parameter beta : {res_weibull['beta_shape']}")
        print(f"Scale Factor lambda  : {res_weibull['lambda_scale_per_hour']}/hour")
        print("=" * 65)
        if args.out_json:
            Path(args.out_json).write_text(json.dumps(res_weibull, indent=2), encoding="utf-8")
            print(f"Weibull JSON data saved: {args.out_json}")
        return

    # Repairable Renewal Analysis Branch
    if args.repairable:
        print(f"Auditing Repairable Network Renewal Duality: {topo.name}")
        print(f"Terminals: {source} <--> {target} | Lambda: {args.hazard_rate}/hr | Mu: {args.repair_rate}/hr")
        res_rep = engine.audit_repairable_network(
            source=source,
            target=target,
            failure_rate_per_hour=args.hazard_rate,
            repair_rate_per_hour=args.repair_rate,
        )
        print("\n" + "=" * 65)
        print(" SAT-Frontier Repairable Network Renewal Summary")
        print("=" * 65)
        print(f"Status               : {res_rep['status'].upper()}")
        print(f"Availability         : {res_rep['availability_float'] * 100:.6f}% ({res_rep['nines']:.2f} nines)")
        print(f"Availability Exact   : {res_rep['availability_exact']}")
        print(f"Failure Frequency    : {res_rep['failure_frequency_exact']} failures/hour")
        print(f"System MTBF          : {res_rep['mtbf_hours_float']:.2f} hours (Exact: {res_rep['mtbf_hours_exact']})")
        print(f"System MTTR          : {res_rep['mttr_hours_float']:.2f} hours (Exact: {res_rep['mttr_hours_exact']})")
        print(f"Minimal Cuts Count   : {res_rep['cuts_count']}")
        print("=" * 65)
        if args.out_json:
            Path(args.out_json).write_text(json.dumps(res_rep, indent=2), encoding="utf-8")
            print(f"Repairable JSON data saved: {args.out_json}")
        return

    # Monotone Enclosure Bounding Branch
    if args.enclosure:
        print(f"Auditing Any-Time Monotone Dual Enclosure: {topo.name}")
        print(f"Terminals: {source} <--> {target} | Max Paths: {args.max_paths} | Max Cuts: {args.max_cuts}")
        res_enc = engine.audit_enclosure_bounds(
            source=source,
            target=target,
            max_paths=args.max_paths,
            max_cuts=args.max_cuts,
        )
        print("\n" + "=" * 65)
        print(" SAT-Frontier Certified Monotone Enclosure Summary")
        print("=" * 65)
        print(f"Status               : {res_enc['status'].upper()}")
        print(f"Certified Lower Bound: {res_enc['lower_bound_float']:.6f} (Exact: {res_enc['lower_bound_exact']})")
        print(f"Certified Upper Bound: {res_enc['upper_bound_float']:.6f} (Exact: {res_enc['upper_bound_exact']})")
        print(f"Certificate Gap      : {res_enc['gap_float']:.6f} (Exact: {res_enc['gap_exact']})")
        print(f"Guaranteed Enclosed  : {res_enc['enclosed']}")
        print(f"Paths Evaluated      : {res_enc['paths_count']}")
        print(f"Cuts Evaluated       : {res_enc['cuts_count']}")
        print("=" * 65)
        if args.out_json:
            Path(args.out_json).write_text(json.dumps(res_enc, indent=2), encoding="utf-8")
            print(f"Enclosure JSON data saved: {args.out_json}")
        return

    # Single-Pair SLA Audit Branch
    print(f"Auditing system: {topo.name}")
    print(f"Terminals: {source} <--> {target}")
    print(f"Compiling and evaluating exact reliability...")

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

