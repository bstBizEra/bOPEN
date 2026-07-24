# EVD-SKEL-002 — SKEL-P0-01 Skeleton Maker Candidate (sole-maker, on accepted base')

**Status:** Maker candidate; draft; not accepted. Independent exact-SHA checker review pending.
**Work package:** `docs/work-packages/SKEL-P0-01.md` (Proposed; not accepted)
**Phase:** PG-P0 (preparation/review only)
**Sole maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Independent checker:** BST-Codex-Motor — must review the exact final candidate SHA.
**Base (base'):** `aab8bd9a94c0297da60830af934c66b330b47a81` — governed base + the human-accepted
MANIFEST-P0-01 reproducibility fix.
**References the human acceptance:** MANIFEST-P0-01 `ACCEPT_WORK_ITEM` by HUMAN-OPERATOR-001 at
predecessor `78e985b41ed8354f6525154d5cdfbe4b1052a2d5` (see `docs/work-packages/MANIFEST-P0-01.md`).

## Why sole-Claude on base' (Option B)

The human accepted MANIFEST-P0-01 separately, so the manifest reproducibility fix is inherited
from the accepted base and this SKEL candidate does not own a shared-governance-tool change. Every
byte of the SKEL delta is authored solely by Claude; the earlier operator replay (`700cf1e`)
carried Codex-authored bytes from conflict resolution and is therefore not eligible — it is
superseded by this fresh sole-maker build. `tools/validate_skeleton.py` is the maker's own
re-authored implementation (AST-based Python detection; fail-closed rule that a non-`.d.ts`
script in a kernel zone is runtime, closing the paren-less-arrow bypass found earlier).

## Delivered (additive on base')

Draft platform/event/audit contract shells; typed `@bopen/kernel-*` package roots; five
fail-closed test tiers with recursive guards; the re-authored skeleton validator wired into
`pnpm validate`; the reconciled `pnpm-lock.yaml` (canonical gate stays clean under
`--frozen-lockfile`); traceability, this evidence, append-only root-ledger events with GOV-P0-03
rebound, and the GOV-P0-02 document manifest rebound (now date-invariant, from base').

## Governance boundary

Additive only; the five root-control ledgers are exact byte-prefix extensions of base';
`docs/00-governance/**` and PG-G0 outcomes byte-unchanged; every shell `draft`; zero production
logic in kernel zones. No migration, merge, release, deployment, runtime activation, PG-P0
completion or PG-P1 transition is performed or authorized. Requires an independent BST-Codex-Motor
exact-SHA receipt and an attributable Human Engineering Authority `ACCEPT_WORK_ITEM`.
