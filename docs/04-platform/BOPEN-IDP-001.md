# BOPEN-IDP-001 — Enterprise Identity, Federation, Provisioning, and Session Claims Standard

**Version:** 1.0  
**Date:** 2026-07-29  
**Document class:** Normative architecture and security specification  
**Phase:** Phase 2 — Membership & Enterprise Onboarding  
**Status:** APPROVED FOR PHASE 2 IMPLEMENTATION  
**Supersedes:** `BOPEN-IDP-001-DRAFT.md` when that draft is introduced into the controlled repository  
**Owner:** Engineering Authority  
**Approval basis:** Explicit project direction dated 2026-07-29  
**Approval boundary:** Phase 2 implementation only; not production activation  

## 1. Executive decision

bOPEN will use a protocol-neutral enterprise identity boundary that:

1. accepts enterprise authentication through SAML 2.0 or OpenID Connect;
2. provisions and deprovisions enterprise users and groups through SCIM 2.0;
3. maps external identities to one immutable bOPEN Principal;
4. maps tenant relationships to explicit Membership records;
5. issues short-lived, tenant-bound bOPEN session tokens;
6. derives roles and scopes from authoritative bOPEN state rather than trusting inbound role claims;
7. rotates the tenant context without requiring the user to authenticate again when the existing authentication session remains valid; and
8. emits correlated audit evidence for every security-relevant identity, membership, and context operation.

The approved integration pattern is an adapter around **BoxyHQ Jackson, now Ory Polis**, or an equivalent conformant enterprise SSO/directory-sync broker. The broker terminates and normalizes enterprise protocols. The bOPEN Platform Kernel remains the source of truth for principals, memberships, tenant context, roles, scopes, delegated grants, and authorization.

## 2. Approval interpretation

This specification is approved as the normative Phase 2 contract. Approval means implementation may be planned and executed under an authorized work package and exact repository baseline.

It does not:

- activate an identity provider in production;
- authorize storage or use of production credentials;
- approve a specific deployment topology or cloud provider;
- authorize Phase 3 entitlement implementation;
- make broker-issued attributes authoritative for bOPEN authorization;
- waive independent security review, conformance tests, or the Phase 2 exit gate.

## 3. Business and platform outcome

### 3.1 Value proposition

- Reduce enterprise onboarding lead time through standards-based SSO and directory sync.
- Preserve one governed authorization model across local, SAML, and OIDC authentication.
- Make tenant context explicit, short-lived, and auditable.
- Automate joiner, mover, and leaver controls without allowing an external directory to bypass bOPEN policy.
- Provide a stable SDK and token contract for every future bOPEN product.
- Support partner and support operations through time-bounded, revocable access.

### 3.2 Measurable outcomes

1. An invited user can accept exactly one valid invitation and obtain an active membership.
2. An expired, declined, consumed, revoked, or tenant-mismatched invitation cannot activate membership.
3. SAML and OIDC logins resolve to the same Principal only through an approved identity-linking rule.
4. SCIM creates, updates, suspends, and deprovisions bOPEN relationships idempotently.
5. A context token identifies one active principal, tenant, and membership relationship.
6. Context switching never carries a membership, role, scope, or grant from the previous tenant.
7. Removing or revoking membership prevents further token issuance and invalidates active context within the approved propagation objective.
8. Delegated access expires and revokes automatically.
9. Security events are correlated without logging credentials, assertions, bearer tokens, or unbounded personal data.

## 4. Scope

### 4.1 In scope

- Principal invitation lifecycle.
- Membership lifecycle and transition enforcement.
- Tenant context selection and switching.
- SAML 2.0 service-provider integration.
- OpenID Connect relying-party integration.
- SCIM 2.0 Users and Groups provisioning.
- External identity-link records.
- Identity-provider connection records and tenant binding.
- Internal session and context token claims.
- Key rotation, token validation, session invalidation, and logout hooks.
- Time-bounded delegated partner and support access.
- Audit, security, privacy, tests, evidence, and operational controls.
- TypeScript and Python SDK contracts for tenant-context switching.

### 4.2 Explicitly out of scope

