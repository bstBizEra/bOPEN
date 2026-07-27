# PG-P0 Closure Mandate v2 - UNSIGNED HUMAN SIGNING PACKET

**Version:** 0.1
**Status:** `READY_FOR_HUMAN_SIGNATURE`
**NOT SIGNED. NOT AUTHORIZED. NOT EFFECTIVE.** This packet grants nothing, completes no phase,
moves no ref, and consumes no decision. It is content staged for the accountable human authority.
**Maker:** Claude Opus 5 (BST-SA Motor worker agent), sole maker. The maker did not, and cannot,
sign this.
**Independent checker:** required before reliance; not yet performed on this packet.

## Why a NEW mandate is required (do not reuse the C4 signature)

The operator's existing C4 signature covers decision `PG-P0-CLOSURE-001`, whose subject binds the
frozen C3 closure manifest at raw-bytes SHA-256 `7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`. That signature
**cannot** bind any corrected manifest: changing the manifest changes its digest, and a signature
is over exact bytes. A prior candidate asserted otherwise and was rejected `REJECT_EXACT_SHA`
(commit `2134ea2d53f78b79522b476e78f4b33022595615`).

The frozen manifest is therefore left **byte-identical** (append-only), and all corrections live in
a separate superseding proposal that requires this new signature under a new decision id.

## What you would be signing

- **Payload file:** `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE-V2-PROPOSAL.payload.json`
  (already RFC 8785 canonical; do not reformat, re-indent, or re-serialize it - any byte change
  invalidates the signature)
- **The file has NO trailing newline, deliberately.** Its on-disk bytes ARE the payload bytes, so
  `sha256` of the file equals the payload digest below with no stripping, slicing, or normalization
  step. Any editor that "helpfully" appends a final newline on save invalidates the signature; check
  the digest again after any tool touches the file.
- **Payload RFC 8785 SHA-256:** `30f9605f2847b7bf3ff95dfbf10a38028db1611666bcc94f2fbb65ede8b9c3fe`
- **DSSE payloadType:** `application/vnd.bopen.phase-completion-mandate+json`
- **PAE SHA-256 (the bytes actually signed):** `6239d13663f25854c7122dffef51f5a713a43e2c80e9cb369947b47e2576ec3d`
- **PAE length:** 2343 bytes
- **decision_id:** `PG-P0-CLOSURE-002-PROPOSAL` (new; `PG-P0-CLOSURE-001` remains the prior signed decision)

## Exact bindings carried in the payload's `closure_binding`

| Binding | Value |
|---|---|
| closure_manifest_digest | `9d4a2568b53997b2c940d863edef9129173450492e4c7e24b6065ebe53622347` |
| permitted_effects_digest | `c867b7ff5287803af2e30c76fa05d72b226110f9f8de657136d564a712d59861` |
| predecessor_commit | `042dda535be70927b73cd1a131b2545349729643` |
| predecessor_tree | `637af7c870218360c3458b0fb54695a3450dedb5` |
| target_ref | `refs/heads/pg-p0-closure-lineage` |
| expected_old | `042dda535be70927b73cd1a131b2545349729643` |
| revocation_state_digest | `ef3610d0217746d00c6ced6cbd69b262e4ec976110ea9baf5f55ae001491fb87` |
| consumed_state_digest | `bbd628ee8c13107f958f8053ff647cf9ed923d08b9139bfeab5a4dfee46a06b2` |
| successor_blobs_status | `UNRESOLVED_PENDING_HUMAN_EXECUTION_BYTES` |

### Seven successor blobs (one per permitted effect)

- `docs/00-governance/registers/SCHEDULE-REGISTER.json`
  - `UNRESOLVED` - **UNRESOLVED** - execution bytes not yet constructed
- `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md`
  - `48f03ad9baa611c051b3ed13189b43e42e938d77` - unchanged at C8 (created at C4, exists before the execution commit)
- `docs/CHANGELOG.md`
  - `UNRESOLVED` - **UNRESOLVED** - execution bytes not yet constructed
