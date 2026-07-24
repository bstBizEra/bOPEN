# MANIFEST-P0-01 — Deterministic document-manifest check (Proposal + demonstrated fix)

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Authorization source:** None yet. `tools/generate_document_manifest.py` is a governance validator outside SKEL-P0-01's allowed paths. This branch **demonstrates** the fix for operator disposition; accepting/merging it requires a separate operator decision and binding into `SCHEDULE-REGISTER` `PG-P0.work_item_refs`.
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Independent checker:** BST-Codex-Motor (must review the exact final SHA if accepted)
**Base:** governed PG-P0 `ACTIVE` substrate `29949f460345a55b8f8079cad802d6ca85cbe46e`

## Defect

`tools/generate_document_manifest.py` stamped `generated` with
`datetime.now(timezone.utc).date()`. Because `--check` required a byte-exact match of
the whole file including that field, the committed `GOV-P0-02-DOCUMENT-MANIFEST.json`
went **stale at every UTC-midnight rollover with zero content change**. A byte-frozen
candidate that verified green one day failed `pnpm validate` the next through no change
of its own.

This **breaks exact-SHA reproducibility** — the property the entire governance model
depends on. Observed directly this session: `ca92c7c` verified green on 2026-07-23 UTC
and failed `manifest snapshot stale` on 2026-07-24 UTC, all 292 records byte-identical.
It was independently re-derived by two conformance reviewers. (Note: the GOV-P0-03
package manifest is unaffected — it uses a fixed `"generated": "2026-07-23"`.)

## Fix (demonstrated on this branch)

In `--check` mode the checker now adopts the committed `generated` value before
comparing, so a stale date alone cannot fail the check while genuine content drift
(paths, titles, statuses, sha256, bytes, count) still does. Write mode uses
`newline="\n"` so the manifest is emitted LF-consistently on Windows (the secondary
`Path.write_text` CRLF defect). The `generated` field is retained as a human-facing
stamp; only its participation in the equality gate is removed.

Live proof: this branch's committed manifest is dated `2026-07-23`; on 2026-07-24
`pnpm validate` is **exit 0** with the fix (it would be red without it).

## In scope

`tools/generate_document_manifest.py` (the two-part fix), a regression test
(`tests/governance/test_document_manifest_reproducibility.py`), and documentation.

## Out of scope

Any manifest content change; changes to signed artifacts, registers or root surfaces;
merge, release, deployment, runtime; the GOV-P0-03 package manifest.

## Acceptance criteria

- `--check` is date-invariant yet still fails on any content drift (both proven by the
  regression test);
- full governed `pnpm validate` chain and complete test suite pass at the exact SHA;
- the ONLY document-manifest (`GOV-P0-02`) record changes are the documents this commit
  itself adds or changes — namely the added `docs/work-packages/MANIFEST-P0-01.md` and the
  changed `docs/CHANGELOG.md`; no other record (path/title/status/sha256/bytes) changes, and
  no signed byte changes (`docs/00-governance/**` and the five root ledgers unchanged);
- independent checker (Codex) accepts the exact final SHA;
- Human Engineering Authority records acceptance before merge.

## Rollback

Revert the isolated candidate branch; no signed, runtime or content state is touched.

## Completion record

Pending. This proposed record does not accept itself.

## Append-only human acceptance record — 2026-07-24

**Outcome:** ACCEPTED; effective for governed preparation lineage
**Accepted by:** HUMAN-OPERATOR-001 (Engineering Authority, DIRECT)
**Attestation:** "As HUMAN-OPERATOR-001, Engineering Authority, I ACCEPT_WORK_ITEM MANIFEST-P0-01 at exact SHA 78e985b41ed8354f6525154d5cdfbe4b1052a2d5. I have reviewed the evidence and take accountability for this acceptance."
**Accepted at:** 2026-07-24T16:22:25+07:00
**Accepted exact SHA:** 78e985b41ed8354f6525154d5cdfbe4b1052a2d5
**Accepted tree:** 85cdc3f3413e5ad301e8f3ff96bcb640f1e6d953
**Predecessor base:** 29949f460345a55b8f8079cad802d6ca85cbe46e
**Technical evidence:** Two independent `ACCEPT_EXACT_SHA` receipts; canonical frozen-install/validate gate; targeted reproducibility tests 2/2; full suite 148/148; clean worktree.

This record binds acceptance to the exact predecessor object above. It does not authorize merge, release, deployment, runtime activation, production implementation, PG-P0 completion, or PG-P1 transition. Any governed-base successor and subsequent SKEL rebuild MUST reference this acceptance record and remain separately reviewable.
