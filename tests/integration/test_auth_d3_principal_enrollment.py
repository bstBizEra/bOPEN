"""`D-D3-002` Option B — principal creation is out-of-band, not a public endpoint.

Governed by [`DEC-P35-AUTH-D3-DOCKET`](../../docs/decisions/DEC-P35-AUTH-D3-DOCKET.md) `D-D3-002`,
operator-disposed 2026-08-02 to **Option B**: keep principal creation out of the exposed kernel
surface. Principals are provisioned by an out-of-band operator/SCIM path, not through a public
`POST /v1/principals` endpoint, and **no new bearer-by-identifier enrollment credential is added**
(that would be Option A, which reintroduces the class `AUTH-D1` retired).

The consequence of "no new credential" is that the refusal is **503, not 401**: there is no
assertion a caller could present that opens this endpoint, so 401 (which implies a credential would
help) would be a lie. This mirrors `_refuse_unauthenticated` for context issuance before an
authenticator existed, and differs deliberately from tenant provisioning (`AUTH-D3` Row 1(a)),
which DID gain an assertion path because it names an already-existing principal.

Behaviour, three cases:
  - an authenticator is configured (a real deployment) -> 503, and the development flag does NOT
    reopen it (parity with context issuance and tenant provisioning);
  - no authenticator, development flag unset -> 503 (an unaffirmed deployment is refused);
  - no authenticator, development flag set -> 201 (local/out-of-band provisioning, unchanged).

Tests written before the code, per the engineering loop.
"""

from __future__ import annotations

import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fastapi.testclient import TestClient

from platform_kernel import subject_assertion
from platform_kernel.api import app

ISSUER = "https://authenticator.test.invalid"
AUDIENCE = "bopen-kernel-test"
FLAG = "BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"


def _keypair() -> tuple[Ed25519PrivateKey, str]:
    private = Ed25519PrivateKey.generate()
    public_pem = (
        private.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private, public_pem


def _private_pem(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _assertion(private: Ed25519PrivateKey, subject: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=120)).timestamp()),
            "jti": str(uuid.uuid4()),
        },
        _private_pem(private),
        algorithm="EdDSA",
    )


class PrincipalCreationIsOutOfBand(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)
        self._saved = {
            n: os.environ.get(n)
            for n in (
                subject_assertion.ENV_ASSERTION_ISSUER,
                subject_assertion.ENV_ASSERTION_PUBLIC_KEY,
                subject_assertion.ENV_ASSERTION_AUDIENCE,
                FLAG,
            )
        }
        # Start from a clean slate: no authenticator, flag unset. Each test opts in.
        for n in (
            subject_assertion.ENV_ASSERTION_ISSUER,
            subject_assertion.ENV_ASSERTION_PUBLIC_KEY,
            subject_assertion.ENV_ASSERTION_AUDIENCE,
            FLAG,
        ):
            os.environ.pop(n, None)

    def tearDown(self) -> None:
        for n, v in self._saved.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v

    def _configure_authenticator(self) -> Ed25519PrivateKey:
        private, public_pem = _keypair()
        os.environ[subject_assertion.ENV_ASSERTION_ISSUER] = ISSUER
        os.environ[subject_assertion.ENV_ASSERTION_PUBLIC_KEY] = public_pem
        os.environ[subject_assertion.ENV_ASSERTION_AUDIENCE] = AUDIENCE
        return private

    def _register(self, assertion: str | None = None) -> object:
        headers = {"X-Correlation-ID": str(uuid.uuid4())}
        if assertion is not None:
            headers["X-Subject-Assertion"] = assertion
        return self.client.post(
            "/v1/principals",
            json={"email": f"p-{uuid.uuid4().hex[:8]}@example.com", "type": "human"},
            headers=headers,
        )

    # -- the three cases ---------------------------------------------------------------

    def test_no_authenticator_and_flag_unset_is_refused(self) -> None:
        """An unaffirmed deployment refuses principal creation."""
        r = self._register()
        self.assertEqual(r.status_code, 503, r.text)

    def test_no_authenticator_and_flag_set_provisions(self) -> None:
        """Local/out-of-band provisioning is unchanged when the deployment affirms non-production."""
        os.environ[FLAG] = "1"
        r = self._register()
        self.assertEqual(r.status_code, 201, r.text)

    def test_a_configured_authenticator_closes_the_endpoint(self) -> None:
        """A real deployment: principals come from an out-of-band path, not this endpoint."""
        self._configure_authenticator()
        r = self._register()
        self.assertEqual(r.status_code, 503, r.text)

    def test_the_development_flag_cannot_reopen_it_against_a_configured_authenticator(self) -> None:
        """Parity with AUTH-D1/AUTH-D3: a configured authenticator is not overridable by the flag."""
        self._configure_authenticator()
        os.environ[FLAG] = "1"
        r = self._register()
        self.assertEqual(r.status_code, 503, "the dev flag reopened principal creation")

    def test_no_assertion_opens_it_option_b_adds_no_credential(self) -> None:
        """Option B adds no enrollment credential: presenting a valid assertion does not open it."""
        private = self._configure_authenticator()
        # a well-formed assertion for some subject — under Option A this might enroll; under B it must not
        r = self._register(assertion=_assertion(private, f"usr_{uuid.uuid4()}"))
        self.assertEqual(r.status_code, 503, "an assertion opened principal creation (that is Option A)")


if __name__ == "__main__":
    unittest.main()
