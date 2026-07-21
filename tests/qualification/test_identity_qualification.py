"""Adversarial contract tests for the QUAL-P0-02 synthetic identity subject."""

from __future__ import annotations

import copy
import json
import re
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
    identity_key_sha256,
    validate_catalog,
    validate_identity_package,
    validate_identity_schema,
    validate_manifest,
    validate_semantics,
    validate_suite_graph,
)


def identity_key(issuer: str, subject: str) -> dict:
    return {
        "issuer_uri": issuer,
        "subject": subject,
        "canonicalization": "RFC8785_EXACT_ISSUER_AND_SUBJECT",
        "issuer_subject_sha256": identity_key_sha256(issuer, subject),
    }


def valid_suite_graph() -> tuple[dict, dict]:
    run_id = "IDQ-RUN-001"
    candidate_id = "IDQ-CANDIDATE-SYNTHETIC-A"
    correlation_id = "synthetic-correlation-001"
    audit_ref = "synthetic-audit-identity-run-001"
    envelope = {"qualification_run_id": run_id}

    def record(record_id: str, **values) -> dict:
        return {
            "record_id": record_id,
            "work_package_id": "QUAL-P0-02",
            "qualification_id": "DEC-0005-QUAL-001",
            "candidate_id": candidate_id,
            "qualification_only": True,
            "synthetic_data_only": True,
            "qualification_envelope": dict(envelope),
            "correlation_id": correlation_id,
            "audit_event_ref": audit_ref,
            **values,
        }

    issuer_plain = "https://issuer-a.synthetic.example"
    issuer_slash = "https://issuer-a.synthetic.example/"
    key_plain = identity_key(issuer_plain, "SubjectAlpha")
    key_slash = identity_key(issuer_slash, "SubjectAlpha")
    key_case = identity_key(issuer_plain, "subjectalpha")
    cases = [
        record(
            f"IDQ-CASE-{index:03d}",
            case_id=f"IDQ-T{index:03d}",
            category=category,
            skipped=False,
        )
        for index, category in enumerate(sorted(NEGATIVE_CATEGORIES), start=1)
    ]
    records = {
        "provider_connection_observations": [
            record("IDQ-PC-001", provider_connection_id="IDQ-CONNECTION-A", issuer_uri=issuer_plain),
            record("IDQ-PC-002", provider_connection_id="IDQ-CONNECTION-B", issuer_uri=issuer_slash),
        ],
        "external_identity_binding_projections": [
            record("IDQ-BIND-001", identity_binding_id="IDQ-IDENTITY-A", provider_connection_id="IDQ-CONNECTION-A", source_assertion_ref="IDQ-ASSERT-001", source_link_ref="IDQ-LINK-001", identity_key=key_plain)
        ],
        "auth_assertion_observations": [
            record("IDQ-ASSERT-001", assertion_id="IDQ-ASSERT-001", provider_connection_id="IDQ-CONNECTION-A", identity_key=key_plain)
        ],
        "principal_session_projections": [
            record("IDQ-SESSION-001", session_projection_id="IDQ-SESSION-001", identity_binding_ref="IDQ-IDENTITY-A", assertion_ref="IDQ-ASSERT-001", assurance_ref="IDQ-ASSURANCE-001")
        ],
        "assurance_evidence_observations": [
            record("IDQ-ASSURANCE-001", assurance_evidence_id="IDQ-ASSURANCE-001", assertion_ref="IDQ-ASSERT-001")
        ],
        "account_link_state_projections": [
            record("IDQ-LINK-001", link_event_id="IDQ-LINK-001", proof_assertion_refs=["IDQ-ASSERT-001"], proof_session_ref=None, identity_key=key_plain)
        ],
        "test_case_result_observations": cases,
        "migration_evidence_observations": [
            record("IDQ-MIG-001", migration_evidence_id="IDQ-MIG-001", source_connection_ref="IDQ-CONNECTION-A", target_connection_ref="IDQ-CONNECTION-B")
        ],
    }
    all_record_ids = [item["record_id"] for group in records.values() for item in group]
    suite = {
        "record_id": "IDQ-SUITE-001",
        "work_package_id": "QUAL-P0-02",
        "qualification_id": "DEC-0005-QUAL-001",
        "candidate_id": candidate_id,
        "qualification_run_id": run_id,
        "qualification_only": True,
        "synthetic_data_only": True,
        "qualification_envelope": dict(envelope),
        "provider_connection_refs": ["IDQ-CONNECTION-A", "IDQ-CONNECTION-B"],
        "case_ids": [item["case_id"] for item in cases],
        "record_refs": {group: [item["record_id"] for item in items] for group, items in records.items()},
        "correlation_bindings": [{"correlation_id": correlation_id, "record_refs": all_record_ids, "audit_event_refs": [audit_ref]}],
        "identity_key_distinctions": [
            {"distinction_kind": "ISSUER_TRAILING_SLASH", "left": key_plain, "right": key_slash, "expected_distinct": True},
            {"distinction_kind": "SUBJECT_CASE", "left": key_plain, "right": key_case, "expected_distinct": True},
        ],
        "coverage_summary": {"mandatory_category_count": len(NEGATIVE_CATEGORIES), "observed_category_count": len(NEGATIVE_CATEGORIES), "missing_category_count": 0, "duplicate_category_count": 0, "skipped_case_count": 0},
        "correlation_id": correlation_id,
        "audit_event_ref": audit_ref,
    }
    return suite, records


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

    def test_valid_suite_binds_one_run_candidate_and_reference_graph(self):
        suite, records = valid_suite_graph()
        self.assertEqual(validate_suite_graph(suite, records), [])

    def test_mixed_run_candidate_and_correlation_fail(self):
        suite, records = valid_suite_graph()
        records["auth_assertion_observations"][0]["qualification_envelope"]["qualification_run_id"] = "IDQ-RUN-999"
        records["assurance_evidence_observations"][0]["candidate_id"] = "IDQ-CANDIDATE-OTHER"
        records["principal_session_projections"][0]["correlation_id"] = "synthetic-correlation-other"
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("mixed qualification run" in item for item in errors))
        self.assertTrue(any("mixed candidate" in item for item in errors))
        self.assertTrue(any("mixed correlation" in item for item in errors))

    def test_dangling_cross_record_reference_fails(self):
        suite, records = valid_suite_graph()
        records["principal_session_projections"][0]["identity_binding_ref"] = "IDQ-IDENTITY-MISSING"
        records["migration_evidence_observations"][0]["target_connection_ref"] = "IDQ-CONNECTION-MISSING"
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("dangling session ref" in item for item in errors))
        self.assertTrue(any("dangling migration provider ref" in item for item in errors))

    def test_missing_duplicate_and_skipped_mandatory_cases_fail(self):
        suite, records = valid_suite_graph()
        cases = records["test_case_result_observations"]
        cases[1]["category"] = cases[0]["category"]
        cases[2]["skipped"] = True
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("duplicate mandatory negative category" in item for item in errors))
        self.assertTrue(any("coverage incomplete" in item for item in errors))
        self.assertTrue(any("skipped mandatory" in item for item in errors))

    def test_duplicate_case_and_record_refs_fail(self):
        suite, records = valid_suite_graph()
        suite["case_ids"][1] = suite["case_ids"][0]
        suite["record_refs"]["auth_assertion_observations"].append("IDQ-ASSERT-001")
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("case IDs missing, duplicate or dangling" in item for item in errors))
        self.assertTrue(any("duplicate record refs" in item for item in errors))

    def test_coverage_summary_or_nonqualification_record_fails(self):
        suite, records = valid_suite_graph()
        suite["coverage_summary"]["missing_category_count"] = 1
        records["auth_assertion_observations"][0]["qualification_only"] = False
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("coverage summary" in item for item in errors))
        self.assertTrue(any("record qualification_only mismatch" in item for item in errors))

    def test_trailing_slash_issuer_is_valid_and_byte_distinct(self):
        provider = self.schemas["provider-connection.observation.schema.json"]
        pattern = provider["properties"]["issuer_uri"]["pattern"]
        plain = "https://issuer-a.synthetic.example"
        slash = plain + "/"
        self.assertIsNotNone(re.fullmatch(pattern, plain))
        self.assertIsNotNone(re.fullmatch(pattern, slash))
        self.assertNotEqual(identity_key_sha256(plain, "SubjectAlpha"), identity_key_sha256(slash, "SubjectAlpha"))
        suite, records = valid_suite_graph()
        self.assertEqual(validate_suite_graph(suite, records), [])

    def test_subject_case_is_preserved_and_wrong_digest_fails(self):
        issuer = "https://issuer-a.synthetic.example"
        self.assertNotEqual(identity_key_sha256(issuer, "SubjectAlpha"), identity_key_sha256(issuer, "subjectalpha"))
        suite, records = valid_suite_graph()
        records["auth_assertion_observations"][0]["identity_key"]["issuer_subject_sha256"] = "0" * 64
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("exact issuer+subject digest mismatch" in item for item in errors))

    def test_correlation_binding_dangling_and_duplicate_membership_fail(self):
        suite, records = valid_suite_graph()
        suite["correlation_bindings"][0]["record_refs"].append("IDQ-ASSERT-999")
        suite["correlation_bindings"].append(copy.deepcopy(suite["correlation_bindings"][0]))
        errors = validate_suite_graph(suite, records)
        self.assertTrue(any("correlation binding dangling" in item for item in errors))
        self.assertTrue(any("exactly one correlation binding" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
