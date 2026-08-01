"""
bOPEN Platform Kernel HTTP surface — Phase 1 vertical slice.

Work package: BOPEN-P35-001 (WP-P35-02, deliverable D-07)
Governing artifacts: BOPEN-ARCH-PLAN-001 section 3 (layer 3), BOPEN-AUTHZ-001,
                     BOPEN-TENANT-001, AGENTS.md section 3, section 8, section 9
Contracts: contracts/schemas/tenant-context.json, contracts/schemas/authorization-decision.json
Header contract: sdk/headers/HTTP_HEADER_SPEC.md

Scope is strictly the Phase 1 chain that `AGENTS.md` section 3 authorizes:

    register principal -> provision tenant -> create owner membership
    -> establish context -> authorize -> emit audit event

No Phase 2 (SSO, SCIM, invitation, delegation) or Phase 3 (capability, entitlement, metering)
endpoint is exposed here. Those belong to work packages that `DEC-P35-RUNTIME` has not yet
authorized, and adding them would resolve reserved decisions by code default.

This is the layer that changes what bOPEN is. Until it existed, a satellite product could only
`import kernel_core` and run the kernel inside its own process, which would give each product
its own copy of tenant and membership state and make the kernel a shared library rather than an
isolation boundary. Over HTTP there is one kernel and one tenant boundary.

--------------------------------------------------------------------------------------------
How the tenant is established, and why the client is not trusted
--------------------------------------------------------------------------------------------
`AGENTS.md` section 8: *"Never trust tenant IDs supplied by clients without server-side context
validation."*

There are two ways to establish the tenant, in strict precedence order.

**Preferred — `Authorization: Bearer <context access token>`.** The tenant comes from the
token's signed `tid` claim (`BOPEN-IDP-001` §12.2). `X-Tenant-ID` is not consulted at all on
this path; if present and contradictory, the request is refused rather than resolved in either
direction. The tenant identity is *attested by a signature* rather than asserted and then
checked, which is what lets a gateway or a satellite product verify the claim independently
against the published JWKS without calling back into the kernel.

**Legacy — `X-Context-ID` with `X-Tenant-ID`.** Here the header is an unauthenticated routing
hint: it selects which tenant's row-level security session to open, and nothing more. Authority
comes from the context row, read inside that tenant's own isolation policy. A client that lies
about `X-Tenant-ID` gains nothing, because the lookup runs in the tenant it claimed and the
context is not there.

Both paths re-read the stored context row. The token attests the tenant identity; it does not
attest that the context is still live. Skipping the read would leave a window equal to the token
lifetime in which a revoked context keeps working.

--------------------------------------------------------------------------------------------
Divergences from HTTP_HEADER_SPEC.md, recorded rather than silently resolved
--------------------------------------------------------------------------------------------
1. The spec describes `X-Tenant-ID` as "Explicit UUID" while its own example is
   `tnt_88a11b22-...`, which is not a UUID. Migration 001 declares these columns `UUID`, and
   `tnt_<uuid>` does not cast. This module accepts either form and normalises to the bare UUID.
   The contradiction is in the spec and needs a decision, not a silent choice.

2. The spec makes `Authorization: Bearer <JWT>` mandatory. `WP-P35-03` now issues and verifies
   it, but the header is accepted rather than required, because the `X-Context-ID` path predates
   it and removing that path would break any caller written against the earlier surface. What
   this module will never do is accept a bearer value it has not verified: an unsigned token, an
   unknown `kid`, or `alg=none` is refused, and no code path treats an unverified token as
   present-therefore-valid. Making the header mandatory is a one-line change once every caller
   has migrated, and is deliberately left as a decision rather than taken silently.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field

from kernel_core.evaluator import AuthorizationEvaluator
from kernel_core.types import (
    AuthorizationRequest,
    ContextPayload,
    DecisionResult,
)
from platform_kernel import repositories as repo
from platform_kernel import subject_assertion
from platform_kernel import tokens
from platform_kernel.db import DatabaseNotConfiguredError

API_VERSION = "1.0.0"

# --------------------------------------------------------------------------------------
# Unauthenticated identity assertions — the gap, and the guard over it
# --------------------------------------------------------------------------------------
# `POST /v1/contexts` mints a signed bearer token. It verifies that the membership exists in the
# named tenant, belongs to the named principal, and is active. It does **not** verify that the
# caller *is* that principal, because Phase 1 has no authentication mechanism to verify it with —
# no password, no IdP, no session. `BOPEN-P1-001` specifies the chain as register, provision,
# establish context, authorize; authentication arrives with the IdP bridge in Phase 2.
#
# So knowledge of three identifiers — tenant, principal, membership — is sufficient to obtain an
# `owner` token. Confirmed by execution 2026-07-30: a client with no prior state and no credential
# header received 201, a signed token with `roles: ["owner"]`, and an ALLOW on `/v1/authorize`.
#
# None of those identifiers is treated as a secret anywhere in this system. They are UUIDv4 and
# therefore unguessable, and no endpoint echoes them back, so there is no in-band harvest path
# today. That is a property of the current endpoint set, not a control.
#
# The danger is that this looks finished. There is a signed-token issuer, a JWKS endpoint,
# row-level security and an audit trail — a reader has every reason to think the surface is
# complete, and the missing half is invisible from outside.
#
# Hence the guard below rather than a comment alone. The kernel refuses to act on an identity
# claim it cannot check, unless the operator has affirmed that this deployment is not
# production. The same shape as `BOPEN_DB_NON_PRODUCTION` guarding the destructive rollback in
# `tools/db_bootstrap.py`: a deployment that forgets is refused, not silently open.
#
# It gates two endpoints, not one. `POST /v1/contexts` lets a caller assert "I am this
# principal, give me a token". `POST /v1/tenants` lets a caller assert "I am this principal,
# make me the owner of a new tenant" — and that second one was missed when the guard was first
# written, because the finding that prompted it named only context issuance. Following it up
# showed the endpoint has the same hole and reproduces over HTTP:
#
#     POST /v1/tenants  owner_principal_id = <a principal belonging to someone else>  -> 201
#
# A tenant is created naming a third party as its owner, with no step at which that party
# agrees. Phase 2's invitation engine exists precisely to model that consent — invited, then
# accepted — and this path goes around it. It also answers whether a principal identifier
# exists at all, 201 against 422, which is the same oracle as `POST /v1/principals`.
#
# The variable is named for the assertion rather than for either endpoint, so the next endpoint
# that trusts an unproven identity claim has an obvious place to attach.
ENV_ALLOW_UNAUTHENTICATED_IDENTITY = "BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"


def unauthenticated_identity_assertion_permitted() -> bool:
    return os.environ.get(ENV_ALLOW_UNAUTHENTICATED_IDENTITY, "").strip() == "1"


def _refuse_unauthenticated(action: str, consequence: str) -> None:
    """Refuse an unverifiable identity claim with 503.

    503 rather than 401: there is no credential the caller could have supplied that would change
    the answer, and 401 would imply there is one.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": f"{action} is disabled",
            "reason": (
                f"This kernel cannot authenticate the caller. Phase 1 has no authentication "
                f"mechanism, so {consequence}"
            ),
            "remediation": (
                f"Set {ENV_ALLOW_UNAUTHENTICATED_IDENTITY}=1 to affirm that this deployment is "
                f"not production. Do not set it on any deployment reachable by a party you "
                f"would not hand an owner token to."
            ),
            "resolved_by": "WP-P35-05 — the enterprise IdP bridge",
        },
    )

