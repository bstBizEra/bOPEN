# SKEL-P0-01 — bOPEN Repository Skeleton (PG-P0 Preparation Scope)

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Authorization source:** SIGNING-PASS-5 PG-P0 phase opening (preparation/review scope); BOPEN-BOOT-001 §3 (draft structures, interfaces, schemas marked draft, test harnesses and documentation are allowed before the implementation gate)
**Accepted by/at:** Pending attributable Human Engineering Authority disposition
**Maker:** Claude (BST-SA Motor worker agent)
**Independent checker:** BST-Codex-Motor (must review the exact final SHA)
**Phase:** PG-P0
**Expiry:** 2026-08-21T00:00:00+07:00

## Objective

Populate the clean bOPEN zones with a governed, fail-closed skeleton: directory structure, scoped agent instructions, draft contract shells traced to the normative drafts, and test-harness scaffolding — with zero production business logic.

## In scope

1. **Structure:** `apps/`, `services/`, `packages/`, `contracts/`, `sdk/`, `infrastructure/`, `tools/`, `tests/` populated with README and scoped `AGENTS.md` per zone (stricter rules than root; no weakening).
2. **Contract shells (all marked `draft`):** platform-kernel surfaces traced one-to-one to BOPEN-TENANT-001 (tenant/organization/membership/context), BOPEN-AUTHZ-001 (authorization decision interface), BOPEN-ENT-001 (entitlement), BOPEN-MOD-001 (module manifest/capability), BOPEN-PARTY-001 (party), plus event/audit envelope shells per BOPEN-ARCH-001. Each shell carries artifact ID, version, `status: draft`, owner and traceability links; none is a stable dependency.
3. **Package skeletons:** empty typed package roots under `packages/` (e.g., kernel-contracts, kernel-testing) with build/lint/test wiring but no domain logic.
4. **Test harness:** `tests/` tiers for future unit/contract/integration/tenant-isolation/authorization suites, each with a placeholder that fails closed if a real implementation appears without its required negative tests (guard tests, not business tests).
5. **Validation:** extend `pnpm validate` with a skeleton validator asserting: no business logic in kernel zones (import/AST heuristics), every contract shell marked draft with required control fields, scoped `AGENTS.md` present per populated zone.
6. **Documentation and traceability:** DOCUMENT-STATUS, manifests, evidence (`EVD-SKEL-001`), ledger appends with package-manifest rebind in the same commit.

## Out of scope

Production business logic, migrations, runtime configuration, secrets, deployments; changes to signed PG-G0 outcomes, dockets, registers or root-ledger genesis; research-zone changes; normative artifact approval (drafting proceeds under separate packages).

## Allowed paths

`apps/`, `services/`, `packages/`, `contracts/`, `sdk/`, `infrastructure/`, `tools/validate_skeleton.py`, `tests/`, `docs/` (status/manifest/evidence/work-package/ledger surfaces), `package.json` (validate chain only).

## Prohibited paths

`research/upstream/`, signed dockets and binding inventories, root-ledger genesis bytes, `docs/00-governance/registers/` contents (read-only), secrets.

## Acceptance criteria

- Every skeleton artifact is additive and marked draft; no signed byte changes;
- skeleton validator, full repository validation chain and complete test suite pass at the exact candidate SHA;
- zero production logic detectable in kernel zones;
- every contract shell traces to a named normative draft artifact and requirement IDs where they exist;
- ledgers extended append-only with manifest rebound atomically;
- independent checker (Codex) accepts the exact final SHA;
- Human Engineering Authority acceptance recorded before the skeleton is treated as a stable base.

## Risks and rollback

Risk: skeleton shells mistaken for approved contracts. Control: mandatory `draft` status, fail-closed validator, no version above 0.x. Risk: scope creep into implementation. Control: skeleton validator's business-logic guard plus checker review. Rollback: revert the isolated candidate branch; no signed or runtime state is touched.

## Completion record

Pending. This proposed record does not accept itself.

## Append-only scope amendment - 2026-07-24 - canonical reproducibility (maker, in response to independent findings)

An independent BST-Codex-Motor exact-SHA review of candidate `0cf5f9cd` found two
reproducibility blockers that cannot be resolved within the original allowed paths:

1. The canonical gate `pnpm validate` mutated `pnpm-lock.yaml` (added workspace importer
   entries for the new `packages/kernel-*` projects), so a python-only run could not prove
   a clean canonical gate.
2. `tools/generate_document_manifest.py` stamped `generated` from wall-clock UTC, so a
   byte-frozen candidate went stale at UTC-midnight rollover — breaking exact-SHA
   reproducibility.

**Reason:** a repository skeleton that adds workspace packages cannot be canonically
reproducible without (a) a reconciled lockfile and (b) a date-invariant manifest check.
Both are prerequisites of acceptance criterion "full repository validation chain passes at
the exact candidate SHA." **Benefit of the old phase:** the original narrow paths kept the
first candidates minimal and surfaced these two controls through independent review rather
than assumption. **Expected outcome:** one canonically-reproducible sole-Claude candidate
whose `pnpm validate` is clean and date-stable.

**Allowed paths extended (append-only) to include:**
- `pnpm-lock.yaml` — reconciled to the workspace so the canonical `pnpm validate` does not
  mutate it (verified stable across repeated runs).
- `tools/generate_document_manifest.py` — the manifest-`--check` reproducibility fix
  (adopt the committed `generated` date; write LF), integrating the MANIFEST-P0-01 fix.
- `tests/governance/test_document_manifest_reproducibility.py` — regression test for it.

This amendment is itself part of the proposal and requires Human Engineering Authority
acceptance of the amended work package. It does not accept itself.
