"""Adversarial contract tests for the QUAL-P0-02 synthetic identity subject."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from validate_identity_qualification import (  # noqa: E402
    CATALOG,
    COMMON_CATALOG_SHA256,
    NEGATIVE_CATEGORIES,
    SCHEMA_FILES,
    build_manifest,
    validate_catalog,
    validate_identity_package,
    validate_identity_schema,
    validate_manifest,
    validate_semantics,
)


class IdentityQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schemas, cls.catalog_errors = validate_catalog(ROOT)

    def test_catalog_and_offline_refs_are_valid(self):
        self.assertEqual(self.catalog_errors, [])
        self.assertEqual(set(self.schemas), set(SCHEMA_FILES))
        catalog = json.loads((ROOT / CATALOG).read_text(encoding="utf-8"))
        self.assertEqual(catalog["imports"][0]["sha256"], COMMON_CATALOG_SHA256)

    def test_every_schema_is_synthetic_qualification_only(self):
        for name, schema in self.schemas.items():
            props = schema["properties"]
            self.assertEqual(props["qualification_only"], {"const": True}, name)
            self.assertEqual(props["synthetic_data_only"], {"const": True}, name)
            self.assertEqual(validate_identity_schema(schema, name), [])

    def test_exact_issuer_subject_and_no_claim_authority(self):
        self.assertEqual(validate_semantics(self.schemas), [])
        provider = self.schemas["provider-connection.observation.schema.json"]
        self.assertEqual(provider["properties"]["identity_key_policy"]["const"], "EXACT_ISSUER_AND_SUBJECT")
        rendered = json.dumps(self.schemas, sort_keys=True)
        for marker in ("email_linking_authorized", "domain_linking_authorized", "group_linking_authorized", "role_linking_authorized", "tenant_authority_authorized"):
            self.assertIn(f'"{marker}": {{"const": false}}', rendered)

    def test_all_downstream_effects_are_none(self):
        for name, schema in self.schemas.items():
            effects = schema["$defs"]["downstreamEffects"]["properties"]
            self.assertTrue(effects)
            self.assertTrue(all(value == {"const": "NONE"} for value in effects.values()), name)

    def test_full_negative_catalog_is_mandatory(self):
        testcase = self.schemas["test-case-result.observation.schema.json"]
        categories = set(testcase["properties"]["category"]["enum"])
        self.assertEqual(categories, NEGATIVE_CATEGORIES)
        self.assertEqual(testcase["properties"]["skipped"], {"const": False})

    def test_key_policy_mutation_fails(self):
        changed = copy.deepcopy(self.schemas)
        changed["provider-connection.observation.schema.json"]["properties"]["identity_key_policy"] = {"const": "EMAIL"}
        errors = validate_semantics(changed)
        self.assertTrue(any("exact issuer+subject" in item for item in errors))

    def test_missing_negative_case_fails(self):
        changed = copy.deepcopy(self.schemas)
        changed["test-case-result.observation.schema.json"]["properties"]["category"]["enum"].remove("OIDC_ISSUER_MIXUP")
        errors = validate_semantics(changed)
        self.assertTrue(any("mandatory negative categories missing" in item for item in errors))

    def test_runtime_or_tenant_effect_mutation_fails(self):
        schema = copy.deepcopy(self.schemas["principal-session.projection.schema.json"])
        schema["$defs"]["downstreamEffects"]["properties"]["tenant"] = {"const": "CREATED"}
        errors = validate_identity_schema(schema, "principal-session.projection.schema.json")
        self.assertTrue(any("must be NONE: tenant" in item for item in errors))
        schema = copy.deepcopy(self.schemas["principal-session.projection.schema.json"])
        schema["properties"]["tenant_context_ref"] = {"type": ["string", "null"]}
        changed = dict(self.schemas)
        changed["principal-session.projection.schema.json"] = schema
        self.assertTrue(any("must not create tenant context" in item for item in validate_semantics(changed)))

    def test_raw_token_and_acceptance_fields_fail(self):
        changed = copy.deepcopy(self.schemas)
        changed["auth-assertion.observation.schema.json"]["properties"]["raw_token_present"] = {"type": "boolean"}
        self.assertTrue(any("raw tokens" in item for item in validate_semantics(changed)))
        testcase = copy.deepcopy(self.schemas["test-case-result.observation.schema.json"])
        testcase["properties"]["verifier"] = {"type": "string"}
        testcase["required"].append("verifier")
        errors = validate_identity_schema(testcase, "test-case-result.observation.schema.json")
        self.assertTrue(any("prohibited acceptance" in item for item in errors))

    def test_manifest_binds_raw_bytes(self):
        expected = build_manifest(ROOT)
        self.assertGreater(len(expected["records"]), 10)
        self.assertTrue(all(record["bytes"] > 0 for record in expected["records"]))
        self.assertEqual(validate_manifest(ROOT), [])

    def test_complete_package_validates_without_execution(self):
        self.assertEqual(validate_identity_package(ROOT), [])
        self.assertFalse((ROOT / "docs/evidence/qualification/QUAL-P0-02/checker-receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
