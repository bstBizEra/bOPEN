"""Negative and positive tests for the authority identity register validator.

Covers the EVD-GOV-005 corrections: status-dependent approval provenance,
evidence requirements, docket-compatible identity semantics and the
DIRECT-only authority mode for this revision.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.validate_authority_identity_register import (  # noqa: E402
    BOUND_PATH,
    DRAFT_PATH,
    validate_authority_identity_register,
)


class AuthorityIdentityRegisterTests(unittest.TestCase):
    @staticmethod
    def load_live_register() -> dict:
        source = ROOT / BOUND_PATH
        if not source.is_file():
            source = ROOT / DRAFT_PATH
        return json.loads(source.read_text(encoding="utf-8"))

    @classmethod
    def draft_baseline(cls) -> dict:
        register = cls.load_live_register()
        register["status"] = "draft"
        if not register["version"].endswith("-draft"):
            register["version"] += "-draft"
        register["approved_by"] = None
        register["approved_at"] = None
        register["approval_ref"] = None
        for entry in register["entries"]:
            entry["status"] = "pending"
        return register

    def make_root(self, temporary: str) -> Path:
        root = Path(temporary)
        register = self.draft_baseline()
        referenced = set()
        for entry in register["entries"]:
            referenced.update(entry["subject_refs"])
            referenced.update(entry["evidence_refs"])
        for relative in referenced:
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_file():
                shutil.copy2(source, target)
            else:
                target.write_text("placeholder\n", encoding="utf-8")
        self.save(root, register)
        return root

    @staticmethod
    def load(root: Path) -> dict:
        return json.loads((root / DRAFT_PATH).read_text(encoding="utf-8"))

    @staticmethod
    def save(root: Path, register: dict, path: Path = DRAFT_PATH) -> None:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(register, indent=2) + "\n", encoding="utf-8")

    def test_current_draft_register_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            self.assertEqual(validate_authority_identity_register(root), [])

    def test_live_repository_register_passes(self):
        self.assertEqual(validate_authority_identity_register(ROOT), [])

    def test_missing_register_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors = validate_authority_identity_register(Path(temporary))
        self.assertTrue(any("REGISTER MISSING" in item for item in errors))

    def test_approved_register_requires_full_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["status"] = "approved"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("requires approved_by" in item for item in errors))
        self.assertTrue(any("requires approved_at" in item for item in errors))
        self.assertTrue(any("requires approval_ref" in item for item in errors))
        self.assertTrue(any("must not use a draft version" in item for item in errors))

    def test_draft_register_must_not_carry_approval_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["approved_by"] = "HUMAN-OPERATOR-001"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("must not carry approval provenance" in item for item in errors))

    def test_entry_cannot_be_approved_inside_draft_register(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["status"] = "approved"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("cannot be approved while the register is not approved" in item for item in errors))

    def test_docket_incompatible_identity_semantics_fail(self):
        cases = (
            ("identity_provider", "google", "identity_provider must be"),
            ("identity_subject", "ounkhamvilay@gmail.com", "identity_subject must match HUMAN-*"),
            ("authority_mode", "DELEGATED", "authority_mode must be DIRECT"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = self.make_root(temporary)
                register = self.load(root)
                register["entries"][0][field] = value
                self.save(root, register)
                errors = validate_authority_identity_register(root)
                self.assertTrue(any(expected in item for item in errors), errors)

    def test_identity_id_and_subject_must_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["identity_subject"] = "HUMAN-OTHER-001"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("must be identical" in item for item in errors))

    def test_empty_or_missing_evidence_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["evidence_refs"] = []
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("evidence_refs must be a non-empty unique list" in item for item in errors))
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["evidence_refs"] = ["docs/evidence/DOES-NOT-EXIST.md"]
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("evidence ref missing on disk" in item for item in errors))

    def test_validity_window_must_be_ordered(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["valid_from"] = "2026-09-01T00:00:00+07:00"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("valid_from must precede expires_at" in item for item in errors))

    def test_revocation_state_is_coupled_to_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["status"] = "revoked"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("revoked entries require a revoked_at timestamp" in item for item in errors))
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["revoked_at"] = "2026-07-22T00:00:00+07:00"
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("must keep revoked_at null" in item for item in errors))

    def test_unapproved_register_at_bound_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            self.save(root, register, BOUND_PATH)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("validator-bound path must be approved" in item for item in errors))

    def test_unknown_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(temporary)
            register = self.load(root)
            register["entries"][0]["can_delegate"] = True
            self.save(root, register)
            errors = validate_authority_identity_register(root)
        self.assertTrue(any("unknown keys" in item and "can_delegate" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
