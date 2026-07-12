"""Tests for the Phase 0 secret and supply-chain controls."""

import tempfile
import unittest
from pathlib import Path

from tools.check_secrets import scan_repository, scan_text
from tools.check_supply_chain import check_baseline


class SecretControlTests(unittest.TestCase):
    def test_detects_private_key_marker(self):
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        self.assertIn("private key", scan_text(marker))

    def test_detects_assigned_credential(self):
        credential = "client_secret" + "=" + "not-a-real-secret-value"
        self.assertIn("assigned credential", scan_text(credential))

    def test_repository_is_free_of_detected_credentials(self):
        self.assertEqual(scan_repository(), [])


class SupplyChainControlTests(unittest.TestCase):
    def test_repository_supply_chain_baseline_passes(self):
        errors, _warnings = check_baseline()
        self.assertEqual(errors, [])

    def test_missing_controls_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors, _warnings = check_baseline(Path(temporary))
        self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