- Password storage or a custom password authentication service.
- Consumer social login unless separately approved.
- Entitlement catalogs, subscriptions, billing, metering, or licensing.
- Product-specific permissions beyond Phase 2 bootstrap scopes.
- Human-resources master-data ownership.
- Identity proofing, government identity verification, or regulated eKYC.
- Privileged access management for infrastructure.
- Production deployment and production credential provisioning.
- User interfaces except minimal protocol callbacks or test harnesses.

## 5. Normative principles

- **Authentication is not authorization.**
- **External identity is not the Principal primary key.**
- **Tenant selection is explicit.**
- **Membership is authoritative for tenant relationship state.**
- **Roles and scopes are derived server-side.**
- **Every protocol boundary fails closed.**
- **Tokens are short-lived, audience-restricted, and tenant-bound.**
- **Directory synchronization is idempotent and replay-safe.**
- **Deprovisioning has priority over convenience.**
- **No account linking by mutable attributes alone.**
- **Secrets and raw tokens never enter audit metadata.**
- **All time comparisons use UTC and an injected clock in tests.**

## 6. Domain model

### 6.1 ExternalIdentity

| Field | Requirement |
|---|---|
| `external_identity_id` | Immutable opaque identifier |
| `principal_id` | Immutable reference to one bOPEN Principal |
| `tenant_id` | Required for tenant-managed enterprise identity |
| `connection_id` | Identity-provider connection |
| `protocol` | `saml` or `oidc` |
| `issuer` | Canonical issuer/entity identifier |
| `subject` | Stable provider subject; encrypted or protected as confidential data |
| `email_snapshot` | Optional, non-authoritative display/contact snapshot |
| `status` | `active`, `disabled`, or `unlinked` |
| `created_at`, `updated_at` | UTC timestamps |
| `version` | Positive concurrency version |

Uniqueness is enforced on canonical `(connection_id, issuer, subject)`. Email address alone must never establish identity equivalence.

### 6.2 IdentityProviderConnection

| Field | Requirement |
|---|---|
| `connection_id` | Immutable opaque identifier |
| `tenant_id` | Exact owning tenant |
| `protocol` | `saml` or `oidc` |
| `broker_connection_ref` | Protected broker reference |
| `issuer` | Expected SAML entity ID or OIDC issuer |
| `status` | `draft`, `verified`, `active`, `suspended`, `retired` |
| `domain_hints` | Optional hints; never sufficient authorization |
| `jit_policy` | `disabled`, `invitation_only`, or separately approved mode |
| `created_by`, `approved_by` | Distinct accountable identities where required |
| `verified_at` | UTC timestamp after metadata/connection verification |
| `version` | Positive concurrency version |

Only an `active` connection can start new enterprise authentication.

### 6.3 SCIMDirectory

| Field | Requirement |
|---|---|
| `directory_id` | Immutable opaque identifier |
| `tenant_id` | Exact owning tenant |
| `broker_directory_ref` | Protected broker reference |
| `status` | `draft`, `active`, `suspended`, `retired` |
| `provisioning_mode` | `users`, `users_and_groups` |
| `deprovision_policy` | Approved mapping to membership state |
| `last_sync_at` | Optional UTC timestamp |
| `version` | Positive concurrency version |

### 6.4 Invitation

| Field | Requirement |
|---|---|
| `invitation_id` | Immutable opaque identifier |
| `tenant_id` | Target tenant |
| `email_normalized` | Confidential, normalized destination |
| `requested_roles` | Approved bootstrap roles only |
| `requested_scopes` | Approved Phase 2 scopes only |
| `state` | `invited`, `active`, `declined`, or `expired` |
| `token_digest` | One-way digest; raw token is never stored |
| `invited_by_principal_id` | Active authorized inviter |
| `principal_id` | Set after secure acceptance/linking |
| `membership_id` | Set on successful activation |
| `issued_at`, `expires_at` | UTC timestamps |
| `accepted_at`, `declined_at` | Optional terminal timestamps |
| `version` | Positive concurrency version |

`active` means the invitation was successfully accepted and its membership was activated. The invitation token is single-use.

### 6.5 Membership

