# EVD-VERIFY-001 — Executable Verifier for a Human-Applied Phase Transition

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** VERIFY-P0-01 (proposed)
**Generated:** 2026-07-25
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`) — sole maker
**Independent checker:** BST-Codex-Motor (exact-SHA review pending)
**Base:** accepted head `73912e4`
**Verdict:** self-certified maker evidence only; not an acceptance.

## What is demonstrated

The tool `tools/verify_phase_transition.py` makes the signature-safe transition controls
**executable and adversarially tested**, under the "verifier + human apply" design where git's
single-commit ref update is the authoritative compare-and-swap and atomic incorporation.

## Commands and results (at the candidate SHA, clean worktree)

- `python -m unittest tests.governance.test_phase_transition_verify` — **27/27 passed**.
- `python -m unittest discover -s tests -p "test_*.py"` — full governance + contract suite green.
- `pnpm validate` — exit 0 (repository, contracts, program controls, authority-identity,
  program-G0, docket, document manifest `--check`, clean-room, secrets, supply-chain, skeleton).
- CLI end-to-end: `verify_phase_transition.py --predecessor … --successor … --mandate … `
  `--trust-root … --identity-register … --verification-time …` → `VERIFIED: VERIFIED_EXACT`.

## Controls proven (each by test)

- **RFC 8785**: member names ordered by UTF-16 code units — proven to sort U+10000 (surrogate
  pair `D800 DC00`) **before** U+FFFF, diverging correctly from a naive code-point sort;
  duplicate-key, float, NaN/Infinity rejection.
- **Ed25519 (RFC 8032)**: accepts the §7.1 published vector, rejects a bit-flipped signature,
  round-trips sign/verify. Clean-room from-spec implementation; production may swap a vetted
  library behind `verify_ed25519()`.
- **DSSE / trust**: untrusted key id, wrong signing key under a trusted id, and non-canonical
  signed payload are all rejected.
- **Authority**: missing required role or action, before `valid_from`, at/after `expires_at`,
  and key / decision / identity revocation are all rejected; validity is evaluated at a supplied
  (normalized) time, never the wall clock.
- **Anti-replay CAS**: predecessor-digest mismatch rejected; single-use — a reused decision id
  against a different transition rejected, the byte-identical transition returns
  `ALREADY_VERIFIED_EXACT`.
- **Recompute equality (crux)**: a proposed successor that smuggles any extra change is rejected
  as `SUCCESSOR_MISMATCH`; the invariant that `PG-P1` stays `NOT_READY` is enforced.

## Boundary

Advisory verification only. The tool signs nothing, issues no keys, mutates no register,
consumes no real decision, and merges nothing. It changes no governed state; wiring it into a
live gate and running it at apply time against the real register are separate human-authority
acts. `main` unchanged; schedule `PG-P0 ACTIVE`, `PG-P1 NOT_READY`; G3–G7 open.
