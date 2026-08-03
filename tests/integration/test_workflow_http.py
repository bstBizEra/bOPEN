"""MILE-4.2 workflow state engine over HTTP — bearer-gated, tenant-isolated (DEC-P4-ENTRY §8).

Governed by DEC-P4-ENTRY §8, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed HTTP against PostgreSQL), R4 (the refusals are the
point — a disallowed transition and a cross-tenant read), R5 (loud).

The engine is a state machine, not a mutable field. The proof is `test_a_disallowed_transition_is_
refused_and_leaves_the_state_unchanged`: a move the definition does not list returns 422 and the
instance stays where it was. The isolation probes show a definition and an instance are private to
their tenant over the wire, and history accumulates append-only in order.
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


# A small approval workflow reused across tests.
STATES = ["draft", "submitted", "approved", "rejected"]
TRANSITIONS = [
    ["draft", "submitted"],
    ["submitted", "approved"],
    ["submitted", "rejected"],
]


class TestWorkflowHttpEvidenceCanBeProduced(unittest.TestCase):
    def test_workflow_http_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "stack unavailable — reported by the guard test")
class TestWorkflowHttp(unittest.TestCase):
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

    def _define(self, token: str) -> str:
        r = self.client.post(
            "/v1/workflow-definitions",
            json={
                "name": "Approval",
                "initial_state": "draft",
                "states": STATES,
                "transitions": TRANSITIONS,
            },
            headers=self._auth(token),
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["definition_id"]

    def _start(self, token: str, definition_id: str, subject: str = "doc-1") -> str:
        r = self.client.post(
            "/v1/workflow-instances",
            json={"definition_id": definition_id, "subject_ref": subject},
            headers=self._auth(token),
        )
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()["instance_id"]

    def _transition(self, token: str, instance_id: str, to_state: str):
        return self.client.post(
            f"/v1/workflow-instances/{instance_id}/transitions",
            json={"to_state": to_state},
            headers=self._auth(token),
        )

    # -- the flow -----------------------------------------------------------------------

    def test_define_start_and_read_begins_at_initial_state(self):
        t = self._tenant_with_token()
        d = self._define(t["token"])
        i = self._start(t["token"], d)
        r = self.client.get(f"/v1/workflow-instances/{i}", headers=self._auth(t["token"]))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["current_state"], "draft")
        self.assertEqual(r.json()["definition_id"], d)

    def test_an_allowed_transition_moves_the_instance_and_records_history(self):
        t = self._tenant_with_token()
        i = self._start(t["token"], self._define(t["token"]))
        r = self._transition(t["token"], i, "submitted")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["current_state"], "submitted")

        h = self.client.get(f"/v1/workflow-instances/{i}/history", headers=self._auth(t["token"]))
        self.assertEqual(h.status_code, 200, h.text)
        self.assertEqual(len(h.json()), 1)
        self.assertEqual(h.json()[0]["from_state"], "draft")
        self.assertEqual(h.json()[0]["to_state"], "submitted")

    def test_history_accumulates_in_order_across_transitions(self):
        t = self._tenant_with_token()
        i = self._start(t["token"], self._define(t["token"]))
        self.assertEqual(self._transition(t["token"], i, "submitted").status_code, 200)
        self.assertEqual(self._transition(t["token"], i, "approved").status_code, 200)
        h = self.client.get(f"/v1/workflow-instances/{i}/history", headers=self._auth(t["token"]))
        pairs = [(e["from_state"], e["to_state"]) for e in h.json()]
        self.assertEqual(pairs, [("draft", "submitted"), ("submitted", "approved")])

    # -- the state-machine invariant (the refusal) --------------------------------------

    def test_a_disallowed_transition_is_refused_and_leaves_the_state_unchanged(self):
        t = self._tenant_with_token()
        i = self._start(t["token"], self._define(t["token"]))
        # draft -> approved is not an edge; only draft -> submitted is.
        r = self._transition(t["token"], i, "approved")
        self.assertEqual(r.status_code, 422, r.text)
        after = self.client.get(f"/v1/workflow-instances/{i}", headers=self._auth(t["token"]))
        self.assertEqual(after.json()["current_state"], "draft", "state moved on a refused edge")
        # And no history row was written for the refused move.
        h = self.client.get(f"/v1/workflow-instances/{i}/history", headers=self._auth(t["token"]))
        self.assertEqual(h.json(), [])

    def test_a_malformed_definition_is_refused(self):
        t = self._tenant_with_token()
        r = self.client.post(
            "/v1/workflow-definitions",
            json={
                "name": "Bad",
                "initial_state": "nowhere",  # not among states
                "states": STATES,
                "transitions": TRANSITIONS,
            },
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 422, r.text)

    # -- isolation (the refusals) -------------------------------------------------------

    def test_an_instance_is_invisible_to_another_tenant_over_http(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        i = self._start(a["token"], self._define(a["token"]))
        r = self.client.get(f"/v1/workflow-instances/{i}", headers=self._auth(b["token"]))
        self.assertEqual(r.status_code, 404, "tenant B read tenant A's instance over HTTP")

    def test_a_definition_is_invisible_to_another_tenant_over_http(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        d = self._define(a["token"])
        r = self.client.get(f"/v1/workflow-definitions/{d}", headers=self._auth(b["token"]))
        self.assertEqual(r.status_code, 404, "tenant B read tenant A's definition over HTTP")

    def test_another_tenant_cannot_transition_your_instance(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        i = self._start(a["token"], self._define(a["token"]))
        # B holds a valid bearer for its own tenant and names A's instance.
        r = self._transition(b["token"], i, "submitted")
        self.assertEqual(r.status_code, 404, "tenant B transitioned tenant A's instance")

    def test_starting_an_instance_requires_a_bearer(self):
        r = self.client.post(
            "/v1/workflow-instances",
            json={"definition_id": str(uuid.uuid4()), "subject_ref": "x"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)


if __name__ == "__main__":
    unittest.main()