The Phase 2 closed state set is:

```text
invited | active | suspended | revoked | expired | left | removed
```

The canonical transition matrix is governed by `membership-transition.json`. The implementation must reject any transition absent from that file.

Minimum transition intent:

| From | To | Authorized cause |
|---|---|---|
| `invited` | `active` | Valid invitation acceptance or approved SCIM activation |
| `invited` | `expired` | Expiry scheduler or validation-on-read |
| `invited` | `removed` | Authorized tenant administrator |
| `active` | `suspended` | Tenant administrator, security control, or SCIM inactive |
| `active` | `revoked` | Security/authority revocation |
| `active` | `expired` | Time-bounded relationship reaches expiry |
| `active` | `left` | Principal-initiated leave where policy permits |
| `active` | `removed` | Authorized tenant administrator |
| `suspended` | `active` | Authorized reinstatement after precondition checks |
| `suspended` | `revoked` | Security/authority revocation |
| `suspended` | `removed` | Authorized tenant administrator |

Terminal states do not reactivate implicitly. A new relationship requires a new membership unless a specifically approved transition permits reinstatement.

## 7. Protocol trust boundaries

```mermaid
flowchart LR
    IdP["Enterprise IdP"] --> Broker["SSO / SCIM Broker"]
    Broker --> Bridge["bOPEN IdP Bridge"]
    Bridge --> Kernel["Platform Kernel"]
    Kernel --> Token["bOPEN Session Issuer"]
```

The broker:

- validates protocol-specific messages according to its supported configuration;
- normalizes authentication and directory events;
- protects broker administration APIs;
- provides stable connection and directory references.

The bOPEN bridge:

- validates broker authenticity, audience, tenant binding, replay controls, and event schema;
- maps the event to one connection and tenant;
- resolves or creates only permitted bOPEN records;
- never accepts inbound roles or groups as direct authorization;
- calls the kernel for membership and context decisions;
- emits correlated audit evidence.

The kernel:

- owns Principal and Membership state;
- derives roles and scopes;
- authorizes context issuance;
- enforces revocation and tenant isolation.

## 8. SAML 2.0 profile

### 8.1 Required flow

- Service-provider-initiated SSO is the default.
- Identity-provider-initiated SSO is disabled unless explicitly approved per tenant.
- Each SAML connection is bound to exactly one bOPEN tenant and product/application context.
- Assertion consumer service URLs, entity IDs, and audiences are exact allowlisted values.

### 8.2 Validation requirements

Before accepting an authentication result:

- validate broker callback authenticity;
- validate SAML signature and certificate chain through the broker;
- validate issuer, audience, recipient, destination, and time conditions;
- reject unsigned or ambiguously signed responses according to the frozen broker profile;
- reject replayed response/assertion identifiers;
- apply bounded clock skew;
- require an approved stable subject attribute;
- reject tenant or connection mismatch;
- redact raw assertions from logs and evidence.

### 8.3 Attribute mapping

Permitted inbound attributes are allowlisted per connection. Typical attributes include stable subject, email, display name, and group identifiers. Attributes are profile inputs only.

Group-to-role mapping must pass through a versioned bOPEN mapping policy and can never override:

- inactive Principal;
- inactive Tenant;
- non-active Membership;
- explicit deny;
- delegated-grant expiry;
- tenant mismatch.

## 9. OpenID Connect profile

### 9.1 Required flow

- Authorization Code flow with PKCE is required.
- Redirect URIs are exact registered values.
- `state` and `nonce` are unique, high-entropy, single-use values.
- Provider discovery metadata and signing keys are fetched through approved, bounded adapters and cached with rotation support.

### 9.2 ID Token validation

Validate at minimum:

- expected `iss`;
- intended `aud`;
- `azp` when required by multiple audiences;
- signature and allowed algorithm;
- `exp`, `iat`, and `nbf` when present;
- exact `nonce`;
- stable `sub`;
- tenant/connection binding;
- approved authentication assurance requirements, when configured.

Unknown algorithms, missing mandatory claims, key-resolution failure, issuer mismatch, or time failure produce a typed denial.

## 10. SCIM 2.0 profile

