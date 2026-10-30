"""Unit tests for Desktop Launcher and Server Lifecycle."""
import json
import unittest
import urllib.request

from sat_frontier.enterprise.desktop import DesktopApp, find_free_port


class DesktopLauncherTests(unittest.TestCase):

    def test_find_free_port(self):
        port = find_free_port()
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 1024)

    def test_desktop_app_lifecycle_and_health(self):
        """Test starting DesktopApp in background, hitting health endpoint, and stopping."""
        app = DesktopApp()
        base_url = app.start_background()
        self.assertTrue(base_url.startswith("http://127.0.0.1:"))

        health_url = f"{base_url}api/v1/health"
        with urllib.request.urlopen(health_url, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "healthy")

        app.stop()


if __name__ == "__main__":
    unittest.main()

