# EVD-QUAL-INTEG-001 — Non-Merge Review Candidate Evidence

**Document ID:** EVD-QUAL-INTEG-001
**Version:** 0.1
**Status:** Draft maker evidence; independent review pending
**Owner:** Engineering Authority
**Issued:** 2026-07-22
**Work package:** QUAL-INTEG-001
**Environment:** Windows / `C:\laragon\www\bopen-worktrees\qual-integ-001-review-candidate`
**Base commit/tree:** `82ed6b38b118aab14a9961c5d75a33e515cb136a` / `cad6b595fb74a70cc706a78d45778e15524aebd9`
**Maker:** `/root/gov_p0_03_preflight`
**Checker:** Pending different-agent exact-SHA review
**Authority effect:** None

## Procedure

Replay exact accepted commits without merge or history rewrite, reconcile shared PR7 paths by semantic union, preserve all package-local bytes, bind historical manifests to source Git objects, generate a separate current aggregate manifest, and run the aggregate validation DAG.

## Source-to-replay mapping

The machine-readable mapping and stable patch IDs are in `docs/manifests/QUAL-INTEG-001-INTEGRATION-MANIFEST.json`. GOV-P0-03, QUAL-P0-00, TECH-P0-01 and QUAL-P0-02 preserve full stable patch IDs. RES-P0-05 preserves a stable patch ID after excluding the ten shared PR7/PR8 paths for `8bc3e2a`, and after excluding only historical `docs/DOCUMENT-MANIFEST.json` for the three later commits.

TECH-P0-01 and QUAL-P0-02 are sibling source chains whose first commits both descend from QUAL-P0-00 `a2fc4b1`; their linear replay order does not convert identity qualification into a technology child or approval dependency.

## Conflict resolution ledger

| Source commit | Path | Resolution |
|---|---|---|
| 8bc3e2a | `.gitea/workflows/governance.yml` | Union: retain full-history checkout, program/docket/snapshot checks and add G3 validation. |
| 8bc3e2a | `.github/workflows/bootstrap-governance.yml` | Same semantic union as Gitea workflow. |
| 8bc3e2a | `.gitignore` | Retain program readiness exceptions and add research G3 readiness. |
| 8bc3e2a | `docs/CHANGELOG.md` | Preserve both histories and append G3 design entry. |
| 8bc3e2a | `docs/DOCUMENT-MANIFEST.json` | Preserve exact PR8 historical bytes; redirect final PR7 bytes to `RES-P0-05-DOCUMENT-MANIFEST.json`. |
| 8bc3e2a | `docs/DOCUMENT-STATUS.md` | Retain B0-B6/B7 state and add G3 design state; no gate claim. |
| 8bc3e2a | `docs/decisions/DECISION-REGISTER.md` | Retain DEC-0010/0012 and add proposed, ineffective DEC-0011. |
| 8bc3e2a | `docs/evidence/EVIDENCE-INDEX.md` | Union GOV and RES evidence rows plus historical supersession note. |
| 8bc3e2a | `package.json` | Union validation and report command surfaces without running writers in validation. |
| 8bc3e2a | `docs/TRACEABILITY-MATRIX.md` | Git auto-merge preserved both GOV and RES rows; subsequently asserted by integration tests. |
| 952e9b3/f501cdc/4b1cb21 | `docs/DOCUMENT-MANIFEST.json` | Preserve historical PR8 bytes; retain non-manifest patch equivalence and exact final PR7 manifest as immutable RES snapshot. |

## Historical manifest preservation

- `docs/DOCUMENT-MANIFEST.json` remains byte-identical to the PR8 `82ed6b3` Git object.
- `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` remains byte-identical to its `82ed6b3` Git object.
- Accepted GOV/QUAL/TECH/identity package manifests remain byte-identical to their accepted source heads.
- `docs/manifests/RES-P0-05-DOCUMENT-MANIFEST.json` is byte-identical to `4b1cb21:docs/DOCUMENT-MANIFEST.json`.

## Expected result

Aggregate composition and all package controls validate, tests exceed the pre-integration floor of 222, and the candidate remains Draft, Inactive, non-merge and non-effective.

## Actual result

Pending final maker execution. No unexecuted test or review is represented as passed.

### Append-only maker execution record â€” 2026-07-22T01:32:30+07:00

**Source:** Explicit user-level QUAL-INTEG-001 integration-maker instruction
**Agent ID:** `/root/gov_p0_03_preflight`

- Portable raw-byte stable patch-ID validation: PASS for all twelve source/replay mappings. Nine initially recorded IDs produced through a PowerShell text pipeline were rejected and replaced with canonical byte-preserving values before evidence finalization.
- Immutable manifest index: PASS, 10 exact records with normalized non-symlink paths, exact key/mode enforcement and ordered prefix chaining.
- Package validation: PASS for GOV-P0-03 root controls, QUAL-P0-00 common, TECH-P0-01 technology and QUAL-P0-02 identity contracts; package-local raw bytes match their accepted source heads.
- Repository, contract, program-control, Program G0 report, PG-G0 authority docket and G3 design validation: PASS. G3 state remains `DESIGN_READY_FOR_AUTHORITY_REVIEW`; runtime, G3 and production flags remain false.
- Security validation: clean-room PASS; secret scan PASS; supply-chain PASS; `git diff --check` PASS.
- Tests: contracts 41/41 PASS; governance 144/144 PASS; qualification 45/45 PASS; complete suite 230/230 PASS. The 8 QUAL-INTEG-001 tests increase the pre-integration floor of 222 to 230.
- `npm run validate`: PASS using validator/report checks only; research report and inventory writers were not executed by validation.