_PREFIXED_ID = re.compile(
    r"^(?:usr|tnt|mem|ctx|corr)_([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$"
)

principals = repo.PrincipalRepository()
tenants = repo.TenantRepository()
memberships = repo.MembershipRepository()
contexts = repo.ContextRepository()
audit = repo.AuditRepository()
resources = repo.TenantResourceRepository()
evaluator = AuthorizationEvaluator()


def normalise_id(value: str, field_name: str) -> str:
    """Accept either a bare UUID or the `xxx_<uuid>` form from HTTP_HEADER_SPEC.md.

    Rejects anything else rather than passing it to the database, so a malformed identifier
    produces a 400 naming the field instead of a 500 from a failed cast.
    """
    candidate = value.strip()
    match = _PREFIXED_ID.match(candidate)
    if match:
        candidate = match.group(1)
    try:
        return str(uuid.UUID(candidate))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a UUID, optionally prefixed (e.g. tnt_<uuid>)",
        )


# --------------------------------------------------------------------------------------
# Storage limits
# --------------------------------------------------------------------------------------
# Column widths in `audit_events` and `tenant_resources` (migrations 003 and 001). Every value
# the authorization path accepts is written into one of these columns, so a request carrying a
# longer one cannot be audited — and BOPEN-AUTHZ-001 requires that both allow and deny outcomes
# are audited, without exception.
#
# The path used to handle that in two different wrong ways, both found by security review on
# 2026-07-30 and both reproduced:
#
#   body     a 256-character resource_id was accepted, the decision was evaluated, and the
#            audit INSERT then raised StringDataRightTruncation. The caller got a 500 and the
#            decision that had already been made was recorded nowhere. An unauditable decision
#            is worse than a refused request, because the refusal leaves no unrecorded act.
#
#   header   X-Correlation-ID was silently truncated to 64 characters. The docstring on
#            `require_correlation_id` explains that the header is rejected rather than
#            generated when absent, so that an audit trail which cannot be joined to the
#            caller's own logs does not look as though it can be. Silent truncation produces
#            exactly the trail that reasoning exists to prevent.
#
# So the limits are declared here, enforced at the boundary, and asserted equal to the live
# column widths by the integration suite. Over-length input is now a 422 or 400 before any
# decision is evaluated: the request is refused, nothing happens, and nothing goes unrecorded.
AUDIT_CORRELATION_ID_MAX = 64    # audit_events.correlation_id
AUDIT_ACTION_MAX = 128           # audit_events.action
AUDIT_RESOURCE_TYPE_MAX = 128    # audit_events.resource_type
AUDIT_RESOURCE_ID_MAX = 255      # audit_events.resource_id
RESOURCE_NAME_MAX = 255          # tenant_resources.resource_name


