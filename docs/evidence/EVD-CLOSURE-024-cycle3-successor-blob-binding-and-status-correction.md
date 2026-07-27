# EVD-CLOSURE-024 - Maker evidence: cycle-3 successor-blob binding and status correction

**Version:** 0.1
**Status:** Maker-authored remediation evidence (advisory; NOT an independent-checker receipt).
**Class:** PG-P0 closure repair, remediation cycle 3. Additive follow-up commit on branch
`claude/PG-P0-closure-repair-c8-v2`; no governed history rewritten.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker.
**Authorizes nothing.** Signs nothing, applies nothing, moves no ref, consumes no decision.

## Predecessor candidate: REJECTED

Candidate `17b9075d97c9022c698097e4d88ca628fc9e9c31` received `REJECT_EXACT_SHA` from the independent
Codex checker. Cycle 3 is an **additive follow-up commit** on the same maker branch, per instruction:
`17b9075` is preserved in history, not amended or rebased.

## Correction 1 - successor_blobs strictly bound to real execution bytes

**Defect:** cycle 2 validated only that `successor_blobs` was a non-empty object. It accepted the
literal string `UNRESOLVED` as a value, never checked that the map's keys matched the manifest's
permitted-effect paths, and never compared any bound id against real bytes. A mandate could
therefore name one path, or a wrong path, or a placeholder, and still reach a `VERIFIED` verdict.

**Correction (`tools/verify_phase_transition.py`):**

- `validate_successor_blobs()` now requires, in closure mode:
  - keys **exactly equal** the manifest's permitted-effect path set - any missing path or any extra
    path is `SUCCESSOR_BLOBS_INCOMPLETE` (a renamed path is caught as both at once);
  - every value a **40-character lowercase hex** git object id - `UNRESOLVED`, non-hex, uppercase and
    truncated ids are all `SUCCESSOR_BLOBS_UNRESOLVED`;
  - an `--execution-root` to be supplied, else `EXECUTION_ROOT_REQUIRED`;
  - every bound id to equal `git_blob_oid()` recomputed from the actual file bytes at that path under
    the root, else `SUCCESSOR_BLOB_MISMATCH`.
- `git_blob_oid()` implements git's object format, `sha1(b"blob <len>\0" + data)`, anchored by a test
  against git's well-known empty-blob id `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`. SHA-1 here is
  content addressing to cross-check `git rev-parse HEAD:<path>`, never a security primitive; all
  security-bearing digests in the module remain SHA-256.
- `resolve_execution_path()` bounds resolution inside the root: absolute paths, drive-qualified
  paths, and `..` traversal are `EXECUTION_PATH_UNSAFE`, so a manifest path cannot be used to hash a
  file outside the tree under review.
- Five new reason codes: `SUCCESSOR_BLOBS_INCOMPLETE`, `SUCCESSOR_BLOBS_UNRESOLVED`,
  `SUCCESSOR_BLOB_MISMATCH`, `EXECUTION_ROOT_REQUIRED`, `EXECUTION_PATH_UNSAFE`.

**Negative tests added (18):** unresolved placeholder (one, and all), non-hex, uppercase, truncated
id, missing path, extra path, renamed path, **runtime byte mismatch**, missing execution file,
absent execution root, path traversal, absolute path, plus the git-blob-id anchor, a resolved happy
path against real bytes, and non-closure-mode reporting that never silently asserts verification.

**A cycle-2 test fixture was itself caught by the new rule** - its `successor_blobs` named only one of
its manifest's two effect paths and now correctly fails `SUCCESSOR_BLOBS_INCOMPLETE`. The fixture was
corrected to carry a real execution tree with resolved ids; the control was not weakened to
accommodate it.

**Demonstrated live against the shipped artifacts:**

```
as shipped, 6 of 7 blobs UNRESOLVED   -> REJECTED SUCCESSOR_BLOBS_UNRESOLVED
missing one permitted-effect path     -> REJECTED SUCCESSOR_BLOBS_INCOMPLETE
extra path smuggled in                -> REJECTED SUCCESSOR_BLOBS_INCOMPLETE
non-hex object id                     -> REJECTED SUCCESSOR_BLOBS_UNRESOLVED
uppercase object ids                  -> REJECTED SUCCESSOR_BLOBS_UNRESOLVED
valid-looking ids vs real repo bytes  -> REJECTED SUCCESSOR_BLOB_MISMATCH
no execution root supplied            -> REJECTED EXECUTION_ROOT_REQUIRED
```