This is maker evidence for independent exact-SHA review. It does not accept the package or authorize technology/provider selection, qualification execution, gate passage, merge, release, runtime, deployment or production implementation.

### Append-only REQUEST_CHANGES rework 001 record â€” 2026-07-22

**Source:** QUAL-INTEG-001 independent review REQUEST_CHANGES instruction
**Agent ID:** `/root/gov_p0_03_preflight`

Blocker 1 is addressed by create-once manifest writes: no write is possible without explicit `--aggregate`; canonical, existing, historical and indexed targets are denied; only a previously nonexistent normalized versioned path directly under `docs/manifests/` is eligible. The two package scripts that exposed canonical and GOV-P0-02 overwrite commands were removed. Check modes remain read-only.

Blocker 2 is addressed by binary Git-object history validation. The validator locates index genesis, reads every committed blob without text conversion, requires each successor and pending worktree version to contain the prior blob as an exact prefix, and requires the suffix to contain valid LF-only JSONL objects. Adversarial temporary-repository tests cover valid append, truncation, prior-line mutation, reorder, CRLF and malformed append rejection.

Final successor aggregate, readiness record, test totals, validation results and exact commit/tree are recorded by the rework completion record below. This rework does not modify any prior manifest or authority state.

### Append-only rework 001 maker completion â€” 2026-07-22

- Create-once generator adversarial tests: 4/4 PASS for canonical, indexed historical, existing target and missing-`--aggregate` refusal.
- Binary index-history adversarial tests: 6/6 PASS for valid append acceptance and truncation, mutation, reorder, CRLF and malformed append rejection.
- Manifest index: PASS with the original 10 lines preserved as an exact raw-byte prefix and two precheck records appended.
- Contracts: 41/41 PASS. Qualification: 45/45 PASS. Governance: 154/154 PASS. Complete suite: 240/240 PASS.
- `npm run validate`: PASS across repository, contracts, program controls, reports, root/common/technology/identity packages, G3 design, manifest history, integration validation, clean-room, secret and supply-chain checks.
- `git diff --check`: PASS. No research report/inventory writer, runtime, merge or push was executed.

The final rework aggregate is a new create-once `REWORK-002` snapshot appended to the index after this evidence. Independent exact-SHA review remains required; all authority and activation flags remain false.

## Security and clean-room declaration

No credentials, personal data, upstream source, runtime execution, application/service/package/infrastructure change, migration, deployment or production activation is introduced by this integration package.

## Independent verdict

Pending exact final commit and tree. Technical acceptance cannot authorize merge, technology selection, gate passage, release, runtime or production implementation.

### Append-only current-tree readiness projection evidence - 2026-07-22

**Source:** QUAL-INTEG-001 REQUEST_CHANGES rework instruction
**Agent ID:** `/root/gov_p0_03_preflight`

- Historical evidence preservation: `PG-G0-AUTH-001.json` remains 12,851 bytes with SHA-256 `255fd6ae1b88de89b5a89d9575c5e97b4417115b4985a18426414b8003773795`; `program-g0-authority-readiness.json` remains 1,451 bytes with SHA-256 `d444da84d8ed06c5bc1852f0c581d1ba63a27962d3f56e402dcc3e2b5dbe242a`.
- Bound/current distinction: the historical docket remains bound to commit/tree `c893062c197e74c15214e5ce1c425b9e9ed8002f` / `f336976981c9b7e95c96ec8289589e53c1ac506c`; the technical projection evaluates authorized base commit/tree `4a98cb45748ded2b209786bcb9242664aa0795aa` / `8900b871e1f436d5ee21919764a31f955f42d5bf` and verifies that commit remains an ancestor of the candidate.
- Projection result: 18 historical blockers retained in original order; 1 classified `RESOLVED_TECHNICALLY_IN_CURRENT_TREE`; 17 remain active. Human dispositions are never machine-resolved, unknown blockers default active, and CI/PR prose is not authority evidence.
- Focused negative suite: 10/10 PASS, covering missing, wrong-case, symlink and malformed root controls; human-only blockers; unknown blockers; CI/PR non-authority; all-false authority flags; false readiness while human blockers remain; and closed object boundaries.
- Complete suite: 250/250 PASS. Contract validation: 45 machine-readable contracts PASS. Repository and QUAL integration validators: PASS. `npm run validate`: PASS. Clean-room, secret, supply-chain and `git diff --check`: PASS.

These are maker technical results only. Qualification was not executed, no technology or identity provider was approved, and no gate, merge, release, runtime activation or production implementation was authorized.

The current projection is retained through an exact `.gitignore` exception. The create-once `REWORK-003` pre-final aggregate and final `REWORK-004` aggregate are separately indexed; neither prior snapshot nor any existing index line was rewritten.
