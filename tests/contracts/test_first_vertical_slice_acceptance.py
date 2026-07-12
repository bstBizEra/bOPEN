import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "docs/06-contracts/acceptance/first-vertical-slice.acceptance.json"


class FirstVerticalSliceAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.scenarios = cls.fixture["scenarios"]

    def test_acceptance_fixture_covers_all_slice_scenarios(self):
        self.assertEqual(
            [scenario["id"] for scenario in self.scenarios],
            ["PVS-001", "PVS-002", "PVS-003", "PVS-004", "PVS-005", "PVS-006", "PVS-007"],
        )

    def test_chain_stays_inside_phase_zero_specification_boundary(self):
        self.assertEqual(self.fixture["work_package"], "BOOT-P0-11")
        self.assertIn("BOPEN-TENANT-001-DRAFT", self.fixture["governing_artifacts"])
        self.assertIn("BOPEN-AUTHZ-001-DRAFT", self.fixture["governing_artifacts"])

    def test_every_authorization_decision_has_reason_policy_and_correlation(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                decision = scenario["authorization_decision"]
                self.assertIn(decision["decision"], {"ALLOW", "DENY"})
                self.assertTrue(decision["reason_code"])
                self.assertTrue(decision["policy_version"])
                self.assertTrue(decision["correlation_id"])

    def test_every_audit_event_matches_authorization_correlation(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                decision = scenario["authorization_decision"]
                audit_event = scenario["audit_event"]
                self.assertEqual(audit_event["correlation_id"], decision["correlation_id"])
                self.assertEqual(audit_event["result"], decision["decision"])
                self.assertEqual(audit_event["reason_code"], decision["reason_code"])
                self.assertEqual(audit_event["policy_version"], decision["policy_version"])

    def test_negative_scenarios_are_deny_by_default(self):
        deny_reason_by_id = {
            scenario["id"]: scenario["authorization_decision"]["reason_code"]
            for scenario in self.scenarios
            if scenario["authorization_decision"]["decision"] == "DENY"
        }

        self.assertEqual(
            deny_reason_by_id,
            {
                "PVS-002": "TENANT_PROVISIONING_INCOMPLETE",
                "PVS-003": "NO_ACTIVE_MEMBERSHIP",
                "PVS-004": "ACTIVE_CONTEXT_NOT_SERVER_VALIDATED",
                "PVS-005": "CROSS_TENANT_ACCESS_DENIED",
            },
        )


if __name__ == "__main__":
    unittest.main()