# --------------------------------------------------------------------------------------
# Request and response models
# --------------------------------------------------------------------------------------


class RegisterPrincipalRequest(BaseModel):
    email: EmailStr
    type: str = Field(default="human", pattern="^(human|service|application|device|agent)$")


class PrincipalResponse(BaseModel):
    principal_id: str
    type: str
    email: str
    status: str


class ProvisionTenantRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    owner_principal_id: str


class ProvisionTenantResponse(BaseModel):
    tenant_id: str
    name: str
    status: str
    owner_membership_id: str


class EstablishContextRequest(BaseModel):
    principal_id: str
    membership_id: str


class TenantContextResponse(BaseModel):
    """Shaped to satisfy contracts/schemas/tenant-context.json.

    Two fields exist here because the frozen contract requires them and the in-memory
    `ContextPayload` dataclass does not provide them:

    - `context_id` is a bare UUID. The contract declares `format: uuid`, and the existing
      `establish_context` in `service.py` emits `ctx_<uuid>`, which does not satisfy it.
    - `expires_at` is required by the contract and absent from the dataclass entirely.

    Both are the same class of defect as the Phase 3 `RateLimitDecision` divergence: a frozen
    schema that nothing validated an instance against.
    """

    context_id: str
    principal_id: str
    tenant_id: str
    active_membership_id: str
    organization_id: Optional[str] = None
    workspace_id: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    issued_at: str
    expires_at: str


class EstablishContextResponse(BaseModel):
    """Envelope carrying the contract-shaped context and the credential for it.

    The token is a sibling of `context`, never a field inside it. `tenant-context.json` declares
    `additionalProperties: false`, so adding `access_token` to the payload would put the response
    permanently out of conformance with its own frozen contract — the exact class of defect this
    work package exists to remove, and one that would have been introduced while adding a
    security feature.

    Keeping them separate is also the better shape: `context` is the view a client may inspect,
    `access_token` is the credential it presents back. Merging them would force a client to parse
    a credential in order to read its own context.
    """

    context: TenantContextResponse
    access_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    token_status: str = "issued"


class AuthorizeRequest(BaseModel):
    action: str = Field(min_length=1, max_length=AUDIT_ACTION_MAX)
    resource_type: str = Field(min_length=1, max_length=AUDIT_RESOURCE_TYPE_MAX)
    resource_id: str = Field(max_length=AUDIT_RESOURCE_ID_MAX)


class AuthorizationDecisionResponse(BaseModel):
    decision_id: str
    principal_id: str
    tenant_id: str
    context_id: str
    action: str
    resource_type: str
    resource_id: str
    decision: str
    reason_code: str
    evaluated_at: str
    audit_event_id: str


# --------------------------------------------------------------------------------------
# Header dependencies
# --------------------------------------------------------------------------------------


class ResolvedContext(BaseModel):
    """A context that has been validated server-side, not merely asserted by the caller."""

    tenant_id: str
    context_id: str
    principal_id: str
    membership_id: str
    correlation_id: str
    roles: list[str]


def require_correlation_id(
    x_correlation_id: Annotated[Optional[str], Header(alias="X-Correlation-ID")] = None,
) -> str:
    """Mandatory per HTTP_HEADER_SPEC.md.

    Rejected rather than generated when absent. Generating one server-side would make an
    audit trail that cannot be joined to the caller's own logs look as though it can be.

    Over-length is rejected for the same reason, rather than truncated. This used to return
    `value[:64]`, so a longer identifier was accepted and a different one was recorded — which
    is the trail the paragraph above exists to prevent, arrived at by a different route. The
    caller who cannot join their logs to it is no better off for the request having succeeded.
    """
    if not x_correlation_id or not x_correlation_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Correlation-ID is mandatory (HTTP_HEADER_SPEC.md)",
        )

    correlation_id = x_correlation_id.strip()
    if len(correlation_id) > AUDIT_CORRELATION_ID_MAX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"X-Correlation-ID must be at most {AUDIT_CORRELATION_ID_MAX} characters; "
                f"the audit record stores it at that width and a truncated identifier would "
                f"not match the one you logged"
            ),
        )
    return correlation_id


