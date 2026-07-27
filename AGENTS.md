# agents.md — bOPEN Antigravity Team Adapter

Canonical authority: `AGENTS.md` and `docs/00-governance/BOPEN-GOV-001_v0.1.md`.

## Team

- Governance Lead
- Product and Requirements Analyst
- Platform Architect
- Security and Tenant-Isolation Architect
- Backend Maker
- Portal and Experience Maker
- Test and Conformance Verifier
- Evidence Auditor
- Release Coordinator

## Operating pipeline

```text
/intake
→ /specify
→ /architecture
→ /authorize
→ /implement
→ /verify
→ /evidence
→ /review
→ /release-readiness
```

Use `.agents/skills/` for reusable procedures and `.agents/workflows/` for pipeline
commands. Generated plans, screenshots, browser recordings and task lists are supporting
artifacts; they are not acceptance evidence until linked to requirements and checked.

## Clean-room controls

- Review governed candidates in a fresh isolated worktree.
- Bind claims to exact commit, tree, file bytes, commands and evidence.
- Do not use a dirty checkout as acceptance evidence.

## Architectural invariants

- The platform kernel remains module-neutral and tenant context is explicit.
- Registered interfaces and contracts are the only cross-module integration seams.
- Preparation, checking, acceptance, activation and release remain separate actions.

## Stop conditions

- Stop on unresolved conflicts, stale manifests, missing evidence, unknown identity or failed validation.
- Stop before merge, activation, release, deployment or production mutation unless a human authority has explicitly authorized that action.

## Tenant data safety

- Missing tenant context and cross-tenant access must fail closed.
- Never expose plaintext credentials or unscoped tenant data in logs, evidence or handoffs.
- Tenant-isolation claims require negative tests and independent verification.

## Shared skill registry

All harnesses MUST discover reusable bOPEN procedures from `.agents/skills/` and resolve
their lifecycle metadata through `docs/registers/skill-registry.json`. Runtime-specific
or user-scoped installations are adapters to that canonical repository package and MUST
NOT silently fork its contents. Skill availability never grants permission or approval;
candidate and inactive skills remain advisory and may not self-promote.

Every agent must inherit the same tenant-isolation, credential, worktree, maker–checker,
evidence and release constraints defined in root `AGENTS.md`.
