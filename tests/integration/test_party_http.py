"""MILE-4.1 party graph over HTTP — bearer-gated, tenant-isolated (BOPEN-PARTY-001).

Governed by DEC-P4-ENTRY, BOPEN-PARTY-001, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed HTTP against PostgreSQL), R4 (the refusals are the
point), R5 (loud).

The isolation probes here are the first proof that the Phase 3.5 boundary holds for real business
data over the wire: a party created by one tenant is invisible to another through the API, and a
relationship cannot be formed across tenants. Every write goes through a signed bearer token — a
party endpoint is not a new unauthenticated hole.
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))


def _unavailable_reason() -> str | None:
    try:
        import psycopg  # noqa: F401
    except ImportError:
        return "psycopg is not installed."
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set."
    if not os.environ.get("BOPEN_CONTEXT_TOKEN_KEY", "").strip():
        return "BOPEN_CONTEXT_TOKEN_KEY is not set."
    return None


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


class TestPartyHttpEvidenceCanBeProduced(unittest.TestCase):
    def test_party_http_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "stack unavailable — reported by the guard test")
class TestPartyHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from platform_kernel.api import app

        cls.client = TestClient(app, raise_server_exceptions=False)

    def _tenant_with_token(self) -> dict:
        principal = self.client.post(
            "/v1/principals",
            json={"email": f"p-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(principal.status_code, 201, principal.text)
        principal_id = principal.json()["principal_id"]
        tenant = self.client.post(
            "/v1/tenants",
            json={"name": f"T{uuid.uuid4().hex[:8]}", "owner_principal_id": principal_id},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(tenant.status_code, 201, tenant.text)
        envelope = self.client.post(
            "/v1/contexts",
            json={
                "principal_id": principal_id,
                "membership_id": tenant.json()["owner_membership_id"],
            },
            headers={"X-Tenant-ID": tenant.json()["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(envelope.status_code, 201, envelope.text)
        return {"tenant_id": tenant.json()["tenant_id"], "token": envelope.json()["access_token"]}

    def _auth(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "X-Correlation-ID": corr()}

    def _create_party(self, token: str, name: str, party_type: str = "organization") -> str:
        r = self.client.post(
            "/v1/parties",
            json={"party_type": party_type, "display_name": name},
            headers=self._auth(token),
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["party_id"]

    # -- the flow -----------------------------------------------------------------------

    def test_create_and_read_a_party(self):
        t = self._tenant_with_token()
        party_id = self._create_party(t["token"], "Acme Corp", "organization")
        r = self.client.get(f"/v1/parties/{party_id}", headers=self._auth(t["token"]))
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["display_name"], "Acme Corp")
        self.assertEqual(body["party_type"], "organization")
        self.assertEqual(body["tenant_id"], t["tenant_id"])

    def test_a_relationship_between_two_parties_in_a_tenant(self):
        t = self._tenant_with_token()
        seller = self._create_party(t["token"], "Seller Ltd")
        buyer = self._create_party(t["token"], "Buyer Ltd")
        r = self.client.post(
            "/v1/party-relationships",
            json={"from_party_id": seller, "to_party_id": buyer, "relationship_type": "supplies"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["relationship_type"], "supplies")

    # -- isolation and integrity (the refusals) -----------------------------------------

    def test_a_party_is_invisible_to_another_tenant_over_http(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        party_id = self._create_party(a["token"], "A private customer")
        r = self.client.get(f"/v1/parties/{party_id}", headers=self._auth(b["token"]))
        self.assertEqual(r.status_code, 404, "tenant B read tenant A's party over HTTP")

    def test_a_relationship_cannot_cross_tenants_over_http(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        a_party = self._create_party(a["token"], "A org")
        b_party = self._create_party(b["token"], "B org")
        # A holds a valid bearer; it names a party of B as the other endpoint.
        r = self.client.post(
            "/v1/party-relationships",
            json={"from_party_id": a_party, "to_party_id": b_party, "relationship_type": "supplies"},
            headers=self._auth(a["token"]),
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_a_self_relationship_is_refused(self):
        t = self._tenant_with_token()
        p = self._create_party(t["token"], "Solo")
        r = self.client.post(
            "/v1/party-relationships",
            json={"from_party_id": p, "to_party_id": p, "relationship_type": "owns"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 422, r.text)

    def test_creating_a_party_requires_a_bearer(self):
        r = self.client.post(
            "/v1/parties",
            json={"party_type": "person", "display_name": "No Auth"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)

    def test_an_unknown_party_type_is_refused(self):
        t = self._tenant_with_token()
        r = self.client.post(
            "/v1/parties",
            json={"party_type": "alien", "display_name": "Invalid"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 422, r.text)


if __name__ == "__main__":
    unittest.main()
