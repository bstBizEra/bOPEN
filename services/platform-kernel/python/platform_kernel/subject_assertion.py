"""Verification of an external authenticator's assertion about who the caller is.

`WP-P35-05a` — the kernel authentication boundary, per
[`DEC-P35-IDP-SPLIT`](../../../../docs/decisions/DEC-P35-IDP-SPLIT.md) §4.

Until now the kernel could not authenticate anyone. `POST /v1/contexts` issued an owner bearer
token to any caller who knew three identifiers, guarded only by
`BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`. That is a flag, not a mechanism: a deployment
that sets it hands an owner token to whoever can reach it.

This module gives the kernel something to check. An external authenticator — outside the kernel
process, per `DEC-P35-AUTH-BOUNDARY` §2, which keeps the kernel from becoming an IdP — signs a
short-lived assertion naming the principal. The kernel verifies it and refuses to take the
caller's word for who they are.

**Scope, stated plainly.** One authenticator for the whole kernel, configured by environment.
There is no per-tenant connection model and no new table, because `sso_connections` and
`external_identities` do not exist and creating them needs `D-P35-004`..`D-P35-010`, which are
unratified. This is a boundary where there was none. It is not federation, and it must not be
widened into federation without those decisions — see `DEC-P35-IDP-SPLIT` §6.1.

Verification discipline is copied from `tokens.py` rather than reinvented, including the two
rules that matter most: the algorithm is supplied by this module and never read from the token,
and claims are inspected only after the signature holds.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ENV_ASSERTION_ISSUER = "BOPEN_SUBJECT_ASSERTION_ISSUER"
ENV_ASSERTION_PUBLIC_KEY = "BOPEN_SUBJECT_ASSERTION_PUBLIC_KEY"
ENV_ASSERTION_AUDIENCE = "BOPEN_SUBJECT_ASSERTION_AUDIENCE"

_ALGORITHM = "EdDSA"

# Matches `tokens.MAX_CLOCK_SKEW`. An assertion is short-lived by design, so leeway is the only
# thing standing between a correct deployment and spurious refusals on modest clock drift.
MAX_CLOCK_SKEW = 60

MANDATORY_CLAIMS = ("iss", "aud", "sub", "exp", "iat", "jti")


class SubjectAssertionError(RuntimeError):
    """Base class for assertion failures."""


class AssertionNotConfiguredError(SubjectAssertionError):
    """Raised when verification is attempted with no authenticator configured."""


class AssertionVerificationError(SubjectAssertionError):
    """Raised when an assertion is present but not acceptable.

    `reason` is for the audit record. It is deliberately not returned to the caller: telling a
    forger which check failed is how a forgery gets refined.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class SubjectClaims:
    """What the authenticator vouched for. Never persisted (`D-P35-010`)."""

    principal_id: str
    issuer: str
    assertion_id: str


def _configured_issuer() -> Optional[str]:
    value = os.environ.get(ENV_ASSERTION_ISSUER, "").strip()
    return value or None


def _configured_public_key() -> Optional[str]:
    value = os.environ.get(ENV_ASSERTION_PUBLIC_KEY, "").strip()
    return value or None


def _configured_audience() -> Optional[str]:
    value = os.environ.get(ENV_ASSERTION_AUDIENCE, "").strip()
    return value or None


def authenticator_configured() -> bool:
    """True when this kernel has an authenticator to check against.

    All three of issuer, key and audience are required together. A partial configuration returns
    False, which routes the caller to the 503 refusal rather than to a verification path that
    could not succeed — and, critically, never to the unauthenticated path. A half-configured
    authenticator is an operator error, and the safe reading of an operator error that concerns
    authentication is that authentication was intended.
    """
    return bool(_configured_issuer() and _configured_public_key() and _configured_audience())