def require_tenant_hint(
    x_tenant_id: Annotated[Optional[str], Header(alias="X-Tenant-ID")] = None,
) -> str:
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID is mandatory (HTTP_HEADER_SPEC.md)",
        )
    return normalise_id(x_tenant_id, "X-Tenant-ID")


ENV_LEGACY_CONTEXT_PROFILE = "BOPEN_LEGACY_CONTEXT_HEADER_PROFILE"
ENV_DEPLOYMENT_PROFILE = "BOPEN_ENV"


def legacy_context_header_profile_enabled() -> bool:
    """True only where the `X-Context-ID`-without-a-token path is still permitted.

    `AUTH-D1` (ACCEPTED 2026-08-01, option 3) makes protected endpoints bearer-only and
    `X-Context-ID` non-authoritative. Two independent engines reproduced why on 2026-07-31: a
    tenant member presenting another member's context identifier, with no token and no signature,
    obtained `200 ALLOW` and acted as that member — and the identifier is published to every
    member of the tenant by `GET /v1/audit-events`, so obtaining one required no attack.

    Three properties, each required by the disposition and each enforced here rather than
    documented:

    1. **Off by default.** An unset variable is a closed door.
    2. **Cannot be enabled on a production profile.** An escape hatch a production deployment can
       switch on is not test-only; it is a switch waiting for a bad day. `BOPEN_ENV=production`
       refuses regardless of the flag.
    3. **Separately named.** It does not share a variable with
       `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`, so turning one on cannot turn the other
       on by accident.

    This path is unsupported, is not a client contract, and is scheduled for removal.
    """
    if os.environ.get(ENV_LEGACY_CONTEXT_PROFILE, "").strip() != "1":
        return False
    profile = os.environ.get(ENV_DEPLOYMENT_PROFILE, "").strip().lower()
    return profile != "production"


def _authenticated_principal(assertion: Optional[str]) -> Optional[str]:
    """Return the principal an external authenticator vouched for, or None if none is configured.

    `WP-P35-05a`. The order of these checks is the security property, so it is spelled out:

    1. **A partial configuration refuses.** Some settings present and others missing is an
       operator error, and the safe reading of an error concerning authentication is that
       authentication was intended. Treating it as "no authenticator" would silently open the
       unauthenticated path on a deployment that was trying to close it.
    2. **A configured authenticator cannot be overridden.** If one is configured, an assertion is
       required, and `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION` is not consulted. A
       development escape that can disable a configured authenticator is not a boundary; it is a
       switch, and it would be the first thing set on the day something is hard to debug.
    3. **Only with no authenticator at all** does the caller fall through to the pre-existing
       flag-guarded path, which behaves exactly as before.

    Returns the normalised principal identifier, so the caller compares like with like.
    """
    if subject_assertion.configuration_is_partial():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "context issuance is disabled",
                "reason": (
                    "the subject-assertion authenticator is partially configured, so this "
                    "kernel cannot tell whether it is meant to authenticate callers"
                ),
                "remediation": (
                    f"set all of {subject_assertion.ENV_ASSERTION_ISSUER}, "
                    f"{subject_assertion.ENV_ASSERTION_PUBLIC_KEY} and "
                    f"{subject_assertion.ENV_ASSERTION_AUDIENCE}, or none of them"
                ),
            },
        )

    if not subject_assertion.authenticator_configured():
        return None

    if not assertion or not assertion.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Subject-Assertion is required by this deployment",
        )

    try:
        claims = subject_assertion.verify_subject_assertion(assertion.strip())
    except subject_assertion.AssertionVerificationError:
        # The reason belongs in an audit record, not in a response an attacker can use to refine
        # a forgery. Mirrors the context-token path above.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="assertion is not valid"
        )
    except subject_assertion.AssertionNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="kernel authentication is not configured",
        )

    return normalise_id(claims.principal_id, "assertion subject")


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def _load_validated_context(tenant_id: str, context_id: str) -> ResolvedContext:
    """Confirm the context row is still live and its membership still exists.

    Performed even when a signed token was presented. The token attests the tenant identity;
    it does not attest that the context is still valid, and a five-minute lifetime would
    otherwise leave a five-minute window in which a revoked context keeps working. Checking the
    row makes revocation immediate at the cost of one scoped read.
    """
    try:
        stored = contexts.get(tenant_id, context_id)
    except repo.ContextNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="context is not valid"
        )

    if not stored.is_live:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="context is not valid"
        )

    try:
        membership = memberships.get(stored.tenant_id, stored.membership_id)
    except repo.MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="context is not valid"
        )

    return ResolvedContext(
        tenant_id=stored.tenant_id,
        context_id=stored.id,
        principal_id=stored.principal_id,
        membership_id=stored.membership_id,
        correlation_id="",
        roles=[membership.role],
    )