### 10.1 Supported resources

Phase 2 supports:

- `/Users`;
- `/Groups`;
- `/ServiceProviderConfig`;
- `/ResourceTypes`;
- `/Schemas`.

Bulk operations and optional extensions are deferred unless specifically enabled and tested.

### 10.2 User mapping

| SCIM field | bOPEN interpretation |
|---|---|
| `id` | Broker/provider resource reference; not Principal ID |
| `externalId` | Tenant-scoped external correlation value |
| `userName` | Directory identifier; confidential |
| `active` | Provisioning signal mapped through membership policy |
| `name`, `displayName`, `emails` | Profile snapshots; not authorization |
| `groups` | Relationship inputs evaluated through a versioned mapping |
| `meta.version` | Concurrency/replay input when supported |

### 10.3 Idempotency and ordering

- Create replay with the same directory resource identity returns the existing logical mapping.
- Conflicting reuse of `externalId` is rejected and audited.
- Updates use version-aware or deterministic last-observed semantics approved before coding.
- Out-of-order events cannot reactivate a more recently deprovisioned relationship.
- Deprovision events are processed with higher security priority than profile updates.
- Delete or `active:false` maps to the approved non-active membership transition; hard deletion of audit-relevant identity records is prohibited.

### 10.4 Group mapping

SCIM Groups can propose tenant roles or team relationships only through an approved mapping table:

```text
directory_id + group_external_id
    -> mapping_policy_version
    -> approved bOPEN role/team target
```

Unmapped groups have no authorization effect.

## 11. Identity linking

Identity linking is permitted only when one of these conditions holds:

1. an authenticated active Principal accepts a link challenge for the new enterprise identity;
2. a valid invitation is bound to the same tenant and verified email, followed by provider authentication;
3. a privileged, separately authorized administrative recovery procedure is completed with audit evidence.

Forbidden:

- automatic linking solely because email strings match;
- linking across tenants through a domain hint;
- overwriting an existing external identity binding;
- reassigning a stable `(issuer, subject)` to another Principal.

## 12. bOPEN session and context token standard

### 12.1 Token classes

| Token | Purpose | Tenant-bound |
|---|---|---|
| Authentication session | Proves a recent validated authentication session | No, but restricted to the principal and client |
| Context access token | Authorizes API access in one tenant context | Yes |
| Refresh/rotation handle | Obtains a new context token under server-side checks | Bound to session and client |
| Delegation evidence | References an approved delegated grant | Yes |

### 12.2 Mandatory JWT claims

The context access token contains:

| Claim | Meaning |
|---|---|
| `iss` | bOPEN token issuer |
| `aud` | Exact bOPEN API/resource audience |
| `sub` | Immutable Principal ID |
| `tid` | Active Tenant ID |
| `mid` | Active Membership ID |
| `roles` | Server-derived closed list |
| `scopes` | Server-derived closed list |
| `iat` | Issued-at time |
| `nbf` | Not-before time when used |
| `exp` | Expiry time |
| `jti` | Unique token identifier |
| `sid` | Authentication session identifier |
| `ctx` | Context identifier/version |

Optional claims:

- `dgr`: delegated-grant reference;
- `amr`: authentication methods, if verified;
- `acr`: authentication assurance, if verified and policy-relevant;
- `ver`: token schema version.

### 12.3 Claim rules

- `sub`, `tid`, and `mid` must resolve to one active relationship chain.
- `roles` and `scopes` are fetched or derived from authoritative bOPEN state at issuance.
- A token contains exactly one active tenant context.
- `roles` and `scopes` use stable identifiers, not display labels.
- Tokens contain no email address, name, raw group list, secrets, or provider assertion.
- `dgr` is mandatory for delegated context and must resolve to an active unexpired grant.

### 12.4 Signing and validation

- Use asymmetric signing keys managed outside source control.
- Publish a versioned JWKS endpoint for verifier key discovery.
- Include `kid`; reject unknown keys and disallowed algorithms.
- Rotate keys with an overlap period shorter than the maximum accepted token lifetime plus clock skew.
- Validate signature, algorithm, issuer, audience, time, and mandatory claims before resolving context.
- Never accept an unsigned token or `alg=none`.
- Do not log complete token values.

