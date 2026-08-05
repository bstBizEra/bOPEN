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
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from kernel_core.evaluator import AuthorizationEvaluator
from kernel_core.types import (
    AuthorizationRequest,
    ContextPayload,
    DecisionResult,
)
from decimal import Decimal

from platform_kernel import contact_point_repositories as contact_point_repo
from platform_kernel import location_repositories as location_repo
from platform_kernel import money
from platform_kernel import money_repositories as money_repo
from platform_kernel import party_repositories as party_repo
from platform_kernel import placement
from platform_kernel import repositories as repo
from platform_kernel import uom
from platform_kernel import uom_repositories as uom_repo
from platform_kernel import workflow_repositories as workflow_repo
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
parties = party_repo.PartyRepository()
contact_points = contact_point_repo.ContactPointRepository()
locations = location_repo.LocationRepository()
exchange_rates_repo = money_repo.ExchangeRateRepository()
workflows = workflow_repo.WorkflowRepository()
uom_units = uom_repo.CustomUnitRepository()
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


# MILE-4.1 — party graph (BOPEN-PARTY-001)


class CreatePartyRequest(BaseModel):
    party_type: str = Field(pattern="^(person|organization)$")
    display_name: str = Field(min_length=1, max_length=255)


class PartyResponse(BaseModel):
    party_id: str
    tenant_id: str
    party_type: str
    display_name: str
    status: str


class CreatePartyRelationshipRequest(BaseModel):
    from_party_id: str = Field(min_length=1, max_length=64)
    to_party_id: str = Field(min_length=1, max_length=64)
    relationship_type: str = Field(
        pattern="^(employs|supplies|bills|owns|member_of)$"
    )


class PartyRelationshipResponse(BaseModel):
    relationship_id: str
    tenant_id: str
    from_party_id: str
    to_party_id: str
    relationship_type: str


# MILE-4.2 — Party ContactPoint extension (BOPEN-PARTY-002, DEC-P4-ENTRY §10). The endpoint value is a
# plain string field; it is classified sensitive (CP-INV-06) and redacted from audit and logs — only
# the contact-point id and type are recorded there, never the value.


class CreateContactPointRequest(BaseModel):
    endpoint_type: str = Field(pattern="^(email|phone)$")
    endpoint_value: str = Field(min_length=1, max_length=320)
    purpose: str = Field(pattern="^(security_operational|transactional|billing|general)$")
    provenance: Optional[str] = Field(default=None, max_length=64)


class UpdateContactPointRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    endpoint_value: Optional[str] = Field(default=None, min_length=1, max_length=320)
    purpose: Optional[str] = Field(
        default=None, pattern="^(security_operational|transactional|billing|general)$"
    )


class ContactPointResponse(BaseModel):
    contact_point_id: str
    tenant_id: str
    party_id: str
    endpoint_type: str
    endpoint_value: str
    purpose: str
    verification_state: str
    verification_method: Optional[str]
    is_primary: bool
    revision: int


class VerifyContactPointRequest(BaseModel):
    # Administrative-assertion verify: the one governed, audited verify path in this slice. The
    # challenge ceremony (OTP/magic-link) is deferred (CP-D-05).
    method: str = Field(default="administrative_assertion", pattern="^administrative_assertion$")


class ResolveRecipientRequest(BaseModel):
    purpose: str = Field(pattern="^(security_operational|transactional|billing|general)$")
    channel: str = Field(min_length=1, max_length=32)


class RecipientSnapshotResponse(BaseModel):
    endpoint_type: str
    endpoint_value: str
    purpose: str
    party_id: str
    resolved_at: str


# MILE-4.2 — Location foundation (BOPEN-LOC-001, DEC-P4-ENTRY §11). Coordinate fields are named
# `longitude`/`latitude` explicitly — never a bare [a,b] pair — so a caller cannot silently transpose
# the axes. Coordinates cross as decimal strings (validated server-side); the accuracy radius crosses as
# {value, unit} decimal strings; precise coordinates are redacted from every audit record.


class CreateLocationRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    location_type: str = Field(pattern="^(site|building|depot|office|warehouse|other)$")


class UpdateLocationRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    code: Optional[str] = Field(default=None, min_length=1, max_length=64)


class TransitionLocationRequest(BaseModel):
    to_state: str = Field(pattern="^(proposed|active|inactive|retired)$")


class LocationResponse(BaseModel):
    location_id: str
    tenant_id: str
    code: str
    name: str
    location_type: str
    lifecycle_state: str
    current_address_version_id: Optional[str]
    current_geometry_observation_id: Optional[str]
    revision: int


class CreateAddressVersionRequest(BaseModel):
    country_code: str = Field(pattern="^[A-Za-z]{2}$")
    original_input: str = Field(min_length=1)
    premise: Optional[str] = Field(default=None, max_length=255)
    thoroughfare: Optional[str] = Field(default=None, max_length=255)
    locality: Optional[str] = Field(default=None, max_length=255)
    admin_area: Optional[str] = Field(default=None, max_length=255)
    postal_code: Optional[str] = Field(default=None, max_length=32)
    recipient: Optional[str] = Field(default=None, max_length=255)
    components: Optional[dict] = None
    rendered: Optional[str] = None
    language_tag: Optional[str] = Field(default=None, max_length=32)
    script_tag: Optional[str] = Field(default=None, max_length=32)
    template_profile: Optional[str] = Field(default=None, max_length=64)


class AddressVersionResponse(BaseModel):
    address_version_id: str
    location_id: str
    version_number: int
    country_code: str
    premise: Optional[str]
    thoroughfare: Optional[str]
    locality: Optional[str]
    admin_area: Optional[str]
    postal_code: Optional[str]
    recipient: Optional[str]
    original_input: str
    rendered: Optional[str]
    verification_state: str
    is_current: bool


class AccuracyRadius(BaseModel):
    value: str = Field(pattern=r"^\d+(\.\d+)?$")
    unit: str = Field(min_length=1, max_length=64)


