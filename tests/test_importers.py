"""Unit tests for enterprise network topology importers."""
import unittest
from pathlib import Path
from fractions import Fraction

from sat_frontier.enterprise.importers import (
    import_csv,
    import_gml,
    import_graphml,
    import_json,
    load_topology,
    parse_availability_value,
)
from sat_frontier.enterprise.engine import EnterpriseReliabilityEngine

ROOT = Path(__file__).resolve().parent.parent
TOPOLOGIES_DIR = ROOT / "instances" / "topologies"


class ImportersTest(unittest.TestCase):

    def test_parse_availability_value(self):
        self.assertEqual(parse_availability_value("0.99"), Fraction(99, 100))
        self.assertEqual(parse_availability_value("99.9%"), Fraction(999, 1000))
        self.assertEqual(parse_availability_value("9999/10000"), Fraction(9999, 10000))
        self.assertEqual(parse_availability_value(0.95), Fraction(19, 20))
        self.assertEqual(parse_availability_value(None, default=Fraction(9, 10)), Fraction(9, 10))

    def test_import_graphml_abilene(self):
        p = TOPOLOGIES_DIR / "abilene.graphml"
        topo = import_graphml(p)
        self.assertEqual(topo.name, "Abilene")
        self.assertEqual(len(topo.links), 14)
        self.assertIn("Seattle", topo.node_to_id)
        self.assertIn("NewYork", topo.node_to_id)
        
        # Test audit on imported topology
        engine = EnterpriseReliabilityEngine(topo)
        res = engine.audit_terminal_pair("Seattle", "NewYork")
        self.assertEqual(res.status, "exact")
        self.assertGreater(float(res.availability_fraction), 0.99)
        self.assertEqual(len(res.single_points_of_failure), 0)

    def test_import_gml_internet2(self):
        p = TOPOLOGIES_DIR / "internet2.gml"
        topo = import_gml(p)
        self.assertEqual(topo.name, "Internet2")
        self.assertEqual(len(topo.links), 13)
        self.assertIn("SaltLakeCity", topo.node_to_id)
        self.assertIn("WashingtonDC", topo.node_to_id)

        engine = EnterpriseReliabilityEngine(topo)
        res = engine.audit_terminal_pair("SaltLakeCity", "WashingtonDC")
        self.assertEqual(res.status, "exact")
        self.assertGreater(float(res.availability_fraction), 0.99)

    def test_import_csv_bellsouth(self):
        p = TOPOLOGIES_DIR / "bellsouth.csv"
        topo = import_csv(p)
        self.assertEqual(len(topo.links), 15)
        self.assertIn("Atlanta", topo.node_to_id)
        self.assertIn("Miami", topo.node_to_id)

        engine = EnterpriseReliabilityEngine(topo)
        res = engine.audit_terminal_pair("Atlanta", "Miami")
        self.assertEqual(res.status, "exact")
        self.assertGreater(float(res.availability_fraction), 0.99)

    def test_import_json_colt(self):
        p = TOPOLOGIES_DIR / "colt.json"
        topo = import_json(p)
        self.assertEqual(topo.name, "Colt_Telecom_European_Backbone")
        self.assertEqual(len(topo.links), 16)
        self.assertIn("London", topo.node_to_id)
        self.assertIn("Milan", topo.node_to_id)

        engine = EnterpriseReliabilityEngine(topo)
        res = engine.audit_terminal_pair("London", "Milan")
        self.assertEqual(res.status, "exact")
        self.assertGreater(float(res.availability_fraction), 0.99)

    def test_universal_loader_and_geant(self):
        p = TOPOLOGIES_DIR / "geant.graphml"
        topo = load_topology(p)
        self.assertEqual(topo.name, "GEANT_Core")
        self.assertEqual(len(topo.links), 18)

        engine = EnterpriseReliabilityEngine(topo)
        res = engine.audit_terminal_pair("London", "Vienna")
        self.assertEqual(res.status, "exact")
        self.assertGreater(float(res.availability_fraction), 0.99)


if __name__ == "__main__":
    unittest.main()
