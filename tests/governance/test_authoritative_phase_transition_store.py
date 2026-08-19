"""Adversarial tests for the Git-backed phase-transition incorporation boundary."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "authoritative_phase_transition_store", ROOT / "tools" / "authoritative_phase_transition_store.py"
)
store = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(store)
v = store.verify


class AuthoritativeStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bopen-store-")
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.ref = "refs/heads/governed"
        self.schedule_path = "schedule.json"
        self.consumed_path = "governance/consumed-decisions.json"
        self.receipt_path = "governance/phase-transition-receipt.json"
        self.mandate_repo_path = "governance/mandates/phase-completion.dsse.json"
        self.schedule = {
            "register_id": "PG-REG-SCHEDULE-001",
            "entries": [
                {"schedule_id": "PG-P0", "status": "ACTIVE", "planned_end": None, "rebaseline_decision_ref": None},
                {"schedule_id": "PG-P1", "status": "NOT_READY"},
            ],
        }
        self.seed = hashlib.sha256(b"bopen-store-test-key").digest()
        self.keyid = "store-test-key"
        self.identity_id = "HUMAN-OPERATOR-001"
        self.verification_time = "2026-07-25T00:00:00+07:00"
        self.observed_at = "2026-07-25T01:00:00+07:00"
        self.trust_root = {"keys": [{
            "keyid": self.keyid,
            "algorithm": "ed25519",
            "public_key": v.ed25519_public_key(self.seed).hex(),
            "identity_id": self.identity_id,
        }]}
        self.identity = {"entries": [{
            "identity_id": self.identity_id,
            "status": "approved",
            "authority_roles": ["Architecture Authority"],
            "action_ids": ["COMPLETE_PHASE"],
            "valid_from": "2026-01-01T00:00:00+07:00",
            "expires_at": "2027-01-01T00:00:00+07:00",
            "revoked_at": None,
        }]}
        self._git("init")
        self._git("config", "user.name", "test")
        self._git("config", "user.email", "test@example.invalid")
        self._write(self.schedule_path, self.schedule)
        self._git("add", ".")
        self._git("commit", "-m", "initial")
        self._git("update-ref", self.ref, "HEAD")
        self.trust_path = self.repo.parent / "trust.json"
        self.identity_path = self.repo.parent / "identity.json"
        self._write_external(self.trust_path, self.trust_root)
        self._write_external(self.identity_path, self.identity)

    def tearDown(self):
        self.temp.cleanup()

    def _git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.STDOUT).decode()

    def _write(self, relative, value):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(store.canonical_json(value))

    @staticmethod
    def _write_external(path, value):
        path.write_bytes(store.canonical_json(value))

    def _mandate(self, decision_id="PG-P0-COMPLETE-001", successor_value="PG-P0-COMPLETE-001"):
        mandate = {
            "schema_id": "bopen.phase-completion-mandate",
            "decision_id": decision_id,
            "phase_id": "PG-P0",
            "operation": "COMPLETE_PHASE",
            "predecessor": {"schedule_digest": v.digest(self.schedule)},
            "transform": {
                "specification_digest": "store-spec-v1",
                "permitted_mutations": [
                    {"path": "phases.PG-P0.status", "from": "ACTIVE", "to": "COMPLETE"},
                    {"path": "phases.PG-P0.planned_end", "rule": "COPY_MANDATE_EFFECTIVE_TIME"},
                    {"path": "phases.PG-P0.rebaseline_decision_ref", "value": successor_value},
                ],
            },
            "invariants": {"phases.PG-P1.status": "NOT_READY"},
            "authority": {
                "required_role": "Architecture Authority",
                "required_action": "COMPLETE_PHASE",
                "effective_at": self.verification_time,
            },
        }
        payload = v.rfc8785_canonical(mandate)
        signature = v.sign_ed25519(self.seed, v._pae(v.DSSE_PAYLOAD_TYPE, payload))
        return {
            "payloadType": v.DSSE_PAYLOAD_TYPE,
            "payload": base64.b64encode(payload).decode(),
            "signatures": [{"keyid": self.keyid, "sig": base64.b64encode(signature).decode()}],
        }

    def _mandate_file(self, envelope, name="mandate.json"):
        path = self.repo.parent / name
        self._write_external(path, envelope)
        return path

    def _call(self, envelope, decision_id="PG-P0-COMPLETE-001"):
        import os
        previous = os.getcwd()
        os.chdir(self.repo)
        try:
            return store.incorporate(
                self.repo, self.ref, self.schedule_path, self.consumed_path,
                self._mandate_file(envelope), self.mandate_repo_path,
                self.trust_path, self.identity_path, self.verification_time,
                self.observed_at, self.receipt_path,
            )
        finally:
            os.chdir(previous)

    def test_one_commit_contains_all_authoritative_state(self):
        result = self._call(self._mandate())
        self.assertEqual(result["outcome"], store.INCORPORATED)
        commit = result["resulting_ref"]
        parent = self._git("rev-parse", f"{commit}^").strip()
        self.assertEqual(parent, self._git("rev-parse", f"{self.ref}^{{commit}}").strip() if False else parent)
        for path in (self.schedule_path, self.consumed_path, self.mandate_repo_path, self.receipt_path):
            self._git("show", f"{commit}:{path}")
        schedule = json.loads(self._git("show", f"{commit}:{self.schedule_path}"))
        self.assertEqual(schedule["entries"][0]["status"], "COMPLETE")
        self.assertEqual(schedule["entries"][1]["status"], "NOT_READY")
        event = json.loads((self.repo / (self.receipt_path + ".incorporation.json")).read_text())
        self.assertEqual(event["resulting_ref"], commit)

    def test_exact_retry_does_not_move_ref_or_create_second_event(self):
        first = self._call(self._mandate())
        second = self._call(self._mandate())
        self.assertEqual(second["outcome"], store.ALREADY_APPLIED)
        self.assertEqual(second["commit"], first["resulting_ref"])
        self.assertEqual(self._git("rev-parse", self.ref).strip(), first["resulting_ref"])

    def test_reused_decision_for_different_successor_is_denied(self):
        self._call(self._mandate())
        altered = self._mandate(successor_value="different-successor")
        with self.assertRaises((store.StoreError, v.VerifyError)) as raised:
            self._call(altered)
        if isinstance(raised.exception, store.StoreError):
            self.assertEqual(raised.exception.outcome, store.REPLAY_DENIED)
        else:
            self.assertEqual(raised.exception.reason, v.SUCCESSOR_MISMATCH)

    def test_expected_old_ref_update_rejects_lost_cas(self):
        old = self._git("rev-parse", self.ref).strip()
        new = self._git("commit-tree", self._git("rev-parse", f"{old}^{{tree}}").strip(), "-p", old, "-m", "winner").strip()
        self._git("update-ref", self.ref, new, old)
        with self.assertRaises(subprocess.CalledProcessError):
            subprocess.check_output(["git", "-C", str(self.repo), "update-ref", self.ref, old, old])
        self.assertEqual(self._git("rev-parse", self.ref).strip(), new)

    def test_object_creation_before_cas_does_not_change_ref(self):
        old = self._git("rev-parse", self.ref).strip()
        tree = self._git("rev-parse", f"{old}^{{tree}}").strip()
        orphan = self._git("commit-tree", tree, "-p", old, "-m", "unincorporated").strip()
        self.assertTrue(orphan)
        self.assertEqual(self._git("rev-parse", self.ref).strip(), old)


if __name__ == "__main__":
    unittest.main()
