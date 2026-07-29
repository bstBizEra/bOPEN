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
        context = self._establish_context(tenant_id, principal_id, membership_id)
        return {
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "membership_id": membership_id,
            "context": context,
        }

    # -- the slice ----------------------------------------------------------------

    def test_full_phase1_chain_over_http(self):
        """The whole chain, ending in an audit row that the tenant can read back."""
        principal_id = self._register_principal()
        tenant_id, membership_id = self._provision_tenant(principal_id)
        context = self._establish_context(tenant_id, principal_id, membership_id)

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


if __name__ == "__main__":
    unittest.main()