def resolve_context(
    correlation_id: Annotated[str, Depends(require_correlation_id)],
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    x_tenant_id: Annotated[Optional[str], Header(alias="X-Tenant-ID")] = None,
    x_context_id: Annotated[Optional[str], Header(alias="X-Context-ID")] = None,
) -> ResolvedContext:
    """Turn the caller's claims into a server-validated context, or refuse.

    Two paths, in strict precedence order:

    **1. `Authorization: Bearer <context access token>` — preferred.** The tenant is taken from
    the token's signed `tid` claim. `X-Tenant-ID` is not consulted at all on this path, and if it
    is present and disagrees the request is refused rather than resolved in either direction: a
    caller sending contradictory tenant claims is either confused or probing, and neither
    deserves a best-effort interpretation.

    **2. `X-Context-ID` with `X-Tenant-ID` — legacy, retained for compatibility.** Here the
    header is an unauthenticated routing hint and the context row is the authority. A caller who
    lies about the tenant gains nothing, because the lookup runs in the tenant it claimed and the
    context is not there.

    Path 1 is stronger in a way path 2 cannot be: the tenant identity is *attested by a
    signature* rather than *asserted and then checked*. That difference matters once the gateway
    and satellite products sit between the caller and this kernel, because each hop can verify
    the claim independently against the published JWKS without querying the kernel.

    Every refusal returns 403 with an identical body. Distinguishing "no such context" from
    "belongs to another tenant" would confirm another tenant's context to someone who cannot
    read it.
    """
    raw_token = _bearer_token(authorization)

    if raw_token is not None:
        try:
            claims = tokens.verify_context_token(raw_token)
        except tokens.TokenNotConfiguredError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="kernel token verification is not configured",
            )
        except tokens.TokenVerificationError:
            # The specific reason (expired, bad signature, unknown key) is deliberately not
            # returned. It belongs in an audit record, not in a response that an attacker can
            # use to refine a forgery.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="token is not valid"
            )

        if x_tenant_id and x_tenant_id.strip():
            if normalise_id(x_tenant_id, "X-Tenant-ID") != claims.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="tenant claim conflict",
                )

        resolved = _load_validated_context(claims.tenant_id, claims.context_id)

        # The token attests membership and roles at issuance; the stored row is authoritative
        # now. A mismatch means the membership changed after the token was minted, so the token
        # is stale and must not be honoured.
        if resolved.membership_id != claims.membership_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="context is not valid"
            )

        return resolved.model_copy(update={"correlation_id": correlation_id})

    # AUTH-D1: a header cannot create authority. Reaching here means no bearer token was
    # presented — a token that failed verification raised above and never arrives, so there is no
    # fallback path from a rejected signature to header-asserted identity.
    if not legacy_context_header_profile_enabled():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="a signed context access token is required (HTTP_HEADER_SPEC v1.1)",
        )

    if not x_context_id or not x_context_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="an Authorization bearer token or X-Context-ID is required",
        )

    tenant_hint = require_tenant_hint(x_tenant_id)
    context_id = normalise_id(x_context_id, "X-Context-ID")
    resolved = _load_validated_context(tenant_hint, context_id)
    return resolved.model_copy(update={"correlation_id": correlation_id})


# --------------------------------------------------------------------------------------
# Application
# --------------------------------------------------------------------------------------

app = FastAPI(
    title="bOPEN Platform Kernel",
    version=API_VERSION,
    description=(
        "Phase 1 vertical slice of the bOPEN multi-tenant kernel. Tenant isolation is "
        "enforced by PostgreSQL row-level security, not by application filtering."
    ),
)


@app.exception_handler(DatabaseNotConfiguredError)
async def database_not_configured(request: Request, exc: DatabaseNotConfiguredError):
    from fastapi.responses import JSONResponse

    # 503 rather than 500: the service is correctly built and incorrectly deployed, and the
    # remediation text from the persistence layer is actionable.
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "kernel persistence is not configured", "remediation": str(exc)},
    )


@app.get("/health")
def health() -> dict:
    """Liveness only.

    Deliberately does not touch the database. A health probe that opens a connection turns a
    transient database blip into a rolling restart of every kernel replica.
    """
    return {"status": "ok", "version": API_VERSION}


@app.get("/readiness")
def readiness() -> dict:
    """Readiness, which does check persistence and reports honestly when it is unavailable."""
    from platform_kernel import db

    try:
        with db.system_session() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"persistence unavailable: {type(exc).__name__}",
        )
    return {"status": "ready", "version": API_VERSION}