class CreateGeometryObservationRequest(BaseModel):
    # Named fields, never a [a,b] pair: a transposition is unrepresentable at the boundary.
    longitude: str = Field(pattern=r"^-?\d+(\.\d+)?$")
    latitude: str = Field(pattern=r"^-?\d+(\.\d+)?$")
    crs: str = Field(default="OGC:CRS84", max_length=32)
    accuracy_radius: Optional[AccuracyRadius] = None
    capture_method: Optional[str] = Field(default=None, max_length=64)
    source: Optional[str] = Field(default=None, max_length=255)
    confidence: Optional[str] = Field(default=None, pattern=r"^\d+(\.\d+)?$")
    observed_at: Optional[str] = None


class AcceptGeometryObservationRequest(BaseModel):
    # Acceptance is a distinct authorized action; the actor is taken from the signed context, not here.
    note: Optional[str] = Field(default=None, max_length=255)


class RejectGeometryObservationRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)


class GeometryObservationResponse(BaseModel):
    observation_id: str
    location_id: str
    longitude: str
    latitude: str
    crs: str
    accuracy_radius_value: Optional[str]
    accuracy_radius_unit: Optional[str]
    capture_method: Optional[str]
    source: Optional[str]
    confidence: Optional[str]
    observed_at: Optional[str]
    acceptance_state: str
    accepted_by: Optional[str]


class CreateExternalIdentifierRequest(BaseModel):
    scheme: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=255)
    issuer: Optional[str] = Field(default=None, max_length=255)
    is_primary: bool = False
    provenance: Optional[str] = Field(default=None, max_length=64)


class ExternalIdentifierResponse(BaseModel):
    external_identifier_id: str
    location_id: str
    scheme: str
    value: str
    issuer: Optional[str]
    is_primary: bool


class CreateRelationshipRequest(BaseModel):
    from_location_id: str = Field(min_length=1)
    to_location_id: str = Field(min_length=1)
    relationship_type: str = Field(default="contains", pattern="^contains$")


class RelationshipResponse(BaseModel):
    relationship_id: str
    from_location_id: str
    to_location_id: str
    relationship_type: str


# MILE-4.2 — Money & Currency. The rate is a decimal STRING, never a JSON number, so a float can
# never enter the exact-decimal money arithmetic through the request body.


class SetExchangeRateRequest(BaseModel):
    from_currency: str = Field(pattern="^[A-Z]{3}$")
    to_currency: str = Field(pattern="^[A-Z]{3}$")
    rate: str = Field(pattern=r"^\d+(\.\d+)?$")


class ExchangeRateResponse(BaseModel):
    tenant_id: str
    from_currency: str
    to_currency: str
    rate: str


class ConvertMoneyRequest(BaseModel):
    amount_minor: int
    from_currency: str = Field(pattern="^[A-Z]{3}$")
    to_currency: str = Field(pattern="^[A-Z]{3}$")


class MoneyResponse(BaseModel):
    amount_minor: int
    currency: str


# MILE-4.2 — Workflow State Engine. A definition names states and the transitions allowed between
# them; an instance runs one process; a transition moves it along an allowed edge only.


class CreateWorkflowDefinitionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    initial_state: str = Field(min_length=1, max_length=64)
    states: list[str] = Field(min_length=1)
    # Each transition is a [from, to] pair. Validated against `states` in the repository.
    transitions: list[list[str]] = Field(default_factory=list)


class WorkflowDefinitionResponse(BaseModel):
    definition_id: str
    tenant_id: str
    name: str
    initial_state: str
    states: list[str]
    transitions: list[list[str]]


class StartWorkflowInstanceRequest(BaseModel):
    definition_id: str = Field(min_length=1, max_length=64)
    subject_ref: str = Field(min_length=1, max_length=255)


class WorkflowInstanceResponse(BaseModel):
    instance_id: str
    tenant_id: str
    definition_id: str
    current_state: str
    subject_ref: str


class ApplyTransitionRequest(BaseModel):
    to_state: str = Field(min_length=1, max_length=64)


class WorkflowTransitionResponse(BaseModel):
    transition_id: str
    instance_id: str
    from_state: str
    to_state: str
    actor_principal_id: Optional[str] = None


# MILE-4.2 — UOM. The factor and the magnitude cross the boundary as decimal STRINGS, never JSON
# numbers, so a float can never enter the exact-decimal quantity arithmetic through the request body.


class CreateCustomUnitRequest(BaseModel):
    unit_code: str = Field(min_length=1, max_length=64)
    dimension: str = Field(pattern="^(mass|length|area|volume|time|count)$")
    factor_to_base: str = Field(pattern=r"^\d+(\.\d+)?$")
    display_name: str = Field(min_length=1, max_length=255)


class UpdateCustomUnitRequest(BaseModel):
    factor_to_base: str = Field(pattern=r"^\d+(\.\d+)?$")
    display_name: str = Field(min_length=1, max_length=255)


class CustomUnitResponse(BaseModel):
    tenant_id: str
    unit_code: str
    dimension: str
    factor_to_base: str
    display_name: str


class ConvertQuantityRequest(BaseModel):
    magnitude: str = Field(pattern=r"^-?\d+(\.\d+)?$")
    from_unit: str = Field(min_length=1, max_length=64)
    to_unit: str = Field(min_length=1, max_length=64)


