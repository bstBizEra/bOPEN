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

## Append-only scope amendment - 2026-07-24 - lockfile only (Option B, on accepted base')

Built on the governed-base successor `aab8bd9a94c0297da60830af934c66b330b47a81` (base +
the human-accepted MANIFEST-P0-01 reproducibility fix; predecessor acceptance
`78e985b41ed8354f6525154d5cdfbe4b1052a2d5`, HUMAN-OPERATOR-001). Because the manifest fix
is now inherited from the accepted base, this SKEL package does NOT own any change to
`tools/generate_document_manifest.py`. The only path beyond the original allowed set is:

- `pnpm-lock.yaml` — reconciled to include the two workspace importers for
  `packages/kernel-contracts` and `packages/kernel-testing`, so the canonical
  `pnpm validate` (with `--frozen-lockfile`) does not mutate the worktree.

Reason: a skeleton that adds workspace packages must reconcile the lockfile; this is a
direct consequence of SKEL's own additions. This amendment requires Human Engineering
Authority acceptance of the amended work package and references the MANIFEST-P0-01
acceptance record. It does not accept itself.

## Append-only human acceptance record — 2026-07-25

**Outcome:** ACCEPTED; effective for governed preparation lineage
**Accepted by:** HUMAN-OPERATOR-001 (Engineering Authority, DIRECT)
**Attestation:** "As HUMAN-OPERATOR-001, Engineering Authority, I authorize the SKEL-P0-01 pnpm-lock.yaml scope amendment and ACCEPT_WORK_ITEM SKEL-P0-01 at exact SHA f1eea272442a0587ab5843ba28c6ce47b91e1615. I have reviewed the evidence and take accountability."
**Accepted at:** 2026-07-25T00:00:00+07:00
**Accepted exact SHA:** f1eea272442a0587ab5843ba28c6ce47b91e1615
**Accepted tree:** a8d24bce1f0b6cd2993d0087c6da1111660259a7
**Base:** aab8bd9a94c0297da60830af934c66b330b47a81
**Technical evidence:** Independent `ACCEPT_EXACT_SHA`; canonical frozen-install/validate gate; skeleton validator 5/5; full suite 162/162; clean worktree.
**Scope authorization:** `pnpm-lock.yaml` amendment is authorized only for the two workspace importer entries required by `packages/kernel-contracts` and `packages/kernel-testing`.

This record binds acceptance to the exact reviewed predecessor above. It does not authorize merge, release, deployment, runtime activation, PG-P0 phase completion, production implementation, or PG-P1 transition.

## Current status (derived) — 2026-07-25

**Effective status: ACCEPTED / COMPLETE as a work item.** The immutable `**Status:** Proposed;
not accepted` header and the `## Completion record` line above reflect the work package's
authoring-time state and are preserved unchanged under the extend-only principle (headers are
never overwritten). The authoritative current state is the `## Append-only human acceptance
record — 2026-07-25` above: HUMAN-OPERATOR-001 (Engineering Authority) recorded `ACCEPT_WORK_ITEM`
for SKEL-P0-01 at exact SHA `f1eea272442a0587ab5843ba28c6ce47b91e1615`. This derived-status
section only points to that existing acceptance for legibility (Immune scan finding F-1,
2026-07-25); it records no new decision and grants no authority.

**Boundary (unchanged):** acceptance is of the SKEL-P0-01 *work item* only. It does not complete
the PG-P0 *phase* (still `ACTIVE`; completion is a separate human-signed schedule transition
governed by the draft `PG-P0-GATE-CONTRACT` and decision `DEC-0014`), and it does not authorize
merge, PG-P1, research gates G3–G7, or production implementation. `main` remains `a908bbe`.

*Note: the same header-vs-appendix legibility gap exists in other accepted packages
(MANIFEST-P0-01, GOV-P0-01, GOV-P0-04); a repo-wide reconciliation (a machine-checked rule plus
this derived-status convention) is a separate governance-legibility decision, tracked but not
performed here.*
