# PG-P0 Closure Mandate v2 - UNSIGNED DRAFT

**Version:** 0.3
**Machine status:** `DRAFT_NOT_SIGNABLE`
**Blocking state:** `BLOCKED_PENDING_EXECUTION_BYTES`
**NOT SIGNED. NOT AUTHORIZED. NOT EFFECTIVE. NOT YET SIGNABLE.**

**Do not sign this document.** Six of its seven successor blob bindings and its `successor_tree` are
`UNRESOLVED` because the C6-C8 execution bytes have not been constructed. Closure-execution
verification **rejects this draft by design**, and that rejection is the correct current state.

**Proposed decision id:** `PG-P0-CLOSURE-002` (distinct from the already-signed `PG-P0-CLOSURE-001`)
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker. The maker did not, and cannot,
sign this.
**Independent checker:** required before reliance; not yet performed on this draft.

## Why a NEW mandate is required (do not reuse the C4 signature)

The operator's existing C4 signature covers `PG-P0-CLOSURE-001`, whose subject binds the frozen C3
closure manifest at raw-bytes SHA-256 `7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`. That signature cannot bind any corrected
manifest: changing the manifest changes its digest, and a signature is over exact bytes. The frozen
manifest is therefore left byte-identical, and all corrections live in a separate superseding
proposal under this new decision id.

## Draft subject (values WILL change before signing)

- **Payload file:** `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE-V2-PROPOSAL.payload.json`
- **The file has NO trailing newline, deliberately.** Its on-disk bytes ARE the payload bytes.
- **Payload RFC 8785 SHA-256:** `41909b6792ddd0d828c788f26c516f9ca60e3a45bb26404ac4039e1875394bbd`
- **DSSE payloadType:** `application/vnd.bopen.phase-completion-mandate+json`
- **PAE SHA-256:** `ed354c23534860b2d2562cfc0d15ef78db35c0bfc4d2f83457999c5b5860f7e4` (2355 bytes)

Provisional. Resolving the bindings and setting the real `authority.effective_at` both change the
payload bytes, hence both digests. Sign only the re-issued packet.

## Bindings carried in `closure_binding`

| Binding | Value |
|---|---|
| closure_manifest_digest | `2fd049b29f1b27d46a7b0821f607d4c7e8ef43222af9085e59cccf48bdf0e998` |
| permitted_effects_digest | `c867b7ff5287803af2e30c76fa05d72b226110f9f8de657136d564a712d59861` |
| predecessor_commit | `042dda535be70927b73cd1a131b2545349729643` |
| predecessor_tree | `637af7c870218360c3458b0fb54695a3450dedb5` |
| successor_tree | `UNRESOLVED` |
| target_ref | `refs/heads/pg-p0-closure-lineage` |
| expected_old | `042dda535be70927b73cd1a131b2545349729643` |
| revocation_state_digest | `6fda0993bafb18c20424c40f7652751f77cf234f936baf594d209034f2252c2e` |
| consumed_state_digest | `c176b8540a2c09219656a71e75582064263bd0dcf97e5026053a58a7cc2d0f52` |
| successor_blobs_status | `BLOCKED_PENDING_EXECUTION_BYTES` |

### Seven successor blobs (one per permitted effect)

- `docs/00-governance/registers/SCHEDULE-REGISTER.json`
  - **UNRESOLVED** - execution bytes do not exist
- `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md`
  - `48f03ad9baa611c051b3ed13189b43e42e938d77` - resolved; created at C4, unchanged by C8
- `docs/CHANGELOG.md`
  - **UNRESOLVED** - execution bytes do not exist
- `docs/DOCUMENT-MANIFEST.json`
  - **UNRESOLVED** - execution bytes do not exist
- `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json`
  - **UNRESOLVED** - execution bytes do not exist
- `tests/governance/test_program_control_validation.py`
  - **UNRESOLVED** - execution bytes do not exist
- `tools/validate_pg_g0_authority_docket.py`
  - **UNRESOLVED** - execution bytes do not exist

## Scope is established from the COMPLETE change, not the declared paths

An independent attack against the previous draft added an **undeclared file** under the execution
root and verification still accepted, because only the seven declared paths were ever examined. That
escape is closed. Closure-execution verification now:

1. requires a bounded `--repository` git object source;
2. requires `predecessor_tree` and `successor_tree` to be **real git tree objects** (a blob id or an
   unknown id is `TREE_OBJECT_INVALID`);
3. enumerates the **complete** `predecessor_tree -> successor_tree` diff with `--no-renames`, so a
   rename decomposes into a delete plus an add and **both** sides are seen, and rejects **any**
   added, modified, deleted, renamed, mode-changed or type-changed path outside the seven permitted
   effects (`TREE_SCOPE_VIOLATION`);
4. requires each of the seven bound blobs to exist in `successor_tree` as a **regular-file blob**
   (mode 100644/100755 - a symlink is also a blob in git, so the mode is allow-listed) and to match
   the bound id (`SUCCESSOR_TREE_ENTRY_INVALID` / `SUCCESSOR_TREE_BLOB_MISMATCH`);
5. requires the execution root to **be** the successor tree exactly - no extra file, no missing file,
   no differing byte (`EXECUTION_ROOT_MISMATCH`). Untracked bytes are invisible to a tree diff, so
   the root is compared to the tree in full;
6. recomputes every id from real bytes via git blob hashing (sha1("blob <len>\0" + content)).

## Verification-time policy (backdating withdrawn)

An earlier draft printed `--verification-time 2026-07-27T00:00:00+07:00` as example guidance. That is
**withdrawn**. `verification_time` is caller-supplied and the verifier reads no wall clock, so a
stale value is undetectable from a receipt alone. Any verification MUST supply the **actual
wall-clock instant of the verification event** (register offset `+07:00`), record it in the receipt
**with a justification** of why it is the true event time (who ran it, on what host, against what
checkout), and bind the receipt to the exact commit and tree verified.

Separately, `authority.effective_at` is still inherited from the C1-era signed mandate and **must be
replaced with the actual decision time at re-issuance** - this changes `planned_end` via
`COPY_MANDATE_EFFECTIVE_TIME` and therefore the authorized successor digest.

## Verifying (expect rejection today)

```
python tools/verify_phase_transition.py \
  --predecessor docs/00-governance/registers/SCHEDULE-REGISTER.json \
  --successor <recomputed successor> \
  --mandate <DSSE envelope built from the payload once signed> \
  --trust-root docs/00-governance/signing/PG-P0-COMPLETION-TRUST-ROOT-CANDIDATE.json \
  --identity-register docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json \
  --verification-time <ACTUAL EVENT TIME, +07:00> \
  --consumed docs/00-governance/signing/PG-P0-CONSUMED-DECISIONS.json \
  --revocations docs/00-governance/signing/PG-P0-REVOCATIONS.json \
  --closure-manifest docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST-V2-PROPOSAL.json \
  --execution-root <tree holding the constructed execution bytes> \
  --repository <git object source holding both trees> \
  --require-closure-binding
```

Today this rejects. Gate on **both** `rc == 0` **and** stdout containing `VERIFIED_EXACT`.

## External state (neither file is an authority record)

- `PG-P0-CONSUMED-DECISIONS.json` - **empty**. The C5 verification (`EVD-CLOSURE-014`) was advisory,
  not consumption. `PG-P0-CLOSURE-002` is unsigned and cannot have been consumed.
- `PG-P0-REVOCATIONS.json` - **maker scaffold scoped to `PG-P0-CLOSURE-002`**, marked
  `PENDING_HUMAN_ATTESTATION`. Empty lists are not a maker attestation of non-revocation.

## Remaining human-only steps

1. Construct the C6.2-C6.6 execution bytes (`EVD-CLOSURE-012`; `PG-P0-INTERP-002` v0.4 section 5).
2. Commit them so a real `successor_tree` exists; record that tree id and the six blob ids.
3. Replace `authority.effective_at` with the real decision time and recompute the authorized
   successor digest.
4. Attest the revocation state for `PG-P0-CLOSURE-002` is complete and current.
5. Re-issue this packet; its payload and PAE digests change. Verify with a real event time.
6. Sign offline. No agent generates, receives, or holds the private key.
7. Obtain an independent (non-maker, non-Claude) exact-SHA review.
8. Only then: C8, C9 compare-and-swap, C10 post-execution receipt.

## Non-authorization

`PG-P0` remains `ACTIVE`. `PG-P1` remains `NOT_READY`. Production is not authorized. No merge, no
deployment, no ref movement is authorized by this draft.
