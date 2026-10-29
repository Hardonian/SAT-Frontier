"""Unit and regression tests for Enterprise Reliability SDK."""
import json
import unittest
from fractions import Fraction

from sat_frontier.enterprise import (
    EnterpriseAuditResult,
    EnterpriseReliabilityEngine,
    EnterpriseTopology,
    availability_from_fit,
    availability_from_mtbf,
    calculate_downtime_metrics,
    generate_json_audit_summary,
    generate_markdown_audit_report,
)
from sat_frontier.reliability import wheatstone_analytic


class EnterpriseSDKTests(unittest.TestCase):

    def test_mtbf_and_fit_conversions(self):
        """Verify MTBF and FIT parameter conversion functions."""
        # MTBF 99 hours, MTTR 1 hour -> A = 99 / 100 = 0.99
        p_mtbf = availability_from_mtbf(99.0, 1.0)
        self.assertEqual(p_mtbf, Fraction(99, 100))

        # FIT rate 100 over 8760 hours -> unavail = 100 * 1e-9 * 8760 = 0.000876 -> p = 0.999124
        p_fit = availability_from_fit(fit_rate=100.0, mission_hours=8760.0)
        self.assertAlmostEqual(float(p_fit), 0.999124, places=5)

    def test_downtime_metrics_calculation(self):
        """Verify annualized downtime and N-nines classification."""
        # Exactly 99.99% availability (Four Nines)
        p_four_nines = Fraction(9999, 10000)
        metrics = calculate_downtime_metrics(p_four_nines)
        self.assertEqual(metrics.n_nines, "Four Nines (>= 99.99%)")
        self.assertAlmostEqual(metrics.downtime_minutes_per_year, 52.56, places=2)

        # 99.9% availability (Three Nines)
        p_three_nines = Fraction(999, 1000)
        metrics3 = calculate_downtime_metrics(p_three_nines)
        self.assertEqual(metrics3.n_nines, "Three Nines (>= 99.9%)")
        self.assertAlmostEqual(metrics3.downtime_hours_per_year, 8.76, places=2)

    def test_single_point_of_failure_detection(self):
        """Verify engine flags single points of failure correctly."""
        topo = EnterpriseTopology("BridgeTopology")
        # Line 1-2, 2-3: node 2 is a cut-vertex, link (1,2) is a SPOF
        topo.add_link("Client", "Gateway", availability=0.99)
        topo.add_link("Gateway", "Server", availability=0.99)

        engine = EnterpriseReliabilityEngine(topo)
        audit = engine.audit_terminal_pair("Client", "Server")

        self.assertEqual(audit.status, "exact")
        # Both links are single points of failure
        self.assertEqual(len(audit.single_points_of_failure), 2)
        # R = 0.99 * 0.99 = 0.9801
        self.assertEqual(audit.availability_fraction, Fraction(9801, 10000))

    def test_wheatstone_enterprise_audit_and_birnbaum(self):
        """Verify full enterprise audit on Wheatstone bridge topology matches closed form."""
        p_val = Fraction(9, 10)
        topo = EnterpriseTopology("WheatstoneCloud")
        topo.add_link("VPC_A", "R1", availability=p_val)
        topo.add_link("VPC_A", "R2", availability=p_val)
        topo.add_link("R1", "VPC_B", availability=p_val)
        topo.add_link("R2", "VPC_B", availability=p_val)
        topo.add_link("R1", "R2", availability=p_val)  # Cross-link bridge

        engine = EnterpriseReliabilityEngine(topo)
        audit = engine.audit_terminal_pair("VPC_A", "VPC_B", compute_sensitivity=True)

        expected_r = wheatstone_analytic(p_val)
        self.assertEqual(audit.availability_fraction, expected_r)
        self.assertEqual(len(audit.single_points_of_failure), 0)
        self.assertEqual(audit.minimal_cuts_count, 4)

        # Birnbaum sensitivity: all components should have positive importance
        self.assertEqual(len(audit.component_criticality), 5)
        for ci in audit.component_criticality:
            self.assertGreater(ci.birnbaum_importance, 0.0)

        # Generate reports and verify string validity
        md_report = generate_markdown_audit_report(audit)
        self.assertIn("# Infrastructure Reliability & SLA Compliance Audit Report", md_report)
        self.assertIn("WheatstoneCloud", md_report)

        json_summary = generate_json_audit_summary(audit)
        data = json.loads(json_summary)
        self.assertEqual(data["system"], "WheatstoneCloud")
        self.assertEqual(data["vulnerabilities"]["total_minimal_cuts"], 4)

    def test_multi_terminal_enterprise_audit(self):
        """Verify multi-terminal SLA audit on 3-AZ cloud VPC topology."""
        topo = EnterpriseTopology("AWS_TriAZ_VPC")
        topo.add_link("AZ_East", "TGW", availability=0.999)
        topo.add_link("AZ_West", "TGW", availability=0.999)
        topo.add_link("AZ_Central", "TGW", availability=0.999)

        engine = EnterpriseReliabilityEngine(topo)
        audit = engine.audit_multi_terminal(["AZ_East", "AZ_West", "AZ_Central"])

        self.assertEqual(audit.status, "exact")
        # All 3 links must operate for all 3 AZs to be connected to each other through TGW
        # R = 0.999^3 = (999/1000)^3 = 997002999 / 1000000000
        self.assertEqual(audit.availability_fraction, Fraction(997002999, 1000000000))
        # Each link is a SPOF
        self.assertEqual(len(audit.single_points_of_failure), 3)

    def test_parametric_curve_enterprise_audit(self):
        """Verify parametric reliability polynomial curve computation."""
        topo = EnterpriseTopology("BridgeParametric")
        topo.add_link("Client", "Gateway", availability=0.99)
        topo.add_link("Gateway", "Server", availability=0.99)

        engine = EnterpriseReliabilityEngine(topo)
        curve = engine.audit_parametric_curve("Client", "Server")

        self.assertEqual(curve["status"], "exact")
        self.assertEqual(curve["coefficients"], [0, 0, 1])  # Only the state with both edges active connects
        self.assertAlmostEqual(curve["evaluations"]["p=0.90"], 0.81, places=4)
        self.assertAlmostEqual(curve["evaluations"]["p=0.99"], 0.9801, places=4)

    def test_directed_network_enterprise_audit(self):
        """Verify directed reachability audit on microservices DAG."""
        from sat_frontier.dicut_compiler import DirectedNetworkGraph
        dnet = DirectedNetworkGraph()
        dnet.add_edge("Ingress", "API", Fraction(99, 100))
        dnet.add_edge("API", "DB", Fraction(99, 100))

        res = EnterpriseReliabilityEngine.audit_directed_network(dnet, "Ingress", "DB")
        self.assertEqual(res["status"], "exact")
        self.assertEqual(res["availability_fraction"], "9801/10000")
        self.assertEqual(res["minimal_dicuts_count"], 2)


if __name__ == "__main__":
    unittest.main()

