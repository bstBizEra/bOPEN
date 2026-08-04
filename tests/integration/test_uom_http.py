"""MILE-4.2 UOM over HTTP — bearer-gated, tenant-isolated, dimension-safe (DEC-P4-ENTRY §9).

Governed by DEC-P4-ENTRY §9, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed HTTP against PostgreSQL), R4 (the refusals — a
cross-dimension conversion, a temperature conversion, a shadowed standard unit, a cross-tenant read),
R5 (loud).

Standard units are a code constant; custom units are the tenant's own with full CRUD; conversion is
dimension-safe over the wire (kg + m refused) and exact (magnitudes are decimal strings).
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


class TestUomHttpEvidenceCanBeProduced(unittest.TestCase):
    def test_uom_http_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "stack unavailable — reported by the guard test")
class TestUomHttp(unittest.TestCase):
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

    def _convert(self, token, magnitude, from_unit, to_unit):
        return self.client.post(
            "/v1/uom/convert",
            json={"magnitude": magnitude, "from_unit": from_unit, "to_unit": to_unit},
            headers=self._auth(token),
        )

    # -- standard-unit conversion (dimension-safe, exact) ------------------------------

    def test_convert_standard_units_exactly(self):
        t = self._tenant_with_token()
        r = self._convert(t["token"], "2.5", "kg", "g")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), {"magnitude": "2500", "unit": "g"})

    def test_convert_thai_land_units(self):
        t = self._tenant_with_token()
        r = self._convert(t["token"], "1", "rai", "m2")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["magnitude"], "1600")

    def test_a_cross_dimension_conversion_is_refused(self):
        t = self._tenant_with_token()
        r = self._convert(t["token"], "1", "kg", "m")  # mass -> length
        self.assertEqual(r.status_code, 422, r.text)

    def test_a_temperature_conversion_is_refused(self):
        t = self._tenant_with_token()
        r = self._convert(t["token"], "100", "degC", "degF")
        self.assertEqual(r.status_code, 422, r.text)

    def test_an_unknown_unit_is_refused(self):
        t = self._tenant_with_token()
        r = self._convert(t["token"], "1", "smoot", "m")
        self.assertEqual(r.status_code, 422, r.text)

    # -- full CRUD on custom units + conversion through them ----------------------------

    def test_create_read_update_delete_a_custom_unit(self):
        t = self._tenant_with_token()
        # create
        c = self.client.post(
            "/v1/uom/units",
            json={"unit_code": "pallet", "dimension": "count", "factor_to_base": "48",
                  "display_name": "Pallet"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(c.status_code, 201, c.text)
        # convert through the custom unit: 1 pallet -> 4 dozen (48 each / 12)
        conv = self._convert(t["token"], "1", "pallet", "dozen")
        self.assertEqual(conv.status_code, 200, conv.text)
        self.assertEqual(conv.json()["magnitude"], "4")
        # read
        r = self.client.get("/v1/uom/units/pallet", headers=self._auth(t["token"]))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["factor_to_base"], "48")
        # update the factor
        u = self.client.put(
            "/v1/uom/units/pallet",
            json={"factor_to_base": "60", "display_name": "Big Pallet"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(u.status_code, 200, u.text)
        conv2 = self._convert(t["token"], "1", "pallet", "each")
        self.assertEqual(conv2.json()["magnitude"], "60")
        # list
        lst = self.client.get("/v1/uom/units", headers=self._auth(t["token"]))
        self.assertEqual(len(lst.json()), 1)
        # delete
        d = self.client.delete("/v1/uom/units/pallet", headers=self._auth(t["token"]))
        self.assertEqual(d.status_code, 204, d.text)
        gone = self.client.get("/v1/uom/units/pallet", headers=self._auth(t["token"]))
        self.assertEqual(gone.status_code, 404)

    def test_a_custom_unit_cannot_shadow_a_standard_unit(self):
        t = self._tenant_with_token()
        r = self.client.post(
            "/v1/uom/units",
            json={"unit_code": "kg", "dimension": "mass", "factor_to_base": "999",
                  "display_name": "fake kg"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(r.status_code, 409, r.text)

    def test_a_duplicate_custom_unit_is_refused(self):
        t = self._tenant_with_token()
        body = {"unit_code": "box", "dimension": "count", "factor_to_base": "10", "display_name": "Box"}
        self.assertEqual(self.client.post("/v1/uom/units", json=body, headers=self._auth(t["token"])).status_code, 201)
        self.assertEqual(self.client.post("/v1/uom/units", json=body, headers=self._auth(t["token"])).status_code, 409)

    # -- isolation and auth ------------------------------------------------------------

    def test_a_custom_unit_is_private_to_its_tenant(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()
        self.client.post(
            "/v1/uom/units",
            json={"unit_code": "crate", "dimension": "count", "factor_to_base": "24", "display_name": "Crate"},
            headers=self._auth(a["token"]),
        )
        # B cannot read A's custom unit, and a convert using it fails for B (unknown to B).
        self.assertEqual(self.client.get("/v1/uom/units/crate", headers=self._auth(b["token"])).status_code, 404)
        self.assertEqual(self._convert(b["token"], "1", "crate", "each").status_code, 422)
        # A can use it.
        self.assertEqual(self._convert(a["token"], "1", "crate", "each").json()["magnitude"], "24")

    def test_creating_a_custom_unit_requires_a_bearer(self):
        r = self.client.post(
            "/v1/uom/units",
            json={"unit_code": "x", "dimension": "count", "factor_to_base": "1", "display_name": "x"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)


if __name__ == "__main__":
    unittest.main()