class QuantityResponse(BaseModel):
    magnitude: str
    unit: str


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

    # Status-code oracle, found 2026-07-31 and confirmed still reproducible by Codex 2026-08-01.
    #
    # `normalise_id` raises 400 with a message naming the field. A bad signature raises 401 with
    # an opaque body. So the pair distinguished "your assertion verified but its subject is not
    # UUID-shaped" from "your assertion did not verify" — which tells a forger their signature
    # was accepted, the single most useful bit of feedback they could receive.
    #
    # `P35-05a-10` claims the refusal reason is not disclosed. It was, through the status code
    # rather than the body.
    try:
        return normalise_id(claims.principal_id, "assertion subject")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="assertion is not valid"
        )


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

    The freeze is enforced here because both the bearer and the legacy paths pass through this
    function, and it is below the migrate tool (which uses `tenant_session` directly, not this HTTP
    path). A tenant whose data is being moved to a dedicated database is `migrating`, and its
    requests are refused with a retriable 503 so no write lands in the source database after the
    migration's snapshot (PLAN-P35-06-TRIAL-TO-PAID §2).
    """
    if placement.tenant_placement_state(tenant_id) == "migrating":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "tenant is migrating",
                "reason": (
                    "this tenant's data is being moved to a dedicated database; the request was "
                    "refused rather than written to the database being migrated away from"
                ),
                "retriable": True,
            },
        )
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

    D-D3-002 Option B (operator-disposed 2026-08-02, DEC-P35-AUTH-D3-DOCKET): principal creation is
    provisioned out of band (operator/SCIM), not through a public self-service endpoint. Option B
    adds NO enrollment credential, so — unlike tenant provisioning, which names an already-existing
    principal an assertion can vouch for — there is no assertion that opens this. The refusal is
    therefore 503, not 401: no credential the caller could supply would change it. When an
    authenticator is configured the endpoint is closed and the development flag does not reopen it,
    the same rule `_authenticated_principal` applies to context issuance and tenant provisioning.
    When none is configured, the pre-existing non-production affirmation flag still gates it, so
    local and test provisioning is unchanged.
    """
    if subject_assertion.configuration_is_partial() or subject_assertion.authenticator_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "principal registration is disabled",
                "reason": (
                    "an authenticator is configured, so principals are provisioned out of band "
                    "(operator/SCIM) rather than through this public endpoint"
                ),
                "remediation": (
                    "provision principals through the out-of-band operator path; the development "
                    "flag does not reopen this endpoint against a configured authenticator"
                ),
                "resolved_by": "DEC-P35-AUTH-D3-DOCKET D-D3-002 Option B",
            },
        )
    if not unauthenticated_identity_assertion_permitted():
        _refuse_unauthenticated(
            "principal registration",
            "creating a principal here would let an unauthenticated caller populate the identity "
            "namespace and reserve email addresses a named person can never reclaim",
        )
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
    x_subject_assertion: Annotated[
        Optional[str], Header(alias="X-Subject-Assertion")
    ] = None,
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
    # AUTH-D3 Row 1 (a), operator-approved 2026-08-02 (DEC-P35-AUTH-D3-DOCKET). Closes the tenant
    # squatting reproduced by auth-d3-exposure-measurement: an unauthenticated caller binding
    # another principal as owner.
    #
    # `owner_principal_id` must already exist (checked below), so an assertion vouching for that
    # principal authenticates the call with no bootstrap problem — the principal is not being
    # created here. This is exactly the establish_context treatment under AUTH-D1, reused.
    asserted_principal = _authenticated_principal(x_subject_assertion)

    if asserted_principal is None and not unauthenticated_identity_assertion_permitted():
        _refuse_unauthenticated(
            "tenant provisioning",
            "provisioning a tenant here would bind a principal the caller has not proved it is "
            "to a new tenant as its owner, without that principal agreeing.",
        )

    owner_id = normalise_id(body.owner_principal_id, "owner_principal_id")

    if asserted_principal is not None and asserted_principal != owner_id:
        # The authenticator vouched for one principal and the body names another as owner. Without
        # this, a caller holding a valid assertion for themselves could bind anyone as owner —
        # which is the squatting the exposure measured.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="assertion does not vouch for the named owner principal",
        )

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


# MILE-4.1 — party graph endpoints (BOPEN-PARTY-001). Bearer-gated: every one runs behind
# resolve_context, so the tenant comes from the signed context, never from a header, and the party
# is created and read under that tenant's row-level-security scope. Isolation is the database's, not
# these handlers'.


@app.post("/v1/parties", response_model=PartyResponse, status_code=status.HTTP_201_CREATED)
def create_party(
    body: CreatePartyRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> PartyResponse:
    try:
        created = parties.create(ctx.tenant_id, body.party_type, body.display_name)
    except party_repo.PartyRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="domain",
        action="party:create",
        resource_type="party",
        resource_id=created.id,
    )
    return PartyResponse(
        party_id=created.id,
        tenant_id=created.tenant_id,
        party_type=created.party_type,
        display_name=created.display_name,
        status=created.status,
    )


@app.get("/v1/parties", response_model=list[PartyResponse])
def list_parties(
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PartyResponse]:
    return [
        PartyResponse(
            party_id=p.id,
            tenant_id=p.tenant_id,
            party_type=p.party_type,
            display_name=p.display_name,
            status=p.status,
        )
        for p in parties.list(ctx.tenant_id, limit=limit)
    ]


@app.get("/v1/parties/{party_id}", response_model=PartyResponse)
def read_party(
    party_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> PartyResponse:
    try:
        p = parties.get(ctx.tenant_id, normalise_id(party_id, "party_id"))
    except party_repo.PartyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="party not found"
        )
    return PartyResponse(
        party_id=p.id,
        tenant_id=p.tenant_id,
        party_type=p.party_type,
        display_name=p.display_name,
        status=p.status,
    )