@app.get("/.well-known/jwks.json")
def jwks() -> dict:
    """Publish the public verification keys (BOPEN-IDP-001 §12.4).

    Public key material only, and safe to serve unauthenticated — that is what makes it useful.
    The gateway and any satellite product can verify a context token's `tid` claim on their own
    against this document, without calling back into the kernel and without holding a shared
    secret. A shared secret would let every verifier also mint tokens, which is precisely why
    §12.4 mandates asymmetric keys.

    Returns an empty key set rather than an error when no key is configured, because that is the
    truthful answer to "which keys do you sign with": none. A consumer that receives an empty set
    correctly refuses every token, whereas a 500 invites a retry loop.
    """
    return tokens.registry().jwks()


@app.post(
    "/v1/principals",
    response_model=PrincipalResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_principal(
    body: RegisterPrincipalRequest,
    correlation_id: Annotated[str, Depends(require_correlation_id)],
) -> PrincipalResponse:
    """Register a principal.

    No tenant context is required or accepted: a principal exists before it belongs to any
    tenant. `BOPEN-TENANT-001` invariant 1 — a principal is broader than a human user, and
    invariant 4 — membership, not registration, is what binds a principal to a tenant.

    KNOWN AND NOT CLOSED: this endpoint is an account-existence oracle. Measured, 2026-07-31,
    over 150 paired requests — three independent channels answer "is this address registered?":

        status code   409 against 201
        body length   55 bytes against 125
        timing        median 2.5 ms faster when the address exists,
                      P(exists is faster) = 0.657 against 0.500 for indistinguishable

    The timing channel is structural rather than incidental: the existing-address path fails
    fast on the unique constraint instead of completing an insert. Any design that still
    resolves uniqueness synchronously and then decides leaks through it, however identical the
    response is made. What has to match is the work, not the answer.

    An earlier version of this note asserted that the oracle "cannot be closed at this layer",
    because a call returning the new identifier synchronously must say whether it created one.
    That was a design hypothesis stated as a finding, and it is corrected here rather than
    left standing. Research on 2026-07-31 could neither establish it nor refute it: no source
    proved the necessity, and no non-leaking synchronous counter-design survived verification
    either. It remains plausible and unproven, and this file should not have claimed otherwise.

    What the same research did establish, and what makes leaving this open defensible:

      - OWASP ASVS 5.0 is the only named standard extending enumeration resistance to
        registration, and it gates that to Level 3, its highest assurance tier. Below L3 it is
        a recommendation. OWASP WSTG treats the finding as contextual and tells testers to
        check the application's requirements before reporting it at all.
      - NIST SP 800-63B-4 has no normative requirement about enumeration in either direction
        and defers enrolment to SP 800-63A, which is likewise silent.
      - Google Cloud Identity Platform ships this exact oracle. With email enumeration
        protection fully enabled, sign-up still returns a distinguishable EMAIL_EXISTS; the
        documented answer is compensating controls, not a redesigned response.

    And what makes the recorded remedy less obviously right than it looked: an asynchronous,
    verification-gated registration relocates the oracle rather than closing it. The mail send
    is itself both a latency signal and an out-of-band mailbox signal — the address owner
    learns that someone tried to register it, which answers the same question from the other
    end. Google documents retaining that conditional-send behaviour deliberately.

    So this stays open as a decision, not as a blocked task. Accepting it is a defensible
    product position below ASVS L3 with compensating controls; closing it is a design problem
    nobody in the sources surveyed has solved without moving the leak. Either way it belongs
    with WP-P35-05, which is what gives this endpoint any authentication at all — see
    BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION.

    Returning 201 for a duplicate would hide the oracle from a reader of this file without
    closing it: the timing and body-length channels above both still answer the question.
    """
    try:
        created = principals.create(email=str(body.email), principal_type=body.type)
    except psycopg.errors.UniqueViolation:
        # Caught by type, not by searching the driver's message for "unique" or "duplicate".
        # That test passed only because of the wording psycopg happens to use today: a driver
        # upgrade or a non-English server locale would have turned every duplicate address into
        # an unhandled 500, and the endpoint would have looked fine until it was in production.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="a principal with that email already exists",
        )

    return PrincipalResponse(
        principal_id=created.id,
        type=created.type,
        email=created.email,
        status=created.status,
    )


