# VERIFY-P0-01 — Independent Verifier for a Human-Applied Phase Transition

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Architecture Authority
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`) — sole maker
**Independent checker:** BST-Codex-Motor (must review the exact final SHA)
**Base:** accepted head `73912e4` (contains accepted MANIFEST-P0-01 and SKEL-P0-01 lineage)

## Why this exists

An independent review (`REJECT_EXACT_SHA` of the prior encoder `1fcf4fe6`) established that the
PG-P0-completion controls must be a **signature-safe authoritative apply**, not just correct
transform logic, and that the encoder candidate additionally built on the wrong base
(`29949f46`, dropping the accepted MANIFEST/SKEL lineage and reintroducing the reproducibility
time-bomb). The Architecture Authority selected the **"verifier + human apply"** design.

Under that design the authoritative, atomic durable state change is the operator's **single git
commit** that replaces the predecessor schedule-register bytes with the successor bytes: git
supplies the compare-and-swap (the commit parent is exactly the predecessor tree) and the
atomic, crash-safe ref update. No agent performs or is delegated that update. This work item
builds the tool that **proves the human's commit is exactly the sanctioned transition** so an
independent checker and the operator can rely on it.

## In scope (additive; base `73912e4`)

1. `tools/verify_phase_transition.py` — dependency-free (standard library only) verifier:
   - **RFC 8785 (JCS) canonicalization** for every digest and the signed payload — member names
     ordered by **UTF-16 code units** (proven to diverge correctly from code-point order for
     supplementary characters), I-JSON safe-integer profile, duplicate-key / float / NaN /
     Infinity rejection. Closes "JCS-aligned but unproven".
   - **DSSE + Ed25519 (RFC 8032) signature verification** against a trust root binding each key
     id to an authority identity; the signed payload must already be canonical (no re-encode
     ambiguity). A clean-room, from-the-spec Ed25519 is bundled and anchored to the RFC 8032
     §7.1 published test vector; production may substitute a vetted library behind
     `verify_ed25519()`.
   - **Authority / trust enforcement** against the authority-identity register: signer approved,
     holds the required authority role and action, inside its validity window at a **supplied**
     verification time (no wall clock), and neither key- nor decision- nor identity-revoked.
   - **Compare-and-swap anti-replay**: the mandate's bound predecessor digest must equal the
     canonical digest of the supplied predecessor (expected-old), and the decision id is
     single-use (idempotent only for the byte-identical transition).
   - **Recompute equality (the crux)**: the successor is recomputed as a pure function of
     predecessor + transform and its canonical bytes MUST equal the human-proposed successor's;
     any smuggled change yields `SUCCESSOR_MISMATCH`.
   - **Invariant enforcement** (e.g. `PG-P1` stays `NOT_READY`).
   - An advisory **verification receipt** binding predecessor/authorized-successor/proposed-
     successor digests, mandate digest, transform-spec digest, signer identity and time.
2. `tests/governance/test_phase_transition_verify.py` — 27 tests: the RFC 8032 vector (accept,
   bit-flip reject, round-trip), RFC 8785 ordering/float/duplicate, happy path + idempotency,
   and every rejection path (tampered signature, untrusted key, wrong key, non-canonical
   payload, missing role/action, before/after validity, key/decision/identity revocation,
   predecessor mismatch, smuggled-successor mismatch, invariant breach, unknown field, replay).

## How each prior finding is resolved

| Prior finding | Resolution |
|---|---|
| 1 Wrong lineage / time-bomb | Built on accepted head `73912e4`; the date-invariant manifest tool is inherited, not the wall-clock one. |
| 2 No authoritative CAS | The authoritative CAS is the human commit against the exact predecessor tree; the verifier enforces the expected-old predecessor-digest precondition. |
| 3 No atomic incorporation | The atomic incorporation is git's single-commit ref update; the verifier proves the committed successor equals the unique sanctioned recomputation (no partial/other change). |
| 4 No signature/trust enforcement | DSSE + Ed25519 verification, trust root, authority role + action, validity window, revocation. |
| 5 Canonicalization unproven | Real RFC 8785 with UTF-16 member ordering + I-JSON profile, proven by tests. |
| 6 No adversarial probes | 27 tests, mostly adversarial rejection paths, plus the standards vector. |
| 7 Receipt not authoritative | The receipt binds the authorized-successor digest; it is checked against the digest of what the human actually commits, so it evidences the sanctioned incorporation without performing it. |

## Out of scope

Signing a mandate; issuing authority keys; performing the register commit; consuming the real
decision; merge, release, deployment, runtime, PG-P0 completion, or PG-P1. Wiring the verifier
into a live gate and running it against the real register at apply time remain human-authority
acts, separate and reviewed.

## Acceptance criteria

- Full `pnpm validate` chain and complete test suite pass at the exact candidate SHA.
- Every control is executable and adversarially tested; the Ed25519 path matches the RFC 8032
  vector and the canonicalizer matches RFC 8785 UTF-16 ordering.
- Additive only; `docs/00-governance/**` and signed surfaces byte-unchanged; no new dependency.
- Independent BST-Codex-Motor exact-SHA review, then Human Engineering Authority acceptance.

## Completion record

Pending. This proposed record does not accept itself.
