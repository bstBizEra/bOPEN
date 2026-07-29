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

**GATE G7 CLEARED (EVD-RES-001-G7)**. Normative specifications `BOPEN-REQ-001`, `BOPEN-ARCH-001`, `BOPEN-TENANT-001`, and `BOPEN-AUTHZ-001` are **Approved**. 

Production kernel implementation for **Phase 1 Platform Kernel Vertical Slice** (principal, tenant, membership, context, authorization, and audit) in `packages/` and `services/` is **AUTHORIZED**. All code must satisfy deny-by-default access, PostgreSQL Row-Level Security, and contract test fixtures.

### 3.1 Phase 2 — contract freeze only, implementation held

`BOPEN-IDP-001` is **Approved for Phase 2 implementation** and supersedes `BOPEN-IDP-001-DRAFT`.
`BOPEN-P2-001` is bound as the accepted Phase 2 work package governing `MILE-2.1`..`MILE-2.5`.

**Phase 2 code mutation is NOT yet authorized.** Per `BOPEN-P2-001` §26, the disposition is
*"APPROVED FOR PHASE 2 CONTRACT FREEZE; IMPLEMENTATION HOLD UNTIL ENTRY GATE"*, and §1 states
coding begins only after the entry gate, ADRs, contracts, token/security profile, test matrix,
baseline and authority scope are frozen. `BOPEN-IDP-001` §21 makes its own effectiveness
conditional on the same ADR resolution.

Before any agent creates `membership.py`, `idp_bridge.py`, `context.ts`, `context.py` or other
Phase 2 sources, the following must be recorded:

- `ADR-P2-001`..`ADR-P2-010` resolved;
- `D-P2-001`..`D-P2-015` resolved or explicitly classified non-blocking by the Engineering Authority (§21);
- WP-P2-00 baseline receipt and named maker, independent checker, security reviewer and completion authority;
- the §23 entry-gate decision recorded as **GO** or **GO WITH RECORDED CONDITIONS**.

Implementing ahead of this gate silently resolves reserved architecture decisions by code default
and is prohibited. Phase 2 completion does not authorize production activation.

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

1. Read the root and all scoped `AGENTS.md` files and [`docs/00-governance/AGENT-ALIGNMENT.md`](docs/00-governance/AGENT-ALIGNMENT.md).
2. Identify the accepted work-package ID.
3. Identify governing artifact, requirement and ADR IDs.
4. Inspect existing contracts and tests.
5. Make the smallest coherent change.
6. Add or update tests and evidence.
7. Update documentation and traceability.
8. Run repository validation.
9. Report changed files, checks, residual risks and blocked decisions.

A change without traceability is incomplete.

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

## 18. Repository-local skill registry

Canonical bOPEN skills live under `.agents/skills/<skill-name>/`. Register only
packages that contain a validated `SKILL.md`; harness-specific or user-global
copies are adapters and must not silently replace repository-local bytes.

Skill installation grants no approval, activation, merge, release, deployment
or production authority.

| Skill | Entrypoint | Status | Operating boundary |
| --- | --- | --- | --- |
| `git-provenance-audit` | `.agents/skills/git-provenance-audit/SKILL.md` | Installed | Read-only provenance assurance; it does not mutate Git or forge state and cannot create authority. |

## 19. Multi-LLM and multi-agent execution guidelines

This repository supports collaborative execution across multiple AI models and agent runtimes (e.g. Gemini, Claude, Codex, Kimi, DeepSeek). All participating engines shall observe these rules:

1. **Single-workspace execution policy**: All agents shall perform edits, tests, and commits directly in the primary workspace on an explicit target branch. Agents shall not spin up uncoordinated parallel Git worktrees unless explicitly authorized by governance.
2. **Prohibition of transient handoff artifacts**: Agents shall not write untracked coordination files (e.g., `/HANDOFF-*-TO-CODEX.md`) to the repository root. All progress, decisions, and handoffs must be recorded in governed documentation (`docs/CHANGELOG.md`, `docs/DOCUMENT-MANIFEST.json`, or accepted work-package logs).
3. **Model role specialization**:
   - **Gemini / Antigravity**: Architecture synthesis, system design, initial planning, and workspace-wide governance audit.
   - **Claude**: Complex multi-file refactoring, deep unit test suite development, and contract validation.
   - **Codex**: Precise logic implementation, script execution, and verification tool maintenance.
   - **Kimi / DeepSeek**: Long-context research, upstream source inspection, and documentation synthesis.
4. **Mandatory validation engine**: Every agent—regardless of engine or harness—must run `python tools/validate_repository.py` and `python tools/check_clean_room.py` before marking any work package as complete.
5. **No verification deadlocks**: Agents shall not invent self-referential gate assertions or refuse valid transitions over unverified metadata assumptions. If a gate check fails, the agent must fix the underlying logic or log an explicit decision request.
