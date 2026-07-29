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

`X-Tenant-ID` is treated as an unauthenticated **routing hint**: it selects which tenant's
row-level security session to open, and nothing more. Authority comes from `X-Context-ID`,
which must resolve to a live, unrevoked context row *inside that tenant* — a read that is
itself performed under the tenant's isolation policy.

A client that lies about `X-Tenant-ID` therefore gains nothing: the context lookup runs in the
claimed tenant, the context is not there, and the request is refused. To pass, the caller must
present a context that genuinely lives in the tenant it claims.

`WP-P35-03` replaces the lookup with a signed token carrying a `tid` claim, at which point the
header becomes redundant rather than merely unauthoritative.

--------------------------------------------------------------------------------------------
Divergences from HTTP_HEADER_SPEC.md, recorded rather than silently resolved
--------------------------------------------------------------------------------------------
1. The spec describes `X-Tenant-ID` as "Explicit UUID" while its own example is
   `tnt_88a11b22-...`, which is not a UUID. Migration 001 declares these columns `UUID`, and
   `tnt_<uuid>` does not cast. This module accepts either form and normalises to the bare UUID.
   The contradiction is in the spec and needs a decision, not a silent choice.

2. The spec makes `Authorization: Bearer <JWT>` mandatory. No issuer exists yet —
   `WP-P35-03` builds it. This module therefore does **not** enforce it, and deliberately does
   not accept an unverified bearer token either. A code path that accepts any bearer value
   without verifying a signature is a hole that reads as a feature; leaving it absent is
   honest, whereas accepting it unverified would be worse than not having it at all.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from kernel_core.evaluator import AuthorizationEvaluator
from kernel_core.types import (
    AuthorizationRequest,
    ContextPayload,
    DecisionResult,
)
from platform_kernel import repositories as repo
from platform_kernel.db import DatabaseNotConfiguredError

API_VERSION = "1.0.0"

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


class AuthorizeRequest(BaseModel):
    action: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str


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
    """
    if not x_correlation_id or not x_correlation_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Correlation-ID is mandatory (HTTP_HEADER_SPEC.md)",
        )
    return x_correlation_id.strip()[:64]


def require_tenant_hint(
    x_tenant_id: Annotated[Optional[str], Header(alias="X-Tenant-ID")] = None,
) -> str:
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID is mandatory (HTTP_HEADER_SPEC.md)",
        )
    return normalise_id(x_tenant_id, "X-Tenant-ID")


def resolve_context(
    tenant_hint: Annotated[str, Depends(require_tenant_hint)],
    correlation_id: Annotated[str, Depends(require_correlation_id)],
    x_context_id: Annotated[Optional[str], Header(alias="X-Context-ID")] = None,
) -> ResolvedContext:
    """Turn the caller's claims into a server-validated context, or refuse.

    Every refusal below returns 403 with the same body. Distinguishing "no such context" from
    "that context belongs to another tenant" would confirm the existence of another tenant's
    context to a caller who cannot read it.
    """
    if not x_context_id or not x_context_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Context-ID is required for this operation",
        )

    context_id = normalise_id(x_context_id, "X-Context-ID")

    try:
        stored = contexts.get(tenant_hint, context_id)
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
        correlation_id=correlation_id,
        roles=[membership.role],
    )


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
    """
    try:
        created = principals.create(email=str(body.email), principal_type=body.type)
    except Exception as exc:
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="a principal with that email already exists",
            )
        raise

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
    """
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
    response_model=TenantContextResponse,
    status_code=status.HTTP_201_CREATED,
)
def establish_context(
    body: EstablishContextRequest,
    tenant_hint: Annotated[str, Depends(require_tenant_hint)],
    correlation_id: Annotated[str, Depends(require_correlation_id)],
) -> TenantContextResponse:
    """Establish an active context for a principal in a tenant.

    The membership is read under the target tenant's isolation policy, so a caller naming a
    membership that belongs to a different tenant gets the same refusal as one naming a
    membership that does not exist.
    """
    principal_id = normalise_id(body.principal_id, "principal_id")
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

    return TenantContextResponse(
        context_id=stored.id,
        principal_id=stored.principal_id,
        tenant_id=stored.tenant_id,
        active_membership_id=stored.membership_id,
        roles=[membership.role],
        scopes=[],
        issued_at=stored.established_at.isoformat(),
        expires_at=stored.expires_at.isoformat(),
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
    resource_name: str,
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
