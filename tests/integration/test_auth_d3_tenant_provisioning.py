"""`AUTH-D3` Row 1 (a) — tenant provisioning requires an assertion vouching for the owner.

Governed by [`DEC-P35-AUTH-D3-DOCKET`](../../docs/decisions/DEC-P35-AUTH-D3-DOCKET.md) `D-D3-001`,
operator-approved 2026-08-02.

The measured exposure (`auth-d3-exposure-measurement`) reproduced tenant squatting: an
unauthenticated caller provisioned a tenant naming **another** principal as owner, returning 201,
and that owner's authorization decisions were ALLOW. `POST /v1/tenants` names an
`owner_principal_id` that **must already exist**, so an assertion for that principal authenticates
the call — with no bootstrap problem, because the principal is not being created here.

This closes squatting and unauthenticated owner-binding. It does **not** close principal creation
(`POST /v1/principals`), which is the enrollment problem `D-D3-002` addresses.

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
from platform_kernel.api import app, principals

ISSUER = "https://authenticator.test.invalid"
AUDIENCE = "bopen-kernel-test"


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


class TenantProvisioningRequiresOwnerAssertion(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)
        self.private, self.public_pem = _keypair()
        self._saved = {
            n: os.environ.get(n)
            for n in (
                subject_assertion.ENV_ASSERTION_ISSUER,
                subject_assertion.ENV_ASSERTION_PUBLIC_KEY,
                subject_assertion.ENV_ASSERTION_AUDIENCE,
            )
        }
        os.environ[subject_assertion.ENV_ASSERTION_ISSUER] = ISSUER
        os.environ[subject_assertion.ENV_ASSERTION_PUBLIC_KEY] = self.public_pem
        os.environ[subject_assertion.ENV_ASSERTION_AUDIENCE] = AUDIENCE

    def tearDown(self) -> None:
        for n, v in self._saved.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v

    def _provision(self, owner_id: str, assertion: str | None) -> object:
        headers = {"X-Correlation-ID": str(uuid.uuid4())}
        if assertion is not None:
            headers["X-Subject-Assertion"] = assertion
        return self.client.post(
            "/v1/tenants",
            json={"name": f"t-{uuid.uuid4().hex[:8]}", "owner_principal_id": owner_id},
            headers=headers,
        )

    def _register_principal(self) -> str:
        """Provision an owner principal out of band (D-D3-002 Option B).

        These tests configure an authenticator, so `POST /v1/principals` is now closed — principal
        creation is out-of-band, not a public endpoint. The owner is provisioned directly through
        the repository, exactly as an operator/SCIM path would, rather than through the endpoint.
        """
        created = principals.create(
            email=f"owner-{uuid.uuid4().hex[:8]}@example.com", principal_type="human"
        )
        return created.id

    # -- the squatting probe the mitigation closes -------------------------------------

    def test_provisioning_without_an_assertion_is_refused_when_authenticator_configured(
        self,
    ) -> None:
        owner = self._register_principal()
        r = self._provision(owner, assertion=None)
        self.assertEqual(r.status_code, 401, r.text)

    def test_an_assertion_for_a_different_principal_cannot_bind_this_owner(self) -> None:
        """The squatting fix: a caller with an assertion for themselves cannot name someone else."""
        victim = self._register_principal()
        attacker = self._register_principal()
        # attacker holds a valid assertion for attacker, tries to make victim the owner
        r = self._provision(victim, assertion=_assertion(self.private, attacker))
        self.assertEqual(r.status_code, 403, r.text)
        self.assertIn("does not vouch", r.json().get("detail", ""))

    def test_an_assertion_for_the_named_owner_provisions(self) -> None:
        owner = self._register_principal()
        r = self._provision(owner, assertion=_assertion(self.private, owner))
        self.assertEqual(r.status_code, 201, r.text)

    def test_a_forged_assertion_is_refused(self) -> None:
        owner = self._register_principal()
        other, _ = _keypair()
        r = self._provision(owner, assertion=_assertion(other, owner))
        self.assertEqual(r.status_code, 401, r.text)

    def test_the_development_flag_cannot_reopen_provisioning_when_authenticator_configured(
        self,
    ) -> None:
        """Parallel to AUTH-D1: a configured authenticator is not overridable by the dev flag."""
        owner = self._register_principal()
        saved = os.environ.get("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION")
        os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = "1"
        try:
            r = self._provision(owner, assertion=None)
        finally:
            if saved is None:
                os.environ.pop("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION", None)
            else:
                os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = saved
        self.assertEqual(r.status_code, 401, "the dev flag reopened tenant provisioning")


if __name__ == "__main__":
    unittest.main()