### 12.5 Lifetime defaults

Values are pre-coding decisions, not hard-coded protocol facts. Recommended Phase 2 defaults:

| Control | Recommended default |
|---|---|
| Context access-token lifetime | 5 minutes |
| Clock-skew allowance | Maximum 60 seconds |
| Invitation lifetime | 7 days |
| Delegated grant maximum | 8 hours for support; policy-defined for partners |
| Session idle/max lifetime | Defined by tenant policy; server-side revocable |

## 13. Tenant context switching

### 13.1 API contract

Client intent may be expressed through:

- `X-Tenant-ID`: requested tenant;
- `X-Context-ID`: current or expected context correlation identifier.

Headers are untrusted selectors, not authorization evidence.

The context-switch endpoint:

```text
POST /v1/session/context:switch
```

Request:

```json
{
  "tenant_id": "opaque-tenant-id",
  "expected_context_id": "opaque-context-id",
  "idempotency_key": "opaque-key"
}
```

Response:

```json
{
  "context_id": "new-context-id",
  "tenant_id": "opaque-tenant-id",
  "membership_id": "opaque-membership-id",
  "access_token": "<returned only through the approved token channel>",
  "expires_at": "UTC timestamp"
}
```

### 13.2 Switching algorithm

1. Validate the authentication session and client binding.
2. Validate request shape, CSRF protection where applicable, and idempotency.
3. Resolve the requested tenant without disclosing unauthorized tenant details.
4. Resolve the principal’s active membership in that tenant.
5. Resolve active delegated grant if ordinary membership is absent and delegation is permitted.
6. Derive fresh roles and scopes for the target tenant.
7. create a new context identifier.
8. issue a new short-lived context token.
9. invalidate or supersede the prior context according to the session policy.
10. emit `context.switched` with old/new context references but no token.

Failure at any step returns no token.

## 14. Delegated cross-tenant access

### 14.1 Grant fields

| Field | Requirement |
|---|---|
| `grant_id` | Immutable opaque identifier |
| `grant_type` | `partner` or `support` |
| `source_principal_id` | Receiving principal |
| `target_tenant_id` | Exact target tenant |
| `approved_roles`, `approved_scopes` | Minimum bounded grant |
| `reason_code` | Approved business/security reason |
| `approved_by` | Authorized approver |
| `starts_at`, `expires_at` | UTC, bounded |
| `state` | `pending`, `active`, `revoked`, `expired` |
| `revoked_at`, `revoked_by` | Required on revocation |
| `version` | Positive concurrency version |

### 14.2 Controls

- No standing support super-user.
- No wildcard tenant or wildcard scope.
- Grant duration is bounded and cannot be silently extended.
- Support grants require case/ticket correlation.
- Sensitive operations may require step-up authentication or separate approval.
- Grant revocation invalidates future issuance immediately and active contexts within the approved propagation objective.
- All delegated actions include the grant reference in audit evidence.

## 15. Audit event catalog

Minimum Phase 2 events:

- `invitation.issued`
- `invitation.accepted`
- `invitation.declined`
- `invitation.expired`
- `invitation.validation_failed`
- `membership.transitioned`
- `membership.transition_denied`
- `identity.connection_verified`
- `identity.authentication_succeeded`
- `identity.authentication_denied`
- `identity.linked`
- `identity.link_denied`
- `scim.user_provisioned`
- `scim.user_updated`
- `scim.user_deprovisioned`
- `scim.group_mapping_applied`
- `scim.event_denied`
- `context.issued`
- `context.switched`
- `context.switch_denied`
- `context.revoked`
- `delegation.created`
- `delegation.activated`
- `delegation.revoked`
- `delegation.expired`

Audit metadata must be bounded and allowlisted. It may contain identifiers, policy versions, reason codes, outcomes, correlation/causation IDs, and timestamps. It must not contain:

- passwords or secrets;
- SAML assertions;
- OIDC authorization codes;
- access, ID, refresh, invitation, or SCIM bearer tokens;
- complete broker payloads;
- unredacted personal profiles.

