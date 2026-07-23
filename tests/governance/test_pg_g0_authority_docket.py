"""Fail-closed tests for the signed PG-G0 authority docket v0.4 successor."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

from tools.validate_pg_g0_authority_docket import (
    AUTHORITY_MATRIX_PATH,
    BINDING_INVENTORY_PATH,
    DOCKET_PATH,
    ROOT,
    SCHEMA_PATH,
    SIGNED_SUBSTRATE_COMMIT,
    SIGNED_SUBSTRATE_TREE,
    V03_SUBSTRATE_COMMIT,
    V03_SUBSTRATE_TREE,
    build_readiness_report,
    read_file_at_commit as read_repository_file_at_commit,
    validate_pg_g0_authority_docket,
)
from tools.validate_root_control_surfaces import build_package_manifest, validate_root_control_surfaces


AS_OF = datetime(2026, 7, 23, 10, 0, 0, tzinfo=timezone.utc)
BATCH1_TREE = "8789c5e70c2ce87298928d4d02add7ffe5867402"
LEGACY_TREE = "f336976981c9b7e95c96ec8289589e53c1ac506c"


@lru_cache(maxsize=None)
def repository_blob(commit: str, relative: str) -> bytes | None:
    return read_repository_file_at_commit(ROOT, commit, relative)


class PgG0AuthorityDocketV04Tests(unittest.TestCase):
    def make_root(self, temporary: str) -> Path:
        root = Path(temporary)
        docket = json.loads((ROOT / DOCKET_PATH).read_text(encoding="utf-8"))
        paths = {
            DOCKET_PATH,
            SCHEMA_PATH,
            AUTHORITY_MATRIX_PATH,
            BINDING_INVENTORY_PATH,
            Path("docs/00-governance/authority-dockets/PG-G0-AUTH-001-V0.3-BINDING-INVENTORY.json"),
            Path("docs/00-governance/signing/SIGNING-PASS-2.md"),
            Path("docs/00-governance/signing/SIGNING-PASS-3.md"),
            Path("docs/evidence/EVD-GOV-008-docket-v02-independent-review.md"),
            Path("docs/evidence/EVD-GOV-010-docket-v03-independent-review.md"),
            Path("docs/00-governance/PG-G0-OPERATOR-DECISION-PACKET.md"),
        }
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

    def validate(self, root: Path, *, missing: set[str] | None = None) -> list[str]:
        missing = missing or set()

        def committed_file(test_root: Path, commit: str, relative: str):
            if relative in missing:
                return None
            if relative == "docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json":
                source = test_root / relative
                return source.read_bytes() if source.is_file() else None
            committed = repository_blob(commit, relative)
            if committed is not None:
                return committed
            source = test_root / relative
            return source.read_bytes() if source.is_file() else None

        def resolved_tree(_root: Path, commit: str):
            return {
                SIGNED_SUBSTRATE_COMMIT: SIGNED_SUBSTRATE_TREE,
                V03_SUBSTRATE_COMMIT: V03_SUBSTRATE_TREE,
                "26bea090c0aca14f1337c4be1a146fd48bb1f626": BATCH1_TREE,
                "c893062c197e74c15214e5ce1c425b9e9ed8002f": LEGACY_TREE,
            }.get(commit, "f" * 40 if len(commit) == 40 else None)

        with (
            patch("tools.validate_pg_g0_authority_docket.resolve_tree", side_effect=resolved_tree),
            patch("tools.validate_pg_g0_authority_docket.resolve_head", return_value="f" * 40),
            patch("tools.validate_pg_g0_authority_docket.is_ancestor", return_value=True),
            patch("tools.validate_pg_g0_authority_docket.read_file_at_commit", side_effect=committed_file),
            patch(
                "tools.validate_pg_g0_authority_docket.is_tracked_path",
                side_effect=lambda test_root, relative: (test_root / relative).is_file(),
            ),
            patch(
                "tools.validate_pg_g0_authority_docket.commit_datetime",
                return_value=datetime(2026, 7, 23, 8, 0, tzinfo=timezone.utc),
            ),
        ):
            return validate_pg_g0_authority_docket(root, AS_OF)

    def test_repository_v04_is_valid_ready_and_b9_pending(self):
        self.assertEqual(validate_pg_g0_authority_docket(ROOT, AS_OF), [])
        report = build_readiness_report(ROOT, AS_OF)
        self.assertEqual(report["status"], "READY_FOR_HUMAN_GATE_DECISION")
        self.assertTrue(report["ready_for_human_gate_decision"])
        self.assertFalse(report["pg_g0_passed"])
        docket = self.load_docket(ROOT)
        self.assertTrue(docket["effective_outcome"]["ready_for_pg_g0_gate_decision"])
        b8 = docket["decision_requests"][:5]
        self.assertEqual([item["final_disposition"]["value"] for item in b8], ["APPROVE"] * 5)
        b9 = docket["decision_requests"][5]
        self.assertEqual(b9["decision_id"], "PG-G0-DEC-006")
        self.assertEqual(b9["action_id"], "PASS_PG_G0")
        self.assertEqual(b9["final_disposition"]["value"], "PENDING")
        self.assertIsNone(b9["final_authority_actor"])
        self.assertEqual(len(b9["prerequisite_refs"]), 3)

    def test_all_b8_final_actors_bind_to_pass3_identity_register(self):
        docket = self.load_docket(ROOT)
        for decision in docket["decision_requests"][:5]:
            actor = decision["final_authority_actor"]
            self.assertEqual(actor["identity_subject"], "HUMAN-OPERATOR-001")
            self.assertEqual(actor["role_binding_commit_sha"], SIGNED_SUBSTRATE_COMMIT)
            self.assertEqual(actor["role_binding_tree_sha"], SIGNED_SUBSTRATE_TREE)
            self.assertEqual(decision["final_disposition"]["decision_ref"], "docs/00-governance/signing/SIGNING-PASS-3.md#signed-decisions")

    def test_b8_subject_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][2]["subject"]["artifact_ref"] = "docs/decisions/DEC-0007.md"
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("alters the signed v0.3 subject binding" in item for item in errors), errors)

    def test_b8_outcome_cannot_be_changed_or_made_ineffective(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][0]["final_disposition"]["value"] = "REJECT"
            docket["decision_requests"][0]["final_disposition"]["effective"] = False
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("signed B8 outcome must remain APPROVE" in item for item in errors), errors)

    def test_b8_actor_role_binding_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][0]["final_authority_actor"]["authority_role"] = "Product Authority"
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("final authority authority role must be Architecture Authority" in item for item in errors), errors)

    def test_b9_cannot_be_pre_signed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][5]["final_disposition"]["value"] = "APPROVE"
            docket["decision_requests"][5]["final_disposition"]["effective"] = True
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("PG-G0-DEC-006 B9 decision must remain PENDING" in item for item in errors), errors)

    def test_b9_prerequisite_list_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][5]["prerequisite_refs"] = []
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("independent-conformance prerequisites incomplete" in item for item in errors), errors)

    def test_inventory_digest_and_count_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            inventory = json.loads((root / BINDING_INVENTORY_PATH).read_text(encoding="utf-8"))
            inventory["records"][0]["sha256"] = "0" * 64
            (root / BINDING_INVENTORY_PATH).write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
            errors = self.validate(root)
        self.assertTrue(any("binding inventory differs from exact signed-substrate regeneration" in item for item in errors), errors)

    def test_unknown_fields_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["decision_requests"][5]["uncontrolled_approval"] = True
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("unknown field" in item and "uncontrolled_approval" in item for item in errors), errors)

    def test_effective_readiness_cannot_be_false_after_signed_b8(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["effective_outcome"]["ready_for_pg_g0_gate_decision"] = False
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("effective outcomes must match" in item for item in errors), errors)

    def test_prepared_batch2_subjects_remain_immutable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            docket = self.load_docket(root)
            docket["prepared_dispositions"][0]["subject"]["sha256"] = "0" * 64
            self.save_docket(root, docket)
            errors = self.validate(root)
        self.assertTrue(any("alters the signed v0.2 subject" in item for item in errors), errors)

    def test_root_manifest_validation_is_repeatable_and_order_stable(self):
        first = validate_root_control_surfaces()
        second = validate_root_control_surfaces()
        self.assertEqual(first, [])
        self.assertEqual(second, [])
        self.assertEqual(
            build_package_manifest(ROOT),
            json.loads((ROOT / "docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json").read_text(encoding="utf-8")),
        )


if __name__ == "__main__":
    unittest.main()
