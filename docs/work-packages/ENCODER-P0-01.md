# ENCODER-P0-01 — Executable Phase-Transition Encoder (Stage-2 controls)

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`) — sole maker
**Independent checker:** BST-Codex-Motor (must review the exact final SHA)
**Base:** governed substrate `29949f460345a55b8f8079cad802d6ca85cbe46e`

## Why this exists

An independent repository review (BST-Codex-Motor, receipt `cf4a0e2`) found that the PG-P0
completion package **documents** anti-replay, idempotency, and deterministic apply/receipt
controls but does **not implement them as executable code** — `NOT_READY_FOR_SIGNATURE`.
Signing a mandate whose safety controls are only prose would let a stale mandate be replayed
or the encoder double-apply. This work item makes those controls executable and tested, so a
signed Stage-1 mandate can be applied exactly once, deterministically, and verifiably.

## In scope (additive)

1. `tools/apply_phase_transition.py` — dependency-free Stage-2 encoder implementing:
   - **Canonicalization** — JCS-aligned canonical JSON for all digests (recursively sorted
     keys, UTF-8, compact, duplicate-key rejected, no BOM).
   - **Compare-and-swap anti-replay** — the mandate's predecessor schedule digest must equal
     the current authoritative schedule digest, else `REPLAY_DENIED`.
   - **Single-use decision consumption** — a consumed-decisions registry; a decision id is
     consumed once, bound to its exact predecessor/successor digests.
   - **Deterministic transform** — only the mandate's permitted mutations are applied;
     unknown mutation paths and unknown mandate fields are rejected; the successor is a pure
     function of predecessor + transform (a checker can independently recompute it).
   - **Invariant enforcement** — declared invariants (e.g. `phases.PG-P1.status = NOT_READY`)
     must hold in the successor, else `INVARIANT_VIOLATION`.
   - **Idempotency** — `APPLIED_EXACT`; re-apply against the already-authoritative successor →
     `ALREADY_APPLIED_EXACT` (no new transition/receipt); reused decision against another
     state → `REPLAY_DENIED`; divergent state → `CONFLICT`.
   - **Atomic Stage-2 receipt** — binds mandate digest, predecessor/successor digests and
     transform-spec digest.
   - **Independent recompute** — `recompute_successor(predecessor, mandate)` for checker use.
2. `tests/governance/test_phase_transition.py` — proves each control (deterministic bytes,
   anti-replay denial, single-use denial, idempotent re-run, conflict/invariant/unknown-field
   rejection, recompute-equals-maker-output).

## Out of scope

Signing a mandate; granting authority; consuming the real decision; mutating the actual
`SCHEDULE-REGISTER`; merge, release, deployment, runtime, PG-P0 completion, or PG-P1. The tool
only *applies an already-signed mandate to a supplied schedule and emits evidence*; it changes
no governed state until an authority-signed mandate is fed to it as a separate, reviewed act.

## Acceptance criteria

- Full `pnpm validate` chain and complete test suite pass at the exact candidate SHA.
- All Stage-2 controls are executable and each is proven by a test (no prose-only control).
- The encoder is deterministic (byte-identical successor for the same predecessor + mandate)
  and idempotent (`ALREADY_APPLIED_EXACT` on re-apply, no double transition).
- Additive only; `docs/00-governance/**` and signed surfaces byte-unchanged.
- Independent BST-Codex-Motor exact-SHA review, then Human Engineering Authority acceptance.

## Completion record

Pending. This proposed record does not accept itself.