def configuration_is_partial() -> bool:
    """True when some but not all authenticator settings are present.

    Distinguished from "none configured" so the kernel can refuse loudly instead of silently
    behaving as though no authenticator were wanted.
    """
    present = [
        bool(_configured_issuer()),
        bool(_configured_public_key()),
        bool(_configured_audience()),
    ]
    return any(present) and not all(present)


def _load_key(pem: str) -> Ed25519PublicKey:
    normalised = pem.replace("\\n", "\n").strip()
    key = load_pem_public_key(normalised.encode("utf-8"))
    if not isinstance(key, Ed25519PublicKey):
        # `BOPEN-IDP-001` §12.4 mandates asymmetric signing so that a verifier cannot also be an
        # issuer. Accepting another key type here would let a symmetric secret be configured and
        # make this kernel able to mint the assertions it is meant to check.
        raise AssertionNotConfiguredError(
            f"{ENV_ASSERTION_PUBLIC_KEY} is not an Ed25519 public key"
        )
    return key


def verify_subject_assertion(token: str) -> SubjectClaims:
    """Verify an assertion and return what it vouches for, or raise.

    Binding is by **issuer and subject only**. `D-P35-012` forbids linking or routing trust by
    email equality, so no email claim is read here, and adding one would need that decision to
    say otherwise.
    """
    issuer = _configured_issuer()
    public_key_pem = _configured_public_key()
    audience = _configured_audience()
    if not (issuer and public_key_pem and audience):
        raise AssertionNotConfiguredError(
            f"{ENV_ASSERTION_ISSUER}, {ENV_ASSERTION_PUBLIC_KEY} and "
            f"{ENV_ASSERTION_AUDIENCE} must all be set to verify a subject assertion"
        )

    public_key = _load_key(public_key_pem)

    try:
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[_ALGORITHM],  # allowlist, never read from the token
            audience=audience,
            issuer=issuer,
            leeway=MAX_CLOCK_SKEW,
            options={
                "require": list(MANDATORY_CLAIMS),
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )
    except jwt.ExpiredSignatureError:
        raise AssertionVerificationError("assertion is not valid", reason="expired")
    except jwt.InvalidAudienceError:
        raise AssertionVerificationError("assertion is not valid", reason="audience_mismatch")
    except jwt.InvalidIssuerError:
        raise AssertionVerificationError("assertion is not valid", reason="issuer_mismatch")
    except jwt.InvalidSignatureError:
        raise AssertionVerificationError("assertion is not valid", reason="bad_signature")
    except jwt.InvalidTokenError:
        raise AssertionVerificationError("assertion is not valid", reason="invalid")

    missing = [claim for claim in MANDATORY_CLAIMS if claim not in claims]
    if missing:
        raise AssertionVerificationError(
            "assertion is not valid", reason=f"missing_claims:{','.join(missing)}"
        )

    # JWT claims are whatever JSON says they are. `sub` reaches identifier normalisation and then
    # a comparison, and a non-string would compare unequal to everything rather than fail —
    # which reads as "wrong principal" instead of "malformed assertion".
    #
    # HONEST NOTE, measured 2026-07-31: this loop is currently **unreachable**. PyJWT 2.x
    # type-checks `sub`, `iss` and `jti` itself and raises `InvalidTokenError` first, so a
    # non-string claim is refused above with reason `invalid` and never arrives here. It is kept
    # because the guarantee belongs to this module rather than to a dependency's current
    # behaviour, but it is recorded as redundant rather than presented as the thing protecting
    # us. The tests assert that such assertions are *refused*, not that this loop refused them —
    # asserting the layer would fail the day PyJWT changed, without anything being less safe.
    for claim in ("sub", "iss", "jti"):
        if not isinstance(claims[claim], str) or not claims[claim].strip():
            raise AssertionVerificationError(
                "assertion is not valid", reason=f"non_string_claim:{claim}"
            )

    return SubjectClaims(
        principal_id=claims["sub"].strip(),
        issuer=claims["iss"].strip(),
        assertion_id=claims["jti"].strip(),
    )
