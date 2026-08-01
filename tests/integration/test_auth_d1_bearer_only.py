"""`AUTH-D1` — protected endpoints are bearer-only; `X-Context-ID` confers no authority.

Governed by [`DEC-P35-AUTH-CLOSURE`](../../docs/decisions/DEC-P35-AUTH-CLOSURE.md), `AUTH-D1`
ACCEPTED 2026-08-01 (option 3). Normative basis: OWASP ASVS 5.0 §6.8.2 — signature presence and
integrity are always validated, and unsigned or invalid assertions rejected.

These tests were written **before** the code that satisfies them, per the decision's own
sequencing (§4 step 2: "add failing negative tests for the two reproduced probes").

The defect they close was reproduced independently by two engines on 2026-07-31: a tenant member
presenting another member's `X-Context-ID`, with no token, obtained `200 ALLOW` and acted as that
member. The identifier is published to every member of the tenant through `GET /v1/audit-events`,
so acquiring one required no attack.
"""

from __future__ import annotations

import os
import unittest
import uuid

from fastapi.testclient import TestClient

from platform_kernel import api as kernel_api
from platform_kernel.api import app

LEGACY_ENV = "BOPEN_LEGACY_CONTEXT_HEADER_PROFILE"


def _headers(**extra: str) -> dict:
    base = {"X-Correlation-ID": str(uuid.uuid4())}
    base.update(extra)
    return base


class LegacyContextPathConfersNoAuthority(unittest.TestCase):
    """A context identifier alone must reach nothing, in either direction."""

    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)
        self._saved = os.environ.get(LEGACY_ENV)
        os.environ.pop(LEGACY_ENV, None)  # default: legacy profile OFF
        self.tenant = str(uuid.uuid4())
        self.context = str(uuid.uuid4())

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop(LEGACY_ENV, None)
        else:
            os.environ[LEGACY_ENV] = self._saved

    def _legacy(self) -> dict:
        return _headers(**{"X-Tenant-ID": self.tenant, "X-Context-ID": self.context})

    # -- the four operations the disposition names explicitly ---------------------------

    def test_a_context_id_alone_cannot_obtain_an_authorization_decision(self) -> None:
        """The reproduced probe. It returned 200 ALLOW before AUTH-D1."""
        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers=self._legacy(),
        )
        self.assertEqual(
            response.status_code, 401,
            "possession of a context identifier obtained an authorization decision",
        )

    def test_a_context_id_alone_cannot_read(self) -> None:
        response = self.client.get(
            f"/v1/resources/{uuid.uuid4()}", headers=self._legacy()
        )
        self.assertEqual(response.status_code, 401)

    def test_a_context_id_alone_cannot_write(self) -> None:
        response = self.client.post(
            "/v1/resources?resource_name=probe", headers=self._legacy()
        )
        self.assertEqual(response.status_code, 401)

    def test_a_context_id_alone_cannot_enumerate_audit_events(self) -> None:
        """Audit enumeration is how the identifier leaks in the first place."""
        response = self.client.get("/v1/audit-events", headers=self._legacy())
        self.assertEqual(response.status_code, 401)

    # -- the rules that make the refusal a boundary rather than a preference ------------

    def test_a_rejected_token_does_not_fall_back_to_the_header(self) -> None:
        """No automatic fallback after verification failure.

        A caller presenting a bad token *and* a context id must be refused, not quietly
        downgraded to header-asserted identity. A downgrade would make the token optional in
        practice while appearing mandatory in the contract.
        """
        response = self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers=self._legacy() | {"Authorization": "Bearer not.a.valid.token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_the_legacy_profile_is_off_unless_explicitly_set(self) -> None:
        os.environ.pop(LEGACY_ENV, None)
        self.assertFalse(kernel_api.legacy_context_header_profile_enabled())

    def test_the_legacy_profile_cannot_be_enabled_on_a_production_profile(self) -> None:
        """`AUTH-D1`: "cannot be enabled on a production profile".

        Enforced rather than documented. An escape hatch that a production deployment can turn on
        is not test-only; it is a switch waiting for a bad day.
        """
        saved_env = os.environ.get("BOPEN_ENV")
        os.environ[LEGACY_ENV] = "1"
        os.environ["BOPEN_ENV"] = "production"
        try:
            self.assertFalse(
                kernel_api.legacy_context_header_profile_enabled(),
                "the legacy profile was enabled on a production profile",
            )
        finally:
            if saved_env is None:
                os.environ.pop("BOPEN_ENV", None)
            else:
                os.environ["BOPEN_ENV"] = saved_env

    def test_the_legacy_profile_is_available_for_local_development(self) -> None:
        """The transition must not be so strict that no deployment can migrate."""
        saved_env = os.environ.get("BOPEN_ENV")
        os.environ[LEGACY_ENV] = "1"
        os.environ["BOPEN_ENV"] = "local"
        try:
            self.assertTrue(kernel_api.legacy_context_header_profile_enabled())
        finally:
            if saved_env is None:
                os.environ.pop("BOPEN_ENV", None)
            else:
                os.environ["BOPEN_ENV"] = saved_env


if __name__ == "__main__":
    unittest.main()
