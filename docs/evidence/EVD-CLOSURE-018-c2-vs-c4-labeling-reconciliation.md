# EVD-CLOSURE-018 - Maker evidence: C2 vs C4 labeling reconciliation

**Version:** 0.1
**Status:** Maker-authored preparation evidence (advisory; NOT an independent-checker receipt).
Requires independent-checker review before any weight beyond advisory.
**Class:** PG-P0 closure-repair candidate, item 4.
**Persisted:** by Claude (BST-SA Motor, sole maker this session), on isolated candidate branch
`codex/PG-P0-closure-repair-c8`, worktree base commit `042dda535be70927b73cd1a131b2545349729643`.
**Authorizes nothing.**

## Defect audited

`docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST.json`'s `trust_root.activation` field read:

```
"activation": "APPROVED_PENDING_PROOF_OF_POSSESSION -> ACTIVE on this valid C4 signature (SIGNING-PASS-11)"
```

This attributes SIGNING-PASS-11 to **C4** (per `bopen-phase-closure`: "C4 Human signs the DSSE
pre-authentication encoding locally"). But SIGNING-PASS-11 is independently, unambiguously labeled
as a **C2** artifact everywhere else in the lineage:

- Its own file: `docs/00-governance/signing/SIGNING-PASS-11-TRUST-ROOT-C2-APPROVAL.md`, header
  "PG-P0 Signing Pass 11 — **C2** trust-root approval (APPROVED_PENDING_PROOF_OF_POSSESSION)".
- Its durable independent-checker receipt: `docs/evidence/EVD-CLOSURE-005-c2-approval-receipt.md`,
  titled "Durable checker receipt: SIGNING-PASS-11 **C2** trust-root approval encoding", verdict
  `ACCEPT_EXACT_SHA`, `receipt_type: ENCODING_INDEPENDENT_CHECK`.
- The lifecycle transition it encodes, `CANDIDATE_PENDING_C2_APPROVAL -> APPROVED_PENDING_PROOF_OF_POSSESSION`,
  is exactly the **C2** step per `bopen-phase-closure` ("C2 Human keygen offline... approve the
  candidate") - `APPROVED_PENDING_PROOF_OF_POSSESSION` is the state a candidate is in *before* a
  signature exists, i.e. before C4.
- The mandate's own `signing_note` correctly distinguishes the two: "Operator signs the DSSE
  pre-authentication encoding (PAE) with **the C2 candidate private key**" - i.e. SIGNING-PASS-11
  approved *the key*; a later, separate act *signs with* that key.

The actual C4 act (the operator's Ed25519 signature over the mandate PAE) is recorded in
`docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md` and `PG-P0-CLOSURE-MANDATE.dsse.json`
(commit `d38ab2dcf8e158029527e77f6ed19ce8eea68f29`) - a separate artifact from SIGNING-PASS-11, and
one that was never itself given a `SIGNING-PASS-N` label. `PG-P0-CLOSURE-MANDATE.md`'s own title
line hedges this as "(C4/C5)", which is a second, related symptom of the same unresolved labeling
gap (that title conflates the C4 act of recording the signature with the C5 act of independently
verifying it - two different steps per the C0-C11 sequence, done in two different commits:
`d38ab2d` records the signature; `01ddb75` / `EVD-CLOSURE-014` is the independent C5 verification).

## Reconciliation

1. **`PG-P0-CLOSURE-MANIFEST.json` (this branch):** `trust_root.activation` corrected to state that
   SIGNING-PASS-11 is the C2 approval, and that the C4 signature is the one recorded in
   `PG-P0-CLOSURE-MANDATE.md`/`.dsse.json` - not SIGNING-PASS-11 itself. Additive `_status`
   rev-note added; `mandate.mandate_payload_b64` / `digest_rfc8785_sha256` / `pae_sha256` /
   `pae_bytes` are byte-for-byte unchanged (independently re-verified this session: recomputing
   `sha256(base64decode(mandate_payload_b64))` still equals the recorded
   `digest_rfc8785_sha256` `0f34a306ad63bb3457c1fdda3d3c9185bd99636314dc3008f2dc6ebc9acaf92c`), so
   the operator's C4 signature subject is unaffected.
2. **Commit-message label on `d38ab2d`:** that commit's message header reads `[C5] Record
   operator-signed Stage-1 closure mandate (pre-execution)`. Recording the C4 signature artifact is
   itself a C4-stage act, not C5 (C5 is the *independent checker's* verification, which is the next
   commit, `01ddb75`, correctly headed `[EVD-CLOSURE-014] Persist C5 receipt`). Historical commit
   messages on an already-shared lineage are not rewritten under the extend-only principle; this
   record is the append-only correction: **`d38ab2d` is a C4 artifact commit, mislabeled `[C5]` in
   its own subject line; the true C5 artifact is `01ddb75`.**
3. **`PG-P0-CLOSURE-MANDATE.md` title:** left unedited (extend-only) but its "(C4/C5)" hedge is
   resolved by this record: the document itself is the C4 record; the independent verification of
   it is the separate C5 artifact `EVD-CLOSURE-014`.

## Non-effect

No signed subject changed. No register mutated. No ref moved. `trust_root` lifecycle status is
unchanged by this record (still `APPROVED_PENDING_PROOF_OF_POSSESSION -> ACTIVE` on the same real
C4 signature; only the *label* attached to which artifact performed which C-step is corrected).
`PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