- `docs/DOCUMENT-MANIFEST.json`
  - `UNRESOLVED` - **UNRESOLVED** - execution bytes not yet constructed
- `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json`
  - `UNRESOLVED` - **UNRESOLVED** - execution bytes not yet constructed
- `tests/governance/test_program_control_validation.py`
  - `UNRESOLVED` - **UNRESOLVED** - execution bytes not yet constructed
- `tools/validate_pg_g0_authority_docket.py`
  - `UNRESOLVED` - **UNRESOLVED** - execution bytes not yet constructed

**`UNRESOLVED` is load-bearing and blocking.** Six of the seven successor blob OIDs cannot be filled
in because the ACTIVE-to-COMPLETE execution bytes have not been constructed. Every maker attempt to
construct them was refused by the environment's permission classifier (recorded in
`docs/evidence/EVD-CLOSURE-023-*`), and the maker did not bypass that refusal. **Signing this packet
while these remain `UNRESOLVED` would authorize a transition whose resulting bytes nobody has seen.**
Resolve them first (see "Remaining human-only steps"), then re-issue and re-digest this packet.

## Corrected C9 compare-and-swap

```
target_ref  refs/heads/pg-p0-closure-lineage
expected_old 042dda535be70927b73cd1a131b2545349729643
```

The earlier proposal of `refs/heads/main` with expected-old `a908bbea1975ffc52a636765cd9f823dfeb978eb`
is **withdrawn as factually impossible**: `git merge-base a908bbe 042dda5` exits 1. The histories are
disjoint - `main`'s root commit is `a908bbe` itself (a single-commit orphan bootstrap history), while
the closure lineage's root is `9a80f9d042f1ed176c9939bae57953443d0c5964`. A C8 commit descending from
`042dda5` could never fast-forward `main`.

`expected_old` is a snapshot taken at packet authoring. Re-read the live tip immediately before C9.

## External state (neither file is an authority record)

- `docs/00-governance/signing/PG-P0-CONSUMED-DECISIONS.json` - **empty**. The C5 verification
  (`EVD-CLOSURE-014`) was an advisory pre-execution check, not consumption. Only your real C8
  execution consumes a decision.
- `docs/00-governance/signing/PG-P0-REVOCATIONS.json` - **maker scaffold**. Its empty lists are not
  a maker attestation of non-revocation. You must attest completeness at signing time.

## Verifying this packet before signing

```
python tools/verify_phase_transition.py   --predecessor docs/00-governance/registers/SCHEDULE-REGISTER.json   --successor <recomputed successor>   --mandate <a DSSE envelope built from the payload file once signed>   --trust-root docs/00-governance/signing/PG-P0-COMPLETION-TRUST-ROOT-CANDIDATE.json   --identity-register docs/00-governance/registers/AUTHORITY-IDENTITY-REGISTER.json   --verification-time 2026-07-27T00:00:00+07:00   --consumed docs/00-governance/signing/PG-P0-CONSUMED-DECISIONS.json   --revocations docs/00-governance/signing/PG-P0-REVOCATIONS.json   --closure-manifest docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST-V2-PROPOSAL.json   --require-closure-binding
```

Gate on **both** `rc == 0` **and** stdout containing `VERIFIED_EXACT`.

## Remaining human-only steps

1. Construct the C6.2-C6.6 execution bytes (procedure fully specified in `EVD-CLOSURE-012` and
   `PG-P0-INTERP-002` v0.4 section 5) and record the six resolved successor blob OIDs.
2. Re-issue this packet with `successor_blobs` fully resolved; its payload digest and PAE digest
   will change, and the new values are what you sign.
3. Attest the revocation state is complete and current.
4. Generate the signature offline. No agent generates, receives, or holds the private key.
5. Obtain an independent (non-maker, non-Claude) exact-SHA review.
6. Only then: C8 execution commit, then C9 compare-and-swap, then the C10 post-execution receipt.

## Non-authorization

`PG-P0` remains `ACTIVE`. `PG-P1` remains `NOT_READY`. Production is not authorized. No merge, no
deployment, no ref movement is authorized by this packet.
