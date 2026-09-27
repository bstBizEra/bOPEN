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
        return {
            "principal_id": pid,
            "tenant_id": t.json()["tenant_id"],
            "membership_id": t.json()["owner_membership_id"],
            "context_id": c.json()["context"]["context_id"],
            "token": c.json()["access_token"],
        }

    def _actor_token(self, tenant_id: str, role: str = "auditor") -> dict:
        """Create an active same-tenant actor without implicitly granting ContactPoint actions."""
        from platform_kernel.api import memberships

        p = self.client.post(
            "/v1/principals",
            json={"email": f"actor-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(p.status_code, 201, p.text)
        principal_id = p.json()["principal_id"]
        membership = memberships.create(tenant_id, principal_id, role=role, state="active")
        c = self.client.post(
            "/v1/contexts",
            json={"principal_id": principal_id, "membership_id": membership.id},
            headers={"X-Tenant-ID": tenant_id, "X-Correlation-ID": corr()},
        )
        self.assertEqual(c.status_code, 201, c.text)
        return {
            "principal_id": principal_id,
            "membership_id": membership.id,
            "token": c.json()["access_token"],
        }

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

    def _two_parties_with_contact_point(self, endpoint_value="a@example.com"):
        tenant = self._tenant_with_token()
        party_a = self._make_party(tenant["token"])
        party_b = self._make_party(tenant["token"])
        created = self._create_cp(
            tenant["token"], party_a, endpoint_value=endpoint_value
        )
        self.assertEqual(created.status_code, 201, created.text)
        return tenant, party_a, party_b, created.json()

    def _set_lifecycle_state(self, tenant_id: str, cp_id: str, state: str) -> None:
        """Test-only state arrangement; the public lifecycle transition is separately governed."""
        from platform_kernel import db

        with db.tenant_session(tenant_id) as cur:
            cur.execute(
                "UPDATE party_contact_points SET lifecycle_state = %s WHERE id = %s",
                (state, cp_id),
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
        self.assertNotIn("endpoint_value", r.json())
        self.assertEqual(r.json()["endpoint_value_masked"], "o**@example.com")
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

    # -- explicit authorization ---------------------------------------------------------

    def test_default_deny_actor_cannot_use_any_contact_point_action(self):
        """CP-REV-F03. Context and RLS are present; an explicit allow is still required per action."""
        owner = self._tenant_with_token()
        party = self._make_party(owner["token"])
        created = self._create_cp(owner["token"], party, endpoint_value="deny@example.com")
        self.assertEqual(created.status_code, 201, created.text)
        cp_id = created.json()["contact_point_id"]
        actor = self._actor_token(owner["tenant_id"], role="auditor")
        headers = self._auth(actor["token"])

        attempts = {
            "create": lambda: self.client.post(
                f"/v1/parties/{party}/contact-points",
                json={"endpoint_type": "email", "endpoint_value": "blocked@example.com",
                      "purpose": "general"},
                headers=headers,
            ),
            "list": lambda: self.client.get(
                f"/v1/parties/{party}/contact-points", headers=headers
            ),
            "read": lambda: self.client.get(
                f"/v1/parties/{party}/contact-points/{cp_id}", headers=headers
            ),
            "update": lambda: self.client.put(
                f"/v1/parties/{party}/contact-points/{cp_id}",
                json={"expected_revision": 1, "purpose": "billing"}, headers=headers,
            ),
            "retire": lambda: self.client.delete(
                f"/v1/parties/{party}/contact-points/{cp_id}", headers=headers
            ),
            "verify": lambda: self.client.post(
                f"/v1/parties/{party}/contact-points/{cp_id}/verify",
                json={"method": "administrative_assertion"}, headers=headers,
            ),
            "set_primary": lambda: self.client.post(
                f"/v1/parties/{party}/contact-points/{cp_id}/set-primary", headers=headers
            ),
            "resolve": lambda: self._resolve(actor["token"], party),
        }
        for action, attempt in attempts.items():
            with self.subTest(action=action):
                response = attempt()
                self.assertEqual(response.status_code, 403, response.text)

        owner_view = self.client.get(
            f"/v1/parties/{party}/contact-points/{cp_id}",
            headers=self._auth(owner["token"]),
        )
        self.assertEqual(owner_view.status_code, 200, owner_view.text)
        self.assertEqual(owner_view.json()["revision"], 1, "a denied action mutated the row")
        self.assertEqual(owner_view.json()["verification_state"], "unverified")

    # -- item operations bind both the path Party and contact-point id -----------------

    def test_read_refuses_a_contact_point_under_another_party_path(self):
        t, _party_a, party_b, cp = self._two_parties_with_contact_point()
        r = self.client.get(
            f"/v1/parties/{party_b}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 404, r.text)

    def test_update_refuses_another_party_path_without_mutation(self):
        t, party_a, party_b, cp = self._two_parties_with_contact_point()
        r = self.client.put(
            f"/v1/parties/{party_b}/contact-points/{cp['contact_point_id']}",
            json={"expected_revision": 1, "purpose": "billing"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 404, r.text)
        unchanged = self.client.get(
            f"/v1/parties/{party_a}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(unchanged.json()["revision"], 1)
        self.assertEqual(unchanged.json()["purpose"], "transactional")

    def test_retire_refuses_another_party_path_without_mutation(self):
        t, party_a, party_b, cp = self._two_parties_with_contact_point()
        r = self.client.delete(
            f"/v1/parties/{party_b}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 404, r.text)
        still_live = self.client.get(
            f"/v1/parties/{party_a}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(still_live.status_code, 200, still_live.text)
        self.assertEqual(still_live.json()["lifecycle_state"], "active")

    def test_verify_refuses_another_party_path_without_event_or_state_change(self):
        t, party_a, party_b, cp = self._two_parties_with_contact_point()
        r = self.client.post(
            f"/v1/parties/{party_b}/contact-points/{cp['contact_point_id']}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 404, r.text)
        current = self.client.get(
            f"/v1/parties/{party_a}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(current.json()["verification_state"], "unverified")

    def test_set_primary_refuses_another_party_path_without_mutation(self):
        t, party_a, party_b, cp = self._two_parties_with_contact_point()
        r = self.client.post(
            f"/v1/parties/{party_b}/contact-points/{cp['contact_point_id']}/set-primary",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 404, r.text)
        current = self.client.get(
            f"/v1/parties/{party_a}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertFalse(current.json()["is_primary"])

    # -- endpoint identity, verification and lifecycle ---------------------------------

    def test_verified_endpoint_replacement_increments_version_and_requires_reverification(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        created = self._create_cp(t["token"], party, endpoint_value="old@example.com").json()
        cp_id = created["contact_point_id"]
        self.assertEqual(created["endpoint_version"], 1)
        verified = self.client.post(
            f"/v1/parties/{party}/contact-points/{cp_id}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(verified.status_code, 200, verified.text)

        changed = self.client.put(
            f"/v1/parties/{party}/contact-points/{cp_id}",
            json={"expected_revision": verified.json()["revision"],
                  "endpoint_value": "new@example.com"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["endpoint_version"], 2)
        self.assertEqual(changed.json()["verification_state"], "unverified")
        self.assertIsNone(changed.json()["verification_method"])
        self.assertEqual(self._resolve(t["token"], party).status_code, 422)

        reverified = self.client.post(
            f"/v1/parties/{party}/contact-points/{cp_id}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(reverified.status_code, 200, reverified.text)
        self.assertEqual(reverified.json()["endpoint_version"], 2)
        resolved = self._resolve(t["token"], party)
        self.assertEqual(resolved.status_code, 200, resolved.text)
        self.assertEqual(resolved.json()["endpoint_value"], "new@example.com")

    def test_suspended_contact_point_refuses_update_verify_primary_and_resolve(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp = self._create_cp(t["token"], party).json()
        self._set_lifecycle_state(t["tenant_id"], cp["contact_point_id"], "suspended")
        headers = self._auth(t["token"])
        attempts = (
            self.client.put(
                f"/v1/parties/{party}/contact-points/{cp['contact_point_id']}",
                json={"expected_revision": cp["revision"], "purpose": "billing"}, headers=headers,
            ),
            self.client.post(
                f"/v1/parties/{party}/contact-points/{cp['contact_point_id']}/verify",
                json={"method": "administrative_assertion"}, headers=headers,
            ),
            self.client.post(
                f"/v1/parties/{party}/contact-points/{cp['contact_point_id']}/set-primary",
                headers=headers,
            ),
        )
        for response in attempts:
            self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self._resolve(t["token"], party).status_code, 422)

    def test_retired_contact_point_refuses_mutations_and_preserves_snapshot_boundary(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp = self._create_cp(t["token"], party).json()
        retired = self.client.delete(
            f"/v1/parties/{party}/contact-points/{cp['contact_point_id']}",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(retired.status_code, 200, retired.text)
        self.assertEqual(retired.json()["lifecycle_state"], "retired")
        self.assertEqual(self._resolve(t["token"], party).status_code, 422)
        again = self.client.post(
            f"/v1/parties/{party}/contact-points/{cp['contact_point_id']}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(again.status_code, 409, again.text)

    # -- privacy and non-dispatch resolver contract ------------------------------------

    def test_default_crud_responses_mask_the_endpoint_value(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        raw = f"secret-{uuid.uuid4().hex[:8]}@example.com"
        created = self._create_cp(t["token"], party, endpoint_value=raw)
        self.assertEqual(created.status_code, 201, created.text)
        cp_id = created.json()["contact_point_id"]
        responses = (
            created,
            self.client.get(
                f"/v1/parties/{party}/contact-points/{cp_id}", headers=self._auth(t["token"])
            ),
            self.client.get(
                f"/v1/parties/{party}/contact-points", headers=self._auth(t["token"])
            ),
        )
        for response in responses:
            with self.subTest(path=str(response.request.url)):
                self.assertNotIn(raw, response.text)
                body = response.json()
                records = body if isinstance(body, list) else [body]
                self.assertNotIn("endpoint_value", records[0])
                self.assertIn("endpoint_value_masked", records[0])

    def test_resolver_returns_a_frozen_non_dispatch_snapshot_shape(self):
        t = self._tenant_with_token()
        party = self._make_party(t["token"])
        cp = self._create_cp(t["token"], party, endpoint_value="snapshot@example.com").json()
        self.client.post(
            f"/v1/parties/{party}/contact-points/{cp['contact_point_id']}/verify",
            json={"method": "administrative_assertion"}, headers=self._auth(t["token"]),
        )
        snapshot = self._resolve(t["token"], party)
        self.assertEqual(snapshot.status_code, 200, snapshot.text)
        self.assertEqual(
            set(snapshot.json()),
            {
                "contact_point_id", "endpoint_version", "endpoint_type", "endpoint_value",
                "purpose", "party_id", "effective_at", "resolver_version",
            },
        )
        for forbidden in (
            "consent", "authorized", "dispatched", "delivery_status", "message_id", "provider_id"
        ):
            self.assertNotIn(forbidden, snapshot.json())

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
