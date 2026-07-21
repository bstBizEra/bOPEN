# EVD-TECH-001 — Technology Qualification Contract Evidence

**Document ID:** EVD-TECH-001
**Version:** 0.1
**Status:** Draft maker evidence; not independently accepted
**Work package:** TECH-P0-01
**Generated:** 2026-07-22T00:00:00+07:00
**Source/base:** commit `a2fc4b1f907b17911ffbd3cb8e0992b806c90bb6`; tree `a5a63d2fb882939f176139c9f276a8d44faaf6d9`
**Maker:** Codex `/root/tech_qual_schema_blueprint`
**Checker:** Pending independent exact-SHA checker

## Procedure

1. Confirm the isolated worktree, branch, exact accepted QUAL-P0-00 base and allowlist.
2. Pin the raw digest of the common catalog and resolve all common and technology schema references offline.
3. Define only proposal scorecard, case, command-evidence and artifact-inventory contracts.
4. Enforce all 242 Program Goal coverage records, explicit limits and mandatory-failure-before-score ordering.
5. Exercise negative tenant declarations, operational evidence requirements, raw-byte drift, path escape, vendor selection and authority-flag adversarial cases.
6. Run focused/full test discovery, package-manifest, repository, governance and security checks.
7. Hand the exact final commit/tree to a different checker.

## Expected result

The package can validate the shape and semantics of a future bounded technology comparison while remaining unable to approve, freeze, select, merge, release, deploy or activate any technology.

## Actual result

Maker implementation is complete. The package contains contracts and validators only; it contains no qualification run, scorecard instance, case result, candidate ranking or technology decision.

## Security and clean-room declaration

No candidate source, vendor artifact, qualification output, credential, production data or runtime component is included. All test fixtures are synthetic. Catalog resolution is offline, artifact hashing uses exact raw bytes, and evidence paths are repository-relative and fail closed.

## Independent verdict

`PENDING`. Passing maker checks will be technical producer evidence only.

## Decision

No technology or vendor decision is made. Technology approval/freeze, Program G0 passage, production implementation, merge, release and runtime activation remain false and unauthorized.

## Residual risks

- The validator is a bounded semantic checker, not a complete JSON Schema implementation.
- No candidate has been executed or measured; future run evidence must be separately authorized and independently checked.
- Program Goal v0.2 remains Draft, so complete mapping demonstrates coverage discipline rather than goal acceptance or satisfaction.
- Shared validation routing and historical manifest integration remain outside this lane.

## Maker verification — 2026-07-22

Reason: record reproducible producer checks without converting them into independent acceptance. Benefit of the pre-verification record: it made no result claim before the full matrix ran. Expected outcome: an independent checker can reproduce the exact bounded checks and distinguish integration-owned drift from package defects.

- focused TECH-P0-01 suite: 10 passed, 0 failed;
- full repository suite: 169 passed, 0 failed;
- technology catalog: 4 local schemas plus the exact 9-schema common catalog resolved offline;
- Program Goal coverage invariant: all 242 catalog items required exactly once with explicit limits;
- repository validator: pass, 27 mandatory paths;
- contract validator: pass, 33 machine-readable contracts;
- program-control, Program G0 report and PG-G0 authority report checks: pass without asserting gate passage;
- clean-room, secret, supply-chain, Python compilation and `git diff --check`: pass;
- aggregate `npm run validate`: `BLOCKED_UNTIL_QUAL_INTEG_001` at the stale historical `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json`.

The aggregate blocker is not a TECH-P0-01 schema or test failure, but it is also not waived or described as passing. Updating that shared snapshot is prohibited here. The final successor SHA/tree still requires an independent checker.

## Append-only checker rework evidence — 2026-07-22

**Reviewed maker commit:** `1673684b977b2a74a87ee1ffbe044c407e4cbd0e`
**Reviewed maker tree:** `66af315b644208d24dda8e3f1ea51c1fbdb3fce7`
**Disposition:** `REQUEST_CHANGES`

The successor resolves every command evidence reference as a normalized existing repository-bounded path, validates the referenced command document, and requires exact qualification-run, candidate and case bindings. Case and command artifact digest bindings are validated against raw files and must exactly match a supplied validated inventory record. DIRECT Program Goal coverage must cite a case whose `requirement_ids` contains that exact requirement.

Adversarial coverage now includes traversal, missing command documents, malformed or missing artifact bindings, run/candidate/case mismatch, inventory mismatch and irrelevant DIRECT cases. The focused successor suite passes 13/13. The unchanged repository baseline plus the expanded suite totals 172 tests; direct repository, contract, program-control, report, clean-room, secret, supply-chain, compilation and diff checks pass.

Aggregate `npm run validate` remains `BLOCKED_UNTIL_QUAL_INTEG_001` at the historical shared manifest. These maker results do not establish independent acceptance or any technology, gate, merge, release or runtime authority.
