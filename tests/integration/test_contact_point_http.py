"""MILE-4.2 Party ContactPoint extension over HTTP — bearer-gated, tenant-isolated, and the
NotificationRecipientResolver keystone (BOPEN-PARTY-002, DEC-P4-ENTRY §10).

Governed by DEC-P4-ENTRY §10, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed HTTP against PostgreSQL), R4 (the refusals — an
unverified endpoint, a wrong-purpose endpoint, a cross-tenant party, a party with no contact point,
a missing bearer), R5 (loud).

The keystone (CP-INV-03): `resolve-recipient` yields a destination ONLY for a verified contact point
of the authorized purpose belonging to a Party of the caller's tenant. It never reads
principals.email: a party with no contact point resolves to a refusal, not to its owner's login email.
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


class TestContactPointHttpEvidenceCanBeProduced(unittest.TestCase):
    def test_contact_point_http_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "stack unavailable — reported by the guard test")
class TestContactPointHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from platform_kernel.api import app

        cls.client = TestClient(app, raise_server_exceptions=False)

    def _tenant_with_token(self) -> dict:
        p = self.client.post(
            "/v1/principals",
            json={"email": f"p-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(p.status_code, 201, p.text)
        pid = p.json()["principal_id"]
        t = self.client.post(
            "/v1/tenants",
            json={"name": f"T{uuid.uuid4().hex[:8]}", "owner_principal_id": pid},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(t.status_code, 201, t.text)
        c = self.client.post(
            "/v1/contexts",
            json={"principal_id": pid, "membership_id": t.json()["owner_membership_id"]},
            headers={"X-Tenant-ID": t.json()["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(c.status_code, 201, c.text)
        return {"tenant_id": t.json()["tenant_id"], "token": c.json()["access_token"]}

    def _auth(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "X-Correlation-ID": corr()}

    def _make_party(self, token: str) -> str:
        r = self.client.post(
            "/v1/parties",
            json={"party_type": "organization", "display_name": f"Org {uuid.uuid4().hex[:6]}"},
            headers=self._auth(token),
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["party_id"]

    def _create_cp(self, token, party_id, endpoint_type="email",
                   endpoint_value="a@example.com", purpose="transactional"):
        return self.client.post(
            f"/v1/parties/{party_id}/contact-points",
            json={"endpoint_type": endpoint_type, "endpoint_value": endpoint_value,
                  "purpose": purpose},
            headers=self._auth(token),
        )

    def _resolve(self, token, party_id, purpose="transactional", channel="email"):
        return self.client.post(
            f"/v1/parties/{party_id}/resolve-recipient",
            json={"purpose": purpose, "channel": channel},
            headers=self._auth(token),
        )

    # -- full CRUD ---------------------------------------------------------------------

    def test_create_read_list_update_retire_a_contact_point(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        # create
        c = self._create_cp(t["token"], party, endpoint_value="ops@example.com")
        self.assertEqual(c.status_code, 201, c.text)
        cp_id = c.json()["contact_point_id"]
        self.assertEqual(c.json()["verification_state"], "unverified")
        self.assertEqual(c.json()["revision"], 1)
        # read
        r = self.client.get(
            f"/v1/parties/{party}/contact-points/{cp_id}", headers=self._auth(t["token"])
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["endpoint_value"], "ops@example.com")
        # list
        lst = self.client.get(
            f"/v1/parties/{party}/contact-points", headers=self._auth(t["token"])
        )
        self.assertEqual(lst.status_code, 200, lst.text)
        self.assertEqual(len(lst.json()), 1)
        # update the purpose under the current revision
        u = self.client.put(
            f"/v1/parties/{party}/contact-points/{cp_id}",
            json={"expected_revision": 1, "purpose": "billing"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(u.status_code, 200, u.text)
        self.assertEqual(u.json()["purpose"], "billing")
        self.assertEqual(u.json()["revision"], 2)
        # retire (tombstone, not hard delete)
        d = self.client.delete(
            f"/v1/parties/{party}/contact-points/{cp_id}", headers=self._auth(t["token"])
        )
        self.assertEqual(d.status_code, 200, d.text)
        self.assertFalse(d.json()["is_primary"])

    def test_a_stale_revision_update_is_refused(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp_id = self._create_cp(t["token"], party).json()["contact_point_id"]
        u = self.client.put(
            f"/v1/parties/{party}/contact-points/{cp_id}",
            json={"expected_revision": 99, "purpose": "general"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(u.status_code, 409, u.text)

    def test_a_malformed_endpoint_is_refused(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        r = self._create_cp(t["token"], party, endpoint_type="email", endpoint_value="not-an-email")
        self.assertEqual(r.status_code, 422, r.text)
        r2 = self._create_cp(t["token"], party, endpoint_type="phone", endpoint_value="abc")
        self.assertEqual(r2.status_code, 422, r2.text)

    def test_a_contact_point_for_a_missing_party_is_404(self):
        t = self._tenant_with_token()
        r = self._create_cp(t["token"], str(uuid.uuid4()))
        self.assertEqual(r.status_code, 404, r.text)

    # -- set primary -------------------------------------------------------------------

    def test_set_primary_moves_the_flag_within_party_and_type(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        first = self._create_cp(t["token"], party, endpoint_value="one@example.com").json()
        second = self._create_cp(t["token"], party, endpoint_value="two@example.com").json()
        r1 = self.client.post(
            f"/v1/parties/{party}/contact-points/{first['contact_point_id']}/set-primary",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertTrue(r1.json()["is_primary"])
        # promoting the second demotes the first — one live primary per (party, type)
        r2 = self.client.post(
            f"/v1/parties/{party}/contact-points/{second['contact_point_id']}/set-primary",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertTrue(r2.json()["is_primary"])
        again = self.client.get(
            f"/v1/parties/{party}/contact-points/{first['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertFalse(again.json()["is_primary"], "the first primary was not demoted")

    # -- verify then resolve: the keystone success path --------------------------------

    def test_verify_then_resolve_returns_the_snapshot(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp_id = self._create_cp(
            t["token"], party, endpoint_value="dest@example.com", purpose="transactional"
        ).json()["contact_point_id"]
        # before verify, resolve refuses (the seam ships closed — every endpoint starts unverified)
        self.assertEqual(self._resolve(t["token"], party).status_code, 422)
        # administrative-assertion verify
        v = self.client.post(
            f"/v1/parties/{party}/contact-points/{cp_id}/verify",
            json={"method": "administrative_assertion"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(v.status_code, 200, v.text)
        self.assertEqual(v.json()["verification_state"], "verified")
        self.assertEqual(v.json()["verification_method"], "administrative_assertion")
        # now resolve returns the snapshot with the resolved endpoint
        r = self._resolve(t["token"], party, purpose="transactional", channel="email")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["endpoint_value"], "dest@example.com")
        self.assertEqual(r.json()["endpoint_type"], "email")
        self.assertEqual(r.json()["purpose"], "transactional")
        self.assertEqual(r.json()["party_id"], party)

    # -- the keystone refusals ---------------------------------------------------------

    def test_resolve_refuses_an_unverified_endpoint(self):
        """CP-INV-03. An endpoint that exists but is unverified yields no destination."""
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        self._create_cp(t["token"], party, purpose="transactional")  # unverified
        self.assertEqual(self._resolve(t["token"], party, purpose="transactional").status_code, 422)

    def test_resolve_refuses_a_wrong_purpose_endpoint(self):
        """CP-INV-03 / CP-INV-09. A verified endpoint of one purpose does not resolve for another."""
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp_id = self._create_cp(
            t["token"], party, purpose="transactional"
        ).json()["contact_point_id"]
        self.client.post(
            f"/v1/parties/{party}/contact-points/{cp_id}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        # verified, but the caller asks for billing — a refusal, not the transactional endpoint
        self.assertEqual(self._resolve(t["token"], party, purpose="billing").status_code, 422)
        # the authorized purpose resolves
        self.assertEqual(self._resolve(t["token"], party, purpose="transactional").status_code, 200)

    def test_resolve_refuses_a_wrong_channel_endpoint(self):
        """CP-INV-03. A verified email does not answer an sms channel (which maps to phone)."""
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp_id = self._create_cp(t["token"], party, endpoint_type="email").json()["contact_point_id"]
        self.client.post(
            f"/v1/parties/{party}/contact-points/{cp_id}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(self._resolve(t["token"], party, channel="sms").status_code, 422)
        self.assertEqual(self._resolve(t["token"], party, channel="email").status_code, 200)

    def test_resolve_never_uses_principals_email(self):
        """CP-INV-03, the whole point. A party with NO contact point resolves to a refusal — the
        resolver never falls back to the owner principal's authentication email."""
        t = self._tenant_with_token()
        party = self._make_party(t["token"])  # no contact point created
        self.assertEqual(self._resolve(t["token"], party, purpose="transactional").status_code, 422)

    def test_resolve_refuses_across_tenants(self):
        """CP-INV-01/CP-INV-03. Tenant B cannot resolve a recipient against tenant A's party — RLS
        makes A's party indistinguishable from a non-existent one (a uniform refusal)."""
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        party_a = self._make_party(a["token"])
        cp_id = self._create_cp(a["token"], party_a).json()["contact_point_id"]
        self.client.post(
            f"/v1/parties/{party_a}/contact-points/{cp_id}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(a["token"]),
        )
        # A resolves its own; B cannot resolve A's party (404 party or 422 unresolved — both refuse)
        self.assertEqual(self._resolve(a["token"], party_a).status_code, 200)
        self.assertIn(self._resolve(b["token"], party_a).status_code, (404, 422))

    def test_a_contact_point_is_private_to_its_tenant(self):
        """CP-INV-01. Tenant B cannot read tenant A's contact point over HTTP."""
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        party_a = self._make_party(a["token"])
        cp_id = self._create_cp(a["token"], party_a).json()["contact_point_id"]
        r = self.client.get(
            f"/v1/parties/{party_a}/contact-points/{cp_id}", headers=self._auth(b["token"])
        )
        self.assertEqual(r.status_code, 404, r.text)

    # -- auth --------------------------------------------------------------------------

    def test_creating_a_contact_point_requires_a_bearer(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        r = self.client.post(
            f"/v1/parties/{party}/contact-points",
            json={"endpoint_type": "email", "endpoint_value": "x@example.com",
                  "purpose": "general"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)

    def test_resolving_requires_a_bearer(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        r = self.client.post(
            f"/v1/parties/{party}/resolve-recipient",
            json={"purpose": "transactional", "channel": "email"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)


if __name__ == "__main__":
    unittest.main()
