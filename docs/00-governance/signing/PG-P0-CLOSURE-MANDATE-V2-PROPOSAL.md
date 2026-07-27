# PG-P0 Closure Mandate v2 - UNSIGNED DRAFT

**Version:** 0.2
**Machine status:** `DRAFT_NOT_SIGNABLE`
**Blocking state:** `BLOCKED_PENDING_EXECUTION_BYTES`
**NOT SIGNED. NOT AUTHORIZED. NOT EFFECTIVE. NOT YET SIGNABLE.**

**Do not sign this document.** It is a draft whose successor-blob bindings cannot yet be filled in.
Six of its seven bindings are `UNRESOLVED` because the C6-C8 execution bytes have not been
constructed. Closure-execution verification **rejects this draft by design**
(`SUCCESSOR_BLOBS_UNRESOLVED`), and that rejection is the correct current state, not a defect to
work around. A regression test asserts the rejection so it cannot silently become a pass.

**Proposed decision id:** `PG-P0-CLOSURE-002` (distinct from the already-signed `PG-P0-CLOSURE-001`)
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker. The maker did not, and cannot,
sign this.
**Independent checker:** required before reliance; not yet performed on this draft.

## Why a NEW mandate is required (do not reuse the C4 signature)

The operator's existing C4 signature covers `PG-P0-CLOSURE-001`, whose subject binds the frozen C3
closure manifest at raw-bytes SHA-256 `7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`. That signature cannot bind any corrected
manifest: changing the manifest changes its digest, and a signature is over exact bytes. A prior
candidate asserted otherwise and was rejected `REJECT_EXACT_SHA`
(`2134ea2d53f78b79522b476e78f4b33022595615`). The frozen manifest is therefore left byte-identical,
and all corrections live in a separate superseding proposal under this new decision id.

## Draft subject (values WILL change before signing)

- **Payload file:** `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE-V2-PROPOSAL.payload.json`
- **The file has NO trailing newline, deliberately.** Its on-disk bytes ARE the payload bytes, so
  `sha256` of the file equals the digest below with no stripping or normalization step. Any editor
  that appends a final newline invalidates the signature.
- **Payload RFC 8785 SHA-256:** `5e6967ca19533ff02acea03cc1ee32dc1010091b93d25146cd2ae1608d761403`
- **DSSE payloadType:** `application/vnd.bopen.phase-completion-mandate+json`
- **PAE SHA-256:** `d8403e492267ad793627d1fe3498ddca1080074d346f9236193e1e2d49c28e59` (2325 bytes)

These digests are **provisional**. Resolving the six blob bindings and setting the real
`authority.effective_at` both change the payload bytes, hence both digests. Sign only the re-issued
packet.

## Bindings carried in `closure_binding`

| Binding | Value |
|---|---|
| closure_manifest_digest | `bde8922676f7e2d81cee35f17d5fd7b874bc2af440e5f5989ad836fe3071ac7b` |
| permitted_effects_digest | `c867b7ff5287803af2e30c76fa05d72b226110f9f8de657136d564a712d59861` |
| predecessor_commit | `042dda535be70927b73cd1a131b2545349729643` |
| predecessor_tree | `637af7c870218360c3458b0fb54695a3450dedb5` |
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

`successor_blobs` must name **exactly** these seven paths - no missing path, no extra path - and
every value must be a 40-character lowercase git object id. The verifier recomputes each id from the
real file bytes under a bounded `--execution-root` using git blob hashing (sha1("blob <len>\0" + content)), so a
binding that names honest-looking ids but does not match the bytes actually present is rejected
`SUCCESSOR_BLOB_MISMATCH`.

## Verification-time policy (backdating withdrawn)

An earlier draft printed `--verification-time 2026-07-27T00:00:00+07:00` as example guidance. That
is **withdrawn**. `verification_time` is caller-supplied and the verifier deliberately reads no wall
clock, so a stale or convenient value is undetectable from a receipt alone - choosing one to make a
validity window pass is an explicit stop condition.

Any verification of this draft or its successor MUST:

1. supply the **actual wall-clock instant of the verification event**, normalized to the register's
   `+07:00` offset;
2. record that instant in the receipt **together with a justification** of why it is the true event
   time (who ran it, on what host, against what checkout);
3. bind the receipt to the exact commit and tree verified.

Reusing the `2026-07-27` value is not acceptable. Separately, `authority.effective_at` in the payload
is still inherited from the C1-era signed mandate and **must be replaced with the actual decision
time at re-issuance** - note this changes `planned_end` via `COPY_MANDATE_EFFECTIVE_TIME`, and
therefore changes the authorized successor digest, so the V2 manifest's
`successor.authorized_schedule_digest_rfc8785_sha256` must be recomputed at the same time.

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
  --require-closure-binding
```

Today this returns `REJECTED: SUCCESSOR_BLOBS_UNRESOLVED`. That is expected and correct. Gate on
**both** `rc == 0` **and** stdout containing `VERIFIED_EXACT`.

## External state (neither file is an authority record)

- `PG-P0-CONSUMED-DECISIONS.json` - **empty**. The C5 verification (`EVD-CLOSURE-014`) was advisory,
  not consumption. `PG-P0-CLOSURE-002` is unsigned and cannot have been consumed.
- `PG-P0-REVOCATIONS.json` - **maker scaffold scoped to `PG-P0-CLOSURE-002`**, marked
  `PENDING_HUMAN_ATTESTATION`. Empty lists are not a maker attestation of non-revocation.

## Remaining human-only steps

1. Construct the C6.2-C6.6 execution bytes (`EVD-CLOSURE-012`; `PG-P0-INTERP-002` v0.4 section 5).
2. Recompute the six blob ids from those bytes and resolve them in the binding.
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