@app.post(
    "/v1/party-relationships",
    response_model=PartyRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_party_relationship(
    body: CreatePartyRelationshipRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> PartyRelationshipResponse:
    try:
        rel = parties.create_relationship(
            ctx.tenant_id,
            normalise_id(body.from_party_id, "from_party_id"),
            normalise_id(body.to_party_id, "to_party_id"),
            body.relationship_type,
        )
    except party_repo.PartyRelationshipError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="domain",
        action="party_relationship:create",
        resource_type="party_relationship",
        resource_id=rel.id,
    )
    return PartyRelationshipResponse(
        relationship_id=rel.id,
        tenant_id=rel.tenant_id,
        from_party_id=rel.from_party_id,
        to_party_id=rel.to_party_id,
        relationship_type=rel.relationship_type,
    )


# MILE-4.2 — Money & Currency endpoints. Bearer-gated: a tenant's exchange rates are private to it,
# and a conversion uses that tenant's own rate. Money never becomes a float — the rate is exact
# decimal end to end and the amount is integer minor units.


def _require_known_currency(code: str) -> None:
    try:
        money.minor_units(code)
    except money.UnknownCurrencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@app.put("/v1/exchange-rates", response_model=ExchangeRateResponse)
def set_exchange_rate(
    body: SetExchangeRateRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ExchangeRateResponse:
    _require_known_currency(body.from_currency)
    _require_known_currency(body.to_currency)
    try:
        stored = exchange_rates_repo.set(
            ctx.tenant_id, body.from_currency, body.to_currency, Decimal(body.rate)
        )
    except money_repo.ExchangeRateError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return ExchangeRateResponse(
        tenant_id=stored.tenant_id,
        from_currency=stored.from_currency,
        to_currency=stored.to_currency,
        rate=str(stored.rate),
    )


@app.get(
    "/v1/exchange-rates/{from_currency}/{to_currency}",
    response_model=ExchangeRateResponse,
)
def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ExchangeRateResponse:
    try:
        stored = exchange_rates_repo.get(ctx.tenant_id, from_currency, to_currency)
    except money_repo.ExchangeRateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no rate set for this pair"
        )
    return ExchangeRateResponse(
        tenant_id=stored.tenant_id,
        from_currency=stored.from_currency,
        to_currency=stored.to_currency,
        rate=str(stored.rate),
    )


@app.post("/v1/money/convert", response_model=MoneyResponse)
def convert_money(
    body: ConvertMoneyRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> MoneyResponse:
    """Convert an integer-minor-units amount using this tenant's own rate, exactly."""
    try:
        amount = money.Money(body.amount_minor, body.from_currency)
        money.minor_units(body.to_currency)
    except money.MoneyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    try:
        rate = exchange_rates_repo.get(ctx.tenant_id, body.from_currency, body.to_currency).rate
    except money_repo.ExchangeRateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no rate set for this pair"
        )
    converted = amount.convert(rate, body.to_currency)
    return MoneyResponse(amount_minor=converted.amount_minor, currency=converted.currency)


# MILE-4.2 — Workflow State Engine endpoints. Bearer-gated: definitions, instances and history are
# private to the tenant, read and written under its own row-level-security scope. A transition is
# refused unless the definition allows it, and every applied transition is audited — the lifecycle
# event the definition's authorization (DEC-P4-ENTRY §8) requires.


@app.post(
    "/v1/workflow-definitions",
    response_model=WorkflowDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow_definition(
    body: CreateWorkflowDefinitionRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> WorkflowDefinitionResponse:
    try:
        created = workflows.create_definition(
            ctx.tenant_id, body.name, body.initial_state, body.states, body.transitions
        )
    except workflow_repo.WorkflowDefinitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="domain",
        action="workflow_definition:create",
        resource_type="workflow_definition",
        resource_id=created.id,
    )
    return WorkflowDefinitionResponse(
        definition_id=created.id,
        tenant_id=created.tenant_id,
        name=created.name,
        initial_state=created.initial_state,
        states=list(created.states),
        transitions=[list(pair) for pair in created.transitions],
    )


@app.get(
    "/v1/workflow-definitions/{definition_id}",
    response_model=WorkflowDefinitionResponse,
)
def read_workflow_definition(
    definition_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> WorkflowDefinitionResponse:
    try:
        d = workflows.get_definition(ctx.tenant_id, normalise_id(definition_id, "definition_id"))
    except workflow_repo.WorkflowDefinitionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workflow definition not found"
        )
    return WorkflowDefinitionResponse(
        definition_id=d.id,
        tenant_id=d.tenant_id,
        name=d.name,
        initial_state=d.initial_state,
        states=list(d.states),
        transitions=[list(pair) for pair in d.transitions],
    )


@app.post(
    "/v1/workflow-instances",
    response_model=WorkflowInstanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_workflow_instance(
    body: StartWorkflowInstanceRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> WorkflowInstanceResponse:
    try:
        started = workflows.start_instance(
            ctx.tenant_id, normalise_id(body.definition_id, "definition_id"), body.subject_ref
        )
    except workflow_repo.WorkflowDefinitionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workflow definition not found"
        )
    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="domain",
        action="workflow_instance:start",
        resource_type="workflow_instance",
        resource_id=started.id,
    )
    return WorkflowInstanceResponse(
        instance_id=started.id,
        tenant_id=started.tenant_id,
        definition_id=started.definition_id,
        current_state=started.current_state,
        subject_ref=started.subject_ref,
    )


@app.get(
    "/v1/workflow-instances/{instance_id}",
    response_model=WorkflowInstanceResponse,
)
def read_workflow_instance(
    instance_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> WorkflowInstanceResponse:
    try:
        i = workflows.get_instance(ctx.tenant_id, normalise_id(instance_id, "instance_id"))
    except workflow_repo.WorkflowInstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workflow instance not found"
        )
    return WorkflowInstanceResponse(
        instance_id=i.id,
        tenant_id=i.tenant_id,
        definition_id=i.definition_id,
        current_state=i.current_state,
        subject_ref=i.subject_ref,
    )


@app.post(
    "/v1/workflow-instances/{instance_id}/transitions",
    response_model=WorkflowInstanceResponse,
)
def apply_workflow_transition(
    instance_id: str,
    body: ApplyTransitionRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> WorkflowInstanceResponse:
    """Move an instance along an allowed edge. A move the definition does not list is a 422, and the
    instance does not change. The applied transition is audited as the lifecycle event."""
    resolved_instance = normalise_id(instance_id, "instance_id")
    try:
        updated = workflows.apply_transition(
            ctx.tenant_id, resolved_instance, body.to_state, actor_principal_id=ctx.principal_id
        )
    except workflow_repo.WorkflowInstanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="workflow instance not found"
        )
    except workflow_repo.WorkflowTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    audit.record(
        tenant_id=ctx.tenant_id,
        principal_id=ctx.principal_id,
        context_id=ctx.context_id,
        correlation_id=ctx.correlation_id,
        event_type="domain",
        action="workflow_instance:transition",
        resource_type="workflow_instance",
        resource_id=updated.id,
    )
    return WorkflowInstanceResponse(
        instance_id=updated.id,
        tenant_id=updated.tenant_id,
        definition_id=updated.definition_id,
        current_state=updated.current_state,
        subject_ref=updated.subject_ref,
    )


@app.get(
    "/v1/workflow-instances/{instance_id}/history",
    response_model=list[WorkflowTransitionResponse],
)
def list_workflow_history(
    instance_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[WorkflowTransitionResponse]:
    resolved_instance = normalise_id(instance_id, "instance_id")
    return [
        WorkflowTransitionResponse(
            transition_id=t.id,
            instance_id=t.instance_id,
            from_state=t.from_state,
            to_state=t.to_state,
            actor_principal_id=t.actor_principal_id,
        )
        for t in workflows.list_history(ctx.tenant_id, resolved_instance, limit=limit)
    ]


# MILE-4.2 — UOM endpoints. Bearer-gated. Standard units are a code constant; custom units are the
# tenant's own, with full CRUD. Conversion uses the tenant's registry (standard + its custom units)
# and is dimension-safe — kg + m is refused, temperature conversion is refused, magnitudes are exact
# decimal strings so a float never enters the arithmetic.


def _decimal_str(value: Decimal) -> str:
    """Render a Decimal without trailing zeros or scientific notation. The NUMERIC(38,18) factor
    column reads back as e.g. 48.000000000000000000, and a conversion carries that scale; the exact
    value is unchanged, so the wire form is normalised to the shortest faithful decimal ('48', '4',
    '0.0508')."""
    return format(value.normalize(), "f")


def _unit_response(u: uom_repo.StoredCustomUnit) -> CustomUnitResponse:
    return CustomUnitResponse(
        tenant_id=u.tenant_id,
        unit_code=u.unit_code,
        dimension=u.dimension,
        factor_to_base=_decimal_str(u.factor_to_base),
        display_name=u.display_name,
    )


@app.get("/v1/uom/standard-units")
def list_standard_units(
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> dict:
    """The standard unit registry (reference data), grouped by dimension."""
    grouped: dict[str, list[str]] = {}
    for code, definition in sorted(uom.STANDARD_UNITS.items()):
        grouped.setdefault(definition.dimension, []).append(code)
    return grouped


@app.post("/v1/uom/units", response_model=CustomUnitResponse, status_code=status.HTTP_201_CREATED)
def create_custom_unit(
    body: CreateCustomUnitRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> CustomUnitResponse:
    try:
        created = uom_units.create(
            ctx.tenant_id, body.unit_code, body.dimension,
            Decimal(body.factor_to_base), body.display_name,
        )
    except uom_repo.CustomUnitConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except uom_repo.CustomUnitError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="uom_custom_unit:create",
        resource_type="uom_custom_unit", resource_id=created.unit_code,
    )
    return _unit_response(created)


@app.get("/v1/uom/units", response_model=list[CustomUnitResponse])
def list_custom_units(
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> list[CustomUnitResponse]:
    return [_unit_response(u) for u in uom_units.list(ctx.tenant_id)]


@app.get("/v1/uom/units/{unit_code}", response_model=CustomUnitResponse)
def read_custom_unit(
    unit_code: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> CustomUnitResponse:
    try:
        return _unit_response(uom_units.get(ctx.tenant_id, unit_code))
    except uom_repo.CustomUnitNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="custom unit not found")


@app.put("/v1/uom/units/{unit_code}", response_model=CustomUnitResponse)
def update_custom_unit(
    unit_code: str,
    body: UpdateCustomUnitRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> CustomUnitResponse:
    try:
        updated = uom_units.update(
            ctx.tenant_id, unit_code, Decimal(body.factor_to_base), body.display_name
        )
    except uom_repo.CustomUnitNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="custom unit not found")
    except uom_repo.CustomUnitError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="uom_custom_unit:update",
        resource_type="uom_custom_unit", resource_id=unit_code,
    )
    return _unit_response(updated)


@app.delete("/v1/uom/units/{unit_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_unit(
    unit_code: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> Response:
    try:
        uom_units.delete(ctx.tenant_id, unit_code)
    except uom_repo.CustomUnitNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="custom unit not found")
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="uom_custom_unit:delete",
        resource_type="uom_custom_unit", resource_id=unit_code,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/v1/uom/convert", response_model=QuantityResponse)
def convert_quantity(
    body: ConvertQuantityRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> QuantityResponse:
    """Convert a quantity using this tenant's registry (standard units + its custom units). Refuses a
    cross-dimension conversion, an unknown unit, and a temperature (affine) conversion."""
    registry = uom_units.registry_for(ctx.tenant_id)
    try:
        result = registry.convert(uom.Quantity(body.magnitude, body.from_unit), body.to_unit)
    except uom.UomError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return QuantityResponse(magnitude=_decimal_str(result.magnitude), unit=result.unit)


# MILE-4.2 — Party ContactPoint endpoints (BOPEN-PARTY-002, DEC-P4-ENTRY §10). Bearer-gated: every one
# runs behind resolve_context, so the tenant comes from the signed context and the contact point is
# created and read under that tenant's row-level-security scope. A contact point attaches to a Party of
# THIS tenant only — the composite FK refuses a cross-tenant attachment at the database. The endpoint
# value is redacted from every audit record (CP-INV-06): the audit carries the contact-point id and
# type, never the value. `resolve` is the NotificationRecipientResolver keystone and never reads
# principals.email.


def _contact_point_response(cp: contact_point_repo.StoredContactPoint) -> ContactPointResponse:
    return ContactPointResponse(
        contact_point_id=cp.id,
        tenant_id=cp.tenant_id,
        party_id=cp.party_id,
        endpoint_type=cp.endpoint_type,
        endpoint_value=cp.endpoint_value,
        purpose=cp.purpose,
        verification_state=cp.verification_state,
        verification_method=cp.verification_method,
        is_primary=cp.is_primary,
        revision=cp.revision,
    )


@app.post(
    "/v1/parties/{party_id}/contact-points",
    response_model=ContactPointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contact_point(
    party_id: str,
    body: CreateContactPointRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ContactPointResponse:
    try:
        created = contact_points.create(
            ctx.tenant_id,
            normalise_id(party_id, "party_id"),
            body.endpoint_type,
            body.endpoint_value,
            body.purpose,
            body.provenance,
        )
    except contact_point_repo.ContactPointPartyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="party not found")
    except contact_point_repo.ContactPointConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except contact_point_repo.ContactPointValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="party_contact_point:create",
        resource_type="party_contact_point", resource_id=created.id,
    )
    return _contact_point_response(created)


@app.get(
    "/v1/parties/{party_id}/contact-points",
    response_model=list[ContactPointResponse],
)
def list_contact_points(
    party_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ContactPointResponse]:
    return [
        _contact_point_response(cp)
        for cp in contact_points.list(ctx.tenant_id, normalise_id(party_id, "party_id"), limit=limit)
    ]


@app.get(
    "/v1/parties/{party_id}/contact-points/{cp_id}",
    response_model=ContactPointResponse,
)
def read_contact_point(
    party_id: str,
    cp_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ContactPointResponse:
    try:
        cp = contact_points.get(ctx.tenant_id, normalise_id(cp_id, "cp_id"))
    except contact_point_repo.ContactPointNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact point not found")
    return _contact_point_response(cp)


@app.put(
    "/v1/parties/{party_id}/contact-points/{cp_id}",
    response_model=ContactPointResponse,
)
def update_contact_point(
    party_id: str,
    cp_id: str,
    body: UpdateContactPointRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ContactPointResponse:
    try:
        updated = contact_points.update(
            ctx.tenant_id,
            normalise_id(cp_id, "cp_id"),
            body.expected_revision,
            endpoint_value=body.endpoint_value,
            purpose=body.purpose,
        )
    except contact_point_repo.ContactPointNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact point not found")
    except contact_point_repo.ContactPointConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except contact_point_repo.ContactPointValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="party_contact_point:update",
        resource_type="party_contact_point", resource_id=cp_id,
    )
    return _contact_point_response(updated)


@app.delete(
    "/v1/parties/{party_id}/contact-points/{cp_id}",
    response_model=ContactPointResponse,
)
def retire_contact_point(
    party_id: str,
    cp_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ContactPointResponse:
    """Retire (tombstone), not hard delete — a verified/referenced endpoint keeps its row and its
    append-only verification history (CP-D-03)."""
    try:
        retired = contact_points.retire(ctx.tenant_id, normalise_id(cp_id, "cp_id"))
    except contact_point_repo.ContactPointNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact point not found")
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="party_contact_point:retire",
        resource_type="party_contact_point", resource_id=cp_id,
    )
    return _contact_point_response(retired)


@app.post(
    "/v1/parties/{party_id}/contact-points/{cp_id}/verify",
    response_model=ContactPointResponse,
)
def verify_contact_point(
    party_id: str,
    cp_id: str,
    body: VerifyContactPointRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ContactPointResponse:
    """Administrative-assertion verify — the one governed, audited verify path in this slice. Sets the
    contact point verified and records an append-only verification event in the same transaction. The
    challenge ceremony is deferred (CP-D-05)."""
    try:
        verified = contact_points.verify_by_assertion(
            ctx.tenant_id, normalise_id(cp_id, "cp_id"), ctx.principal_id
        )
    except contact_point_repo.ContactPointNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact point not found")
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="party_contact_point:verify",
        resource_type="party_contact_point", resource_id=cp_id,
    )
    return _contact_point_response(verified)


@app.post(
    "/v1/parties/{party_id}/contact-points/{cp_id}/set-primary",
    response_model=ContactPointResponse,
)
def set_primary_contact_point(
    party_id: str,
    cp_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ContactPointResponse:
    try:
        primary = contact_points.set_primary(ctx.tenant_id, normalise_id(cp_id, "cp_id"))
    except contact_point_repo.ContactPointNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="contact point not found")
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain",
        action="party_contact_point:set_primary",
        resource_type="party_contact_point", resource_id=cp_id,
    )
    return _contact_point_response(primary)


@app.post(
    "/v1/parties/{party_id}/resolve-recipient",
    response_model=RecipientSnapshotResponse,
)
def resolve_recipient(
    party_id: str,
    body: ResolveRecipientRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> RecipientSnapshotResponse:
    """The NotificationRecipientResolver keystone over HTTP (CP-INV-03). Resolves a business recipient
    (party + purpose + channel) to a verified, purpose-authorized, effective destination for a Party of
    the caller's tenant. Never principals.email; never a cross-tenant, unverified, wrong-purpose, or
    wrong-channel endpoint. A failure is a single uniform 422 that does not reveal which rung failed
    (CP-INV-05)."""
    try:
        snapshot = contact_points.resolve(
            ctx.tenant_id, normalise_id(party_id, "party_id"), body.purpose, body.channel
        )
    except contact_point_repo.RecipientUnresolved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="no usable destination for this recipient",
        )
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="party_contact_point:resolve",
        resource_type="party", resource_id=snapshot.party_id,
    )
    return RecipientSnapshotResponse(
        endpoint_type=snapshot.endpoint_type,
        endpoint_value=snapshot.endpoint_value,
        purpose=snapshot.purpose,
        party_id=snapshot.party_id,
        resolved_at=snapshot.resolved_at.isoformat(),
    )


# MILE-4.2 — Location foundation endpoints (BOPEN-LOC-001, DEC-P4-ENTRY §11). Bearer-gated: every one
# runs behind resolve_context, so the tenant comes from the signed context and every row is created and
# read under that tenant's row-level-security scope. A geometry observation is a CANDIDATE until an
# explicit `accept` (LOC-INV-06). Precise coordinates are redacted from every audit record (LOC-INV-14):
# the audit carries the location/observation id and the action, never a longitude or latitude.


def _translate_location_error(exc: location_repo.LocationError):
    if isinstance(exc, location_repo.LocationNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, location_repo.LocationConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, location_repo.RelationshipCycleError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(
        exc,
        (
            location_repo.CoordinateValidityError,
            location_repo.ProviderAcceptanceError,
            location_repo.LocationValidationError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _location_response(loc: location_repo.StoredLocation) -> LocationResponse:
    return LocationResponse(
        location_id=loc.id,
        tenant_id=loc.tenant_id,
        code=loc.code,
        name=loc.name,
        location_type=loc.location_type,
        lifecycle_state=loc.lifecycle_state,
        current_address_version_id=loc.current_address_version_id,
        current_geometry_observation_id=loc.current_geometry_observation_id,
        revision=loc.revision,
    )


def _address_response(a: location_repo.StoredAddressVersion) -> AddressVersionResponse:
    return AddressVersionResponse(
        address_version_id=a.id,
        location_id=a.location_id,
        version_number=a.version_number,
        country_code=a.country_code,
        premise=a.premise,
        thoroughfare=a.thoroughfare,
        locality=a.locality,
        admin_area=a.admin_area,
        postal_code=a.postal_code,
        recipient=a.recipient,
        original_input=a.original_input,
        rendered=a.rendered,
        verification_state=a.verification_state,
        is_current=a.effective_to is None,
    )


def _geometry_response(g: location_repo.StoredGeometryObservation) -> GeometryObservationResponse:
    return GeometryObservationResponse(
        observation_id=g.id,
        location_id=g.location_id,
        longitude=_decimal_str(g.longitude),
        latitude=_decimal_str(g.latitude),
        crs=g.crs,
        accuracy_radius_value=(
            _decimal_str(g.accuracy_radius_value) if g.accuracy_radius_value is not None else None
        ),
        accuracy_radius_unit=g.accuracy_radius_unit,
        capture_method=g.capture_method,
        source=g.source,
        confidence=_decimal_str(g.confidence) if g.confidence is not None else None,
        observed_at=g.observed_at.isoformat() if g.observed_at is not None else None,
        acceptance_state=g.acceptance_state,
        accepted_by=g.accepted_by,
    )


def _external_identifier_response(
    e: location_repo.StoredExternalIdentifier,
) -> ExternalIdentifierResponse:
    return ExternalIdentifierResponse(
        external_identifier_id=e.id,
        location_id=e.location_id,
        scheme=e.scheme,
        value=e.value,
        issuer=e.issuer,
        is_primary=e.is_primary,
    )


def _relationship_response(r: location_repo.StoredRelationship) -> RelationshipResponse:
    return RelationshipResponse(
        relationship_id=r.id,
        from_location_id=r.from_location_id,
        to_location_id=r.to_location_id,
        relationship_type=r.relationship_type,
    )


@app.post("/v1/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    body: CreateLocationRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> LocationResponse:
    try:
        created = locations.create(ctx.tenant_id, body.code, body.name, body.location_type)
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:create",
        resource_type="location", resource_id=created.id,
    )
    return _location_response(created)


@app.get("/v1/locations", response_model=list[LocationResponse])
def list_locations(
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[LocationResponse]:
    return [_location_response(loc) for loc in locations.list(ctx.tenant_id, limit=limit)]


@app.get("/v1/locations/{location_id}", response_model=LocationResponse)
def read_location(
    location_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> LocationResponse:
    try:
        loc = locations.get(ctx.tenant_id, normalise_id(location_id, "location_id"))
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    return _location_response(loc)


@app.put("/v1/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: str,
    body: UpdateLocationRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> LocationResponse:
    try:
        updated = locations.update(
            ctx.tenant_id, normalise_id(location_id, "location_id"),
            body.expected_revision, name=body.name, code=body.code,
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:update",
        resource_type="location", resource_id=location_id,
    )
    return _location_response(updated)


@app.post("/v1/locations/{location_id}/transition", response_model=LocationResponse)
def transition_location(
    location_id: str,
    body: TransitionLocationRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> LocationResponse:
    try:
        moved = locations.transition(
            ctx.tenant_id, normalise_id(location_id, "location_id"), body.to_state, ctx.principal_id
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:transition",
        resource_type="location", resource_id=location_id,
    )
    return _location_response(moved)


# -- Address versions ------------------------------------------------------------------


@app.post(
    "/v1/locations/{location_id}/address-versions",
    response_model=AddressVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_address_version(
    location_id: str,
    body: CreateAddressVersionRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> AddressVersionResponse:
    try:
        created = locations.add_address_version(
            ctx.tenant_id, normalise_id(location_id, "location_id"),
            country_code=body.country_code.upper(), original_input=body.original_input,
            premise=body.premise, thoroughfare=body.thoroughfare, locality=body.locality,
            admin_area=body.admin_area, postal_code=body.postal_code, recipient=body.recipient,
            components=body.components, rendered=body.rendered, language_tag=body.language_tag,
            script_tag=body.script_tag, template_profile=body.template_profile,
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:address_add",
        resource_type="location", resource_id=location_id,
    )
    return _address_response(created)


@app.get(
    "/v1/locations/{location_id}/address-versions",
    response_model=list[AddressVersionResponse],
)
def list_address_versions(
    location_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AddressVersionResponse]:
    return [
        _address_response(a)
        for a in locations.list_address_versions(
            ctx.tenant_id, normalise_id(location_id, "location_id"), limit=limit
        )
    ]


@app.post(
    "/v1/locations/{location_id}/address-versions/{version_id}/set-current",
    response_model=AddressVersionResponse,
)
def set_current_address_version(
    location_id: str,
    version_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> AddressVersionResponse:
    try:
        current = locations.set_current_address_version(
            ctx.tenant_id, normalise_id(location_id, "location_id"),
            normalise_id(version_id, "version_id"),
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:address_set_current",
        resource_type="location", resource_id=location_id,
    )
    return _address_response(current)


# -- Geometry observations -------------------------------------------------------------


@app.post(
    "/v1/locations/{location_id}/geometry-observations",
    response_model=GeometryObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_geometry_observation(
    location_id: str,
    body: CreateGeometryObservationRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> GeometryObservationResponse:
    """Record a point observation as a CANDIDATE. HTTP 201 does NOT mean accepted (LOC-INV-06): the
    observation must be accepted by a separate authorized action before it becomes current geometry."""
    observed_at = None
    if body.observed_at:
        try:
            observed_at = datetime.fromisoformat(body.observed_at)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="observed_at must be an ISO-8601 timestamp",
            )
    try:
        created = locations.observe(
            ctx.tenant_id, normalise_id(location_id, "location_id"),
            body.longitude, body.latitude, crs=body.crs,
            accuracy_radius_value=(body.accuracy_radius.value if body.accuracy_radius else None),
            accuracy_radius_unit=(body.accuracy_radius.unit if body.accuracy_radius else None),
            capture_method=body.capture_method, source=body.source,
            confidence=(Decimal(body.confidence) if body.confidence is not None else None),
            observed_at=observed_at,
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    # Precise coordinates are redacted from the audit record (LOC-INV-14): id and action only.
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:geometry_observe",
        resource_type="location_geometry_observation", resource_id=created.id,
    )
    return _geometry_response(created)


@app.get(
    "/v1/locations/{location_id}/geometry-observations",
    response_model=list[GeometryObservationResponse],
)
def list_geometry_observations(
    location_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[GeometryObservationResponse]:
    return [
        _geometry_response(g)
        for g in locations.list_observations(
            ctx.tenant_id, normalise_id(location_id, "location_id"), limit=limit
        )
    ]


@app.post(
    "/v1/locations/{location_id}/geometry-observations/{observation_id}/accept",
    response_model=GeometryObservationResponse,
)
def accept_geometry_observation(
    location_id: str,
    observation_id: str,
    body: AcceptGeometryObservationRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> GeometryObservationResponse:
    """Accept a candidate observation — a distinct authorized action (LOC-INV-05/06). The actor is the
    signed context's principal; provenance (source/observed_at/confidence) must be present."""
    try:
        accepted = locations.accept_observation(
            ctx.tenant_id, normalise_id(observation_id, "observation_id"), ctx.principal_id
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:geometry_accept",
        resource_type="location_geometry_observation", resource_id=observation_id,
    )
    return _geometry_response(accepted)


@app.post(
    "/v1/locations/{location_id}/geometry-observations/{observation_id}/reject",
    response_model=GeometryObservationResponse,
)
def reject_geometry_observation(
    location_id: str,
    observation_id: str,
    body: RejectGeometryObservationRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> GeometryObservationResponse:
    try:
        rejected = locations.reject_observation(
            ctx.tenant_id, normalise_id(observation_id, "observation_id"), body.reason
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:geometry_reject",
        resource_type="location_geometry_observation", resource_id=observation_id,
    )
    return _geometry_response(rejected)


# -- External identifiers --------------------------------------------------------------


@app.post(
    "/v1/locations/{location_id}/external-identifiers",
    response_model=ExternalIdentifierResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_external_identifier(
    location_id: str,
    body: CreateExternalIdentifierRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> ExternalIdentifierResponse:
    try:
        created = locations.add_external_identifier(
            ctx.tenant_id, normalise_id(location_id, "location_id"),
            body.scheme, body.value, issuer=body.issuer, is_primary=body.is_primary,
            provenance=body.provenance,
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:external_id_add",
        resource_type="location", resource_id=location_id,
    )
    return _external_identifier_response(created)


@app.get(
    "/v1/locations/{location_id}/external-identifiers",
    response_model=list[ExternalIdentifierResponse],
)
def list_external_identifiers(
    location_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ExternalIdentifierResponse]:
    return [
        _external_identifier_response(e)
        for e in locations.list_external_identifiers(
            ctx.tenant_id, normalise_id(location_id, "location_id"), limit=limit
        )
    ]


# -- Relationships ---------------------------------------------------------------------


@app.post(
    "/v1/locations/{location_id}/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_relationship(
    location_id: str,
    body: CreateRelationshipRequest,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
) -> RelationshipResponse:
    """Add a `contains` edge. A self-link, a duplicate live edge, a second live parent, and a
    containment cycle are all refused (LOC-INV-09)."""
    try:
        created = locations.add_contains(
            ctx.tenant_id,
            normalise_id(body.from_location_id, "from_location_id"),
            normalise_id(body.to_location_id, "to_location_id"),
        )
    except location_repo.LocationError as exc:
        raise _translate_location_error(exc)
    audit.record(
        tenant_id=ctx.tenant_id, principal_id=ctx.principal_id, context_id=ctx.context_id,
        correlation_id=ctx.correlation_id, event_type="domain", action="location:relationship_add",
        resource_type="location_relationship", resource_id=created.id,
    )
    return _relationship_response(created)


@app.get(
    "/v1/locations/{location_id}/relationships",
    response_model=list[RelationshipResponse],
)
def list_relationships(
    location_id: str,
    ctx: Annotated[ResolvedContext, Depends(resolve_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RelationshipResponse]:
    return [
        _relationship_response(r)
        for r in locations.list_relationships(
            ctx.tenant_id, normalise_id(location_id, "location_id"), limit=limit
        )
    ]