@app.post(
    "/v1/tenants",
    response_model=ProvisionTenantResponse,
    status_code=status.HTTP_201_CREATED,
)
def provision_tenant(
    body: ProvisionTenantRequest,
    correlation_id: Annotated[str, Depends(require_correlation_id)],
) -> ProvisionTenantResponse:
    """Provision a tenant and its owner membership.

    The owner membership is created here rather than in a separate call because a tenant with
    no member is unreachable: no principal could establish a context in it, so nothing could
    ever administer it. Creating both keeps the boundary reachable by exactly one principal at
    the moment it exists.

    That design assumes the caller is the principal it names, and Phase 1 cannot check it. Naming
    someone else's principal as owner returns 201 — a tenant exists with a third party bound to
    it as owner, at no point having agreed. Phase 2's invitation engine models exactly that
    consent, invited then accepted, and this path goes around it. Confirmed over HTTP on
    2026-07-30 while following up the context-issuance finding, which had named only that
    endpoint.
    """
    if not unauthenticated_identity_assertion_permitted():
        _refuse_unauthenticated(
            "tenant provisioning",
            "provisioning a tenant here would bind a principal the caller has not proved it is "
            "to a new tenant as its owner, without that principal agreeing.",
        )

    owner_id = normalise_id(body.owner_principal_id, "owner_principal_id")

    try:
        principals.get(owner_id)
    except repo.PrincipalNotFoundError:
        raise HTTPException(
            status_code=422,
            detail="owner_principal_id does not reference an existing principal",
        )

    tenant = tenants.create(name=body.name)
    membership = memberships.create(
        tenant_id=tenant.id, principal_id=owner_id, role="owner", state="active"
    )

    audit.record(
        tenant_id=tenant.id,
        principal_id=owner_id,
        context_id=None,
        correlation_id=correlation_id,
        event_type="provisioning",
        action="tenant:provision",
        resource_type="tenant",
        resource_id=tenant.id,
    )

    return ProvisionTenantResponse(
        tenant_id=tenant.id,
        name=tenant.name,
        status=tenant.status,
        owner_membership_id=membership.id,
    )


@app.post(
    "/v1/contexts",
    response_model=EstablishContextResponse,
    status_code=status.HTTP_201_CREATED,
)
def establish_context(
    body: EstablishContextRequest,
    tenant_hint: Annotated[str, Depends(require_tenant_hint)],
    correlation_id: Annotated[str, Depends(require_correlation_id)],
    x_subject_assertion: Annotated[
        Optional[str], Header(alias="X-Subject-Assertion")
    ] = None,
) -> EstablishContextResponse:
    """Establish an active context for a principal in a tenant.

    **This endpoint issues a credential without authenticating the caller.** See the note above
    `ENV_ALLOW_UNAUTHENTICATED_IDENTITY` for why Phase 1 has nothing to authenticate with, and why
    the guard exists rather than a comment alone.

    The membership is read under the target tenant's isolation policy, so a caller naming a
    membership that belongs to a different tenant gets the same refusal as one naming a
    membership that does not exist.
    """
    asserted_principal = _authenticated_principal(x_subject_assertion)

    if asserted_principal is None and not unauthenticated_identity_assertion_permitted():
        _refuse_unauthenticated(
            "context issuance",
            "issuing a context here would grant an owner bearer token to anyone who knows a "
            "tenant, principal and membership identifier.",
        )

    principal_id = normalise_id(body.principal_id, "principal_id")

    if asserted_principal is not None and asserted_principal != principal_id:
        # The authenticator vouched for one principal and the body names another. This is the
        # whole point of the boundary: without it, a caller holding a valid assertion for
        # themselves could mint a context for anyone.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="assertion does not vouch for this principal",
        )
    membership_id = normalise_id(body.membership_id, "membership_id")

    try:
        membership = memberships.get(tenant_hint, membership_id)
    except repo.MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="membership is not valid for this tenant",
        )

    if membership.principal_id != principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="membership is not valid for this tenant",
        )

    if membership.state != "active":
        # Deny-by-default: only an active membership justifies a context. An invited,
        # suspended or revoked membership must not become a usable session.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"membership state '{membership.state}' cannot establish a context",
        )

    stored = contexts.establish(
        tenant_id=tenant_hint,
        principal_id=principal_id,
        membership_id=membership_id,
        correlation_id=correlation_id,
    )

    audit.record(
        tenant_id=tenant_hint,
        principal_id=principal_id,
        context_id=stored.id,
        correlation_id=correlation_id,
        event_type="context",
        action="context:establish",
        resource_type="active_context",
        resource_id=stored.id,
    )

    payload = TenantContextResponse(
        context_id=stored.id,
        principal_id=stored.principal_id,
        tenant_id=stored.tenant_id,
        active_membership_id=stored.membership_id,
        roles=[membership.role],
        scopes=[],
        issued_at=stored.established_at.isoformat(),
        expires_at=stored.expires_at.isoformat(),
    )

    # BOPEN-IDP-001 section 12.3 requires roles and scopes to be derived from authoritative
    # bOPEN state at issuance. They are: `membership` was read two steps above under this
    # tenant's own isolation policy, which is the only point at which the sub/tid/mid chain is
    # known to be real.
    try:
        access_token, claims = tokens.issue_context_token(
            principal_id=stored.principal_id,
            tenant_id=stored.tenant_id,
            membership_id=stored.membership_id,
            context_id=stored.id,
            roles=[membership.role],
            scopes=[],
        )
        token_status = "issued"
        expires_in = int((claims.expires_at - claims.issued_at).total_seconds())
    except tokens.TokenNotConfiguredError:
        # The context itself is valid and usable through the X-Context-ID path, so refusing the
        # whole request would break a working deployment over an unconfigured optional key.
        # `token_status` says plainly that no credential was minted rather than returning a
        # null field a client might read as "token not needed".
        access_token, expires_in, token_status = None, None, "unconfigured"

    return EstablishContextResponse(
        context=payload,
        access_token=access_token,
        expires_in=expires_in,
        token_status=token_status,
    )


