"""MILE-4.2 Location foundation over HTTP — bearer-gated, tenant-isolated, with the coordinate-validity
and provider-distrust keystones (BOPEN-LOC-001, DEC-P4-ENTRY §11).

Governed by DEC-P4-ENTRY §11, AGENTS.md section 8.
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed HTTP against PostgreSQL), R4 (the refusals — an invalid
transition, an out-of-range coordinate, a non-length accuracy unit, an unaccepted candidate, an
accept without provenance, a live identifier collision, a containment cycle, a missing bearer), R5.

Keystones: a freshly observed point is a CANDIDATE — a read shows it is NOT accepted, and `accept`
requires an explicit actor plus provenance (LOC-INV-05/06). Coordinate fields are named
`longitude`/`latitude` explicitly so an axis transposition is unrepresentable (LOC-INV-04). Precise
coordinates never appear in an audit record (LOC-INV-14).
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


class TestLocationHttpEvidenceCanBeProduced(unittest.TestCase):
    def test_location_http_evidence_can_be_produced(self):
        self.assertIsNone(_unavailable_reason(), msg=_unavailable_reason())


@unittest.skipIf(_unavailable_reason() is not None, "stack unavailable — reported by the guard test")
class TestLocationHttp(unittest.TestCase):
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

    def _make_location(self, token, code=None, location_type="site"):
        return self.client.post(
            "/v1/locations",
            json={"code": code or f"L{uuid.uuid4().hex[:8]}", "name": "A Site",
                  "location_type": location_type},
            headers=self._auth(token),
        )

    def _observe(self, token, loc_id, longitude="100.523000", latitude="13.736700", **extra):
        body = {"longitude": longitude, "latitude": latitude}
        body.update(extra)
        return self.client.post(
            f"/v1/locations/{loc_id}/geometry-observations", json=body, headers=self._auth(token)
        )

    # -- CRUD + lifecycle --------------------------------------------------------------

    def test_create_read_list_update_a_location(self):
        t = self._tenant_with_token()
        c = self._make_location(t["token"], code="HQ")
        self.assertEqual(c.status_code, 201, c.text)
        loc_id = c.json()["location_id"]
        self.assertEqual(c.json()["lifecycle_state"], "proposed")
        self.assertEqual(c.json()["revision"], 1)
        r = self.client.get(f"/v1/locations/{loc_id}", headers=self._auth(t["token"]))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["code"], "HQ")
        lst = self.client.get("/v1/locations", headers=self._auth(t["token"]))
        self.assertEqual(len(lst.json()), 1)
        u = self.client.put(
            f"/v1/locations/{loc_id}",
            json={"expected_revision": 1, "name": "Head Office"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(u.status_code, 200, u.text)
        self.assertEqual(u.json()["name"], "Head Office")
        self.assertEqual(u.json()["revision"], 2)

    def test_a_duplicate_code_is_refused(self):
        t = self._tenant_with_token()
        self._make_location(t["token"], code="DUP")
        again = self._make_location(t["token"], code="DUP")
        self.assertEqual(again.status_code, 409, again.text)

    def test_lifecycle_transition_and_invalid_transition_refused(self):
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        ok = self.client.post(
            f"/v1/locations/{loc_id}/transition", json={"to_state": "active"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(ok.status_code, 200, ok.text)
        self.assertEqual(ok.json()["lifecycle_state"], "active")
        # proposed->retired is not a defined edge from active either (active->retired is, but
        # reactivation after retirement is not): retire, then attempt to reactivate.
        self.client.post(
            f"/v1/locations/{loc_id}/transition", json={"to_state": "retired"},
            headers=self._auth(t["token"]),
        )
        bad = self.client.post(
            f"/v1/locations/{loc_id}/transition", json={"to_state": "active"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(bad.status_code, 422, "reactivation after retirement was allowed")

    # -- address versioning ------------------------------------------------------------

    def test_address_versioning_and_set_current(self):
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        v1 = self.client.post(
            f"/v1/locations/{loc_id}/address-versions",
            json={"country_code": "TH", "original_input": "123 Sukhumvit", "locality": "Bangkok"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(v1.status_code, 201, v1.text)
        self.assertTrue(v1.json()["is_current"])
        v1_id = v1.json()["address_version_id"]
        v2 = self.client.post(
            f"/v1/locations/{loc_id}/address-versions",
            json={"country_code": "TH", "original_input": "456 Silom", "locality": "Bangkok"},
            headers=self._auth(t["token"]),
        )
        self.assertEqual(v2.status_code, 201, v2.text)
        self.assertTrue(v2.json()["is_current"])
        # only one current at a time
        lst = self.client.get(
            f"/v1/locations/{loc_id}/address-versions", headers=self._auth(t["token"])
        ).json()
        self.assertEqual(sum(1 for a in lst if a["is_current"]), 1)
        # revert to v1
        sc = self.client.post(
            f"/v1/locations/{loc_id}/address-versions/{v1_id}/set-current",
            headers=self._auth(t["token"]),
        )
        self.assertEqual(sc.status_code, 200, sc.text)
        self.assertTrue(sc.json()["is_current"])
        lst2 = self.client.get(
            f"/v1/locations/{loc_id}/address-versions", headers=self._auth(t["token"])
        ).json()
        current = [a["address_version_id"] for a in lst2 if a["is_current"]]
        self.assertEqual(current, [v1_id])

    # -- geometry observe -> accept: the provider-distrust keystone --------------------

    def test_observe_starts_candidate_and_is_not_accepted(self):
        """LOC-INV-06. A freshly observed point is a candidate; a read shows it is NOT accepted."""
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        o = self._observe(t["token"], loc_id)
        self.assertEqual(o.status_code, 201, o.text)
        self.assertEqual(o.json()["acceptance_state"], "candidate")
        obs_id = o.json()["observation_id"]
        # the location's current geometry pointer is NOT set to the candidate
        loc = self.client.get(f"/v1/locations/{loc_id}", headers=self._auth(t["token"])).json()
        self.assertIsNone(loc["current_geometry_observation_id"])
        read = self.client.get(
            f"/v1/locations/{loc_id}/geometry-observations", headers=self._auth(t["token"])
        ).json()
        self.assertEqual(read[0]["observation_id"], obs_id)
        self.assertEqual(read[0]["acceptance_state"], "candidate")

    def test_accept_without_provenance_is_refused(self):
        """LOC-INV-05. An observation missing source/observed_at/confidence cannot be accepted."""
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        obs_id = self._observe(t["token"], loc_id).json()["observation_id"]  # no provenance
        a = self.client.post(
            f"/v1/locations/{loc_id}/geometry-observations/{obs_id}/accept",
            json={}, headers=self._auth(t["token"]),
        )
        self.assertEqual(a.status_code, 422, a.text)

    def test_accept_with_provenance_succeeds_and_updates_current_pointer(self):
        """LOC-INV-06. An accept with an explicit actor (from the context) and full provenance succeeds
        and sets the location's current geometry pointer."""
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        obs_id = self._observe(
            t["token"], loc_id, source="survey", confidence="0.95",
            observed_at="2026-08-05T10:00:00+00:00",
        ).json()["observation_id"]
        a = self.client.post(
            f"/v1/locations/{loc_id}/geometry-observations/{obs_id}/accept",
            json={}, headers=self._auth(t["token"]),
        )
        self.assertEqual(a.status_code, 200, a.text)
        self.assertEqual(a.json()["acceptance_state"], "accepted")
        self.assertIsNotNone(a.json()["accepted_by"])
        loc = self.client.get(f"/v1/locations/{loc_id}", headers=self._auth(t["token"])).json()
        self.assertEqual(loc["current_geometry_observation_id"], obs_id)

    def test_out_of_range_coordinate_is_422(self):
        """LOC-INV-04. A longitude of 200 is refused with 422 before any accept could occur."""
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        o = self._observe(t["token"], loc_id, longitude="200", latitude="10")
        self.assertEqual(o.status_code, 422, o.text)

    def test_accuracy_radius_length_unit(self):
        """LOC-D-04. An accuracy radius with a length unit is accepted; a non-length unit (kg) or an
        unknown unit is refused."""
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        good = self._observe(
            t["token"], loc_id, accuracy_radius={"value": "5", "unit": "m"}
        )
        self.assertEqual(good.status_code, 201, good.text)
        self.assertEqual(good.json()["accuracy_radius_unit"], "m")
        self.assertEqual(good.json()["accuracy_radius_value"], "5")
        bad_mass = self._observe(
            t["token"], loc_id, accuracy_radius={"value": "5", "unit": "kg"}
        )
        self.assertEqual(bad_mass.status_code, 422, "a mass accuracy unit was accepted")
        bad_unknown = self._observe(
            t["token"], loc_id, accuracy_radius={"value": "5", "unit": "zonk"}
        )
        self.assertEqual(bad_unknown.status_code, 422, "an unknown accuracy unit was accepted")

    # -- external identifiers ----------------------------------------------------------

    def test_external_identifier_live_collision_is_409(self):
        t = self._tenant_with_token()
        loc1 = self._make_location(t["token"]).json()["location_id"]
        loc2 = self._make_location(t["token"]).json()["location_id"]
        first = self.client.post(
            f"/v1/locations/{loc1}/external-identifiers",
            json={"scheme": "osm", "value": "way/7"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(first.status_code, 201, first.text)
        dup = self.client.post(
            f"/v1/locations/{loc2}/external-identifiers",
            json={"scheme": "osm", "value": "way/7"}, headers=self._auth(t["token"]),
        )
        self.assertEqual(dup.status_code, 409, dup.text)

    # -- relationships -----------------------------------------------------------------

    def test_relationship_cycle_is_refused(self):
        t = self._tenant_with_token()
        a = self._make_location(t["token"]).json()["location_id"]
        b = self._make_location(t["token"]).json()["location_id"]
        c = self._make_location(t["token"]).json()["location_id"]

        def contains(frm, to):
            return self.client.post(
                f"/v1/locations/{frm}/relationships",
                json={"from_location_id": frm, "to_location_id": to},
                headers=self._auth(t["token"]),
            )

        self.assertEqual(contains(a, b).status_code, 201)
        self.assertEqual(contains(b, c).status_code, 201)
        cyc = contains(c, a)
        self.assertEqual(cyc.status_code, 409, "a containment cycle was allowed")

    # -- auth --------------------------------------------------------------------------

    def test_creating_a_location_requires_a_bearer(self):
        r = self.client.post(
            "/v1/locations",
            json={"code": "X", "name": "X", "location_type": "site"},
            headers={"X-Correlation-ID": corr()},
        )
        self.assertEqual(r.status_code, 401, r.text)

    # -- R5 guard + privacy ------------------------------------------------------------

    def test_precise_coordinates_never_appear_in_an_audit_record(self):
        """LOC-INV-14. The observe/accept audit records carry only ids and actions — a search of the
        tenant's audit trail must not surface the longitude or latitude that was submitted."""
        t = self._tenant_with_token()
        loc_id = self._make_location(t["token"]).json()["location_id"]
        # Distinctive coordinate strings that would be easy to spot if leaked.
        lon, lat = "123.456789", "12.345678"
        obs_id = self._observe(
            t["token"], loc_id, longitude=lon, latitude=lat,
            source="survey", confidence="0.9", observed_at="2026-08-05T10:00:00+00:00",
        ).json()["observation_id"]
        self.client.post(
            f"/v1/locations/{loc_id}/geometry-observations/{obs_id}/accept",
            json={}, headers=self._auth(t["token"]),
        )
        events = self.client.get(
            "/v1/audit-events?limit=200", headers=self._auth(t["token"])
        )
        self.assertEqual(events.status_code, 200, events.text)
        body = events.text
        self.assertNotIn(lon, body, "a precise longitude appeared in the audit trail")
        self.assertNotIn(lat, body, "a precise latitude appeared in the audit trail")


if __name__ == "__main__":
    unittest.main()
