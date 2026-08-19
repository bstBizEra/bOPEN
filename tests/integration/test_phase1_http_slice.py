"""
Phase 1 vertical slice executed end to end over HTTP against PostgreSQL.

Work package: BOPEN-P35-001 (WP-P35-02, deliverable D-07)
Governing artifacts: BOPEN-AUTHZ-001, BOPEN-TENANT-001, AGENTS.md section 8, section 9
Contracts: contracts/schemas/tenant-context.json
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial), R5 (fails loudly)

The chain from FIRST-VERTICAL-SLICE-SPEC.md, driven through a real ASGI transport and landing
in a real database:

    POST /v1/principals -> POST /v1/tenants -> POST /v1/contexts
    -> POST /v1/authorize -> audit row readable under the tenant's own policy

Requests go through `TestClient`, which exercises routing, header dependencies and status
codes. Calling the handler functions directly would bypass exactly the layer this work package
added, and would pass whether or not the HTTP surface worked.

Without BOPEN_DATABASE_URL these tests FAIL rather than skip, per EBIV R5.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))

CONTEXT_SCHEMA = ROOT / "contracts" / "schemas" / "tenant-context.json"


def _unavailable_reason() -> str | None:
    for module in ("psycopg", "fastapi", "httpx", "jsonschema"):
        try:
            __import__(module)
        except ImportError:
            return f"{module} is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return (
            "BOPEN_DATABASE_URL is not set. Provision a verification database with "
            "`python tools/db_bootstrap.py --apply` and export the URL it prints."
        )
    return None


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


class TestHttpSliceAvailability(unittest.TestCase):
    """Guard test — the HTTP slice cannot be verified without a database (EBIV R5)."""

    def test_http_slice_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "The Phase 1 HTTP slice cannot be verified in this environment, so no "
                f"admissible evidence exists for it.\n\n{reason}\n\n"
                "This failure is intentional under BOPEN-GOV-EBIV-001 R5."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database or web stack unavailable — reported as a failure by TestHttpSliceAvailability",
)
class TestPhase1HttpSlice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from platform_kernel.api import app

        cls.client = TestClient(app)
        cls.schema = json.loads(CONTEXT_SCHEMA.read_text(encoding="utf-8"))

    # -- helpers ------------------------------------------------------------------

    def _register_principal(self) -> str:
        response = self.client.post(
            "/v1/principals",
            json={"email": f"p-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["principal_id"]

    def _provision_tenant(self, owner_id: str) -> tuple[str, str]:
        response = self.client.post(
            "/v1/tenants",
            json={"name": f"Tenant {uuid.uuid4().hex[:8]}", "owner_principal_id": owner_id},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        return body["tenant_id"], body["owner_membership_id"]

    def _establish_context(self, tenant_id: str, principal_id: str, membership_id: str) -> dict:
        """Return the envelope from POST /v1/contexts.

        The contract-shaped payload is at `["context"]` and the credential is its sibling.
        They are separate because tenant-context.json declares `additionalProperties: false`,
        so a token field inside the payload would put the response out of conformance with its
        own frozen contract.
        """
        response = self.client.post(
            "/v1/contexts",
            json={"principal_id": principal_id, "membership_id": membership_id},
            headers={"X-Tenant-ID": tenant_id, "X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def _new_tenant_with_context(self) -> dict:
        principal_id = self._register_principal()
        tenant_id, membership_id = self._provision_tenant(principal_id)
        envelope = self._establish_context(tenant_id, principal_id, membership_id)
        return {
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "membership_id": membership_id,
            "context": envelope["context"],
            "envelope": envelope,
        }

    # -- the slice ----------------------------------------------------------------

    def test_full_phase1_chain_over_http(self):
        """The whole chain, ending in an audit row that the tenant can read back."""
        principal_id = self._register_principal()
        tenant_id, membership_id = self._provision_tenant(principal_id)
        envelope = self._establish_context(tenant_id, principal_id, membership_id)
        context = envelope["context"]

        correlation = corr()
        decision = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={
                "X-Tenant-ID": tenant_id,
                "X-Context-ID": context["context_id"],
                "X-Correlation-ID": correlation,
            },
        )
        self.assertEqual(decision.status_code, 200, decision.text)
        body = decision.json()
        self.assertEqual(body["decision"], "ALLOW")
        self.assertEqual(body["reason_code"], "MEMBERSHIP_ROLE_PERMITTED")
        self.assertEqual(body["tenant_id"], tenant_id)

        events = self.client.get(
            "/v1/audit-events",
            headers={
                "X-Tenant-ID": tenant_id,
                "X-Context-ID": context["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(events.status_code, 200, events.text)
        recorded = events.json()["events"]
        matching = [e for e in recorded if e["correlation_id"] == correlation]
        self.assertEqual(
            len(matching), 1, "the authorization decision was not persisted as an audit event"
        )
        self.assertEqual(matching[0]["decision"], "allow")
        self.assertEqual(matching[0]["reason_code"], "MEMBERSHIP_ROLE_PERMITTED")

    def test_context_payload_satisfies_the_frozen_contract(self):
        """tenant-context.json requires `context_id` as format uuid and requires `expires_at`.

        The in-memory `ContextPayload` satisfies neither: it emits `ctx_<uuid>` and has no
        `expires_at` field at all. This assertion is what stops the HTTP surface from
        inheriting that divergence, and is the check whose absence let the Phase 3
        `RateLimitDecision` defect survive a green suite.
        """
        import jsonschema

        context = self._new_tenant_with_context()["context"]
        jsonschema.validate(instance=context, schema=self.schema)
        uuid.UUID(context["context_id"])  # raises if not a bare UUID
        self.assertIn("expires_at", context)
        self.assertGreater(context["expires_at"], context["issued_at"])

    # -- adversarial: cross-tenant ------------------------------------------------

    def test_context_from_another_tenant_is_refused(self):
        """The core cross-tenant probe.

        Tenant A presents its own valid context but claims tenant B in the header. The context
        lookup runs inside tenant B's isolation policy, where A's context does not exist, so
        the request is refused. This is what makes `X-Tenant-ID` safe to accept unauthenticated.
        """
        a = self._new_tenant_with_context()
        b = self._new_tenant_with_context()

        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={
                "X-Tenant-ID": b["tenant_id"],
                "X-Context-ID": a["context"]["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["detail"], "context is not valid")

    def test_audit_events_are_scoped_to_the_callers_tenant(self):
        """Tenant A must not see tenant B's audit trail.

        No tenant filter appears in the query behind this endpoint; the row-level security
        policy is what scopes it. If this assertion fails, the policy is not in force.
        """
        a = self._new_tenant_with_context()
        b = self._new_tenant_with_context()

        b_correlation = corr()
        self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={
                "X-Tenant-ID": b["tenant_id"],
                "X-Context-ID": b["context"]["context_id"],
                "X-Correlation-ID": b_correlation,
            },
        )

        a_view = self.client.get(
            "/v1/audit-events",
            headers={
                "X-Tenant-ID": a["tenant_id"],
                "X-Context-ID": a["context"]["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(a_view.status_code, 200)
        leaked = [e for e in a_view.json()["events"] if e["correlation_id"] == b_correlation]
        self.assertEqual(leaked, [], "tenant A read an audit event belonging to tenant B")

    def test_membership_from_another_tenant_cannot_establish_a_context(self):
        a = self._new_tenant_with_context()
        b = self._new_tenant_with_context()

        response = self.client.post(
            "/v1/contexts",
            json={
                "principal_id": a["principal_id"],
                "membership_id": a["membership_id"],
            },
            headers={"X-Tenant-ID": b["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 403, response.text)

    def test_resource_created_in_one_tenant_is_invisible_to_another(self):
        a = self._new_tenant_with_context()
        b = self._new_tenant_with_context()

        created = self.client.post(
            "/v1/resources",
            params={"resource_name": "confidential"},
            headers={
                "X-Tenant-ID": a["tenant_id"],
                "X-Context-ID": a["context"]["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(created.status_code, 201, created.text)
        resource_id = created.json()["resource_id"]

        # Tenant A can read it.
        own = self.client.get(
            f"/v1/resources/{resource_id}",
            headers={
                "X-Tenant-ID": a["tenant_id"],
                "X-Context-ID": a["context"]["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(own.status_code, 200, own.text)

        # Tenant B, fully authorized within its own boundary, cannot.
        foreign = self.client.get(
            f"/v1/resources/{resource_id}",
            headers={
                "X-Tenant-ID": b["tenant_id"],
                "X-Context-ID": b["context"]["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(
            foreign.status_code,
            404,
            "tenant B read a resource owned by tenant A",
        )

    # -- adversarial: headers and identifiers -------------------------------------

    def test_missing_correlation_id_is_rejected(self):
        """Mandatory per HTTP_HEADER_SPEC.md, and not generated server-side.

        Generating one would produce an audit trail that cannot be joined to the caller's own
        logs while looking as though it can be.
        """
        response = self.client.post(
            "/v1/principals",
            json={"email": "no-corr@example.com", "type": "human"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("X-Correlation-ID", response.json()["detail"])

    def test_missing_tenant_header_is_rejected(self):
        response = self.client.post(
            "/v1/contexts",
            json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("X-Tenant-ID", response.json()["detail"])

    def test_authorize_without_context_is_unauthorized(self):
        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={"X-Tenant-ID": str(uuid.uuid4()), "X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 401)

    def test_prefixed_identifier_form_from_the_header_spec_is_accepted(self):
        """HTTP_HEADER_SPEC.md documents `tnt_<uuid>`; migration 001 stores bare UUID.

        Both forms are accepted at the boundary so a satellite product following the published
        spec is not silently broken by the storage decision.
        """
        a = self._new_tenant_with_context()
        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={
                "X-Tenant-ID": f"tnt_{a['tenant_id']}",
                "X-Context-ID": f"ctx_{a['context']['context_id']}",
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["decision"], "ALLOW")

    def test_malformed_identifier_is_a_client_error_not_a_server_error(self):
        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={
                "X-Tenant-ID": "not-a-uuid",
                "X-Context-ID": str(uuid.uuid4()),
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(response.status_code, 400, response.text)

    def test_unknown_context_is_refused_indistinguishably(self):
        """A context that does not exist and one belonging to another tenant return the same
        body, so a caller cannot use the difference to probe for other tenants' contexts."""
        a = self._new_tenant_with_context()
        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={
                "X-Tenant-ID": a["tenant_id"],
                "X-Context-ID": str(uuid.uuid4()),
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "context is not valid")

    def test_context_issuance_is_refused_unless_the_deployment_affirms_it_is_not_production(self):
        """The guard over an authentication gap that Phase 1 cannot close.

        `POST /v1/contexts` mints a signed bearer token after verifying that a membership exists
        in the named tenant, belongs to the named principal, and is active. It cannot verify that
        the caller *is* that principal, because Phase 1 has no authentication mechanism —
        `BOPEN-P1-001` puts authentication in Phase 2 with the IdP bridge.

        A security review demonstrated the consequence end to end on 2026-07-30: a client with no
        prior state and no credential header received 201, a token carrying `roles: ["owner"]`,
        and an ALLOW on `/v1/authorize`.

        The identifiers involved are UUIDv4 and no endpoint echoes them, so there is no in-band
        harvest path — but that is a property of the current endpoint set, not a control. What
        makes the gap dangerous is that the surface looks finished: signed tokens, a JWKS
        endpoint, row-level security, an audit trail. The missing half is invisible from outside.

        So the kernel refuses by default and the operator must affirm otherwise, in the same shape
        `BOPEN_DB_NON_PRODUCTION` guards the destructive rollback. A deployment that forgets is
        refused rather than silently open.

        503 rather than 401 is deliberate: no credential the caller could supply would change the
        answer, and 401 would imply one exists.
        """
        import os

        from platform_kernel.api import ENV_ALLOW_UNAUTHENTICATED_IDENTITY

        principal_id = self._register_principal()
        tenant_id, membership_id = self._provision_tenant(principal_id)

        previous = os.environ.pop(ENV_ALLOW_UNAUTHENTICATED_IDENTITY, None)
        try:
            response = self.client.post(
                "/v1/contexts",
                json={"principal_id": principal_id, "membership_id": membership_id},
                headers={"X-Tenant-ID": tenant_id, "X-Correlation-ID": corr()},
            )
        finally:
            if previous is not None:
                os.environ[ENV_ALLOW_UNAUTHENTICATED_IDENTITY] = previous

        self.assertEqual(
            response.status_code, 503,
            "an unaffirmed deployment issued a bearer token to an unauthenticated caller",
        )
        detail = response.json()["detail"]
        self.assertIn(ENV_ALLOW_UNAUTHENTICATED_IDENTITY, detail["remediation"])
        self.assertIn("WP-P35-05", detail["resolved_by"])

    def test_provisioning_a_tenant_is_refused_on_an_unaffirmed_deployment(self):
        """
        The same gap as context issuance, on the endpoint it was missed on.

        The guard was written after a finding that named only `POST /v1/contexts`. Following it
        up on 2026-07-30 showed `POST /v1/tenants` has the same hole: it creates a tenant and its
        owner membership from a principal identifier the caller supplies, and Phase 1 cannot
        check that the caller is that principal. Naming someone else's principal returned 201 —
        a tenant exists with a third party bound to it as owner, who never agreed. Phase 2's
        invitation engine models that consent, invited then accepted, and this path went around
        it.

        A test asserting the refusal on one endpoint and not the other is what let this sit, so
        the flag is now named for the assertion rather than for either endpoint.
        """
        import os

        from platform_kernel.api import ENV_ALLOW_UNAUTHENTICATED_IDENTITY

        principal_id = self._register_principal()

        previous = os.environ.pop(ENV_ALLOW_UNAUTHENTICATED_IDENTITY, None)
        try:
            response = self.client.post(
                "/v1/tenants",
                json={"name": "Unaffirmed", "owner_principal_id": principal_id},
                headers={"X-Correlation-ID": corr()},
            )
        finally:
            if previous is not None:
                os.environ[ENV_ALLOW_UNAUTHENTICATED_IDENTITY] = previous

        self.assertEqual(
            response.status_code, 503,
            "an unaffirmed deployment bound a principal it could not authenticate to a new "
            "tenant as its owner",
        )
        detail = response.json()["detail"]
        self.assertIn(ENV_ALLOW_UNAUTHENTICATED_IDENTITY, detail["remediation"])
        self.assertIn("WP-P35-05", detail["resolved_by"])

    def test_one_flag_governs_every_endpoint_that_acts_on_an_unproven_identity(self):
        """
        Removing the affirmation must silence the whole surface that acts on an identity it cannot
        verify, and must leave the rest — /health — working.

        This test once asserted that registration stayed open when the flag was removed, on the
        reasoning that registration "asserts no identity it has not just created". D-D3-002 Option B
        (operator-disposed 2026-08-02) overrides that: principal creation is out of band, not a
        public self-service endpoint, and the operator accepted "no self-service registration" as
        its cost. So with no authenticator and the flag removed, registration is refused too. The
        three endpoints that act on an unproven claim — registration, tenant provisioning, context
        issuance — all answer to the one affirmation; /health acts on no identity and keeps working.
        """
        import os

        from platform_kernel.api import ENV_ALLOW_UNAUTHENTICATED_IDENTITY

        previous = os.environ.pop(ENV_ALLOW_UNAUTHENTICATED_IDENTITY, None)
        try:
            registration = self.client.post(
                "/v1/principals",
                json={"email": f"g-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
                headers={"X-Correlation-ID": corr()},
            )
            provisioning = self.client.post(
                "/v1/tenants",
                json={"name": "G", "owner_principal_id": f"usr_{uuid.uuid4()}"},
                headers={"X-Correlation-ID": corr()},
            )
            context = self.client.post(
                "/v1/contexts",
                json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
                headers={"X-Tenant-ID": str(uuid.uuid4()), "X-Correlation-ID": corr()},
            )
            health = self.client.get("/health", headers={"X-Correlation-ID": corr()})
        finally:
            if previous is not None:
                os.environ[ENV_ALLOW_UNAUTHENTICATED_IDENTITY] = previous

        self.assertEqual(
            registration.status_code, 503,
            "D-D3-002 Option B: principal creation is out-of-band; removing the affirmation "
            "silences it too",
        )
        self.assertEqual(provisioning.status_code, 503)
        self.assertEqual(context.status_code, 503)
        self.assertEqual(health.status_code, 200)

    def test_the_affirmation_does_not_weaken_any_other_check(self):
        """Setting the flag permits issuance; it must not turn off validation.

        A guard that also disabled the membership checks would trade one hole for a wider one, so
        the same refusals are asserted with the affirmation in place.
        """
        a = self._new_tenant_with_context()
        b = self._new_tenant_with_context()

        crossed = self.client.post(
            "/v1/contexts",
            json={"principal_id": a["principal_id"], "membership_id": a["membership_id"]},
            headers={"X-Tenant-ID": b["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(crossed.status_code, 403)

        mismatched = self.client.post(
            "/v1/contexts",
            json={"principal_id": b["principal_id"], "membership_id": a["membership_id"]},
            headers={"X-Tenant-ID": a["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(mismatched.status_code, 403)

    def test_health_does_not_require_the_database(self):
        """A health probe that opens a connection turns a database blip into a rolling
        restart of every replica."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_readiness_reports_persistence(self):
        response = self.client.get("/readiness")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")

    def test_nonexistent_owner_principal_is_rejected(self):
        response = self.client.post(
            "/v1/tenants",
            json={"name": "Orphan", "owner_principal_id": str(uuid.uuid4())},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(response.status_code, 422, response.text)


@unittest.skipIf(
    _unavailable_reason() is not None,
    "database or web stack unavailable — reported as a failure by TestHttpSliceAvailability",
)
class TestAuditableInputBoundary(unittest.TestCase):
    """
    Nothing may be accepted that cannot then be audited.

    BOPEN-AUTHZ-001 requires both allow and deny outcomes to be audited, with no exception. The
    authorization path used to break that in two directions, both reproduced on 2026-07-30:

        body     a 256-character resource_id was accepted, the decision was evaluated, and the
                 audit INSERT raised StringDataRightTruncation. HTTP 500, and the decision that
                 had already been made was recorded nowhere.

        header   X-Correlation-ID was silently truncated to 64 characters, so the audit row
                 carried an identifier the caller had never sent. `require_correlation_id`
                 rejects an absent header precisely so a trail that cannot be joined to the
                 caller's logs does not look joinable; truncation produced that trail anyway.

    Both are now refused at the boundary, before any decision is evaluated. The refusal is the
    point: a rejected request leaves no unrecorded act behind it.
    """

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from platform_kernel.api import app

        cls.client = TestClient(app)

    def _context(self) -> dict:
        principal = self.client.post(
            "/v1/principals",
            json={"email": f"b-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
            headers={"X-Correlation-ID": corr()},
        )
        principal_id = principal.json()["principal_id"]
        tenant = self.client.post(
            "/v1/tenants",
            json={"name": f"B{uuid.uuid4().hex[:8]}", "owner_principal_id": principal_id},
            headers={"X-Correlation-ID": corr()},
        )
        body = tenant.json()
        envelope = self.client.post(
            "/v1/contexts",
            json={"principal_id": principal_id, "membership_id": body["owner_membership_id"]},
            headers={"X-Tenant-ID": body["tenant_id"], "X-Correlation-ID": corr()},
        )
        return {
            "tenant_id": body["tenant_id"],
            "context_id": envelope.json()["context"]["context_id"],
        }

    def _authorize(self, ctx, correlation, **overrides):
        payload = {
            "action": "tenant_resource:read",
            "resource_type": "tenant_resource",
            "resource_id": str(uuid.uuid4()),
        }
        payload.update(overrides)
        return self.client.post(
            "/v1/authorize",
            json=payload,
            headers={
                "X-Tenant-ID": ctx["tenant_id"],
                "X-Context-ID": ctx["context_id"],
                "X-Correlation-ID": correlation,
            },
        )

    def _audit_rows(self, ctx, correlation):
        events = self.client.get(
            "/v1/audit-events",
            headers={
                "X-Tenant-ID": ctx["tenant_id"],
                "X-Context-ID": ctx["context_id"],
                "X-Correlation-ID": corr(),
            },
        )
        self.assertEqual(events.status_code, 200, events.text)
        return [e for e in events.json()["events"] if e["correlation_id"] == correlation]

    def test_a_request_that_fits_is_decided_and_audited(self):
        """The control: the limits must not have made the endpoint refuse ordinary work."""
        ctx = self._context()
        correlation = corr()
        response = self._authorize(ctx, correlation)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(self._audit_rows(ctx, correlation)), 1)

    def test_a_value_too_long_for_the_audit_column_is_refused_before_any_decision(self):
        from platform_kernel.api import (
            AUDIT_ACTION_MAX,
            AUDIT_RESOURCE_ID_MAX,
            AUDIT_RESOURCE_TYPE_MAX,
        )

        ctx = self._context()
        for field, limit in (
            ("resource_id", AUDIT_RESOURCE_ID_MAX),
            ("action", AUDIT_ACTION_MAX),
            ("resource_type", AUDIT_RESOURCE_TYPE_MAX),
        ):
            with self.subTest(field=field):
                correlation = corr()
                response = self._authorize(ctx, correlation, **{field: "A" * (limit + 1)})
                self.assertEqual(
                    response.status_code, 422,
                    f"an over-length {field} was accepted; the decision it produces cannot be "
                    f"stored, so the request must not be",
                )
                self.assertEqual(
                    self._audit_rows(ctx, correlation), [],
                    "a refused request left an audit row behind it",
                )

    def test_an_over_length_correlation_id_is_refused_rather_than_truncated(self):
        from platform_kernel.api import AUDIT_CORRELATION_ID_MAX

        ctx = self._context()
        oversized = "c" * (AUDIT_CORRELATION_ID_MAX + 1)
        response = self._authorize(ctx, oversized)
        self.assertEqual(response.status_code, 400, response.text)

        truncated = oversized[:AUDIT_CORRELATION_ID_MAX]
        self.assertEqual(
            self._audit_rows(ctx, truncated), [],
            "the header was truncated and an audit row was written under an identifier the "
            "caller never sent",
        )

    def test_the_declared_limits_match_the_live_column_widths(self):
        """
        Three constants, each a copy of a column width in a migration. A copy is acceptable only
        while something proves it agrees: if a migration widened `resource_id` the API would
        keep refusing valid input, and if one narrowed it the 500 this class exists to prevent
        would come straight back.
        """
        from platform_kernel import db
        from platform_kernel.api import (
            AUDIT_ACTION_MAX,
            AUDIT_CORRELATION_ID_MAX,
            AUDIT_RESOURCE_ID_MAX,
            AUDIT_RESOURCE_TYPE_MAX,
            RESOURCE_NAME_MAX,
        )

        expected = {
            ("audit_events", "correlation_id"): AUDIT_CORRELATION_ID_MAX,
            ("audit_events", "action"): AUDIT_ACTION_MAX,
            ("audit_events", "resource_type"): AUDIT_RESOURCE_TYPE_MAX,
            ("audit_events", "resource_id"): AUDIT_RESOURCE_ID_MAX,
            ("tenant_resources", "resource_name"): RESOURCE_NAME_MAX,
        }

        with db.system_session() as cur:
            for (table, column), declared in expected.items():
                cur.execute(
                    "SELECT character_maximum_length FROM information_schema.columns "
                    "WHERE table_name = %s AND column_name = %s AND table_schema = "
                    "current_schema()",
                    (table, column),
                )
                row = cur.fetchone()
                self.assertIsNotNone(row, f"{table}.{column} does not exist")
                self.assertEqual(
                    row[0], declared,
                    f"{table}.{column} is {row[0]} wide but the API accepts {declared}",
                )

    def test_registering_an_address_twice_is_a_conflict_not_a_server_error(self):
        """
        The 409 arrives via `psycopg.errors.UniqueViolation`, caught by type. It used to be
        caught by searching the driver's message for "unique" or "duplicate", which worked only
        because of the wording psycopg happens to use: a driver upgrade or a non-English server
        locale would have turned every duplicate address into an unhandled 500.

        This does not close the account-existence oracle — 409 against 201 still answers
        "is this address registered?" to anyone who asks, which security review confirmed and
        `register_principal` records. Removing it means making registration asynchronous behind
        address verification, which belongs to WP-P35-05 along with authenticating this endpoint
        at all.
        """
        email = f"dup-{uuid.uuid4().hex[:12]}@example.com"
        payload = {"email": email, "type": "human"}

        first = self.client.post("/v1/principals", json=payload,
                                 headers={"X-Correlation-ID": corr()})
        second = self.client.post("/v1/principals", json=payload,
                                  headers={"X-Correlation-ID": corr()})

        self.assertEqual(first.status_code, 201, first.text)
        self.assertEqual(second.status_code, 409, second.text)


if __name__ == "__main__":
    unittest.main()
