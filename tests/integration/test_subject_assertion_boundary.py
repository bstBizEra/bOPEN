"""WP-P35-05a — the kernel authentication boundary.

Governed by [`DEC-P35-IDP-SPLIT`](../../docs/decisions/DEC-P35-IDP-SPLIT.md) §4.

Before this work package the kernel could not authenticate anyone: `POST /v1/contexts` issued an
owner bearer token to any caller who knew three identifiers, guarded only by an environment
flag. These tests assert the guard is now a mechanism.

Written to `BOPEN-GOV-EBIV-001` R4. The central negative probe is
`test_the_development_flag_cannot_override_a_configured_authenticator`: if that ever passes with
the override working, the boundary is decorative.
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

#: Sentinel distinguishing "use the default key" from "unset the key" in `_configure`.
_DEFAULT_KEY = object()


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


def _assertion(
    private: Ed25519PrivateKey,
    subject: str,
    *,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    lifetime_seconds: int = 120,
    omit: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=lifetime_seconds)).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if omit:
        claims.pop(omit)
    return jwt.encode(claims, _private_pem(private), algorithm="EdDSA")


class SubjectAssertionBoundaryTests(unittest.TestCase):
    """Each test sets its own environment and restores it, so ordering cannot leak state."""

    def setUp(self) -> None:
        self.private, self.public_pem = _keypair()
        self._saved = {
            name: os.environ.get(name)
            for name in (
                subject_assertion.ENV_ASSERTION_ISSUER,
                subject_assertion.ENV_ASSERTION_PUBLIC_KEY,
                subject_assertion.ENV_ASSERTION_AUDIENCE,
            )
        }
        self.client = TestClient(app)

    def tearDown(self) -> None:
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _configure(self, *, issuer: str | None = ISSUER, key: str | None = _DEFAULT_KEY,
                   audience: str | None = AUDIENCE) -> None:
        """`key=_DEFAULT_KEY` uses this test's public key; `key=None` unsets it.

        A plain `None` default would have made "use the default key" and "unset the key"
        indistinguishable, which is how the first version of this helper silently kept an
        authenticator configured in the test that meant to remove it.
        """
        mapping = {
            subject_assertion.ENV_ASSERTION_ISSUER: issuer,
            subject_assertion.ENV_ASSERTION_PUBLIC_KEY:
                self.public_pem if key is _DEFAULT_KEY else key,
            subject_assertion.ENV_ASSERTION_AUDIENCE: audience,
        }
        for name, value in mapping.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    # -- configuration detection -------------------------------------------------------

    def test_no_configuration_means_no_authenticator(self) -> None:
        self._configure(issuer=None, key=None, audience=None)
        self.assertFalse(subject_assertion.authenticator_configured())
        self.assertFalse(subject_assertion.configuration_is_partial())

    def test_full_configuration_is_detected(self) -> None:
        self._configure()
        self.assertTrue(subject_assertion.authenticator_configured())
        self.assertFalse(subject_assertion.configuration_is_partial())

    def test_partial_configuration_is_not_read_as_absent(self) -> None:
        """The dangerous misreading: half-configured must not mean "no authenticator wanted"."""
        self._configure(audience=None)
        self.assertFalse(subject_assertion.authenticator_configured())
        self.assertTrue(subject_assertion.configuration_is_partial())

    # -- verification ------------------------------------------------------------------

    def test_a_well_formed_assertion_verifies(self) -> None:
        self._configure()
        principal = str(uuid.uuid4())
        claims = subject_assertion.verify_subject_assertion(
            _assertion(self.private, principal)
        )
        self.assertEqual(claims.principal_id, principal)
        self.assertEqual(claims.issuer, ISSUER)

    def test_an_assertion_from_another_key_is_refused(self) -> None:
        self._configure()
        other, _ = _keypair()
        with self.assertRaises(subject_assertion.AssertionVerificationError) as caught:
            subject_assertion.verify_subject_assertion(
                _assertion(other, str(uuid.uuid4()))
            )
        self.assertEqual(caught.exception.reason, "bad_signature")

    def test_an_assertion_from_another_issuer_is_refused(self) -> None:
        self._configure()
        with self.assertRaises(subject_assertion.AssertionVerificationError):
            subject_assertion.verify_subject_assertion(
                _assertion(self.private, str(uuid.uuid4()), issuer="https://evil.invalid")
            )

    def test_an_assertion_for_another_audience_is_refused(self) -> None:
        """An assertion minted for a different relying party must not be replayable here."""
        self._configure()
        with self.assertRaises(subject_assertion.AssertionVerificationError):
            subject_assertion.verify_subject_assertion(
                _assertion(self.private, str(uuid.uuid4()), audience="some-other-service")
            )

    def test_an_expired_assertion_is_refused(self) -> None:
        self._configure()
        with self.assertRaises(subject_assertion.AssertionVerificationError) as caught:
            subject_assertion.verify_subject_assertion(
                _assertion(self.private, str(uuid.uuid4()), lifetime_seconds=-3600)
            )
        self.assertEqual(caught.exception.reason, "expired")

    def test_an_unsigned_assertion_is_refused(self) -> None:
        """`alg: none` is the canonical JWT forgery and must not be honoured."""
        self._configure()
        forged = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": str(uuid.uuid4()),
                "iat": int(datetime.now(timezone.utc).timestamp()),
                "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()),
            },
            key="",
            algorithm="none",
        )
        with self.assertRaises(subject_assertion.AssertionVerificationError):
            subject_assertion.verify_subject_assertion(forged)

    def test_a_missing_mandatory_claim_is_refused(self) -> None:
        self._configure()
        for claim in ("jti", "exp", "sub"):
            with self.subTest(claim=claim):
                with self.assertRaises(subject_assertion.AssertionVerificationError):
                    subject_assertion.verify_subject_assertion(
                        _assertion(self.private, str(uuid.uuid4()), omit=claim)
                    )

    def test_a_non_string_subject_is_refused(self) -> None:
        """JWT claims are whatever JSON says. A dict `sub` must fail, not compare unequal.

        Measured 2026-07-31: PyJWT rejects this itself with `InvalidTokenError`, so the refusal
        carries reason `invalid` rather than reaching this module's own type check. The test
        asserts the refusal, not the layer that produced it — asserting the layer would make it
        fail the day PyJWT changed, without anything having become less safe.

        The explicit type check in `verify_subject_assertion` is kept as defence in depth. It
        covers `jti`, which PyJWT requires to be present but does not type-check.
        """
        self._configure()
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": {"nested": "value"},
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()),
            },
            _private_pem(self.private),
            algorithm="EdDSA",
        )
        with self.assertRaises(subject_assertion.AssertionVerificationError):
            subject_assertion.verify_subject_assertion(token)

    def test_a_non_string_jti_is_refused(self) -> None:
        """As with `sub`, PyJWT refuses this first (measured 2026-07-31, reason `invalid`).

        The test asserts refusal rather than which layer refused, for the same reason as above.
        """
        self._configure()
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": str(uuid.uuid4()),
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": 12345,
            },
            _private_pem(self.private),
            algorithm="EdDSA",
        )
        with self.assertRaises(subject_assertion.AssertionVerificationError):
            subject_assertion.verify_subject_assertion(token)

    def test_a_symmetric_key_cannot_be_configured(self) -> None:
        """BOPEN-IDP-001 12.4 keeps signing asymmetric so a verifier cannot also be an issuer."""
        self._configure(key="not-a-pem-public-key")
        with self.assertRaises(Exception):
            subject_assertion.verify_subject_assertion(
                _assertion(self.private, str(uuid.uuid4()))
            )

    # -- the endpoint boundary ---------------------------------------------------------

    def test_context_issuance_without_an_assertion_is_refused_when_configured(self) -> None:
        self._configure()
        response = self.client.post(
            "/v1/contexts",
            json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
            headers={
                "X-Tenant-ID": str(uuid.uuid4()),
                "X-Correlation-ID": str(uuid.uuid4()),
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_the_development_flag_cannot_override_a_configured_authenticator(self) -> None:
        """The probe this work package exists for.

        `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION` is set to 1 *and* an authenticator is
        configured. If the flag won, a deployment could disable its own authentication with an
        environment variable, and the boundary would be decorative. The request must still be
        refused for want of an assertion.
        """
        self._configure()
        saved = os.environ.get("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION")
        os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = "1"
        try:
            response = self.client.post(
                "/v1/contexts",
                json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
                headers={
                    "X-Tenant-ID": str(uuid.uuid4()),
                    "X-Correlation-ID": str(uuid.uuid4()),
                },
            )
        finally:
            if saved is None:
                os.environ.pop("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION", None)
            else:
                os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = saved

        self.assertEqual(
            response.status_code,
            401,
            "the development flag overrode a configured authenticator",
        )

    def test_partial_configuration_refuses_rather_than_opening_the_flag_path(self) -> None:
        self._configure(audience=None)
        saved = os.environ.get("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION")
        os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = "1"
        try:
            response = self.client.post(
                "/v1/contexts",
                json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
                headers={
                    "X-Tenant-ID": str(uuid.uuid4()),
                    "X-Correlation-ID": str(uuid.uuid4()),
                },
            )
        finally:
            if saved is None:
                os.environ.pop("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION", None)
            else:
                os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = saved

        self.assertEqual(response.status_code, 503)

    def test_an_assertion_for_one_principal_cannot_mint_a_context_for_another(self) -> None:
        """Without this check, anyone holding a valid assertion could impersonate anyone."""
        self._configure()
        vouched_for = str(uuid.uuid4())
        someone_else = str(uuid.uuid4())

        response = self.client.post(
            "/v1/contexts",
            json={"principal_id": someone_else, "membership_id": str(uuid.uuid4())},
            headers={
                "X-Tenant-ID": str(uuid.uuid4()),
                "X-Correlation-ID": str(uuid.uuid4()),
                "X-Subject-Assertion": _assertion(self.private, vouched_for),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("does not vouch", response.json()["detail"])

    def test_a_forged_assertion_is_refused_at_the_endpoint(self) -> None:
        self._configure()
        other, _ = _keypair()
        response = self.client.post(
            "/v1/contexts",
            json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
            headers={
                "X-Tenant-ID": str(uuid.uuid4()),
                "X-Correlation-ID": str(uuid.uuid4()),
                "X-Subject-Assertion": _assertion(other, str(uuid.uuid4())),
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("signature", str(response.json()).lower())

    def test_with_no_authenticator_the_previous_behaviour_is_unchanged(self) -> None:
        """05a is additive. A deployment configuring nothing behaves exactly as before."""
        self._configure(issuer=None, key=None, audience=None)
        saved = os.environ.get("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION")
        os.environ.pop("BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION", None)
        try:
            response = self.client.post(
                "/v1/contexts",
                json={"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())},
                headers={
                    "X-Tenant-ID": str(uuid.uuid4()),
                    "X-Correlation-ID": str(uuid.uuid4()),
                },
            )
        finally:
            if saved is not None:
                os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = saved

        self.assertEqual(response.status_code, 503)


class ResidualDefectsClosed(SubjectAssertionBoundaryTests):
    """The four defects the 2026-07-31 sweep found and Codex confirmed still reproducible.

    Each was disclosed in `EVD-P35-05A-MAKER-R2` §6.3 as open. These close three of them and
    bound the fourth.
    """

    def test_a_malformed_pem_refuses_rather_than_crashing(self) -> None:
        """Was 500. A 500 says the kernel broke; a 503 says this deployment is misconfigured."""
        for bad in (
            "-----BEGIN PUBLIC KEY-----\nnot base64\n-----END PUBLIC KEY-----",
            "not-a-pem-at-all",
        ):
            with self.subTest(key=bad[:24]):
                self._configure(key=bad)
                response = self.client.post(
                    "/v1/contexts",
                    json={
                        "principal_id": str(uuid.uuid4()),
                        "membership_id": str(uuid.uuid4()),
                    },
                    headers={
                        "X-Tenant-ID": str(uuid.uuid4()),
                        "X-Correlation-ID": str(uuid.uuid4()),
                        "X-Subject-Assertion": _assertion(self.private, str(uuid.uuid4())),
                    },
                )
                self.assertEqual(response.status_code, 503, response.text)

    def test_an_assertion_longer_than_the_ceiling_is_refused(self) -> None:
        """Codex accepted a 10-year assertion. Every replay minted a fresh context token."""
        self._configure()
        with self.assertRaises(subject_assertion.AssertionVerificationError) as caught:
            subject_assertion.verify_subject_assertion(
                _assertion(
                    self.private,
                    str(uuid.uuid4()),
                    lifetime_seconds=subject_assertion.MAX_ASSERTION_LIFETIME + 60,
                )
            )
        self.assertEqual(caught.exception.reason, "lifetime_exceeds_ceiling")

    def test_an_assertion_within_the_ceiling_is_accepted(self) -> None:
        self._configure()
        claims = subject_assertion.verify_subject_assertion(
            _assertion(
                self.private,
                str(uuid.uuid4()),
                lifetime_seconds=subject_assertion.MAX_ASSERTION_LIFETIME,
            )
        )
        self.assertIsNotNone(claims.principal_id)

    def test_a_valid_signature_with_a_bad_subject_is_indistinguishable_from_a_bad_signature(
        self,
    ) -> None:
        """The oracle. Two refusals must not differ in what they tell a forger.

        A valid signature carrying a non-UUID `sub` returned 400 and named the field; a forged
        signature returned 401 and said nothing. The difference told an attacker their signature
        had been accepted — the single most useful bit of feedback available to them.
        """
        self._configure()
        other, _ = _keypair()
        headers = {
            "X-Tenant-ID": str(uuid.uuid4()),
            "X-Correlation-ID": str(uuid.uuid4()),
        }
        body = {"principal_id": str(uuid.uuid4()), "membership_id": str(uuid.uuid4())}

        good_sig_bad_sub = self.client.post(
            "/v1/contexts",
            json=body,
            headers=headers | {"X-Subject-Assertion": _assertion(self.private, "auth0|123")},
        )
        bad_sig = self.client.post(
            "/v1/contexts",
            json=body,
            headers=headers | {"X-Subject-Assertion": _assertion(other, str(uuid.uuid4()))},
        )

        self.assertEqual(good_sig_bad_sub.status_code, 401)
        self.assertEqual(bad_sig.status_code, 401)
        self.assertEqual(
            good_sig_bad_sub.json(), bad_sig.json(),
            "the two refusals differ, which tells a forger whether the signature was accepted",
        )


if __name__ == "__main__":
    unittest.main()
