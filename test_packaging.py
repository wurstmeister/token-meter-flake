"""Exercise Nix-managed updates and the launcher used by Settings → MCP."""

import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import meter


class PackagingTests(unittest.TestCase):
    def test_saved_preferences_cannot_enable_updates(self):
        with patch.object(meter, "load_json", return_value={
            "updates": {"enabled": True, "auto_install": True},
        }):
            settings = meter.update_settings()
        self.assertFalse(settings["enabled"])
        self.assertFalse(settings["auto_install"])

    def test_update_status_explains_nix_ownership(self):
        with patch.object(meter, "_update_status_record", return_value={
            "phase": "available", "available": True, "can_update": True,
        }):
            status = meter.software_update_status()
        self.assertEqual(status["managed_by"], "nix")
        self.assertIn("Nix", status["message"])
        self.assertFalse(status["can_update"])
        self.assertFalse(status["actions"]["check"])
        self.assertFalse(status["actions"]["install"])

    def test_enable_check_and_install_do_not_write_or_spawn(self):
        with patch.object(meter, "write_settings_json", side_effect=AssertionError("Settings write")), \
             patch.object(meter, "_run_update_git", side_effect=AssertionError("Git operation")), \
             patch.object(meter.subprocess, "Popen", side_effect=AssertionError("Updater process")):
            results = [
                meter.set_update_settings({"enabled": True, "auto_install": True}),
                meter.trigger_software_update_check(),
                meter.start_software_update(),
            ]
            status = meter.check_for_software_update()
        self.assertFalse(status["enabled"])
        for result in results:
            self.assertFalse(result["ok"])
            self.assertIn("Nix", result["error"])

    def test_ui_mcp_launcher_runs_without_python_on_path(self):
        launcher = meter.agent_access_launcher()
        request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [launcher], input=json.dumps(request) + "\n", capture_output=True,
                text=True, timeout=10,
                env={"HOME": home, "PATH": "/nonexistent", "PYTHONDONTWRITEBYTECODE": "1"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response["id"], 1)
        self.assertIn("serverInfo", response["result"])


if __name__ == "__main__":
    unittest.main()
