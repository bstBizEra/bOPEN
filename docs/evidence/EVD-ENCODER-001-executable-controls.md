# EVD-ENCODER-001 — Executable Phase-Transition Controls

**Status:** Maker candidate; draft; not accepted. Independent exact-SHA review pending.
**Work package:** `docs/work-packages/ENCODER-P0-01.md`
**Sole maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Independent checker:** BST-Codex-Motor
**Base:** `29949f460345a55b8f8079cad802d6ca85cbe46e`

## What this closes

The independent review `cf4a0e2` found the PG-P0 completion controls documented but not
executable (`NOT_READY_FOR_SIGNATURE`). This candidate implements and tests them:

- `tools/apply_phase_transition.py` — Stage-2 encoder (canonicalization, compare-and-swap
  anti-replay, single-use consumption, deterministic transform, invariant enforcement,
  idempotency outcomes, atomic receipt, independent recompute).
- `tests/governance/test_phase_transition.py` — 10 tests proving each control.

## Verification (maker, at the candidate SHA)

- `python -m unittest tests.governance.test_phase_transition` — 10/10 pass.
- Behavioural proof: apply → `APPLIED_EXACT`, PG-P0 `ACTIVE→COMPLETE`, PG-P1 held `NOT_READY`;
  re-apply → `ALREADY_APPLIED_EXACT` (no double transition); wrong predecessor → `REPLAY_DENIED`;
  PG-P1-opening mutation → `INVARIANT_VIOLATION`; unknown/duplicate fields → `MANDATE_INVALID`.
- `pnpm validate` — full governed chain exit 0.

## Boundary

Additive tool + tests only. The encoder changes no governed state on its own — it applies an
already-signed mandate to a supplied schedule and emits evidence. It does not sign, consume the
real decision, mutate the real `SCHEDULE-REGISTER`, complete PG-P0, or open PG-P1. Those remain
separate attributable authority acts. `docs/00-governance/**` byte-unchanged.

## Disposition

Not accepted. Requires independent BST-Codex-Motor exact-SHA review and Human Engineering
Authority acceptance. Once accepted, this encoder is the executable substrate the PG-P0
completion mandate's Stage-2 controls require.
