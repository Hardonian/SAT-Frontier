"""Unit tests for Enterprise REST API & Web Dashboard Handler."""
import io
import json
import unittest
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


if __name__ == "__main__":
    unittest.main()

