"""Verify that Work insights cannot install or manage an Ollama runtime."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from token_meter.services.work_setup import WorkSetup, SetupError, DEFAULT_OLLAMA_URL


class NixOllamaSetupTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        self.setup = WorkSetup(
            base_dir=self.home.name,
            cache_dir=self.home.name,
            launch_agents_dir=self.home.name,
            get_settings=lambda: {"ollama_url": DEFAULT_OLLAMA_URL, "model": "token-meter-gemma"},
            set_ollama_url=Mock(),
            runner=Mock(side_effect=AssertionError("Setup must not launch processes")),
            sleep=Mock(),
            total_memory=lambda: 16 * 1024 ** 3,
        )
        self.setup._download = Mock(side_effect=AssertionError("Runtime download attempted"))
        self.setup.start_agent = Mock(side_effect=AssertionError("Private server start attempted"))

    def test_healthy_server_uses_nix_cli(self):
        self.setup._version = Mock(return_value=(0, 40, 11))
        url, cli = self.setup._ollama(DEFAULT_OLLAMA_URL)
        self.assertEqual(url, DEFAULT_OLLAMA_URL)
        self.assertTrue(cli.startswith("/nix/store/"), cli)
        self.assertTrue(cli.endswith("/bin/ollama"), cli)
        self.assertTrue(os.access(cli, os.X_OK))

    def test_offline_server_does_not_fall_back(self):
        self.setup._version = Mock(return_value=None)
        with self.assertRaises(SetupError) as error:
            self.setup._ollama(DEFAULT_OLLAMA_URL)
        self.assertEqual(error.exception.reason, "ollama_offline")
        self.setup.set_ollama_url.assert_not_called()

    def test_old_server_does_not_install_replacement(self):
        self.setup._version = Mock(return_value=(0, 33, 0))
        with self.assertRaises(SetupError):
            self.setup._ollama(DEFAULT_OLLAMA_URL)
        self.setup._download.assert_not_called()

    def test_custom_endpoint_is_preserved(self):
        self.setup._version = Mock(return_value=(0, 40, 11))
        url = "http://127.0.0.1:12000"
        self.assertEqual(self.setup._ollama(url)[0], url)
        self.setup._version.assert_called_once_with(url)
        self.setup.set_ollama_url.assert_not_called()

    def test_former_private_port_is_treated_as_external(self):
        url = "http://127.0.0.1:11435"
        self.setup.get_settings = lambda: {"ollama_url": url}
        self.setup._version = Mock(return_value=(0, 40, 11))
        self.assertEqual(self.setup._ollama(url)[0], url)
        self.assertFalse(self.setup.status()["managed"])

    def test_install_hook_only_resolves_nix_binary(self):
        self.assertEqual(self.setup._install_ollama(), self.setup._find_cli())
        self.setup._download.assert_not_called()

    def test_existing_model_needs_no_download_or_import(self):
        self.setup._version = Mock(return_value=(0, 40, 11))
        self.setup._has_model = Mock(return_value=True)
        self.setup._download_model = Mock(side_effect=AssertionError("Model already installed"))
        self.setup.run()
        self.assertEqual(self.setup.status()["state"], "ready")

    def test_missing_model_is_imported_with_nix_cli(self):
        self.setup._version = Mock(return_value=(0, 40, 11))
        self.setup._has_model = Mock(return_value=False)
        self.setup._download_model = Mock(return_value=self.home.name + "/model")
        self.setup._import = Mock()
        with patch("token_meter.services.work_setup.shutil.rmtree"):
            self.setup.run()
        self.setup._import.assert_called_once_with(
            self.setup._find_cli(), DEFAULT_OLLAMA_URL, "token-meter-gemma",
            self.home.name + "/model",
        )


if __name__ == "__main__":
    unittest.main()
