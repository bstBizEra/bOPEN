# EVD-QUAL-001 — QUAL-P0-00 Common Qualification Contract Evidence

**Document ID:** EVD-QUAL-001
**Version:** 0.1
**Status:** Draft maker evidence; not independently accepted
**Owner:** Engineering Authority
**Issue date:** 2026-07-21
**Governing artifacts:** Program Goal v0.2; BOPEN-GOV-001 Draft; BOPEN-GOAL-001 Draft
**Dependent artifacts:** QUAL-P0-00; future technology and identity qualification proposals
**Decision references:** None effective
**Evidence ID:** EVD-QUAL-001
**Work package:** QUAL-P0-00
**Generated:** 2026-07-21T00:00:00+07:00
**Environment:** Windows; Python 3.13.12; Git 2.53.0.windows.1
**Source/base:** commit `82ed6b38b118aab14a9961c5d75a33e515cb136a`; tree `cad6b595fb74a70cc706a78d45778e15524aebd9`
**Maker:** Codex `/root/tech_qual_schema_blueprint`
**Checker:** Pending independent exact-SHA checker

## Procedure

1. Verify the isolated worktree, branch, exact base commit and clean starting state.
2. Create only the QUAL-P0-00 allowlisted schemas, catalog, validator, tests, work package, evidence and package-manifest snapshot.
3. Validate catalog digests and every `$ref` with no network fallback.
4. Exercise malformed paths, changed digests, unknown fields, unresolved/network refs, false authority claims, failed secret scans, missing direct evidence, commit/tree drift, self-review and invalid A→B→C storage commits.
5. Run focused tests, full test discovery and all repository security/governance validation commands.
6. Bind the final candidate commit/tree through an independent receipt after the maker commit exists.

## Expected result

All common schemas remain draft and closed; offline resolution, exact bindings, redaction, maker–checker separation and direct-parent evidence lineage fail closed. All non-authority flags remain false. No shared integration or runtime path changes.

## Actual result

Maker implementation is complete. Command counts are recorded in append-only verification notes; the successor commit/tree must be bound externally by a different checker because a committed evidence file cannot truthfully contain its own commit SHA. Independent review remains pending.

## Artifacts/logs

- `contracts/qualification/common/QUAL-P0-00-SCHEMA-CATALOG.json`
- `tools/validate_qualification_common.py`
- `tests/qualification/test_qualification_common.py`
- `docs/manifests/QUAL-P0-00-PACKAGE-MANIFEST.json`

No raw command log containing environment values or credentials is retained. Test fixtures are synthetic and ephemeral.

## Security and clean-room declaration

No upstream source was copied, no external schema was fetched, no credential was read or written, and no runtime/application/database path was changed. Schema resolution is offline and deny-by-default. The redaction contract prohibits production credentials and refuses evidence whose secret scan did not pass.

## Reviewer

Pending a different agent/session reviewing the exact maker SHA and tree.

## Independent verdict

`PENDING`. Passing maker tests is technical producer evidence only.

## Decision

No authority decision is made. QUAL-P0-00 remains a draft proposal; PG-G0, technology and identity decisions, merge, release, runtime activation and production implementation remain unauthorized.

## Residual risks

- The repository has no approved general-purpose Draft 2020-12 runtime validator dependency; the standard-library checker enforces the exact common structures and cross-document invariants but is not advertised as a complete JSON Schema engine.
- Common schema acceptance, specialist review and integrated routing remain pending.
- Later qualification packages must pin the exact accepted common catalog and cannot mutate it in place.

## Maker validation completion — 2026-07-21

Reason: record reproducible producer evidence without treating it as independent acceptance. Benefit of the prior pending record: it made no claim before the full validation chain ran. Expected outcome: the checker can reproduce the exact commands and distinguish the one integration-owned drift result from package-local failures.

- focused QUAL-P0-00 suite: 8 passed, 0 failed;
- full repository suite: 155 passed, 0 failed;
- common catalog and immutable package-manifest check: pass, 9 schemas;
- repository, contract, program-control, Program G0 report and PG-G0 authority report checks: pass;
- clean-room, secret, supply-chain and `git diff --check`: pass;
- aggregate `npm run validate`: reaches the historical `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` check and stops because that shared snapshot does not include the newly authorized package documents. Updating it is prohibited in this lane and reserved for QUAL-INTEG-001.

The aggregate routing result is therefore `HOLD_FOR_QUAL_INTEG_001`, not a QUAL-P0-00 contract/test failure. Independent exact-SHA review remains required.

## Append-only independent checker rework — 2026-07-22

**Reviewed maker commit:** `2e3faf6c6b310f60b5aa763fe3f29886307f3c41`
**Reviewed maker tree:** `cd39284e266a4b2acd3e27adfa799388b7d117c4`
**Disposition:** `REQUEST_CHANGES`

The checker required raw package byte hashes and counts, complete local JSON Pointer resolution, schema-reference cycle rejection, mandatory external storage commit/path for terminal receipts, exactly one parent for both B and C, and unambiguous aggregate validation wording.

Reason: normalized bytes and first-parent-only checks could conceal line-ending drift or merge ancestry, while unresolved fragments could leave a catalog structurally present but unusable. Benefit of the prior phase: the first candidate already denied network fallback, credential exposure and authority claims. Expected outcome: the successor fails closed on each newly identified integrity and lineage condition.

Aggregate `npm run validate` is explicitly `BLOCKED_UNTIL_QUAL_INTEG_001`. It is not passed, waived or converted into package acceptance. Updating the historical shared manifest remains prohibited in this lane.

## Successor maker verification — 2026-07-22

Reason: close the independent checker findings with reproducible adversarial evidence. Benefit of the first candidate: it established the bounded common-contract baseline and exposed the exact integrity gaps for correction. Expected outcome: the successor can be reviewed against raw bytes, complete offline reference resolution and strict direct-parent lineage without implying acceptance.

- focused QUAL-P0-00 suite: 12 passed, 0 failed;
- full repository suite: 159 passed, 0 failed;
- common catalog validation: pass, 9 schemas;
- repository, contract, program-control, Program G0 report and PG-G0 authority report checks: pass;
- clean-room, secret, supply-chain, Python compilation and `git diff --check`: pass;
- adversarial coverage now includes CRLF raw-byte drift, missing JSON Pointer targets, escaped pointer tokens and array-index rules, schema-reference cycles, terminal receipts without external storage binding, and merge commits at both B and C;
- aggregate `npm run validate`: `BLOCKED_UNTIL_QUAL_INTEG_001` at the stale historical `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` snapshot.

These are maker results only. The successor commit/tree and its external receipt storage commit/path remain subject to a different exact-SHA checker; no approval, gate, merge, release or runtime authority is asserted.
