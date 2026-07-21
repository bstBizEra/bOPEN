# TECH-P0-01 — Technology Qualification Proposal Contracts

**Version:** 0.1
**Status:** Drafting authorized; not accepted
**Owner:** Engineering Authority
**Dependencies:** independently accepted QUAL-P0-00 at `a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6`; Program Goal v0.2 Draft
**Authorization:** Explicit bounded user authorization for TECH-P0-01 drafting only
**Maker:** Codex `/root/tech_qual_schema_blueprint`
**Checker:** Independent exact-SHA checker pending
**Branch/worktree:** `codex/TECH-P0-01-technology-qualification` / `C:\laragon\www\bopen-worktrees\tech-p0-01-technology-qualification`
**Base SHA/tree:** `a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6` / `a5a63d2fb882939f176139c9f276a8d44faaf6d9`

## Objective

Define offline, deterministic contracts for comparing technology candidates without running a qualification, selecting a vendor, approving or freezing a stack, passing a gate, or authorizing merge, release, deployment or runtime activation.

## In scope

- candidate scorecard, case result, command evidence and raw-byte artifact inventory schemas;
- a digest-pinned offline catalog importing the exact QUAL-P0-00 catalog;
- complete mapping of all 242 Program Goal catalog items with an explicit coverage level and limitation;
- mandatory tenant RLS, pooled isolation and trusted-context negative case declarations;
- mandatory observability, transactional outbox, recovery and supply-chain evidence categories;
- fail-before-score ordering, deterministic raw-byte package integrity and adversarial tests;
- bounded maker evidence and package manifest.

## Out of scope

Qualification execution or result artifacts; benchmark claims; candidate or vendor selection; stack approval or freeze; architecture/identity decisions; shared indexes, registers, CI, package files or canonical manifests; application, database, infrastructure, migration, deployment or runtime changes.

## Allowed paths

```text
contracts/qualification/technology/candidate-scorecard.schema.json
contracts/qualification/technology/case-result.schema.json
contracts/qualification/technology/command-evidence.schema.json
contracts/qualification/technology/artifact-digest-inventory.schema.json
contracts/qualification/technology/TECH-P0-01-SCHEMA-CATALOG.json
docs/work-packages/TECH-P0-01.md
docs/evidence/EVD-TECH-001-technology-qualification.md
docs/manifests/TECH-P0-01-PACKAGE-MANIFEST.json
tools/validate_technology_qualification.py
tests/qualification/test_technology_qualification.py
```

## Acceptance criteria

- the exact common catalog and every local/imported schema reference resolve offline through pinned SHA-256 digests;
- all four schemas remain closed Draft 2020-12 proposal contracts;
- every one of the 242 Program Goal items appears exactly once in a scorecard coverage map and has an explicit coverage limitation;
- direct coverage requires case references; partial, deferred and uncovered mappings cannot imply passage;
- RLS, pooled-tenant and active-context negative cases are mandatory and explicitly declared negative;
- observability, outbox, recovery and supply-chain cases require command plus artifact evidence;
- any mandatory failure or non-execution stops evaluation before weighted scores; weights total 100 only after mandatory passage;
- every authority, gate, technology approval/freeze, identity, merge, release and runtime flag remains false;
- package hashes and byte counts use exact `Path.read_bytes()` bytes;
- focused/full tests, repository/security checks and exact-SHA independent review pass.

## Stop conditions

Stop if work creates a real qualification output, ranks or selects a candidate, implies technology approval/freeze, omits a Program Goal item or limitation, scores past a mandatory failure, accesses a credential, changes a shared/runtime surface, or sets any authority/effect flag true.

## Risks and rollback

JSON Schema alone cannot establish cross-document completeness, weighted ordering, raw byte integrity or Git authority. The standard-library semantic validator supplies those checks but is not a general JSON Schema runtime. Rollback is deletion of this isolated branch/worktree; no protected branch or runtime is changed.

## Extend-only change note

Reason: technology comparisons require a single reproducible proposal grammar before any candidate is exercised. Benefit of QUAL-P0-00: exact bindings, offline resolution, maker-checker separation and non-authority controls are reused rather than forked. Expected outcome: later authorized runs can produce comparable evidence while mandatory failures and incomplete Program Goal coverage remain fail-closed.

## Completion record

Maker implementation and package-local verification are complete. Focused tests pass 10/10 and full repository test discovery passes 169/169. Independent exact-SHA technical review and attributable Human Engineering Authority acceptance remain required. This package cannot qualify a technology or accept itself.

Aggregate `npm run validate` is `BLOCKED_UNTIL_QUAL_INTEG_001` at the integration-owned historical `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json`. That shared snapshot is prohibited in this lane; the result is not waived or reported as aggregate acceptance.

## Append-only checker rework — 2026-07-22

The first maker commit `1673684b977b2a74a87ee1ffbe044c407e4cbd0e` received `REQUEST_CHANGES`. Its scorecard validator required command and artifact references to be present but did not resolve the command documents, bind them to the run/candidate/case, reconcile artifact bindings with the supplied inventory, or prove that a DIRECT mapping cited a case containing the exact requirement.

Reason: presence-only references could permit unrelated, missing or path-escaped evidence to support a proposal. Benefit of the first candidate: offline catalogs, mandatory-case ordering, complete Program Goal enumeration and non-authority controls were already established. Expected outcome: the successor treats scorecard, cases, commands, artifacts and inventory as one closed evidence graph and rejects irrelevant DIRECT coverage.

This rework remains contract-only. It creates no qualification run, candidate score, vendor choice, stack approval/freeze or authority effect.
