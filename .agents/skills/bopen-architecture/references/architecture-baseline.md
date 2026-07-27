# bOPEN Architecture Baseline

## 1. Platform purpose

bOPEN is an owned, reusable, multi-tenant business-platform kernel. Products such as bPro and future industry systems compose shared platform, foundation, capability, and industry packages rather than reimplementing identity, tenancy, authorization, entitlement, audit, event, and portal foundations.

bOPEN MUST know how to operate a governed multi-tenant platform. It MUST NOT absorb product-specific definitions such as a forklift maintenance rule, property valuation method, insurance claim decision, or project-planning method unless those definitions are generalized into an approved shared capability.

## 2. Canonical execution chain

```text
PLATFORM
  -> PRINCIPAL
  -> TENANT
  -> MEMBERSHIP
  -> ACTIVE CONTEXT
  -> AUTHORIZATION
  -> ENTITLEMENT
  -> PRODUCT
  -> MODULE
  -> CAPABILITY
  -> WORKSPACE
  -> RESOURCE
  -> ACTION
  -> DOMAIN EVENT
  -> WORKFLOW / AUTOMATION / AGENT
  -> AUDIT / USAGE / EVIDENCE
```

Every architecture decision SHOULD identify where it operates in this chain and which earlier gates it depends on.

## 3. Foundational separations

- `Principal`: an actor that may authenticate or act, including a human, service account, application, device, agent, or system.
- `Identity`: authentication and account evidence associated with a principal.
- `Party`: a real-world person or organization participating in a business relationship; a party may exist without a login.
- `Tenant`: commercial, security, policy, and data-isolation boundary.
- `Organization`: business structure inside or associated with a tenant.
- `Legal entity`: legally recognized organization.
- `Membership`: governed relationship between a principal and tenant.
- `Role assignment`: a role granted to a principal within a defined scope and time window.
- `Permission`: authorization to perform an action on a resource.
- `Entitlement`: a tenant's right or capacity to consume a product, module, feature, or quota.
- `Capability`: registered action/resource contract exposed by the platform or a product package.
- `Tool`: callable technical interface.
- `Skill`: reusable operating procedure; it never grants permission.
- `Workflow`: durable, stateful, recoverable orchestration.

## 4. Tenancy and context

A global principal may have zero, one, or many tenant memberships. The active tenant context MUST be derived and validated server-side from trusted authentication, session, route, and membership evidence. A raw tenant identifier supplied by a client is input to validation, not proof of authority.

Pooled data uses `tenant_id` and PostgreSQL RLS as defense in depth. RLS MUST be enabled and default deny. Cross-tenant negative tests are mandatory. bOPEN may later support pooled, bridge, silo, and dedicated isolation profiles without changing product-domain contracts.

## 5. Authorization and entitlement

Access is granted only when all relevant gates pass:

```text
Tenant active
AND Principal active
AND Membership active
AND Active context valid
AND Product/module available
AND Tenant entitled
AND Module enabled
AND Principal authorized
AND Policy conditions satisfied
```

Entitlement does not imply user permission. Role does not imply entitlement. A skill or tool declaration does not grant either.

## 6. P0 topology

P0 uses a modular monolith with explicit package boundaries, owned contracts, PostgreSQL, RLS, transactional outbox, audit, module registry, entitlements, and portal foundations. Microservice extraction is a later operational decision supported by evidence, not a default design style.

Provider-specific services remain behind adapter interfaces for identity, ReBAC, workflow, metering, billing, object storage, notification, search, and agent runtimes.

## 7. Portals and context

Logical surfaces include Platform Console, My bOPEN, Tenant Portal, Work Portal, Security, Billing, Partner, Agent, and Developer experiences. They need not be separate deployables.

Typical context boundaries:

```text
/my/*            = global user context
/{tenantSlug}/*  = tenant context
/platform/*      = platform-operator context
```

Personal identity and security settings belong to the user context. Tenant-specific job title, role, module access, and tenant notification rules belong to membership or tenant context.

## 8. Events, audit, and evidence

Business modules own domain event semantics. bOPEN owns the event envelope, schema versioning, transactional outbox, delivery, deduplication, replay governance, dead-letter handling, correlation, usage extraction, and audit integrity.

Historical audit and evidence records MUST be append-only or cryptographically protected against undetected alteration. Release decisions require verifiable evidence, not only narrative assurance.

## 9. Agent and skill boundary

Agent principals are governed actors. Skills are versioned procedures. Tools expose operations. Every tool call is independently authorized. Tenant context, entitlement, data classification, approval, and runtime policy are revalidated during execution.

## 10. P0 approval posture

Architecture work may be approved for planning or controlled implementation while remaining blocked from production. Entry gates, verification evidence, tenant-isolation tests, recovery tests, supply-chain controls, and exit gates are separate approvals and MUST NOT be collapsed into one status.