## Correction 2 - status is now BLOCKED, not READY

**Defect:** cycle 2 labelled the packet `READY_FOR_HUMAN_SIGNATURE` while six of seven blob bindings
were unresolved. The prose warned against signing, but the machine-readable status invited it.

**Correction:** machine status is `DRAFT_NOT_SIGNABLE` (`_signing_status` in the V2 manifest) with
`_blocking_state: BLOCKED_PENDING_EXECUTION_BYTES`; the binding's `successor_blobs_status` is
`BLOCKED_PENDING_EXECUTION_BYTES`. The packet's title, header and opening paragraph all say **do not
sign**. Two regression tests assert the shipped proposal is rejected `SUCCESSOR_BLOBS_UNRESOLVED` in
closure mode and that both status markers read as blocked - so this state cannot regress into a
silent pass.

**The unsigned proposal being verifier-rejected today is the intended, correct state**, not a defect.

## Correction 3 - revocation scaffold retargeted to PG-P0-CLOSURE-002

**Defect:** cycle 2's revocation narrative referenced `PG-P0-CLOSURE-001` - the operator's
already-signed decision - rather than the proposed new decision this draft belongs to.

**Correction:** `PG-P0-REVOCATIONS.json` now scopes explicitly to `PG-P0-CLOSURE-002` and keyid
`operator-pgp0-completion-1`, carries `_attestation_status: PENDING_HUMAN_ATTESTATION`, and states
that it does **not** scope to closure-001. It remains non-authoritative: an empty list means "this
maker recorded no revocation", never "the operator confirms none exists". The V2 manifest's
`external_state_binding` carries the same scoping. The proposal's `decision_id` is now
`PG-P0-CLOSURE-002` (cycle 2 used the placeholder-ish `PG-P0-CLOSURE-002-PROPOSAL`).

## Correction 4 - backdated verification guidance withdrawn

**Defect:** cycle 2's packet printed `--verification-time 2026-07-27T00:00:00+07:00` as example
guidance. Since the verifier deliberately reads no wall clock, publishing a stale value invites
exactly the documented stop condition: "`verification_time` is chosen to make a validity window pass".

**Correction:** the value is removed and replaced by a **verification-time policy** requiring the
actual wall-clock instant of the verification event (in the register's `+07:00` offset), recorded in
the receipt **with a justification** of why it is the true event time (who ran it, on what host,
against what checkout), and bound to the exact commit and tree verified. The V2 manifest carries the
same policy in `_verification_time_policy`.

**Additionally disclosed** (not requested, but the same defect class): the payload's
`authority.effective_at` is still inherited from the C1-era signed mandate at
`2026-07-27T00:00:00+07:00`. It must be replaced with the real decision time at re-issuance. Because
`COPY_MANDATE_EFFECTIVE_TIME` derives `planned_end` from it, that change also changes the authorized
successor digest, so the V2 manifest's `successor.authorized_schedule_digest_rfc8785_sha256` must be
recomputed at the same time. This is recorded in `_unblocks_when` and in the packet's remaining-steps
list rather than left silent.

## Frozen artifacts

`PG-P0-CLOSURE-MANIFEST.json` (`7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`,
6613 bytes), `PG-P0-CLOSURE-MANDATE.md`, `PG-P0-CLOSURE-MANDATE.dsse.json`,
`SCHEDULE-REGISTER.json` and `EVD-CLOSURE-014` remain byte-identical to base
`042dda535be70927b73cd1a131b2545349729643`.

## Digest consistency

Every digest bound in the payload was recomputed from the on-disk artifact and confirmed to match:
`closure_manifest_digest`, `revocation_state_digest`, `consumed_state_digest`. All packet digests are
generated programmatically by an ephemeral script, deleted after use - never transcribed by hand.

## Scope boundaries observed

No signature generated or requested; no private key generated, received, or held; no C8 execution; no
C9 ref move; no governed ref moved; no merge; `PG-P1` untouched at `NOT_READY`; no deployment; no
production claim; no Graphify artifacts; frozen signed artifacts unchanged; `17b9075` preserved.

## Status effect

None. Pre-execution preparation only. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
The C6-C8 execution bytes remain a human-only blocker (`EVD-CLOSURE-023`, unchanged).
