"""
bOPEN context access token — issuance and verification.

Work package: BOPEN-P35-001 (WP-P35-03, deliverable D-08)
Governing artifact: BOPEN-IDP-001 section 12 (bOPEN session and context token standard)
Registry entry: CRED-TOKEN-CONTEXT-SIGNING in docs/07-security/secrets/BOPEN-SEC-VAULT-001.md

This module implements exactly one of the four token classes in `BOPEN-IDP-001` §12.1: the
**context access token**, which authorizes API access in one tenant context. The authentication
session token, the refresh handle and the delegation evidence token are Phase 2 concerns and are
not implemented here.

Why this token is the highest-value secret in the system: it *attests* which tenant a request
belongs to. Every control beneath it — including the PostgreSQL row-level security policies —
takes the tenant identity as given and enforces consequences. Forging this token therefore
defeats isolation without ever touching the database. That is why §12.4 mandates asymmetric keys
managed outside source control, and why this module refuses several things it could easily allow.

--------------------------------------------------------------------------------------------
Design decisions and why they are not negotiable
--------------------------------------------------------------------------------------------
**The algorithm is never read from the token.** `jwt.decode` is always called with an explicit
`algorithms=[_ALGORITHM]` allowlist. A verifier that selects its algorithm from the token's own
header is the classic JWT confusion vulnerability: an attacker rewrites `alg` and the verifier
obligingly switches to a scheme the attacker controls. `alg=none` is refused by the same
mechanism rather than by a special case, which is stronger — there is no branch to forget.

**An unknown `kid` is refused before signature verification.** §12.4 requires it. Resolving an
unknown key by falling back to "the current key" would silently accept tokens minted under a
retired or foreign key during a rotation window.

**Clock skew is capped, not configurable upward.** §12.5 allows a maximum of 60 seconds.
`leeway` is clamped, so a deployment cannot widen the window that expired tokens remain usable
by setting an environment variable.

**No token value is ever logged or returned in an error.** §12.4. Error messages name the
failure class and nothing else; a log line containing a valid token is a credential in the log.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

try:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError(
        "pyjwt[crypto] is required by the bOPEN context token layer.\n"
        "Install it with:  python -m pip install -r requirements.txt\n"
        "There is no symmetric fallback: BOPEN-IDP-001 section 12.4 mandates asymmetric "
        "signing keys, and a shared secret would let every verifier also mint tokens."
    ) from exc


# EdDSA over Ed25519. Chosen over RS256 and ES256 because it has no parameter choices to get
# wrong: no curve selection, no padding mode, no key-size decision, and no malleable signature
# encoding. For a claim this security-critical, the absence of options is the feature.
_ALGORITHM = "EdDSA"

ENV_PRIVATE_KEY = "BOPEN_CONTEXT_TOKEN_KEY"
ENV_ISSUER = "BOPEN_TOKEN_ISSUER"
ENV_AUDIENCE = "BOPEN_TOKEN_AUDIENCE"

DEFAULT_ISSUER = "https://bopen.local/kernel"
DEFAULT_AUDIENCE = "https://bopen.local/api"

# BOPEN-IDP-001 section 12.5 recommended defaults.
DEFAULT_TOKEN_LIFETIME = timedelta(minutes=5)
MAX_CLOCK_SKEW = timedelta(seconds=60)

# Section 12.2 mandatory claims. Verification refuses a token missing any of them rather than
# treating absence as an empty value, because a missing `tid` read as empty would resolve to no
# tenant and could be mistaken for a legitimately unscoped request.
MANDATORY_CLAIMS = (
    "iss", "aud", "sub", "tid", "mid", "roles", "scopes",
    "iat", "nbf", "exp", "jti", "sid", "ctx",
)


class TokenError(RuntimeError):
    """Base class for token failures. Never carries the token value."""


class TokenNotConfiguredError(TokenError):
    pass


class TokenVerificationError(TokenError):
    """A token was presented and refused. The reason is deliberately coarse.

    Distinguishing "expired" from "bad signature" from "unknown key" gives an attacker a probe
    channel for free. The specific cause is available to operators through the `reason` field,
    which belongs in an audit record and not in an HTTP response body.
    """

    def __init__(self, message: str, reason: str = "invalid_token") -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class ContextClaims:
    """The validated content of a context access token."""

    principal_id: str      # sub
    tenant_id: str         # tid
    membership_id: str     # mid
    context_id: str        # ctx
    session_id: str        # sid
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    token_id: str          # jti
    issued_at: datetime
    expires_at: datetime


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def compute_kid(public_key: Ed25519PublicKey) -> str:
    """RFC 7638 JWK thumbprint.

    Derived from the key rather than assigned, so a `kid` cannot be reused for a different key
    and two deployments holding the same key always agree on its identifier.
    """
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    jwk = {"crv": "Ed25519", "kty": "OKP", "x": _b64url(raw)}
    canonical = json.dumps(jwk, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64url(hashlib.sha256(canonical).digest())


class KeyRegistry:
    """Holds the signing key and every public key a verifier will accept.

    A registry rather than a single key because §12.4 requires rotation with an overlap period.
    During overlap, tokens signed by the outgoing key must still verify while new tokens are
    signed by the incoming one — which is only possible if verification is keyed by `kid`.
    """

    def __init__(self) -> None:
        self._private: Optional[Ed25519PrivateKey] = None
        self._signing_kid: Optional[str] = None
        self._public: dict[str, Ed25519PublicKey] = {}

    def load_signing_key(self, pem: str) -> str:
        key = serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise TokenError(
                f"context token signing key must be Ed25519, got {type(key).__name__}"
            )
        kid = compute_kid(key.public_key())
        self._private = key
        self._signing_kid = kid
        self._public[kid] = key.public_key()
        return kid

    def add_verification_key(self, public_pem: str) -> str:
        key = serialization.load_pem_public_key(public_pem.encode("utf-8"))
        if not isinstance(key, Ed25519PublicKey):
            raise TokenError("verification key must be Ed25519")
        kid = compute_kid(key)
        self._public[kid] = key
        return kid

    @property
    def signing_kid(self) -> str:
        if self._signing_kid is None:
            raise TokenNotConfiguredError(
                f"{ENV_PRIVATE_KEY} is not set.\n"
                f"Generate a development key with:\n"
                f"    python tools/generate_token_key.py\n"
                f"and place the PEM in .env.local. Registry entry: "
                f"CRED-TOKEN-CONTEXT-SIGNING in BOPEN-SEC-VAULT-001."
            )
        return self._signing_kid

    @property
    def private_key(self) -> Ed25519PrivateKey:
        self.signing_kid  # raises the configured error message if absent
        assert self._private is not None
        return self._private

    def public_key(self, kid: str) -> Ed25519PublicKey:
        key = self._public.get(kid)
        if key is None:
            # §12.4: reject unknown keys. Falling back to the current signing key here would
            # accept tokens minted under any key during a rotation window.
            raise TokenVerificationError("unknown key identifier", reason="unknown_kid")
        return key

    def jwks(self) -> dict:
        """Public JWKS document for verifier key discovery (§12.4).

        Contains public keys only. `use` and `alg` are pinned so a consumer cannot be talked
        into using one of these keys for encryption or under a different algorithm.
        """
        keys = []
        for kid, key in sorted(self._public.items()):
            raw = key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            keys.append(
                {
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "x": _b64url(raw),
                    "kid": kid,
                    "use": "sig",
                    "alg": _ALGORITHM,
                }
            )
        return {"keys": keys}

    def is_configured(self) -> bool:
        return self._private is not None


_registry = KeyRegistry()


def registry() -> KeyRegistry:
    """Return the process key registry, loading from the environment on first use."""
    if not _registry.is_configured():
        pem = os.environ.get(ENV_PRIVATE_KEY, "").strip()
        if pem:
            # Environment variables cannot hold literal newlines portably, so an escaped form
            # is accepted. Nothing is read from a file: §12.4 requires keys managed outside
            # source control, and a path-based default invites one being committed.
            _registry.load_signing_key(pem.replace("\\n", "\n"))
    return _registry


def issuer() -> str:
    return os.environ.get(ENV_ISSUER, "").strip() or DEFAULT_ISSUER


def audience() -> str:
    return os.environ.get(ENV_AUDIENCE, "").strip() or DEFAULT_AUDIENCE


def issue_context_token(
    *,
    principal_id: str,
    tenant_id: str,
    membership_id: str,
    context_id: str,
    roles: Sequence[str],
    scopes: Sequence[str] = (),
    lifetime: timedelta = DEFAULT_TOKEN_LIFETIME,
    session_id: Optional[str] = None,
) -> tuple[str, ContextClaims]:
    """Mint a context access token carrying exactly one active tenant context.

    §12.3 requires that `sub`, `tid` and `mid` resolve to one active relationship chain, and
    that `roles` and `scopes` are derived from authoritative bOPEN state at issuance. Both are
    the caller's responsibility: this function signs what it is given. It is called from
    `POST /v1/contexts`, immediately after the membership has been read under the tenant's own
    isolation policy — which is the only place that chain is known to be real.

    `sid` divergence, recorded rather than hidden: §12.2 lists `sid` as the authentication
    session identifier, but Phase 1 has no authentication session distinct from the context. It
    is therefore set to the context identifier. Fabricating an unrelated session identifier would
    put a value in an audit trail that corresponds to nothing. This must be revisited when
    Phase 2 sessions exist.
    """
    reg = registry()
    now = datetime.now(timezone.utc)
    expires = now + lifetime
    sid = session_id or context_id

    claims = {
        "iss": issuer(),
        "aud": audience(),
        "sub": principal_id,
        "tid": tenant_id,
        "mid": membership_id,
        "roles": list(roles),
        "scopes": list(scopes),
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": str(uuid.uuid4()),
        "sid": sid,
        "ctx": context_id,
        "ver": "1.0",
    }

    token = jwt.encode(
        claims,
        reg.private_key,
        algorithm=_ALGORITHM,
        headers={"kid": reg.signing_kid, "typ": "JWT"},
    )

    return token, ContextClaims(
        principal_id=principal_id,
        tenant_id=tenant_id,
        membership_id=membership_id,
        context_id=context_id,
        session_id=sid,
        roles=tuple(roles),
        scopes=tuple(scopes),
        token_id=claims["jti"],
        issued_at=now,
        expires_at=expires,
    )


def verify_context_token(token: str) -> ContextClaims:
    """Validate a context access token and return its claims, or raise.

    Order matters. The `kid` is resolved from the header *before* any signature check, so an
    unknown key is refused without the verifier ever being pointed at attacker-chosen key
    material. The algorithm is supplied by this function, never taken from the token.
    """
    reg = registry()
    if not reg.is_configured():
        raise TokenNotConfiguredError(
            f"{ENV_PRIVATE_KEY} is not set; the kernel cannot verify context tokens"
        )

    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise TokenVerificationError("token is malformed", reason="malformed")

    kid = header.get("kid")
    if not kid:
        # §12.4 requires `kid`. Without it a verifier must guess, and guessing means trying keys
        # until one works — which is indistinguishable from accepting any key it holds.
        raise TokenVerificationError("token has no key identifier", reason="missing_kid")

    public_key = reg.public_key(kid)  # raises unknown_kid

    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[_ALGORITHM],  # allowlist, never read from the token
            audience=audience(),
            issuer=issuer(),
            leeway=MAX_CLOCK_SKEW,
            options={
                "require": ["exp", "nbf", "iat", "iss", "aud", "sub", "jti"],
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )
    except jwt.ExpiredSignatureError:
        raise TokenVerificationError("token is not valid", reason="expired")
    except jwt.InvalidAudienceError:
        raise TokenVerificationError("token is not valid", reason="audience_mismatch")
    except jwt.InvalidIssuerError:
        raise TokenVerificationError("token is not valid", reason="issuer_mismatch")
    except jwt.InvalidSignatureError:
        raise TokenVerificationError("token is not valid", reason="bad_signature")
    except jwt.InvalidTokenError:
        raise TokenVerificationError("token is not valid", reason="invalid")

    missing = [claim for claim in MANDATORY_CLAIMS if claim not in claims]
    if missing:
        # Checked after signature verification: an unsigned token's claims are not worth
        # inspecting, and reporting which claims a forged token lacks would help refine it.
        raise TokenVerificationError(
            "token is not valid", reason=f"missing_claims:{','.join(missing)}"
        )

    if not isinstance(claims["roles"], list) or not isinstance(claims["scopes"], list):
        raise TokenVerificationError("token is not valid", reason="malformed_claims")

    return ContextClaims(
        principal_id=claims["sub"],
        tenant_id=claims["tid"],
        membership_id=claims["mid"],
        context_id=claims["ctx"],
        session_id=claims["sid"],
        roles=tuple(claims["roles"]),
        scopes=tuple(claims["scopes"]),
        token_id=claims["jti"],
        issued_at=datetime.fromtimestamp(claims["iat"], tz=timezone.utc),
        expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
    )


def generate_keypair() -> tuple[str, str, str]:
    """Generate an Ed25519 keypair. Returns (private_pem, public_pem, kid).

    Used by `tools/generate_token_key.py` for development keys. Production keys come from an
    external secret manager per §12.4 and are never generated by application code, because a key
    that application code can generate is a key application code can be tricked into rotating.
    """
    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    public_pem = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return private_pem, public_pem, compute_kid(private.public_key())
