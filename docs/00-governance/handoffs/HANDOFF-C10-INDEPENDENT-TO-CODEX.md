# WITHDRAWN - do not action

**Status:** WITHDRAWN by the maker, 2026-07-28, before any work was started on it.
**Original ask:** an independent C10 review of commit `757f5a13bd675e3813a8549cbb3a1e64a0d23ba8`.
**Reason:** the work was already done, and the premise was wrong.

## Why this was withdrawn

1. **An independent C10 already exists.** `EVD-CLOSURE-017` (on
   `refs/heads/motor/evidence/pg-p0-rehearsal-findings`, `4702a4c`) records that BST-Codex-Motor
   authored the C10 verification and that it returned **`REJECT_EXECUTION_EXACT_COMMIT`**. Asking for
   it again would have been duplicate work on a question already answered.

2. **`757f5a13` is a rehearsal artifact, not a real closure.** Per EVD-CLOSURE-017: *"the PG-P0
   closure exercise was conducted as a rehearsal, not a real governance closure."* PG-P0 is not
   complete. My handoff described it as an executed closure awaiting recognition. That was wrong.

3. **The rejection basis is the one I under-classed.** The independent review classified the
   agent-performed ref move as a real authority violation and disqualifying. I had classified the
   `SIM-EXEC-THROWAWAY` attribution as an audit-trail defect rather than a control failure, on the
   grounds that no governed artifact binds the git ident. The checker's reading governs; mine was
   too generous. The defect is also systemic rather than a single entry - EVD-CLOSURE-017 records
   five prior resets by `BST-DryRun-Throwaway` plus the C9 move by `SIM-EXEC-THROWAWAY`, and states
   that no entry in the closure lineage reflog is operator-attributable.

4. **The rehearsal lineage is not the current repair baseline.** `757f5a13` and the repair track
   `claude/PG-P0-closure-binding-default-cycle7` (`1756bad`) are divergent siblings off `042dda53`.
   The repair track carries remediation cycles 2-7 and **703 added lines** of controls in
   `tools/verify_phase_transition.py` (closure binding, successor blob binding, tree-scope binding,
   rename detection, predecessor anchor, expected-old anchor). The rehearsal apply used the
   unrepaired verifier - `ccf05518...` / 635 lines, byte-identical to the base - so it was verified
   by an instrument six remediation cycles behind the current one.

## What remains true from the withdrawn text

Only the mechanical measurements, and they are already independently corroborated in
EVD-CLOSURE-017 section 2: the transform is deterministic, the signature binds the transition, scope
containment held, PG-P1 stayed NOT_READY, `main` untouched. None of that amounts to a valid closure.

## Correction to my C10 harness disclosure

The harness soft spot I disclosed is the same defect the independent review acted on. `c10_verify.py`
v1.0's check 7 asserted only that the commit ident was non-empty, so it passed the throwaway ident.
v1.1 resolves the ident against the approved identity register; under `--strict-attribution` it
returns REJECT on `757f5a13`, agreeing with the independent verdict. Default remains advisory, which
on this evidence is too lenient a default - it should be reconsidered against EVD-CLOSURE-017
section 3.3 rather than left as I set it.

## No action is requested of the checker

Nothing in this file requires review, and the draft `EVD-CLOSURE-017` advisory receipt it previously
carried is void - that id is taken by the rehearsal findings record. Nothing was committed to any
governed lineage; no ref was moved.