## 16. Security requirements

| Threat | Mandatory control |
|---|---|
| SAML/OIDC replay | Single-use state/nonce/assertion identifiers and bounded replay cache |
| Account takeover by email match | Stable issuer/subject binding and explicit linking |
| Tenant confusion | Connection-to-tenant binding and tenant-first validation |
| Forged role/group claim | Server-side mapping and kernel derivation |
| Stale access after deprovision | Short tokens, server-side session revocation, priority deprovision |
| SCIM replay/out-of-order update | Idempotency, version/order guard, fail-closed conflicts |
| Token substitution | Exact issuer/audience/client validation |
| Key compromise | External key custody, rotation, revocation runbook |
| Delegation persistence | Mandatory expiry and automatic revocation |
| Secret leakage | Structured redaction and prohibited-field tests |

## 17. Privacy and retention

- Collect only attributes required for identity resolution, contact, audit, or approved product needs.
- Classify identity mappings, tenant membership, roles, scopes, and audit events as confidential security data.
- Store raw protocol payloads only when strictly required for short-lived troubleshooting under a separately approved retention rule.
- Support data-subject correction without rewriting immutable audit evidence.
- Retain tombstone/correlation records needed to prevent identity reassignment or replay.
- Document tenant-specific data residency and retention decisions before production.

## 18. Reliability and operational controls

- Broker unavailability prevents new enterprise logins and SCIM processing but does not convert failures into local authorization.
- Existing context tokens remain valid only until their normal expiry unless revoked.
- SCIM handlers support retry with idempotency.
- Dead-lettered events require an operational queue/record with reason, retry count, and manual disposition.
- Clock drift, signing-key age, JWKS refresh, authentication failure rate, SCIM lag, deprovision lag, and context-switch denial rate are monitored.
- Break-glass access is not part of Phase 2 unless separately specified and approved.

## 19. Conformance requirements

Implementation must demonstrate:

- SAML happy path and signature/audience/replay negative paths;
- OIDC code flow with PKCE, state, nonce, issuer, audience, signature, and expiry validation;
- SCIM Users and Groups create/update/deprovision/replay/out-of-order handling;
- invitation single-use, expiry, decline, and tenant-binding behavior;
- every permitted and forbidden membership transition;
- context switch success, cross-tenant denial, stale membership denial, and role isolation;
- delegated grant activation, expiry, revocation, and audit;
- prohibited-field scanning across logs and evidence.

## 20. Architecture decisions required before coding

| ADR | Decision |
|---|---|
| ADR-P2-001 | Broker deployment and adapter boundary |
| ADR-P2-002 | External identity uniqueness and linking |
| ADR-P2-003 | Invitation token generation, hashing, and consumption |
| ADR-P2-004 | Membership transition atomicity and concurrency |
| ADR-P2-005 | Session store, context rotation, and revocation |
| ADR-P2-006 | JWT signing algorithm, key custody, rotation, and JWKS |
| ADR-P2-007 | SCIM ordering, idempotency, and deprovision mapping |
| ADR-P2-008 | Group-to-role mapping governance |
| ADR-P2-009 | Delegated-grant approval and maximum duration |
| ADR-P2-010 | Identity audit data classification and retention |

## 21. Approval conditions

This standard is effective for Phase 2 implementation subject to:

1. an authorized `BOPEN-P2-001` execution package;
2. exact repository baseline and permitted path identification;
3. approval of `membership-transition.json`;
4. resolution of the required ADRs;
5. no production secrets in repository, test fixtures, logs, or evidence;
6. independent security review and reproducible acceptance evidence; and
7. a separate production activation decision.

## 22. Normative references

- SAML 2.0 specifications and profiles published by OASIS.
- OpenID Connect Core 1.0 and Discovery 1.0.
- OAuth 2.0 Authorization Framework, Bearer Token Usage, and PKCE.
- JSON Web Token and JSON Web Signature specifications.
- SCIM Core Schema (RFC 7643) and SCIM Protocol (RFC 7644), including applicable updates.
- Ory Polis / BoxyHQ Jackson deployment and integration documentation for the selected pinned release.

