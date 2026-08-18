"""
Phase 3 producers validated against their own frozen JSON Schemas.

Work package: BOPEN-P35-001
Contracts: contracts/schemas/rate-limit-decision.schema.json
           contracts/schemas/quota-reservation.schema.json
           contracts/schemas/module-manifest.schema.json
           contracts/schemas/entitlement-reason-codes.json
Governing finding: F-4 in docs/evidence/phase-3/completion-decision.md section 4.2

WHY THIS FILE EXISTS

`tests/contracts/test_contract_schemas.py` loads the schema *documents* and asserts things
about them — that required lists contain certain names, that `additionalProperties` is false.
Every one of those assertions passed while `RateLimitDecision.to_dict()` emitted nine schema
violations, because asserting about a schema is not the same as validating an object against
it. A schema document is always consistent with itself.

So these tests do the one thing that suite could not: they construct an instance the way
production constructs it, serialize it, and hand the result to `jsonschema.validate()`. An
instance test fails when the code drifts from the contract. A document test cannot.

Every case here runs the real producer. None of them hand-build a dict that happens to match
the schema — that would test the test. No database is required; all Phase 3 producers in
scope are in-memory.

A NOTE ON `format: date-time`

Both schemas declare `format: date-time`, but `jsonschema` only enforces `format` when a
`FormatChecker` is supplied AND the relevant third-party validator is installed. In this
environment `rfc3339-validator` is absent, so `FormatChecker().checkers` has no `date-time`
entry and the constraint silently no-ops. The checker is still passed (it becomes real if the
dependency is ever added), but the timestamp assertions below parse the emitted strings
explicitly so the date-time claim is genuinely checked either way.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema

from kernel_core.capability import InvalidModuleManifestError, ModuleManifest, ModuleStatus
from kernel_core.entitlement import EntitlementEvaluator, PlanTier, RateLimiter
from kernel_core.types import ContextPayload
from platform_kernel.metering import QuotaWindow, UsageMeterService

ROOT = Path(__file__).resolve().parents[2]

# Test doubles — see tests/support/stores.py for why they are not shipped in the package.
from tests.support.stores import (
    FakeFeatureToggleStore,
    FakeQuotaReservationStore,
    FakeRateLimitStore,
)
SCHEMA_DIR = ROOT / "contracts" / "schemas"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate(instance: dict, schema: dict) -> None:
    """Validate with a format checker attached. See the module docstring on `format`."""
    jsonschema.validate(
        instance=instance,
        schema=schema,
        format_checker=jsonschema.FormatChecker(),
    )


def assert_rfc3339(testcase: unittest.TestCase, value: str, field: str) -> None:
    """
    Parse a serialized timestamp, since the installed `jsonschema` cannot.

    `datetime.fromisoformat` accepts the full ISO 8601 profile that `.isoformat()` emits.
    The offset assertion is the part that matters: a naive timestamp on a billing or
    rate-limiting record is ambiguous by exactly the server's UTC offset.
    """
    parsed = datetime.fromisoformat(value)
    testcase.assertIsNotNone(
        parsed.tzinfo,
        msg=f"{field} serialized without a UTC offset ({value!r}); the instant is ambiguous.",
    )


class RateLimitDecisionInstanceTests(unittest.TestCase):
    """contracts/schemas/rate-limit-decision.schema.json against the real RateLimiter."""

    def setUp(self):
        self.schema = load_schema("rate-limit-decision.schema.json")
        self.reason_codes = load_schema("entitlement-reason-codes.json")
        self.tenant_id = "tnt_alpha"
        self.rate_limits = FakeRateLimitStore()
        self.limiter = RateLimiter(self.rate_limits)

    def test_allowed_decision_validates(self):
        """
        The allow path is the common path, and it was one of the nine violations.

        `additionalProperties: false` means a misnamed field fails twice — once as a missing
        required property, once as a forbidden extra one.
        """
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 5)
        decision = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-allow-1")

        self.assertTrue(decision.allowed)
        validate(decision.to_dict(), self.schema)

    def test_throttled_decision_validates(self):
        """
        The deny path carries the 429 and is what a client sees when throttled, so it has to
        serialize at least as well as the allow path.
        """
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 1)
        self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-deny-1")
        decision = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-deny-2")

        self.assertFalse(decision.allowed)
        validate(decision.to_dict(), self.schema)

    def test_current_rate_is_consumption_not_headroom(self):
        """
        The sharpest assertion in this file.

        `current_rate` and `remaining` are complements, so emitting headroom under the name
        `current_rate` produces a document that validates perfectly against the frozen schema
        and reports the exact opposite number. Schema validation alone cannot catch a semantic
        inversion between two same-typed fields — only a value assertion can.

        Three calls against a limit of ten: consumption is 3, headroom is 7. If those are ever
        swapped, this fails and the two validation tests above still pass.
        """
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 10)
        for i in range(3):
            decision = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", f"corr-{i}")

        payload = decision.to_dict()
        self.assertEqual(payload["current_rate"], 3, "current_rate must count calls consumed")
        self.assertEqual(payload["limit_rate"], 10)
        self.assertEqual(decision.remaining, 7, "remaining is the complement, not the count")
        self.assertEqual(
            payload["current_rate"] + decision.remaining,
            payload["limit_rate"],
            msg="consumed + headroom must equal the limit; a violation here means one is the other",
        )
        validate(payload, self.schema)

    def test_denied_decision_does_not_consume(self):
        """
        A rejected call must not increment consumption. If it did, `current_rate` would climb
        past `limit_rate` on every retry and the reported figure would describe attempts
        rather than usage — which is what a customer gets billed against.
        """
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 2)
        for i in range(2):
            self.limiter.evaluate(self.tenant_id, "cap_invoice_create", f"corr-fill-{i}")

        first_denial = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-x")
        second_denial = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-y")

        self.assertEqual(first_denial.current_rate, 2)
        self.assertEqual(second_denial.current_rate, 2, "a denied call must not consume quota")
        self.assertLessEqual(second_denial.current_rate, second_denial.limit_rate)
        validate(second_denial.to_dict(), self.schema)

    def test_correlation_id_is_the_callers_value(self):
        """
        The schema requires `correlation_id` with `minLength: 1`, which any non-empty
        placeholder satisfies. This asserts the emitted value is the one the caller passed,
        because a constant would validate while destroying the request tracing the field
        exists to provide.
        """
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 5)
        decision = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-traceable-42")

        self.assertEqual(decision.to_dict()["correlation_id"], "corr-traceable-42")
        validate(decision.to_dict(), self.schema)

    def test_status_code_matches_the_canonical_reason_code_map(self):
        """
        `entitlement-reason-codes.json` carries `x-bopen-http-status-map`, the single source
        of truth binding reason codes to HTTP statuses. The rate-limit schema's own
        `status_code` enum only constrains the value to {200, 429} — it cannot tell that a
        200 was paired with a denial. This checks the pairing against the canonical map
        rather than against a number restated in the test.
        """
        status_map = self.reason_codes["x-bopen-http-status-map"]
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 1)

        allowed = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-map-1")
        throttled = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-map-2")

        for decision in (allowed, throttled):
            payload = decision.to_dict()
            self.assertIn(payload["reason_code"], self.reason_codes["enum"])
            self.assertEqual(
                payload["status_code"],
                status_map[payload["reason_code"]],
                msg=f"{payload['reason_code']} must map to {status_map[payload['reason_code']]}",
            )
            validate(payload, self.schema)

    def test_timestamp_carries_an_offset(self):
        """See `assert_rfc3339` — the installed jsonschema cannot enforce `format: date-time`."""
        self.rate_limits.set_policy(self.tenant_id, "cap_invoice_create", 5)
        decision = self.limiter.evaluate(self.tenant_id, "cap_invoice_create", "corr-ts")
        assert_rfc3339(self, decision.to_dict()["evaluated_at"], "evaluated_at")

    def test_decision_reached_through_the_evaluator_validates(self):
        """
        `RateLimiter` is not called directly in production; `EntitlementEvaluator.evaluate`
        drives it. This runs the real path so that the `correlation_id` threading is exercised
        as wired, not as constructed by a test.
        """
        rate_limits = FakeRateLimitStore()
        evaluator = EntitlementEvaluator(
            feature_toggle_store=FakeFeatureToggleStore(), rate_limit_store=rate_limits
        )
        evaluator.register_plan(
            PlanTier(
                plan_id="plan_free",
                name="Free Tier",
                entitlements={"cap_invoice_create": {"type": "boolean", "value": True}},
            )
        )
        evaluator.assign_tenant_plan("tnt_alpha", "plan_free")
        evaluator.set_rate_limit("tnt_alpha", "cap_invoice_create", 1)
        context = ContextPayload(
            context_id="ctx_456",
            principal_id="usr_alice",
            tenant_id="tnt_alpha",
            active_membership_id="mem_alice_alpha",
            roles=["member"],
        )

        evaluator.evaluate(context, "cap_invoice_create", correlation_id="corr-wired-1")
        throttled = evaluator.evaluate(context, "cap_invoice_create", correlation_id="corr-wired-2")

        self.assertEqual(throttled.reason_code, "DENY_RATE_LIMIT_EXCEEDED")
        self.assertEqual(throttled.http_status, 429)
        self.assertEqual(throttled.correlation_id, "corr-wired-2")


class ModuleManifestContractTests(unittest.TestCase):
    """
    contracts/schemas/module-manifest.schema.json against `ModuleManifest.from_dict`.

    `ModuleManifest` has no `to_dict()`, so there is no serialized instance to validate.
    What exists is a consumer: `from_dict` reads manifest documents. So these tests validate
    the document against the schema first, then feed the same document to the consumer —
    checking the direction the contract is actually used in.
    """

    def setUp(self):
        self.schema = load_schema("module-manifest.schema.json")
        self.manifest_doc = {
            "module_id": "mod_leasing",
            "name": "Leasing Management",
            "version": "1.0.0",
            "min_platform_version": "1.0.0",
            "capabilities": ["cap_lease_create", "cap_lease_read"],
            "resources": ["res_lease"],
            "dependencies": [{"module_id": "mod_core", "version_constraint": ">=1.0.0"}],
        }

    def test_schema_valid_manifest_is_accepted(self):
        """A document the contract accepts must be a document the loader accepts."""
        validate(self.manifest_doc, self.schema)

        manifest = ModuleManifest.from_dict(self.manifest_doc)
        self.assertEqual(manifest.module_id, "mod_leasing")
        self.assertEqual(manifest.capabilities, ("cap_lease_create", "cap_lease_read"))
        self.assertEqual(manifest.status, ModuleStatus.REGISTERED)

    def test_loader_rejects_documents_the_schema_rejects(self):
        """
        Dropping a required property must fail both the schema and the loader. If the loader
        accepted it, the schema would be decorative on this path.
        """
        incomplete = dict(self.manifest_doc)
        del incomplete["capabilities"]

        with self.assertRaises(jsonschema.ValidationError):
            validate(incomplete, self.schema)
        with self.assertRaises(InvalidModuleManifestError):
            ModuleManifest.from_dict(incomplete)

    def test_status_key_is_a_known_contract_contradiction(self):
        """
        CHARACTERIZATION TEST — this pins a known defect rather than asserting correct
        behaviour. It should be deleted when governance rules on the contradiction.

        `module-manifest.schema.json` defines no `status` property and sets
        `additionalProperties: false`, so a manifest document carrying `status` is contract-
        invalid. Yet `ModuleManifest.from_dict` reads `data.get("status", ...)` and honours it,
        letting a caller set a module's lifecycle state at load time — bypassing the
        registered -> validated -> approved -> available transitions the registry enforces.

        The schema and the loader disagree about whether `status` is a legal input key. Both
        halves are asserted here so the contradiction is visible in test output instead of
        living only in prose. Resolving it means either adding `status` to the schema or
        removing it from `from_dict`; the schema is frozen, so this test does neither.
        """
        with_status = dict(self.manifest_doc, status="available")

        with self.assertRaises(jsonschema.ValidationError):
            validate(with_status, self.schema)

        manifest = ModuleManifest.from_dict(with_status)
        self.assertEqual(
            manifest.status,
            ModuleStatus.AVAILABLE,
            msg="from_dict honours a key the frozen schema forbids — see this test's docstring",
        )


class QuotaReservationInstance(unittest.TestCase):
    """contracts/schemas/quota-reservation.schema.json against the real UsageMeterService.

    This module's header has listed this schema since it was written, and until now no case in it
    validated a QuotaReservation. The coverage existed only in database-gated integration tests, so
    when the database timed out on 2026-08-17 the conformance gate reported the schema as uncovered
    and returned a false regression.

    The service is constructed with an in-memory reservation store. Nothing is hand-built: the
    instance comes from `create_quota_reservation`, and the store returns a real monthly window so
    the service's own `_assert_window_matches` still runs.
    """

    def setUp(self) -> None:
        self.schema = load_schema("quota-reservation.schema.json")
        self.store = FakeQuotaReservationStore()
        self.service = UsageMeterService(reservations=self.store)

    def _reserve(self, quantity: int = 5) -> object:
        return self.service.create_quota_reservation(
            tenant_id="tnt_11111111-2222-3333-4444-555555555555",
            capability_id="cap_reporting_export",
            reserved_quantity=quantity,
            expires_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
            correlation_id="corr_11111111-2222-3333-4444-555555555555",
            quota_window=QuotaWindow.MONTHLY,
        )

    def test_a_reservation_validates_against_its_frozen_schema(self) -> None:
        reservation = self._reserve()
        validate(reservation.to_dict(), self.schema)

    def test_the_producer_actually_ran(self) -> None:
        """A validate() over a dict the test built itself would pass while proving nothing."""
        reservation = self._reserve(7)
        self.assertEqual(len(self.store.created), 1, "the service never reached the store")
        self.assertEqual(reservation.reserved_quantity, 7)
        self.assertEqual(reservation.reservation_id, self.store.created[0].reservation_id)

    def test_the_service_window_check_is_still_enforced(self) -> None:
        """The fake must not be able to dodge a check the real repository cannot dodge."""
        self.store.window_end = self.store.window_start + timedelta(days=3)
        with self.assertRaises(Exception) as caught:
            self._reserve()
        self.assertIn("window", str(caught.exception).lower())


if __name__ == "__main__":
    unittest.main()