@app.post("/v1/authorize", response_model=AuthorizationDecisionResponse)
def authorize(
    body: AuthorizeRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> AuthorizationDecisionResponse:
    """Evaluate an authorization request and record the decision.

    The decision comes from `kernel_core.evaluator.AuthorizationEvaluator`, the same
    deny-by-default engine the Phase 1 unit tests exercise. It is not reimplemented here:
    `AGENTS.md` section 9 requires decisions to use the approved decision interface, and a
    second copy of the rules would drift from the first.

    Both allow and deny outcomes are audited. Recording only denials would leave no evidence
    of who did read what, which is the half of an audit trail that matters after an incident.
    """
    membership = memberships.get(ctx.tenant_id, ctx.membership_id)

    payload = ContextPayload(
        context_id=ctx.context_id,
        principal_id=ctx.principal_id,
        tenant_id=ctx.tenant_id,
        active_membership_id=ctx.membership_id,
        roles=ctx.roles,
    )

    request = AuthorizationRequest(
        principal_id=ctx.principal_id,
        tenant_id=ctx.tenant_id,
        action=body.action,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        context=payload,
    )

    decision = evaluator.evaluate(request, active_membership_state=membership.state)

    audit_event_id = audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="authorization",
        action=body.action,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        decision="allow" if decision.decision == DecisionResult.ALLOW else "deny",
        reason_code=decision.reason_code,
    )

    return AuthorizationDecisionResponse(
        decision_id=decision.decision_id,
        principal_id=decision.principal_id,
        tenant_id=decision.tenant_id,
        context_id=ctx.context_id,
        action=decision.action,
        resource_type=decision.resource_type,
        resource_id=decision.resource_id,
        decision=decision.decision.value,
        reason_code=decision.reason_code,
        evaluated_at=decision.evaluated_at.isoformat(),
        audit_event_id=audit_event_id,
    )


@app.get("/v1/audit-events")
def list_audit_events(
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: int = 50,
) -> dict:
    """List audit events for the caller's tenant.

    No tenant filter appears in the query. The read runs inside the tenant's row-level
    security session, so the database decides what is visible. This endpoint is the clearest
    demonstration of that: a bug here cannot leak another tenant's audit trail, because the
    policy and not this function is what scopes the result.
    """
    return {
        "tenant_id": ctx.tenant_id,
        "events": audit.list_for_tenant(ctx.tenant_id, limit=min(limit, 500)),
    }


@app.post("/v1/resources", status_code=status.HTTP_201_CREATED)
def create_resource(
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    resource_name: Annotated[str, Query(min_length=1, max_length=RESOURCE_NAME_MAX)],
) -> dict:
    """Create a tenant-owned resource, used by the slice as an authorization target."""
    resource_id = resources.create(ctx.tenant_id, resource_name)
    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="domain",
        action="tenant_resource:create",
        resource_type="tenant_resource",
        resource_id=resource_id,
    )
    return {"resource_id": resource_id, "resource_name": resource_name}


@app.get("/v1/resources/{resource_id}")
def read_resource(
    resource_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> dict:
    """Read a tenant-owned resource, gated by an authorization decision.

    The decision is evaluated before the read and the read is scoped by the policy, so there
    are two independent barriers: authorization says whether the caller may, and isolation
    says which rows exist for them at all. Either alone would be a single point of failure.
    """
    membership = memberships.get(ctx.tenant_id, ctx.membership_id)

    payload = ContextPayload(
        context_id=ctx.context_id,
        principal_id=ctx.principal_id,
        tenant_id=ctx.tenant_id,
        active_membership_id=ctx.membership_id,
        roles=ctx.roles,
    )
    request = AuthorizationRequest(
        principal_id=ctx.principal_id,
        tenant_id=ctx.tenant_id,
        action="tenant_resource:read",
        resource_type="tenant_resource",
        resource_id=resource_id,
        context=payload,
    )
    decision = evaluator.evaluate(request, active_membership_state=membership.state)

    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="authorization",
        action="tenant_resource:read",
        resource_type="tenant_resource",
        resource_id=resource_id,
        decision="allow" if decision.decision == DecisionResult.ALLOW else "deny",
        reason_code=decision.reason_code,
    )

    if decision.decision != DecisionResult.ALLOW:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"decision": "DENY", "reason_code": decision.reason_code},
        )

    record = resources.read(ctx.tenant_id, normalise_id(resource_id, "resource_id"))
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="resource not found"
        )
    return record
