# SKEL-P0-01 — bOPEN Repository Skeleton (PG-P0 Preparation Scope)

**Version:** 0.1  
**Status:** Proposed; not accepted  
**Owner:** Engineering Authority  
**Authorization source:** SIGNING-PASS-5 PG-P0 phase opening (preparation/review scope); BOPEN-BOOT-001 §3  
**Accepted by/at:** Pending attributable Human Engineering Authority disposition  
**Maker:** Claude (BST-SA Motor worker agent), as named by the proposed package  
**Independent checker:** BST-Codex-Motor; must review the exact final SHA  
**Phase:** PG-P0  
**Expiry:** 2026-08-21T00:00:00+07:00

## Objective

Populate the clean bOPEN zones with a governed, fail-closed skeleton: directory structure, scoped agent instructions, draft contract shells traced to normative drafts, and test-harness scaffolding—with zero production business logic.

## In scope

1. `apps/`, `services/`, `packages/`, `contracts/`, `sdk/`, `infrastructure/`, `tools/`, and `tests/` receive README and scoped `AGENTS.md` controls.
2. Eleven platform-kernel contract shells remain open, non-enforcing, version 0.x, `status: draft`, and non-stable.
3. Private typed package roots `@bopen/kernel-contracts` and `@bopen/kernel-testing` expose no runtime entry point or domain type.
4. Unit, contract, integration, tenant-isolation, and authorization tiers contain fail-closed guard tests.
5. `pnpm validate` chains package wiring, skeleton validation, and the complete guard harness.
6. Document status, traceability, evidence, package manifest, and a non-root append-only preparation ledger are included.

## Out of scope

Production business logic, migrations, runtime configuration, secrets, deployments, signed PG-G0 outcomes, dockets, binding inventories, governance-register contents, root-ledger genesis, research-zone changes, and normative approval.

## Allowed paths

`apps/`, `services/`, `packages/`, `contracts/`, `sdk/`, `infrastructure/`, `tools/README.md`, `tools/AGENTS.md`, `tools/validate_skeleton.py`, `tests/`, `docs/`, and root `package.json` for the validate chain only.

## Prohibited paths

`research/upstream/`, signed dockets and binding inventories, root-ledger genesis bytes, `docs/00-governance/registers/`, and all secret-bearing paths.

## Acceptance criteria

- Every artifact is additive, draft-marked, 0.x, and non-stable.
- The full validation chain and guard suite pass for the exact candidate tree.
- No production logic is detected in kernel zones.
- Every contract shell traces one-to-one to a named normative draft artifact; unknown requirement identifiers are not invented.
- The preparation ledger binds the package manifest atomically without claiming root-governance authority.
- BST-Codex-Motor accepts the exact final SHA.
- Attributable Human Engineering Authority acceptance is recorded before stable use.

## Risks and rollback

**Draft mistaken for stable contract:** controlled by mandatory draft metadata, 0.x versions, open shells, consumer warnings, and validator rejection.  
**Scope creep into implementation:** controlled by runtime-extension and AST/import heuristics plus five negative-test guards.  
**Governance overclaim:** controlled by proposed/draft status and explicit separation of preparation, checker, and human acceptance.  
**Rollback:** delete or revert the isolated candidate branch; no runtime or signed state is touched.

## Completion record

Candidate preparation is complete only when `EVD-SKEL-001`, the package manifest, and the repository-change ledger validate at the candidate tree. Independent checker and Human Engineering Authority dispositions remain pending and cannot be self-recorded by this package.

**Base commit:** `9a80f9d042f1ed176c9939bae57953443d0c5964`  
**Candidate branch:** `agent/skel-p0-01-repository-skeleton`
