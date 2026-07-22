---
name: bopen-architecture
description: Design, research, review, and govern bOPEN platform architecture and P0 implementation controls. Use for bOPEN tenancy, principals, membership, active tenant context, authorization/RLS/ReBAC, entitlements, products/modules/capabilities, portals, events/outbox/audit, agent skills, ADRs, conformance reviews, implementation plans, and verification matrices. Do not use for unrelated software architecture or product-domain implementation that does not affect bOPEN platform contracts.
license: Proprietary. See LICENSE.txt
metadata:
  author: BizEra
  version: "0.1.1"
  bopen.skill.id: io.bizera.bopen.architecture
  bopen.lifecycle.stage: candidate
  bopen.risk.class: SKR1
allowed-tools: Read Grep Glob
---

# bOPEN Architecture

Use this skill to produce governed, evidence-backed architecture work for the bOPEN platform kernel and products built on it.

**Compatibility:** Agent Skills-compatible; optimized for Codex and ChatGPT with filesystem access. Python 3.11+ is required only for bundled validation and artifact scripts. Network access is optional and must follow the research policy.

## Activation boundary

Use this skill when the task concerns one or more of these areas:

- bOPEN platform or product architecture research, design, review, or conformance;
- principals, identities, parties, tenants, organizations, legal entities, memberships, or active context;
- authorization, PostgreSQL row-level security, policy conditions, ReBAC seams, support access, or cross-tenant controls;
- products, modules, features, capabilities, entitlements, package contracts, or portal composition;
- events, transactional outbox, audit, workflow boundaries, usage, metering, or provider-neutral adapters;
- agent principals, tools, skills, runtime bindings, evaluation, provenance, or approval controls;
- ADRs, implementation control packages, verification matrices, evidence envelopes, risks, and exit gates.

Do not activate for generic architecture questions unrelated to bOPEN, routine code edits that do not change architecture contracts, or industry-domain behavior that belongs entirely inside a product or industry pack.

## Authority order

Apply sources in this order:

1. Applicable repository governance and an effective, bounded authority record.
2. Approved bOPEN requirements, architecture, governance, and implementation-control artifacts.
3. The user's explicit current instruction, only within the effective authority and governance boundary.
4. Repository contracts, schemas, migrations, tests, and ADRs that implement the approved baseline.
5. Current primary external sources and standards when research is required.
6. Clean-room observations from open-source systems.
7. Clearly labeled assumptions that do not substitute for authority.

Missing, expired, ambiguous, or mismatched authority is a blocker. Never convert
missing authority into an assumption, and never treat skill discovery or invocation
as permission to mutate files or systems.

Never silently replace an approved bOPEN decision with an external product's model. Identify conflicts and recommend an ADR or change request.

## Non-negotiable bOPEN baseline

Preserve these rules unless the task explicitly requests a governed architecture change:

- A global principal relates to a tenant through a first-class membership and operates through validated active tenant context.
- Principal, user identity, party, tenant, organization, legal entity, membership, role, permission, entitlement, capability, tool, skill, and workflow are distinct concepts.
- Tenant is the commercial, security, and data-isolation boundary; organization and legal entity model business structure.
- Membership is not a role. A role is not a job title. Permission is not entitlement. A skill is not permission.
- bOPEN owns platform concerns; product and industry packages own domain behavior.
- P0 is a modular monolith unless an approved ADR establishes a stronger reason to split a boundary.
- PostgreSQL RLS is a hard tenant-isolation control for pooled data. Missing context or missing policy must fail closed.
- Client-supplied tenant identifiers never establish tenant authority by themselves.
- Every privileged operation is independently authorized in current context; discovery or procedure selection does not grant authority.
- Durable state changes use explicit transactions, idempotency, audit correlation, and a transactional outbox where asynchronous delivery is required.
- Provider integrations remain behind owned bOPEN contracts and replaceable adapters.
- Cross-tenant disclosure, unauthorized elevation, and mutable historical evidence are blocking defects.

Read [references/architecture-baseline.md](references/architecture-baseline.md) and [references/domain-glossary.md](references/domain-glossary.md) when the task touches foundational concepts.

## Procedure

### 1. Classify the work

Select the primary mode:

- `research`: compare standards, products, or patterns and derive bOPEN implications;
- `design`: define a target architecture, contracts, boundaries, flows, and controls;
- `review`: evaluate an existing design, repository, or proposal against the baseline;
- `adr`: record one material decision and alternatives;
- `gap-analysis`: compare current and target states;
- `implementation-control`: decompose approved architecture into governed work packages and gates;
- `conformance-review`: issue a pass, conditional pass, or fail verdict supported by evidence.

Use the corresponding template in `assets/`. When multiple modes apply, choose one controlling artifact and attach supporting sections rather than mixing several uncontrolled documents.

### 2. Establish scope and evidence

