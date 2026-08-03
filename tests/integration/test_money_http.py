"""MILE-4.2 Money & Currency over HTTP — bearer-gated, tenant-isolated exchange rates + convert.

Governed by DEC-P4-ENTRY (MILE-4.2), AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed HTTP against PostgreSQL), R4 (refusals), R5 (loud).

A tenant's exchange rates are private to it (row-level security), and a conversion uses that
tenant's own rate and stays exact — integer minor units in, exact-decimal rate, integer minor units
out. Every write goes through a signed bearer.
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


class TestMoneyHttpEvidenceCanBeProduced(unittest.TestCase):
    def test_money_http_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "stack unavailable — reported by the guard test")
class TestMoneyHttp(unittest.TestCase):
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
        t = self.client.post(
            "/v1/tenants",
            json={"name": f"T{uuid.uuid4().hex[:8]}", "owner_principal_id": p.json()["principal_id"]},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(t.status_code, 201, t.text)
        e = self.client.post(
            "/v1/contexts",
            json={"principal_id": p.json()["principal_id"], "membership_id": t.json()["owner_membership_id"]},
            headers={"X-Tenant-ID": t.json()["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(e.status_code, 201, e.text)
        return {"tenant_id": t.json()["tenant_id"], "token": e.json()["access_token"]}

    def _auth(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "X-Correlation-ID": corr()}

    def _set_rate(self, token, frm, to, rate):
        return self.client.put(
            "/v1/exchange-rates",
            json={"from_currency": frm, "to_currency": to, "rate": rate},
            headers=self._auth(token),
        )

    # -- set / get / convert ------------------------------------------------------------

    def test_set_and_get_a_rate(self):
        t = self._tenant_with_token()
        r = self._set_rate(t["token"], "USD", "THB", "33.00")
        self.assertEqual(r.status_code, 200, r.text)
        g = self.client.get("/v1/exchange-rates/USD/THB", headers=self._auth(t["token"]))
        self.assertEqual(g.status_code, 200, g.text)
        self.assertEqual(g.json()["from_currency"], "USD")

    def test_convert_uses_the_tenants_rate_exactly(self):
        t = self._tenant_with_token()
        self._set_rate(t["token"], "USD", "THB", "33.00")
        r = self.client.post(
            "/v1/money/convert",
            json={"amount_minor": 1050, "from_currency": "USD", "to_currency": "THB"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 200, r.text)
        # 10.50 USD * 33.00 = 346.50 THB = 34650 minor units, exactly.
        self.assertEqual(r.json(), {"amount_minor": 34650, "currency": "THB"})

    def test_convert_into_a_zero_minor_unit_currency(self):
        t = self._tenant_with_token()
        self._set_rate(t["token"], "USD", "JPY", "150")
        r = self.client.post(
            "/v1/money/convert",
            json={"amount_minor": 1050, "from_currency": "USD", "to_currency": "JPY"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {"amount_minor": 1575, "currency": "JPY"})

    # -- isolation and refusals ---------------------------------------------------------

    def test_a_rate_is_private_to_its_tenant(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        self._set_rate(a["token"], "USD", "THB", "33.00")
        g = self.client.get("/v1/exchange-rates/USD/THB", headers=self._auth(b["token"]))
        self.assertEqual(g.status_code, 404, "tenant B saw tenant A's rate")

    def test_convert_without_a_rate_is_refused(self):
        t = self._tenant_with_token()
        r = self.client.post(
            "/v1/money/convert",
            json={"amount_minor": 1000, "from_currency": "USD", "to_currency": "EUR"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 404, r.text)

    def test_an_unknown_currency_is_refused(self):
        t = self._tenant_with_token()
        r = self._set_rate(t["token"], "USD", "XYZ", "1.00")
        self.assertEqual(r.status_code, 422, r.text)

    def test_a_non_positive_rate_is_refused(self):
        t = self._tenant_with_token()
        # 0 passes the format pattern but the database CHECK refuses it.
        r = self._set_rate(t["token"], "USD", "THB", "0")
        self.assertEqual(r.status_code, 422, r.text)

    def test_setting_a_rate_requires_a_bearer(self):
        r = self.client.put(
            "/v1/exchange-rates",
            json={"from_currency": "USD", "to_currency": "THB", "rate": "33.00"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)


if __name__ == "__main__":
    unittest.main()
