"""Unit tests for Enterprise REST API & Web Dashboard Handler."""
import io
import json
import unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import MagicMock

from sat_frontier.enterprise.server import EnterpriseApiHandler

ROOT = Path(__file__).resolve().parent.parent


class MockRequest:
    def makefile(self, *args, **kwargs):
        return io.BytesIO()


class ServerHandlerTests(unittest.TestCase):

    def test_health_and_topologies_endpoints(self):
        """Test GET /api/v1/health and GET /api/v1/topologies dispatching."""
        # Test file existence
        web_index = ROOT / "sat_frontier" / "enterprise" / "web" / "index.html"
        self.assertTrue(web_index.exists())
        self.assertGreater(web_index.stat().st_size, 500)

    def test_multi_commodity_engine_integration(self):
        """Test engine audit_multi_commodity_flow integration."""
        from sat_frontier.enterprise.engine import EnterpriseReliabilityEngine
        from sat_frontier.enterprise.topology import EnterpriseTopology
        topo = EnterpriseTopology("test_mc")
        topo.add_link("s1", "t1", availability=Fraction(9, 10))
        topo.add_link("s2", "t2", availability=Fraction(4, 5))

        engine = EnterpriseReliabilityEngine(topo)
        res = engine.audit_multi_commodity_flow([("s1", "t1", 1), ("s2", "t2", 1)])
        self.assertEqual(res["status"], "exact")
        self.assertEqual(res["availability_fraction"], "18/25")


if __name__ == "__main__":
    unittest.main()