State:

- objective, system boundary, actors, tenants, products, modules, data classes, and environments;
- authoritative sources and their dates or versions;
- explicit constraints, assumptions, exclusions, and unresolved facts;
- whether current web research is required.

For web research, follow [references/research-and-evidence-policy.md](references/research-and-evidence-policy.md). Prefer primary sources, verify freshness, separate observed fact from inference, and record citations in the artifact.

### 3. Model the architecture

Cover only the layers relevant to the task, but check the complete execution chain:

```text
PRINCIPAL
  -> MEMBERSHIP
  -> ACTIVE TENANT CONTEXT
  -> AUTHORIZATION
  -> ENTITLEMENT
  -> PRODUCT / MODULE / CAPABILITY
  -> WORKSPACE / RESOURCE
  -> ACTION
  -> DOMAIN EVENT
  -> WORKFLOW / AUTOMATION / AGENT
  -> AUDIT / USAGE / EVIDENCE
```

Define component ownership, trust boundaries, data ownership, APIs, events, state machines, invariants, dependencies, and failure behavior. Distinguish authoritative contracts from illustrative implementation detail.

### 4. Evaluate alternatives

For each material decision:

- define the problem and decision drivers;
- compare at least two credible options when alternatives exist;
- assess tenancy, security, consistency, operability, cost, reversibility, portability, and P0 complexity;
- state the recommendation, rejected options, consequences, and migration trigger.

Use [references/decision-and-review-model.md](references/decision-and-review-model.md).

### 5. Apply control analysis

Check:

- tenant-context derivation and propagation;
- authorization and entitlement separation;
- RLS/default-deny behavior and cross-tenant negative cases;
- privilege boundaries for humans, services, devices, and agents;
- secrets, data classification, retention, and support access;
- transaction, concurrency, idempotency, retry, compensation, and recovery;
- event ordering, deduplication, replay, dead-letter handling, and audit correlation;
- supply-chain, provenance, dependency, and publication controls;
- human approval boundaries for material or externally visible decisions.

Read [references/security-and-tenancy.md](references/security-and-tenancy.md) for mandatory checks.

### 6. Define implementation and verification

Translate the recommendation into:

- sequenced work packages with owners, dependencies, entry criteria, acceptance criteria, and evidence;
- API, schema, migration, event, policy, portal, and operational changes;
- happy-path, invalid-input, unauthorized-principal, missing-entitlement, wrong-tenant, concurrency, idempotency, partial-failure, rollback, recovery, and audit-integrity tests;
- release, rollback, observability, backup/restore, and exit gates.

Use [references/quality-gates.md](references/quality-gates.md). Cross-tenant failures allowed: zero.

### 7. Produce the artifact

The artifact must contain:

- artifact ID, title, version, status, date, owner, and scope;
- executive summary and disposition;
- current state, target state, architecture, and decision rationale;
- security, tenancy, data, operational, and supply-chain controls;
- risks, gaps, assumptions, dependencies, and unresolved items;
- implementation plan, verification matrix, evidence requirements, and exit gates;
- source register and change-control requirements.

Use precise normative language: `MUST`, `MUST NOT`, `SHOULD`, `MAY`. Label proposals and assumptions so they cannot be mistaken for approved controls.

### 8. Validate before completion

When working in a filesystem under separately verified mutation authority:

1. Create an artifact skeleton if useful:
   `python scripts/new_artifact.py --type <type> --id <ID> --title "<title>" --output-dir <authorized-directory> --output <relative-path>`
2. Check an architecture document:
   `python scripts/check_architecture.py <artifact.md> --strict`
3. Validate this package after edits:
   `python scripts/validate_package.py`
4. Run deterministic package evaluations:
   `python scripts/run_static_evals.py --output-dir <authorized-directory> --output <relative-report-path>`

Do not claim independent approval, cryptographic signing, production validation, or model-level evaluation unless the corresponding evidence exists.

## Output dispositions

Use one recommendation-only disposition:

- `RECOMMEND_APPROVAL`: all mandatory controls and evidence pass;
- `RECOMMEND_APPROVAL_WITH_CONDITIONS`: bounded gaps have owners, deadlines, and non-bypassable conditions;
- `RECOMMEND_RETURN_FOR_REVISION`: material design gaps remain but no immediate stop condition exists;
- `RECOMMEND_REJECTION`: the proposal violates a core boundary or would create unacceptable risk;
- `RECOMMEND_BLOCK`: a non-waivable tenant-isolation, authorization, evidence-integrity, or safety control fails.

These values are advisory recommendations. They are not approval, gate passage,
activation, release, or deployment decisions.

## Publication and authority

This skill may generate recommendations and local artifacts. It does not approve architecture, grant permissions, publish externally, change production systems, or authorize tenant access. Human architecture and security authorities remain accountable for approval and release.
