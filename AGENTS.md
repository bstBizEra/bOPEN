# AGENTS.md — bOPEN Repository Operating Instructions

## 1. Scope and precedence

This file applies to the entire repository. A deeper `AGENTS.md` may add stricter directory-specific rules but may not weaken or contradict this file.

Instruction precedence:

```text
Current user instruction
  > applicable AGENTS.md files, deepest first
  > approved normative artifacts
  > approved ADRs and contracts
  > accepted work package
  > existing implementation convention
```

When requirements conflict, stop and record the conflict. Do not silently choose an architecture.

## 2. Mission

Build bOPEN as an independently governed multi-tenant, multi-industry platform kernel. bOPEN owns platform concerns; industry products own industry semantics.

bOPEN may own:

- principals, identity and authentication boundaries;
- tenants, organizations, memberships and context;
- authorization, entitlement and capability contracts;
- shared business foundations;
- events, audit, workflow integration and usage contracts;
- module registration and product composition;
- isolation, security and operational controls.

bOPEN shall not embed forklift, property valuation, insurance claim, coffee processing or project-management semantics inside the platform kernel.

## 3. Current implementation gate

Repository bootstrap, documentation, research and contract drafting are authorized. Production kernel implementation is not authorized until:

1. BOPEN-RES-001 Gate G7 passes;
2. applicable normative artifacts are approved;
3. an implementation work package is accepted;
4. required contracts and acceptance tests exist.

Creating empty directories, interfaces, schemas marked draft, test harnesses and documentation is allowed. Implementing production business logic before the gate is prohibited.

## 4. Mandatory source-of-truth hierarchy

```text
Approved normative artifact
  > Approved ADR
  > Versioned contract
  > Accepted work package
  > Implementation
  > Test evidence
  > Informal note
```

Never use an upstream project, UI mockup, comment or prompt as a substitute for an approved bOPEN decision.

## 5. Required workflow for every change

1. Read the root and all scoped `AGENTS.md` files.
2. Identify the accepted work-package ID.
3. Identify governing artifact, requirement and ADR IDs.
4. Inspect existing contracts and tests.
5. Make the smallest coherent change.
6. Add or update tests and evidence.
7. Update documentation and traceability.
8. Run repository validation.
9. Report changed files, checks, residual risks and blocked decisions.

A change without traceability is incomplete.

## 5a. Shared skill discovery and eligibility

- Discover reusable repository skills only from `.agents/skills/<skill-name>/SKILL.md`.
- Resolve identity, lifecycle, activation, invocation policy and dependencies through `docs/registers/skill-registry.json` before use.
- Apply ownership and overlap boundaries from `.agents/SKILL-ROUTING.md`; do not infer routing from directory presence.
- Treat user-scoped or harness-specific installations as adapters or caches; they may not silently fork the repository package.
- `candidate` or `activation: inactive` skills are discoverable for evaluation and advisory analysis only. They cannot authorize tools, mutation, approval, activation, gate passage, release or deployment.
- Invoke transactional, admission and gate skills only when explicitly named and independently authorized.
- Prefer the narrowest specialist skill. Use orchestrator skills only to sequence registered specialists; never let an orchestrator replace their mandatory checks.
- Stop when a workflow references an unknown, duplicate, unregistered, digest-drifted or ineligible skill.

## 6. Clean-room controls

Repository zones:

```text
research/upstream/       upstream inspection only
research/findings/       observations and evidence only
docs/resources/          controlled research records
apps/, services/, packages/, contracts/   clean bOPEN zones
```

Prohibited actions:

- copying or translating upstream source into bOPEN code;
- renaming upstream tables, classes, routes or UI and treating them as original design;
- importing upstream migrations into production zones;
- using upstream tests as bOPEN tests without independent specification;
- removing license, copyright or provenance metadata;
- committing upstream source outside `research/upstream/`.

Allowed flow:

```text
Observation -> Evidence -> Finding -> Requirement/ADR -> Contract -> Independent implementation
```

## 7. Architectural invariants

Agents shall preserve these invariants unless an approved ADR changes them:

