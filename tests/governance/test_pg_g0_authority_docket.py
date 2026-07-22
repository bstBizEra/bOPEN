"""Fail-closed tests for the proposed PG-G0 authority docket."""

from __future__ import annotations

import json
import hashlib
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from tools.generate_document_manifest import build_manifest
from tools.validate_pg_g0_authority_docket import (
    AUTHORITY_MATRIX_PATH,
    DOCKET_PATH,
    ROOT,
    SCHEMA_PATH,
    build_readiness_report,
    check_report,
    format_report,
    read_file_at_commit as read_repository_file_at_commit,
    validate_pg_g0_authority_docket,
)


AS_OF = datetime(2026, 7, 23, 0, 0, 0, tzinfo=timezone.utc)
EXPECTED_TREE = "8789c5e70c2ce87298928d4d02add7ffe5867402"
LEGACY_TREE = "f336976981c9b7e95c96ec8289589e53c1ac506c"


class PgG0AuthorityDocketTests(unittest.TestCase):
    def make_root(self, temporary: str) -> Path:
        root = Path(temporary)
        docket = json.loads((ROOT / DOCKET_PATH).read_text(encoding="utf-8"))
        paths = {DOCKET_PATH, SCHEMA_PATH, AUTHORITY_MATRIX_PATH, Path("docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.2-BINDING-INVENTORY.json")}
        paths.update(Path(item["artifact_ref"]) for item in docket["governing_artifacts"])
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return root

    @staticmethod
    def load_docket(root: Path) -> dict:
        return json.loads((root / DOCKET_PATH).read_text(encoding="utf-8"))

    @staticmethod
    def save_docket(root: Path, docket: dict) -> None:
        (root / DOCKET_PATH).write_text(json.dumps(docket, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def authority_actor(identity: str, role: str, *, kind: str = "HUMAN") -> dict:
        return {
            "actor_kind": kind,
            "human_identity_ref": identity,
            "identity_provider": "bopen-authority-identity-registry",
            "identity_subject": "HUMAN-TEST",
            "authority_role": role,
            "role_binding_ref": "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json#HUMAN-TEST",
            "role_binding_sha256": "0" * 64,
            "role_binding_commit_sha": "a" * 40,
            "role_binding_tree_sha": EXPECTED_TREE,
            "role_binding_status": "approved",
            "authority_mode": "DIRECT",
            "delegation_ref": None,
            "delegation_binding": None,
        }

    def validate(
        self,
        root: Path,
        *,
        ancestor: bool = True,
        missing_committed_paths: set[str] | None = None,
    ) -> list[str]:
        missing_committed_paths = missing_committed_paths or set()

        def committed_file(test_root: Path, _commit: str, relative: str):
            if relative in missing_committed_paths:
                return None
            source = test_root / relative
            if relative == "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json" or relative.startswith("docs/00-governance/delegations/"):
                return source.read_bytes() if source.is_file() else None
            committed = read_repository_file_at_commit(ROOT, _commit, relative)
            if committed is not None:
                return committed
            return source.read_bytes() if source.is_file() else None

        def resolved_tree(_root: Path, commit: str):
            return LEGACY_TREE if commit == "c893062c197e74c15214e5ce1c425b9e9ed8002f" else EXPECTED_TREE

        with (
            patch("tools.validate_pg_g0_authority_docket.resolve_tree", side_effect=resolved_tree),
            patch("tools.validate_pg_g0_authority_docket.resolve_head", return_value="f" * 40),
            patch("tools.validate_pg_g0_authority_docket.is_ancestor", return_value=ancestor),
            patch("tools.validate_pg_g0_authority_docket.read_file_at_commit", side_effect=committed_file),
            patch("tools.validate_pg_g0_authority_docket.is_tracked_path", side_effect=lambda test_root, relative: (test_root / relative).is_file()),
            patch("tools.validate_pg_g0_authority_docket.commit_datetime", return_value=datetime(2026, 7, 21, 0, 0, tzinfo=timezone.utc)),
        ):
            return validate_pg_g0_authority_docket(root, AS_OF)

    def install_identity_registry(self, root: Path, identity: str, subject: str, role: str) -> dict:
        relative = Path("docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json")
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        registry = {
            "status": "approved",
            "entries": [{
                "identity_id": subject,
                "status": "approved",
                "human_identity_ref": identity,
                "identity_provider": "bopen-authority-identity-registry",
                "identity_subject": subject,
                "authority_roles": [role],
                "action_ids": ["ACCEPT_EVIDENCE"],
                "subject_refs": ["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
                "valid_from": "2026-07-21T00:00:00Z",
                "expires_at": "2026-08-01T00:00:00Z",
                "revoked_at": None,
                "evidence_refs": ["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
            }],
        }
        path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        actor = self.authority_actor(identity, role)
        actor["identity_subject"] = subject
        actor["role_binding_ref"] = f"{relative.as_posix()}#{subject}"
        actor["role_binding_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return actor

    def install_delegated_actor(self, root: Path) -> tuple[dict, Path, Path]:
        subject_ref = "docs/evidence/EVD-GOV-001-program-g0-controls.md"
        actor = self.install_identity_registry(
            root, "human:delegate", "HUMAN-DELEGATE", "Engineering Authority"
        )
        registry_path = root / "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["entries"].append({
            "identity_id": "HUMAN-GRANTOR",
            "status": "approved",
            "human_identity_ref": "human:grantor",
            "identity_provider": "bopen-authority-identity-registry",
            "identity_subject": "HUMAN-GRANTOR",
            "authority_roles": ["Engineering Authority"],
            "can_delegate": True,
            "delegation_action_ids": ["ACCEPT_EVIDENCE"],
            "delegation_subject_refs": [subject_ref],
            "valid_from": "2026-07-21T00:00:00Z",
            "expires_at": "2026-08-01T00:00:00Z",
            "revoked_at": None,
            "evidence_refs": [subject_ref],
        })
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        actor["role_binding_sha256"] = hashlib.sha256(registry_path.read_bytes()).hexdigest()

        delegation_path = root / "docs/00-governance/delegations/engineering.json"
        delegation_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "delegation_id": "DELEGATION-001",
            "grantor_human_identity_ref": "human:grantor",
            "delegate_human_identity_ref": "human:delegate",
            "authority_role": "Engineering Authority",
            "action_ids": ["ACCEPT_EVIDENCE"],
            "subject_refs": [subject_ref],
            "valid_from": "2026-07-21T00:00:00Z",
            "expires_at": "2026-08-01T00:00:00Z",
            "revoked_at": None,
            "evidence_refs": [subject_ref],
        }
        delegation_path.write_text(json.dumps({"entries": [record]}, indent=2) + "\n", encoding="utf-8")
        actor.update({
            "authority_mode": "DELEGATED",
            "delegation_ref": "docs/00-governance/delegations/engineering.json#DELEGATION-001",
            "delegation_binding": {
                "delegation_id": "DELEGATION-001",
                "artifact_ref": "docs/00-governance/delegations/engineering.json",
                "artifact_sha256": hashlib.sha256(delegation_path.read_bytes()).hexdigest(),
                "commit_sha": "a" * 40,
                "tree_sha": EXPECTED_TREE,
                **record,
            },
        })
        return actor, registry_path, delegation_path

    def install_actor_on_evidence_decision(self, root: Path, actor: dict) -> None:
        docket = self.load_docket(root)
        decision = docket["decision_requests"][4]
        decision["checked_by"] = {
            "actor_kind": "AGENT", "identity_ref": "checker", "role": "QA & Evidence Agent",
            "registration_ref": None, "session_ref": None,
        }
        decision["final_authority_actor"] = actor
        decision["final_disposition"] = {
            "value": "REJECT", "decided_at": "2026-07-21T15:00:00Z",
            "reason_code": "REJECT", "decision_ref": "AUTH-REJECT",
            "evidence_refs": ["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
            "effective": False,
        }
        self.save_docket(root, docket)

    def test_repository_docket_is_valid_but_not_ready(self):
        self.assertEqual(validate_pg_g0_authority_docket(ROOT, AS_OF), [])
        report = build_readiness_report(ROOT, AS_OF)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertFalse(report["ready_for_human_gate_decision"])
        self.assertFalse(report["pg_g0_passed"])
        self.assertFalse(report["production_implementation_authorized"])
        self.assertGreaterEqual(len(report["blockers"]), 10)

    def test_committed_file_mock_prefers_temp_fixture_over_repository_file(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            tempfile.TemporaryDirectory() as repository,
        ):
            root = self.make_root(temporary)
            actor = self.install_identity_registry(
                root, "human:engineering", "HUMAN-ENGINEERING", "Engineering Authority"
            )
            self.install_actor_on_evidence_decision(root, actor)

            repository_root = Path(repository)
            decoy = repository_root / "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json"
            decoy.parent.mkdir(parents=True, exist_ok=True)
            decoy.write_text("not-json\n", encoding="utf-8")

            with patch(f"{__name__}.ROOT", repository_root):
                errors = self.validate(root)

        self.assertFalse(
            any("approved identity registry invalid" in item for item in errors), errors
        )

    def test_missing_docket_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            (root / DOCKET_PATH).unlink()
            errors = self.validate(root)
        self.assertIn("authority docket missing", errors)

    def test_missing_or_duplicate_decision_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"] = docket["decision_requests"][:-1]
            self.save_docket(root, docket)
            missing_errors = self.validate(root)
            docket["decision_requests"].append(docket["decision_requests"][0])
            self.save_docket(root, docket)
            duplicate_errors = self.validate(root)
        self.assertTrue(any("decision set" in item for item in missing_errors))
        self.assertTrue(any("decision set" in item for item in duplicate_errors))

    def test_unknown_top_level_field_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["uncontrolled_approval"] = True
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("unknown field" in item and "uncontrolled_approval" in item for item in errors))

    def test_unknown_nested_decision_field_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][0]["uncontrolled_approval"] = True
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("unknown field" in item and "uncontrolled_approval" in item for item in errors))

    def test_malformed_commit_and_wrong_tree_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["repository_binding"]["commit_sha"] = "not-a-sha"
            self.save_docket(root, docket)
            with patch(
                "tools.validate_pg_g0_authority_docket.resolve_tree",
                side_effect=lambda _root, commit: EXPECTED_TREE if len(commit) == 40 else None,
            ):
                malformed = validate_pg_g0_authority_docket(root, AS_OF)
            docket = self.load_docket(root)
            docket["repository_binding"]["commit_sha"] = "c893062c197e74c15214e5ce1c425b9e9ed8002f"
            docket["repository_binding"]["tree_sha"] = "0" * 40
            self.save_docket(root, docket)
            wrong_tree = self.validate(root)
        self.assertTrue(any("commit does not resolve" in item for item in malformed))
        self.assertTrue(any("commit/tree mismatch" in item for item in wrong_tree))

    def test_stale_artifact_hash_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            path = root / "docs/decisions/DEC-0010.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nstale mutation\n", encoding="utf-8")
            errors = self.validate(root)
        self.assertTrue(any("artifact drift" in item and "DEC-0010" in item for item in errors))

    def test_append_only_governing_artifact_rewrite_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            path = root / "docs/decisions/DEC-0013.md"
            path.write_bytes(b"rewritten predecessor\n" + path.read_bytes())
            errors = self.validate(root)
        self.assertTrue(any("artifact drift" in item and "DEC-0013" in item for item in errors), errors)

    def test_post_bound_mutation_cannot_be_hidden_by_rewriting_docket_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            target = root / "docs/decisions/DEC-0010.md"
            target.write_text(target.read_text(encoding="utf-8") + "\npost-bound mutation\n", encoding="utf-8")
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            docket = self.load_docket(root)
            for artifact in docket["governing_artifacts"]:
                if artifact["artifact_id"] == "DEC-0010":
                    artifact["sha256"] = digest
            for decision in docket["decision_requests"]:
                if decision["subject"]["artifact_id"] == "DEC-0010":
                    decision["subject"]["sha256"] = digest
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("bound commit sha256 mismatch" in item and "DEC-0010" in item for item in errors))

    def test_subject_must_match_exact_governing_artifact_map(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][2]["subject"]["artifact_ref"] = "docs/decisions/DEC-0007.md"
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("subject artifact/path mismatch" in item for item in errors))
        self.assertTrue(any("exactly match governing artifact" in item for item in errors))

    def test_agent_cannot_be_final_human_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            decision = docket["decision_requests"][0]
            decision["final_authority_actor"] = self.authority_actor(
                "AGT-ARCHI", "Architecture Authority", kind="AGENT"
            )
            decision["checked_by"] = decision["prepared_by"]
            decision["final_disposition"] = {
                "value": "APPROVE", "decided_at": "2026-07-22T00:00:00Z",
                "reason_code": "AGENT_SELF_APPROVAL", "decision_ref": "invalid",
                "evidence_refs": ["invalid"], "effective": True,
            }
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("final authority must be human" in item for item in errors))
        self.assertTrue(any("terminal receipt incomplete" in item for item in errors))

    def test_pending_decision_cannot_claim_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][1]["final_disposition"]["effective"] = True
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("pending disposition claims effect" in item for item in errors))

    def test_pending_concurrence_cannot_claim_actor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            concurrence = docket["decision_requests"][0]["required_concurrences"][0]
            concurrence["authority_actor"] = {
                "actor_kind": "HUMAN", "human_identity_ref": "human:example",
                "authority_role": "Security Authority", "authority_mode": "DIRECT", "delegation_ref": None,
            }
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("pending Security Authority concurrence claims authority" in item for item in errors))

    def test_self_reviewed_technical_acceptance_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            review = docket["technical_review"]
            review["checker"] = review["maker"]
            review["candidate_commit_sha"] = docket["repository_binding"]["commit_sha"]
            review["candidate_tree_sha"] = docket["repository_binding"]["tree_sha"]
            review["verdict"] = "ACCEPT_EXACT_SHA"
            review["independence_asserted"] = True
            review["reviewed_at"] = "2026-07-21T20:30:00+07:00"
            review["evidence_refs"] = ["docs/evidence/EVD-GOV-001-program-g0-controls.md"]
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("maker and checker must differ" in item for item in errors))

    def test_normalized_technical_identities_cannot_bypass_self_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            review = docket["technical_review"]
            review["maker"]["identity_ref"] = "  Same   Agent "
            review["checker"] = {
                **review["maker"],
                "identity_ref": "same agent",
            }
            review["candidate_commit_sha"] = docket["repository_binding"]["commit_sha"]
            review["candidate_tree_sha"] = docket["repository_binding"]["tree_sha"]
            review["verdict"] = "ACCEPT_EXACT_SHA"
            review["independence_asserted"] = True
            review["reviewed_at"] = "2026-07-21T20:30:00+07:00"
            review["evidence_refs"] = ["docs/evidence/EVD-GOV-001-program-g0-controls.md"]
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("maker and checker must differ" in item for item in errors))

    def test_future_review_and_missing_evidence_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            review = docket["technical_review"]
            review["candidate_commit_sha"] = docket["repository_binding"]["commit_sha"]
            review["candidate_tree_sha"] = docket["repository_binding"]["tree_sha"]
            review["checker"] = {
                "actor_kind": "AGENT", "identity_ref": "independent-checker",
                "role": "QA & Evidence Agent", "registration_ref": None, "session_ref": None,
            }
            review["verdict"] = "ACCEPT_EXACT_SHA"
            review["independence_asserted"] = True
            review["reviewed_at"] = "2027-07-22T00:00:00Z"
            review["evidence_refs"] = ["does/not/exist.md"]
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("reviewed_at chronology invalid" in item for item in errors))
        self.assertTrue(any("evidence missing" in item for item in errors))

    def test_technical_acceptance_requires_distinct_resolved_candidate_and_bound_evidence(self):
        candidate = "b" * 40
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            evidence = root / "docs/evidence/candidate-review.md"
            evidence.write_text(f"# Review\nExact candidate: `{candidate}`\n", encoding="utf-8")
            docket = self.load_docket(root)
            review = docket["technical_review"]
            review.update({
                "candidate_commit_sha": candidate,
                "candidate_tree_sha": EXPECTED_TREE,
                "checker": {
                    "actor_kind": "AGENT", "identity_ref": "independent-checker",
                    "role": "QA & Evidence Agent", "registration_ref": None, "session_ref": None,
                },
                "independence_asserted": True,
                "verdict": "ACCEPT_EXACT_SHA",
                "reviewed_at": "2026-07-21T20:30:00+07:00",
                "evidence_refs": ["docs/evidence/candidate-review.md"],
            })
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertFalse(any("technical review" in item for item in errors), errors)

    def test_technical_acceptance_rejects_repository_binding_as_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            review = docket["technical_review"]
            candidate = docket["repository_binding"]["commit_sha"]
            evidence = root / "docs/evidence/candidate-review.md"
            evidence.write_text(candidate, encoding="utf-8")
            review.update({
                "candidate_commit_sha": candidate,
                "candidate_tree_sha": EXPECTED_TREE,
                "checker": {"actor_kind":"AGENT","identity_ref":"checker","role":"QA & Evidence Agent","registration_ref":None,"session_ref":None},
                "independence_asserted": True, "verdict": "ACCEPT_EXACT_SHA",
                "reviewed_at": "2026-07-21T20:30:00+07:00",
                "evidence_refs": ["docs/evidence/candidate-review.md"],
            })
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("must not equal repository binding" in item for item in errors))

    def test_technical_acceptance_rejects_wrong_tree_and_unbound_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            evidence = root / "docs/evidence/candidate-review.md"
            evidence.write_text("no candidate binding", encoding="utf-8")
            review = docket["technical_review"]
            review.update({
                "candidate_commit_sha": "b" * 40, "candidate_tree_sha": "0" * 40,
                "checker": {"actor_kind":"AGENT","identity_ref":"checker","role":"QA & Evidence Agent","registration_ref":None,"session_ref":None},
                "independence_asserted": True, "verdict": "ACCEPT_EXACT_SHA",
                "reviewed_at": "2026-07-21T20:30:00+07:00",
                "evidence_refs": ["docs/evidence/candidate-review.md"],
            })
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("candidate commit/tree mismatch" in item for item in errors))
        self.assertTrue(any("evidence must contain exact candidate SHA" in item for item in errors))

    def test_technical_acceptance_rejects_non_ancestor_candidate(self):
        candidate = "b" * 40
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            evidence = root / "docs/evidence/candidate-review.md"
            evidence.write_text(candidate, encoding="utf-8")
            docket = self.load_docket(root)
            docket["technical_review"].update({
                "candidate_commit_sha":candidate, "candidate_tree_sha":EXPECTED_TREE,
                "checker":{"actor_kind":"AGENT","identity_ref":"checker","role":"QA & Evidence Agent","registration_ref":None,"session_ref":None},
                "independence_asserted":True, "verdict":"ACCEPT_EXACT_SHA",
                "reviewed_at":"2026-07-21T20:30:00+07:00",
                "evidence_refs":["docs/evidence/candidate-review.md"],
            })
            self.save_docket(root, docket)
            errors = self.validate(root, ancestor=False)
        self.assertTrue(any("candidate must be between repository binding and HEAD" in item for item in errors))

    def test_expired_decision_request_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][0]["expires_at"] = "2026-07-21T12:00:00Z"
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("PG-G0-DEC-001 expired" in item for item in errors))

    def test_terminal_reject_still_requires_human_independence_and_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            decision = docket["decision_requests"][1]
            decision["checked_by"] = decision["prepared_by"]
            decision["final_authority_actor"] = self.authority_actor(
                decision["prepared_by"]["identity_ref"], "Engineering Authority", kind="AGENT"
            )
            decision["final_disposition"] = {
                "value": "REJECT", "decided_at": None, "reason_code": "REJECTED",
                "decision_ref": None, "evidence_refs": [], "effective": False,
            }
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("final authority must be human" in item for item in errors))
        self.assertTrue(any("maker, checker and final authority must be distinct" in item for item in errors))
        self.assertTrue(any("requires evidence" in item for item in errors))

    def test_all_terminal_dispositions_remain_ineffective_without_approved_trust_root(self):
        for value in ("APPROVE", "REJECT", "DEFER", "WITHDRAW", "EXPIRE"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                root = self.make_root(temporary)
                docket = self.load_docket(root)
                decision = docket["decision_requests"][4]
                decision["checked_by"] = {
                    "actor_kind": "AGENT", "identity_ref": "independent-evidence-checker",
                    "role": "QA & Evidence Agent", "registration_ref": None, "session_ref": None,
                }
                decision["final_authority_actor"] = self.install_identity_registry(
                    root, "human:engineering", "HUMAN-ENGINEERING", "Engineering Authority"
                )
                if value == "EXPIRE":
                    decision["expires_at"] = "2026-07-21T12:00:00Z"
                    decided_at = "2026-07-21T13:00:00Z"
                else:
                    decided_at = "2026-07-21T15:00:00Z"
                decision["final_disposition"] = {
                    "value": value,
                    "decided_at": decided_at,
                    "reason_code": f"HUMAN_{value}",
                    "decision_ref": f"AUTH-DECISION-{value}",
                    "evidence_refs": ["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
                    "effective": False,
                }
                self.save_docket(root, docket)
                errors = self.validate(root)
            self.assertTrue(
                any("requires an approved effective authority source" in item for item in errors),
                f"{value}: {errors}",
            )
            self.assertFalse(any("terminal receipt incomplete" in item for item in errors), errors)

    def test_fabricated_identity_binding_fails_without_approved_registry_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            decision = docket["decision_requests"][4]
            decision["checked_by"] = {
                "actor_kind":"AGENT", "identity_ref":"checker", "role":"QA & Evidence Agent",
                "registration_ref":None, "session_ref":None,
            }
            decision["final_authority_actor"] = self.authority_actor(
                "fabricated:human", "Engineering Authority"
            )
            decision["final_disposition"] = {
                "value":"REJECT", "decided_at":"2026-07-21T15:00:00Z",
                "reason_code":"REJECT", "decision_ref":"AUTH-REJECT",
                "evidence_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
                "effective":False,
            }
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("approved identity record missing" in item for item in errors), errors)

    def test_identity_binding_hash_tree_status_and_structured_record_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor = self.install_identity_registry(
                root, "human:engineering", "HUMAN-ENGINEERING", "Engineering Authority"
            )
            actor["identity_subject"] = "HUMAN-OTHER"
            actor["role_binding_sha256"] = "0" * 64
            actor["role_binding_tree_sha"] = "0" * 40
            actor["role_binding_status"] = "draft"
            docket = self.load_docket(root)
            decision = docket["decision_requests"][4]
            decision["checked_by"] = {"actor_kind":"AGENT","identity_ref":"checker","role":"QA & Evidence Agent","registration_ref":None,"session_ref":None}
            decision["final_authority_actor"] = actor
            decision["final_disposition"] = {"value":"REJECT","decided_at":"2026-07-21T15:00:00Z","reason_code":"REJECT","decision_ref":"AUTH-REJECT","evidence_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],"effective":False}
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("role binding status must be approved" in item for item in errors))
        self.assertTrue(any("role binding commit/tree mismatch" in item for item in errors))
        self.assertTrue(any("role binding sha256 mismatch" in item for item in errors))
        self.assertTrue(any("record does not match actor" in item for item in errors))

    def test_delegation_ref_and_bound_record_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor = self.install_identity_registry(
                root, "human:delegate", "HUMAN-DELEGATE", "Engineering Authority"
            )
            delegation_path = root / "docs/00-governance/delegations/engineering.json"
            delegation_path.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "delegation_id":"DELEGATION-001", "grantor_human_identity_ref":"human:grantor",
                "delegate_human_identity_ref":"human:delegate", "authority_role":"Engineering Authority",
                "action_ids":["ACCEPT_EVIDENCE"],
                "subject_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
                "valid_from":"2026-07-21T00:00:00Z", "expires_at":"2026-08-01T00:00:00Z",
                "revoked_at":None, "evidence_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],
            }
            delegation_path.write_text(json.dumps({"entries":[record]}, indent=2)+"\n", encoding="utf-8")
            actor["authority_mode"] = "DELEGATED"
            actor["delegation_ref"] = "docs/00-governance/delegations/engineering.json#WRONG-ID"
            actor["delegation_binding"] = {
                "delegation_id":"DELEGATION-001", "artifact_ref":"docs/00-governance/delegations/engineering.json",
                "artifact_sha256":hashlib.sha256(delegation_path.read_bytes()).hexdigest(),
                "commit_sha":"a"*40, "tree_sha":EXPECTED_TREE, **record,
            }
            docket = self.load_docket(root)
            decision = docket["decision_requests"][4]
            decision["checked_by"] = {"actor_kind":"AGENT","identity_ref":"checker","role":"QA & Evidence Agent","registration_ref":None,"session_ref":None}
            decision["final_authority_actor"] = actor
            decision["final_disposition"] = {"value":"REJECT","decided_at":"2026-07-21T15:00:00Z","reason_code":"REJECT","decision_ref":"AUTH-REJECT","evidence_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],"effective":False}
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("delegation_ref does not match binding" in item for item in errors))

    def test_delegation_bound_hash_and_structured_scope_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor = self.install_identity_registry(root, "human:delegate", "HUMAN-DELEGATE", "Engineering Authority")
            path = root / "docs/00-governance/delegations/engineering.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            record = {"delegation_id":"DELEGATION-001","grantor_human_identity_ref":"human:grantor","delegate_human_identity_ref":"human:delegate","authority_role":"Engineering Authority","action_ids":["ACCEPT_EVIDENCE"],"subject_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],"valid_from":"2026-07-21T00:00:00Z","expires_at":"2026-08-01T00:00:00Z","revoked_at":None,"evidence_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"]}
            path.write_text(json.dumps({"entries":[record]}, indent=2)+"\n", encoding="utf-8")
            actor.update({
                "authority_mode":"DELEGATED",
                "delegation_ref":"docs/00-governance/delegations/engineering.json#DELEGATION-001",
                "delegation_binding":{
                    "delegation_id":"DELEGATION-001","artifact_ref":"docs/00-governance/delegations/engineering.json",
                    "artifact_sha256":"0"*64,"commit_sha":"a"*40,"tree_sha":EXPECTED_TREE,
                    **{**record, "subject_refs":["docs/other.md"]},
                },
            })
            docket = self.load_docket(root)
            decision = docket["decision_requests"][4]
            decision["checked_by"]={"actor_kind":"AGENT","identity_ref":"checker","role":"QA & Evidence Agent","registration_ref":None,"session_ref":None}
            decision["final_authority_actor"]=actor
            decision["final_disposition"]={"value":"REJECT","decided_at":"2026-07-21T15:00:00Z","reason_code":"REJECT","decision_ref":"AUTH-REJECT","evidence_refs":["docs/evidence/EVD-GOV-001-program-g0-controls.md"],"effective":False}
            self.save_docket(root,docket)
            errors=self.validate(root)
        self.assertTrue(any("delegation subject scope missing" in item for item in errors))
        self.assertTrue(any("delegation bound artifact sha256 mismatch" in item for item in errors))
        self.assertTrue(any("delegation record does not match binding" in item for item in errors))

    def test_delegation_grantor_requires_explicit_action_and_subject_scopes(self):
        for malformed in (False, True):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as temporary:
                root = self.make_root(temporary)
                actor, registry_path, _ = self.install_delegated_actor(root)
                registry = json.loads(registry_path.read_text(encoding="utf-8"))
                grantor = registry["entries"][1]
                if malformed:
                    grantor["delegation_action_ids"] = None
                    grantor["delegation_subject_refs"] = 7
                else:
                    grantor.pop("delegation_action_ids")
                    grantor.pop("delegation_subject_refs")
                registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
                actor["role_binding_sha256"] = hashlib.sha256(registry_path.read_bytes()).hexdigest()
                self.install_actor_on_evidence_decision(root, actor)
                errors = self.validate(root)
            self.assertTrue(any("delegation grantor action scope missing" in item for item in errors), errors)
            self.assertTrue(any("delegation grantor subject scope missing" in item for item in errors), errors)

    def test_revoked_delegate_and_grantor_identities_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor, registry_path, _ = self.install_delegated_actor(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["entries"][0]["revoked_at"] = "2026-07-21T12:00:00Z"
            registry["entries"][1]["revoked_at"] = "2026-07-21T12:00:00Z"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            actor["role_binding_sha256"] = hashlib.sha256(registry_path.read_bytes()).hexdigest()
            self.install_actor_on_evidence_decision(root, actor)
            errors = self.validate(root)
        self.assertTrue(any("identity role binding is revoked" in item for item in errors), errors)
        self.assertTrue(any("delegation grantor is revoked" in item for item in errors), errors)

    def test_identity_validity_and_evidence_are_mandatory_and_well_formed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor, registry_path, _ = self.install_delegated_actor(root)
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            delegate, grantor = registry["entries"]
            delegate["valid_from"] = "not-a-date"
            delegate.pop("expires_at")
            delegate.pop("revoked_at")
            delegate.pop("evidence_refs")
            grantor["valid_from"] = "not-a-date"
            grantor.pop("expires_at")
            grantor.pop("revoked_at")
            grantor.pop("evidence_refs")
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
            actor["role_binding_sha256"] = hashlib.sha256(registry_path.read_bytes()).hexdigest()
            self.install_actor_on_evidence_decision(root, actor)
            errors = self.validate(root)
        self.assertTrue(any("identity role binding is not currently effective" in item for item in errors), errors)
        self.assertTrue(any("identity role binding must be an array" in item for item in errors), errors)
        self.assertTrue(any("identity role binding is revoked or lacks revocation state" in item for item in errors), errors)
        self.assertTrue(any("delegation grantor is not currently effective" in item for item in errors), errors)
        self.assertTrue(any("delegation grantor must be an array" in item for item in errors), errors)
        self.assertTrue(any("delegation grantor is revoked or lacks revocation state" in item for item in errors), errors)

    def test_delegation_scope_types_fail_closed_without_exceptions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor, _, _ = self.install_delegated_actor(root)
            actor["delegation_binding"]["action_ids"] = None
            actor["delegation_binding"]["subject_refs"] = 7
            self.install_actor_on_evidence_decision(root, actor)
            errors = self.validate(root)
        self.assertTrue(any("delegation action scope missing" in item for item in errors), errors)
        self.assertTrue(any("delegation subject scope missing" in item for item in errors), errors)

    def test_identity_evidence_must_exist_at_bound_commit(self):
        evidence_ref = "docs/evidence/EVD-GOV-001-program-g0-controls.md"
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            actor = self.install_identity_registry(
                root, "human:engineering", "HUMAN-ENGINEERING", "Engineering Authority"
            )
            self.install_actor_on_evidence_decision(root, actor)
            errors = self.validate(root, missing_committed_paths={evidence_ref})
        self.assertTrue(any(
            "identity role binding evidence absent at bound commit" in item for item in errors
        ), errors)

    def test_nonconcur_requires_attributable_human_time_expiry_and_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            concurrence = docket["decision_requests"][0]["required_concurrences"][0]
            concurrence["disposition"] = "NONCONCUR"
            concurrence["authority_actor"] = self.authority_actor("AGT-SEC", "Security Authority", kind="AGENT")
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("final authority must be human" in item for item in errors))
        self.assertTrue(any("requires decided_at and expires_at" in item for item in errors))
        self.assertTrue(any("requires evidence" in item for item in errors))

    def test_matrix_self_approval_safeguard_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            matrix_path = root / AUTHORITY_MATRIX_PATH
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
            matrix["entries"][0]["self_approval_allowed"] = True
            matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
            digest = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
            docket = self.load_docket(root)
            docket["authority_source"]["sha256"] = digest
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("action safeguards invalid" in item for item in errors))

    def test_matrix_action_class_concurrence_and_expiry_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            matrix_path = root / AUTHORITY_MATRIX_PATH
            matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
            action = matrix["entries"][0]
            action["action_class"] = "pending"
            action["required_concurrence"] = ["Architecture Authority", "Architecture Authority"]
            action["expiry_required"] = "yes"
            matrix_path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
            digest = hashlib.sha256(matrix_path.read_bytes()).hexdigest()
            docket = self.load_docket(root)
            docket["authority_source"]["sha256"] = digest
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("action_class invalid" in item for item in errors))
        self.assertTrue(any("required_concurrence invalid" in item for item in errors))
        self.assertTrue(any("expiry_required invalid" in item for item in errors))

    def test_invalid_state_transition_and_future_history_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            first = docket["state_history"][0]
            docket["state_history"] = [first, {
                **first,
                "sequence": 2,
                "from": "DRAFT",
                "to": "DISPOSED",
                "changed_at": "2027-07-22T00:00:00Z",
            }]
            docket["state"] = "DISPOSED"
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("transition DRAFT->DISPOSED invalid" in item for item in errors))
        self.assertTrue(any("chronology invalid" in item for item in errors))

    def test_terminal_state_is_immutable_and_ready_can_only_dispose(self):
        for current, target in (("DISPOSED", "SUPERSEDED"), ("READY_FOR_FINAL_DISPOSITION", "WITHDRAWN")):
            with self.subTest(current=current, target=target), tempfile.TemporaryDirectory() as temporary:
                root = self.make_root(temporary)
                docket = self.load_docket(root)
                first = docket["state_history"][0]
                docket["state_history"].extend([
                    {**first, "sequence":2, "from":"DRAFT", "to":"TECHNICAL_REVIEW", "changed_at":"2026-07-21T14:00:00Z"},
                    {**first, "sequence":3, "from":"TECHNICAL_REVIEW", "to":"PENDING_HUMAN_DECISIONS", "changed_at":"2026-07-21T15:00:00Z"},
                    {**first, "sequence":4, "from":"PENDING_HUMAN_DECISIONS", "to":"READY_FOR_FINAL_DISPOSITION", "changed_at":"2026-07-21T16:00:00Z"},
                ])
                sequence = 5
                if current == "DISPOSED":
                    docket["state_history"].append({**first, "sequence":sequence, "from":"READY_FOR_FINAL_DISPOSITION", "to":"DISPOSED", "changed_at":"2026-07-21T17:00:00Z"})
                    sequence += 1
                docket["state_history"].append({**first, "sequence":sequence, "from":current, "to":target, "changed_at":"2026-07-21T18:00:00Z"})
                docket["state"] = target
                self.save_docket(root, docket)
                errors = self.validate(root)
            self.assertTrue(any(f"transition {current}->{target} invalid" in item for item in errors))

    def test_expired_docket_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            with patch("tools.validate_pg_g0_authority_docket.resolve_tree", return_value=EXPECTED_TREE):
                errors = validate_pg_g0_authority_docket(
                    root, datetime(2026, 8, 22, tzinfo=timezone.utc)
                )
        self.assertIn("authority docket expired", errors)

    def test_missing_instruction_surface_must_be_disclosed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["blockers"] = [item.replace("Roadmap.md", "roadmap") for item in docket["blockers"]]
            (root / "Roadmap.md").unlink()
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertIn("missing controlled path must be disclosed: Roadmap.md", errors)

    def test_non_authority_flags_must_all_remain_false(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["non_authority_flags"]["production_implementation_authorized"] = True
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertIn("pending authority docket cannot grant authority", errors)

    def test_prepared_dispositions_are_exact_pending_and_ineffective(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["prepared_dispositions"] = docket["prepared_dispositions"][:-1]
            docket["prepared_dispositions"][0]["effective"] = True
            docket["prepared_dispositions"][1]["authority_actor"] = self.authority_actor(
                "human:operator-001", "Engineering Authority"
            )
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("must match Batch 2" in item for item in errors), errors)
        self.assertTrue(any("must remain pending and ineffective" in item for item in errors), errors)
        self.assertTrue(any("claims human disposition" in item for item in errors), errors)

    def test_binding_inventory_digest_and_count_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            inventory_path = root / "docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.2-BINDING-INVENTORY.json"
            inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory["records"][0]["sha256"] = "0" * 64
            inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
            digest_errors = self.validate(root)
        self.assertTrue(any("digest mismatch" in item for item in digest_errors), digest_errors)

        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["binding_inventory"]["record_count"] += 1
            self.save_docket(root, docket)
            count_errors = self.validate(root)
        self.assertTrue(any("record count mismatch" in item for item in count_errors), count_errors)

    def test_adopted_matrix_must_match_signed_proposal_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            matrix = json.loads((root / AUTHORITY_MATRIX_PATH).read_text(encoding="utf-8"))
            matrix["entries"][0]["action_class"] = "invented"
            (root / AUTHORITY_MATRIX_PATH).write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
            errors = self.validate(root)
        self.assertTrue(any("differ from signed substrate proposal" in item for item in errors), errors)

    def test_report_integrity_detects_missing_and_stale_output(self):
        expected = format_report(build_readiness_report(ROOT, AS_OF))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            self.assertTrue(any("missing" in item for item in check_report(path, expected)))
            path.write_text("{}\n", encoding="utf-8")
            self.assertTrue(any("stale" in item for item in check_report(path, expected)))
            path.write_text(expected, encoding="utf-8")
            self.assertEqual(check_report(path, expected), [])

    def test_committed_readiness_report_is_current(self):
        expected = format_report(build_readiness_report(ROOT))
        report_path = ROOT / "artifacts/validation/program-g0-authority-readiness.json"
        self.assertEqual(check_report(report_path, expected), [])

    def test_versioned_manifest_excludes_canonical_and_its_own_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs/manifests").mkdir(parents=True)
            (root / "docs/example.md").write_text("# Example\n", encoding="utf-8")
            (root / "docs/DOCUMENT-MANIFEST.json").write_text("{}\n", encoding="utf-8")
            output = Path("docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json")
            (root / output).write_text("{}\n", encoding="utf-8")
            manifest = build_manifest(output, root)
        self.assertEqual([item["path"] for item in manifest["documents"]], ["docs/example.md"])

    def test_versioned_manifest_normalizes_text_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs/manifests").mkdir(parents=True)
            document = root / "docs/example.md"
            output = Path("docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json")
            document.write_bytes(b"# Example\r\n\r\n**Status:** Draft\r\n")
            windows_record = build_manifest(output, root)["documents"][0]
            document.write_bytes(b"# Example\n\n**Status:** Draft\n")
            unix_record = build_manifest(output, root)["documents"][0]
        self.assertEqual(windows_record, unix_record)

    def test_versioned_manifest_uses_platform_independent_path_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs/manifests").mkdir(parents=True)
            (root / "docs/a.md").write_text("# Lower\n", encoding="utf-8")
            (root / "docs/B.md").write_text("# Upper\n", encoding="utf-8")
            output = Path("docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json")
            paths = [item["path"] for item in build_manifest(output, root)["documents"]]
        self.assertEqual(paths, ["docs/B.md", "docs/a.md"])


if __name__ == "__main__":
    unittest.main()
