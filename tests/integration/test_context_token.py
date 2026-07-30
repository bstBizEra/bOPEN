"""
Context access token — adversarial verification.

Work package: BOPEN-P35-001 (WP-P35-03, deliverable D-08)
Governing artifact: BOPEN-IDP-001 section 12
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R4 (adversarial), R5 (fails loudly)

This token attests which tenant a request belongs to. Every control beneath it — including the
PostgreSQL row-level security policies — takes that identity as given. Forging it therefore
defeats isolation without touching the database, which makes it the single highest-value secret
in the system and the place where a negative test matters most.

Almost every test below is an attack. A suite that only proved a valid token works would
establish nothing about the ones that must not.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))


def _unavailable_reason() -> str | None:
    for module in ("psycopg", "fastapi", "httpx", "jwt", "cryptography"):
        try:
            __import__(module)
        except ImportError:
            return f"{module} is not installed. Run: python -m pip install -r requirements.txt"
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        return "BOPEN_DATABASE_URL is not set. Run: python tools/db_bootstrap.py --apply"
    if not os.environ.get("BOPEN_CONTEXT_TOKEN_KEY", "").strip():
        return (
            "BOPEN_CONTEXT_TOKEN_KEY is not set. Generate a development key with "
            "`python tools/generate_token_key.py` and place it in .env.local."
        )
    return None


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class TestTokenEvidenceAvailability(unittest.TestCase):
    """EBIV R5 — a token check that cannot run reports failure, never success."""

    def test_token_evidence_can_be_produced(self):
        reason = _unavailable_reason()
        self.assertIsNone(
            reason,
            msg=(
                "Context token behaviour cannot be verified in this environment, so no "
                f"admissible evidence exists for it.\n\n{reason}\n\n"
                "This failure is intentional under BOPEN-GOV-EBIV-001 R5."
            ),
        )


@unittest.skipIf(
    _unavailable_reason() is not None,
    "token stack unavailable — reported as a failure by TestTokenEvidenceAvailability",
)
class TestContextTokenSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from platform_kernel import tokens
        from platform_kernel.api import app

        cls.tokens = tokens
        cls.client = TestClient(app)

    # -- fixtures -----------------------------------------------------------------

    def _tenant_with_token(self) -> dict:
        principal = self.client.post(
            "/v1/principals",
            json={"email": f"t-{uuid.uuid4().hex[:12]}@example.com", "type": "human"},
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
        tenant_id = tenant.json()["tenant_id"]
        membership_id = tenant.json()["owner_membership_id"]

        envelope = self.client.post(
            "/v1/contexts",
            json={"principal_id": principal_id, "membership_id": membership_id},
            headers={"X-Tenant-ID": tenant_id, "X-Correlation-ID": corr()},
        )
        self.assertEqual(envelope.status_code, 201, envelope.text)
        body = envelope.json()
        return {
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "membership_id": membership_id,
            "context_id": body["context"]["context_id"],
            "token": body["access_token"],
        }

    def _authorize(self, headers: dict):
        return self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={"X-Correlation-ID": corr(), **headers},
        )

    # -- the token works at all ---------------------------------------------------

    def test_a_valid_token_alone_authorizes_without_any_tenant_header(self):
        """The point of the whole deliverable.

        No `X-Tenant-ID` and no `X-Context-ID` are sent. The tenant comes from the signed `tid`
        claim. If this passes while the cross-tenant tests below also pass, the tenant identity
        is attested rather than asserted.
        """
        a = self._tenant_with_token()
        self.assertIsNotNone(a["token"], "no token was issued")

        response = self._authorize({"Authorization": f"Bearer {a['token']}"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["decision"], "ALLOW")
        self.assertEqual(response.json()["tenant_id"], a["tenant_id"])

    def test_token_carries_every_mandatory_claim(self):
        """BOPEN-IDP-001 §12.2. A missing claim is refused rather than read as empty."""
        a = self._tenant_with_token()
        claims = self.tokens.verify_context_token(a["token"])
        self.assertEqual(claims.tenant_id, a["tenant_id"])
        self.assertEqual(claims.principal_id, a["principal_id"])
        self.assertEqual(claims.membership_id, a["membership_id"])
        self.assertEqual(claims.context_id, a["context_id"])
        self.assertEqual(claims.roles, ("owner",))
        self.assertTrue(claims.token_id)

    def test_lifetime_matches_the_approved_default(self):
        """§12.5 recommends a five-minute context access token lifetime."""
        a = self._tenant_with_token()
        claims = self.tokens.verify_context_token(a["token"])
        lifetime = claims.expires_at - claims.issued_at
        self.assertEqual(lifetime, timedelta(minutes=5))

    # -- attacks: signature and algorithm -----------------------------------------

    def test_alg_none_is_refused(self):
        """The canonical JWT attack.

        A verifier that reads `alg` from the token can be told to use no algorithm at all. This
        kernel never reads `alg` from the token — `jwt.decode` is always given an explicit
        allowlist — so the attack fails without a dedicated branch to forget.
        """
        a = self._tenant_with_token()
        header, payload, _ = a["token"].split(".")
        decoded_header = json.loads(base64.urlsafe_b64decode(header + "=="))
        forged_header = _b64url(
            json.dumps({"alg": "none", "typ": "JWT", "kid": decoded_header["kid"]}).encode()
        )
        forged = f"{forged_header}.{payload}."

        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)
        self.assertEqual(response.json()["detail"], "token is not valid")

    def test_a_tampered_tenant_claim_is_refused(self):
        """Rewriting `tid` is the direct route to another tenant's data.

        The payload is re-encoded with tenant B's identifier while keeping tenant A's signature.
        If this ever returned 200, every isolation control below it would be irrelevant.
        """
        a = self._tenant_with_token()
        b = self._tenant_with_token()

        header, payload, signature = a["token"].split(".")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
        claims["tid"] = b["tenant_id"]
        forged = f"{header}.{_b64url(json.dumps(claims).encode())}.{signature}"

        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)

    def test_a_token_signed_by_an_unknown_key_is_refused(self):
        """§12.4 requires unknown `kid` to be rejected.

        Falling back to the current signing key for an unrecognised `kid` would accept tokens
        minted under any key an attacker chose to name.
        """
        import jwt

        from platform_kernel import tokens as tok

        a = self._tenant_with_token()
        private_pem, _public_pem, foreign_kid = tok.generate_keypair()
        from cryptography.hazmat.primitives import serialization

        foreign_key = serialization.load_pem_private_key(private_pem.encode(), password=None)

        now = datetime.now(timezone.utc)
        forged = jwt.encode(
            {
                "iss": tok.issuer(),
                "aud": tok.audience(),
                "sub": a["principal_id"],
                "tid": a["tenant_id"],
                "mid": a["membership_id"],
                "roles": ["owner"],
                "scopes": [],
                "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()),
                "sid": a["context_id"],
                "ctx": a["context_id"],
            },
            foreign_key,
            algorithm="EdDSA",
            headers={"kid": foreign_kid},
        )

        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)

    def test_a_correctly_signed_token_with_a_foreign_kid_is_refused(self):
        """Isolates the `kid` check itself, which the test above does not.

        `test_a_token_signed_by_an_unknown_key_is_refused` was found by mutation probe MUT-J to
        pass even with the unknown-`kid` rejection removed: a token signed by a foreign key fails
        signature verification regardless, so that test exercises the signature check and not the
        key-resolution check. It was not testing what its name claimed.

        This token is signed by the *real* key and carries a *foreign* `kid`. With the §12.4
        rejection in place it is refused. Without it, key resolution falls back to the current
        signing key, the signature verifies, and the token is accepted — so this assertion fails
        exactly when the control it names is removed.
        """
        import jwt

        from platform_kernel import tokens as tok

        a = self._tenant_with_token()
        _private_pem, _public_pem, foreign_kid = tok.generate_keypair()
        self.assertNotEqual(foreign_kid, tok.registry().signing_kid)

        now = datetime.now(timezone.utc)
        forged = jwt.encode(
            {
                "iss": tok.issuer(), "aud": tok.audience(), "sub": a["principal_id"],
                "tid": a["tenant_id"], "mid": a["membership_id"], "roles": ["owner"],
                "scopes": [], "iat": int(now.timestamp()), "nbf": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()), "sid": a["context_id"], "ctx": a["context_id"],
            },
            tok.registry().private_key,          # the real signing key
            algorithm="EdDSA",
            headers={"kid": foreign_kid},        # a key identifier the kernel does not hold
        )

        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(
            response.status_code, 401,
            "a token naming an unknown kid was accepted because key resolution fell back",
        )

    def test_a_token_without_a_key_identifier_is_refused(self):
        """Without `kid` a verifier must guess, and guessing means trying every key it holds —
        which is indistinguishable from accepting any of them."""
        import jwt

        from platform_kernel import tokens as tok

        a = self._tenant_with_token()
        now = datetime.now(timezone.utc)
        forged = jwt.encode(
            {
                "iss": tok.issuer(), "aud": tok.audience(), "sub": a["principal_id"],
                "tid": a["tenant_id"], "mid": a["membership_id"], "roles": ["owner"],
                "scopes": [], "iat": int(now.timestamp()), "nbf": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()), "sid": a["context_id"], "ctx": a["context_id"],
            },
            tok.registry().private_key,
            algorithm="EdDSA",
        )
        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)

    # -- attacks: claim validation ------------------------------------------------

    def test_an_expired_token_is_refused(self):
        import jwt

        from platform_kernel import tokens as tok

        a = self._tenant_with_token()
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        forged = jwt.encode(
            {
                "iss": tok.issuer(), "aud": tok.audience(), "sub": a["principal_id"],
                "tid": a["tenant_id"], "mid": a["membership_id"], "roles": ["owner"],
                "scopes": [], "iat": int(past.timestamp()), "nbf": int(past.timestamp()),
                "exp": int((past + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()), "sid": a["context_id"], "ctx": a["context_id"],
            },
            tok.registry().private_key,
            algorithm="EdDSA",
            headers={"kid": tok.registry().signing_kid},
        )
        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)

    def test_a_token_for_a_different_audience_is_refused(self):
        """A token minted for another bOPEN service must not be replayable against the kernel."""
        import jwt

        from platform_kernel import tokens as tok

        a = self._tenant_with_token()
        now = datetime.now(timezone.utc)
        forged = jwt.encode(
            {
                "iss": tok.issuer(), "aud": "https://example.com/other-service",
                "sub": a["principal_id"], "tid": a["tenant_id"], "mid": a["membership_id"],
                "roles": ["owner"], "scopes": [], "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()), "sid": a["context_id"], "ctx": a["context_id"],
            },
            tok.registry().private_key,
            algorithm="EdDSA",
            headers={"kid": tok.registry().signing_kid},
        )
        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)

    def test_a_token_missing_a_mandatory_claim_is_refused(self):
        """§12.2 lists `mid` as mandatory. A missing `mid` read as empty would leave the
        sub/tid/mid chain unresolvable while the request still proceeded."""
        import jwt

        from platform_kernel import tokens as tok

        a = self._tenant_with_token()
        now = datetime.now(timezone.utc)
        forged = jwt.encode(
            {
                "iss": tok.issuer(), "aud": tok.audience(), "sub": a["principal_id"],
                "tid": a["tenant_id"],  # mid deliberately omitted
                "roles": ["owner"], "scopes": [], "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "jti": str(uuid.uuid4()), "sid": a["context_id"], "ctx": a["context_id"],
            },
            tok.registry().private_key,
            algorithm="EdDSA",
            headers={"kid": tok.registry().signing_kid},
        )
        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401, response.text)

    # -- attacks: cross-tenant and conflict ---------------------------------------

    def test_a_token_cannot_reach_another_tenants_audit_trail(self):
        a = self._tenant_with_token()
        b = self._tenant_with_token()

        b_correlation = corr()
        self.client.post(
            "/v1/authorize",
            json={
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            },
            headers={"Authorization": f"Bearer {b['token']}", "X-Correlation-ID": b_correlation},
        )

        a_view = self.client.get(
            "/v1/audit-events",
            headers={"Authorization": f"Bearer {a['token']}", "X-Correlation-ID": corr()},
        )
        self.assertEqual(a_view.status_code, 200, a_view.text)
        leaked = [e for e in a_view.json()["events"] if e["correlation_id"] == b_correlation]
        self.assertEqual(leaked, [], "a token holder read another tenant's audit event")

    def test_a_contradictory_tenant_header_is_refused_not_reconciled(self):
        """A caller sending a token for tenant A and a header naming tenant B is either
        confused or probing. Neither deserves a best-effort interpretation, so the request is
        refused rather than resolved in favour of either claim."""
        a = self._tenant_with_token()
        b = self._tenant_with_token()

        response = self._authorize(
            {"Authorization": f"Bearer {a['token']}", "X-Tenant-ID": b["tenant_id"]}
        )
        self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(response.json()["detail"], "tenant claim conflict")

    def test_a_matching_tenant_header_is_harmless(self):
        a = self._tenant_with_token()
        response = self._authorize(
            {"Authorization": f"Bearer {a['token']}", "X-Tenant-ID": a["tenant_id"]}
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_revoking_the_context_invalidates_an_unexpired_token(self):
        """Revocation must be immediate, not delayed until the token expires.

        The token is still cryptographically valid and well inside its five-minute lifetime.
        The stored context row is re-read on every request precisely so that revocation does not
        have to wait for expiry.
        """
        a = self._tenant_with_token()

        # Establishing a new context for the same principal revokes the previous one.
        second = self.client.post(
            "/v1/contexts",
            json={"principal_id": a["principal_id"], "membership_id": a["membership_id"]},
            headers={"X-Tenant-ID": a["tenant_id"], "X-Correlation-ID": corr()},
        )
        self.assertEqual(second.status_code, 201, second.text)

        stale = self._authorize({"Authorization": f"Bearer {a['token']}"})
        self.assertEqual(
            stale.status_code, 403,
            "a token for a revoked context was still honoured",
        )

    # -- key publication ----------------------------------------------------------

    def test_jwks_publishes_public_material_only(self):
        """The private key must never appear in the JWKS document.

        Ed25519 JWKs use `d` for the private scalar. Its presence would publish the signing key
        to every consumer of the discovery endpoint.
        """
        response = self.client.get("/.well-known/jwks.json")
        self.assertEqual(response.status_code, 200)
        document = response.json()
        self.assertGreaterEqual(len(document["keys"]), 1)

        for key in document["keys"]:
            self.assertEqual(key["kty"], "OKP")
            self.assertEqual(key["crv"], "Ed25519")
            self.assertEqual(key["alg"], "EdDSA")
            self.assertEqual(key["use"], "sig")
            self.assertNotIn("d", key, "the private key was published in the JWKS document")

        serialised = json.dumps(document)
        self.assertNotIn("PRIVATE", serialised)
        self.assertNotIn("BEGIN", serialised)

    def test_the_published_kid_matches_the_kid_in_issued_tokens(self):
        """A JWKS whose key identifiers do not match issued tokens is unusable for verification,
        and the failure would only surface at the gateway."""
        a = self._tenant_with_token()
        header = json.loads(base64.urlsafe_b64decode(a["token"].split(".")[0] + "=="))

        document = self.client.get("/.well-known/jwks.json").json()
        published = {key["kid"] for key in document["keys"]}
        self.assertIn(header["kid"], published)

    def test_no_token_value_appears_in_a_refusal_body(self):
        """§12.4 forbids logging complete token values. A refusal body that echoed the token
        would put a credential wherever that response is captured."""
        a = self._tenant_with_token()
        header, payload, signature = a["token"].split(".")
        forged = f"{header}.{payload}.{signature[:-4]}AAAA"

        response = self._authorize({"Authorization": f"Bearer {forged}"})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(payload, response.text)
        self.assertNotIn(signature[:20], response.text)


class TestContextTokenClaimTypes(unittest.TestCase):
    """
    Claim types, checked after the signature and before the claims are used.

    `roles` and `scopes` were type-checked; `sub`, `tid`, `mid`, `ctx`, `sid` and `jti` were not.
    Security review raised this on 2026-07-30 and rated it low, correctly — forging a token needs
    the Ed25519 private key, so nothing arrives here unsigned. It is fixed anyway because the
    omission was an inconsistency rather than a decision, and because the consequence leaves this
    module: `tid` flows into `db.tenant_session`, which would bind a non-string through `str()`,
    match no policy, and be read by the caller as "this tenant has no data" rather than as an
    error.

    Every token below is signed with the real signing key, so nothing here is testing signature
    verification.
    """

    @classmethod
    def setUpClass(cls):
        import time

        from cryptography.hazmat.primitives import serialization

        from platform_kernel import tokens

        cls.tokens = tokens
        cls.time = time
        registry = tokens.registry()
        if not registry.is_configured():
            raise unittest.SkipTest("BOPEN_CONTEXT_TOKEN_KEY is not set")
        cls.kid = registry.signing_kid
        cls.private_pem = registry.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")

    def _forge(self, **overrides) -> str:
        import jwt as pyjwt

        now = int(self.time.time())
        claims = {
            "iss": self.tokens.issuer(),
            "aud": self.tokens.audience(),
            "sub": str(uuid.uuid4()),
            "tid": str(uuid.uuid4()),
            "mid": str(uuid.uuid4()),
            "ctx": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "jti": str(uuid.uuid4()),
            "roles": ["owner"],
            "scopes": ["tenant:read"],
            "iat": now,
            "nbf": now,
            "exp": now + 300,
        }
        claims.update(overrides)
        return pyjwt.encode(
            claims, self.private_pem, algorithm="EdDSA", headers={"kid": self.kid}
        )

    def test_a_correctly_shaped_token_still_verifies(self):
        """
        The control. Without it every assertion below is satisfied by a function that rejects
        everything, which is a way of passing a security test while breaking the product.
        """
        claims = self.tokens.verify_context_token(self._forge())
        self.assertIsInstance(claims.tenant_id, str)
        self.assertEqual(claims.roles, ("owner",))

    def test_an_identifier_claim_that_is_not_a_string_is_refused(self):
        for claim in ("sub", "tid", "mid", "ctx", "sid", "jti"):
            for value in ({"$ne": None}, 12345, ["a"], None, "", "   "):
                with self.subTest(claim=claim, value=value):
                    with self.assertRaises(self.tokens.TokenVerificationError):
                        self.tokens.verify_context_token(self._forge(**{claim: value}))

    def test_a_role_or_scope_that_is_not_a_string_is_refused(self):
        """
        A non-string member compares unequal to every real role, so it fails closed — but
        silently, and it would then be written into the audit record as something no reviewer
        could match against anything.
        """
        for override in (
            {"roles": [{"role": "owner"}]},
            {"roles": [1]},
            {"roles": ["owner", None]},
            {"roles": "owner"},
            {"scopes": [1]},
            {"scopes": [["tenant:read"]]},
            {"scopes": ""},
        ):
            with self.subTest(**override):
                with self.assertRaises(self.tokens.TokenVerificationError):
                    self.tokens.verify_context_token(self._forge(**override))


if __name__ == "__main__":
    unittest.main()