1. `Principal` is broader than human user.
2. `Tenant` is a commercial, policy, security and isolation boundary.
3. `Organization` and `Legal Entity` are not synonyms for tenant.
4. `Membership` is a first-class principal-to-tenant relationship.
5. Membership is not role, job title, permission or entitlement.
6. Active context must be explicit, validated and auditable.
7. Authorization is deny-by-default.
8. Entitlement is separate from authorization and feature rollout.
9. Capability contracts are versioned and independent of UI routes.
10. Tenant-owned data requires an approved ownership and isolation strategy.
11. Domain events and audit events are distinct but correlated.
12. Industry semantics belong in capability or industry packages, not the platform kernel.

## 8. Tenant data safety

No tenant-owned storage may be introduced without:

- explicit tenant ownership field or approved physical isolation;
- foreign-key and uniqueness strategy that includes tenant scope where required;
- database enforcement, not only application filtering;
- deny-by-default access policy;
- cross-tenant negative tests;
- migration, rollback and data-retention consideration;
- audit treatment for privileged access.

Never trust tenant IDs supplied by clients without server-side context validation.

## 9. Authorization safety

Do not add permission checks ad hoc inside UI components. Authorization decisions shall use the approved decision interface and include:

- principal;
- tenant and active context;
- action;
- resource type and identifier;
- scope;
- applicable role/grant/policy;
- entitlement and capability state where relevant;
- decision and reason code;
- correlation/audit metadata.

Never equate `isAdmin` with unrestricted platform access.

## 10. Contract-first rule

For externally observable behavior, define or update the contract before implementation:

- API schema;
- event schema;
- module manifest;
- authorization decision schema;
- error code;
- migration contract;
- compatibility and versioning rule.

Draft contracts must be marked `draft` and cannot be treated as stable dependencies.

## 11. Testing expectations

Every change shall include appropriate tests. Security-sensitive work requires negative tests.

Minimum categories:

- unit tests for deterministic logic;
- contract tests for APIs/events/manifests;
- integration tests for database boundaries;
- tenant-isolation tests;
- authorization allow and deny tests;
- migration and rollback tests where data changes;
- end-to-end tests for accepted vertical slices;
- evidence artifact linked to the work package.

Never delete, skip or weaken a failing test without documenting the reason and obtaining approval.

## 12. Documentation requirements

Update documentation in the same change when behavior, contracts, architecture or operating procedures change.

Every controlled document requires:

- document ID;
- version;
- status;
- owner;
- issue/update date;
- governing and dependent artifacts;
- decision and evidence references.

Use `docs/templates/` rather than inventing new formats.

## 13. Security and secrets

- Never commit credentials, tokens, private keys or real personal data.
- Use example values clearly marked as non-production.
- Treat logs and evidence as potentially sensitive.
- Redact secrets from failure output.
- Pin third-party actions and dependencies where practical.
- Record dependency and license changes.
- Do not disable security scanners to make CI pass.

## 14. Database and migration rules

- Migrations are append-only after merge.
- Every migration must have forward, rollback or compensating strategy.
- Destructive changes require a staged rollout plan.
- Tenant-scoped uniqueness must include tenant scope unless globally unique by design.
- Database security policies must be tested as database behavior.
- Seed data must be synthetic and deterministic.

## 15. Change-size and review rules

Prefer small work-package-aligned changes. Separate:

- mechanical formatting;
- generated outputs;
- schema changes;
- behavior changes;
- dependency upgrades;
- documentation-only changes.

Security, tenancy, authorization, entitlement and migration changes require designated review under CODEOWNERS.

## 16. Stop conditions

Stop and create a decision request when:

- a required normative artifact is absent;
- two approved artifacts conflict;
- tenant ownership is ambiguous;
- authorization precedence is undefined;
- a change crosses the clean-room boundary;
- a license obligation is unclear;
- a destructive migration lacks recovery strategy;
- a product requirement would leak industry logic into the kernel;
- the requested scope exceeds the accepted work package.

## 17. Completion report

At completion, report:

- work-package and artifact IDs;
- files changed;
- contracts changed;
- checks run and results;
- evidence path;
- residual risks;
- decisions still required.
