# EVD-CLOSURE-AUTH-001 -- PG-P0 preparation decision support

Status: ADVISORY_MAKER_PACKET -- NOT A COMPLETION RECEIPT  
Prepared by: Codex (maker-side coordinator)  
Prepared on: 2026-07-28 (Asia/Vientiane)  
Project: bOPEN  
Phase: PG-P0  

## Exact subject

- Governed ref: `refs/heads/pg-p0-closure-lineage`
- Governed commit: `042dda535be70927b73cd1a131b2545349729643`
- Governed tree: `637af7c870218360c3458b0fb54695a3450dedb5`
- Recorded phase state: `PG-P0 ACTIVE`
- Required invariant: `PG-P1 NOT_READY`
- Candidate examined but not integrated:
  `2a18ed5352930f7603543cdab00fe397e6b11dc4`
- Candidate tree:
  `13cef32de469db3769898c0b0ec6c477fc634ab2`

This packet does not authorize a signature, C8 commit, C9 ref movement, PG-P0
completion, PG-P1 opening, release, deployment or production.

## Root-clause finding

The current V2 proposal is not constructible as written when its C3 signed
payload binds the final Git tree or blob containing its future C4 signature.
Adding the signature changes that blob and tree, which changes the payload that
was signed. This is a temporal self-reference, not merely a missing-byte
problem.

The existing signed decision `PG-P0-CLOSURE-001` cannot substitute for a new
decision. Its signed payload predates and does not bind the proposed exact
parent, target ref, expected-old value, execution-byte set, successor blobs or
successor tree.

## Minimum non-weakening correction

The new C3 subject for `PG-P0-CLOSURE-002` should bind:

1. predecessor commit and tree;
2. `expected_old` equal to the predecessor commit;
3. `target_ref` equal to `refs/heads/pg-p0-closure-lineage`;
4. the semantic `PG-P0 ACTIVE -> COMPLETE` transition;
5. the invariant `PG-P1 NOT_READY`;
6. the complete permitted and prohibited path/mode set;
7. exact signature-independent source blobs;
8. the deterministic renderer and manifest-generator digests and execution
   order;
9. an explicit closed list of signature-dependent outputs deferred until after
   C4.

The C3 subject must not bind:

- its own future DSSE-envelope or signature-bearing record blob;
- signature-dependent manifest blobs;
- the final C8 commit;
- the final successor tree;
- the post-execution C10 receipt.

C5 must independently verify the human signature and exact subject. At C6 the
maker may deterministically construct the deferred outputs in an isolated
worktree. C7 must independently validate the resulting complete
predecessor-to-successor diff before publication. C10 must then externally bind
the actual C8 commit, parent, tree, changed paths, modes, blobs, CAS old/new
values, payload and PAE digests, signer key ID, final schedule digest and
test-output digests.

## Evidence reviewed

1. Live governed ref and schedule state were read directly from Git.
2. The V2 proposal states that six successor blobs and `successor_tree` are
   unresolved and that a new signature is required.
3. Two Codex reviewer results, relayed to this maker but not yet persisted as
   immutable receipts, reported:
   - the signature/tree self-reference;
   - `PG-P0-CLOSURE-001` is insufficient for the proposed package;
   - a detached signature plus external C10 tree attestation removes the
     circularity without requiring two execution commits.
4. A relayed Claude CLI advisory result agreed that
   `PG-P0-CLOSURE-001` cannot bind the new manifest, but its proposed sequence
   was rejected where it:
   - targeted `main` instead of `refs/heads/pg-p0-closure-lineage`; and
   - attempted to resolve signature-dependent successor blobs before signing,
     leaving the circularity intact.
5. The aborted Claude scratch clone was quarantined at
   `C:\tmp\b-exec-aborted-20260728-1017`.
   - base: `042dda535be70927b73cd1a131b2545349729643`
   - changed paths: six
   - diff stat: 109 insertions, 17 deletions
   - stable patch id: `6bf21e12921c952bb0f5538b016b178a12818240`
   - disposition: forensic input only; not accepted execution evidence.

## Missing evidence

The following must exist before Decision A:

- proposed non-circular reconciliation of the C3/C4/C10 layering;
- exact authority-scope finding identifying the human holder, validity and
  non-revocation, and mapping authority to every changed component, including
  `APPROVE_PROGRAM_REGISTERS`, `APPROVE_GOVERNANCE_BASELINE`, signing-record
  encoding, derived artifacts and the human ref movement;
- evidence supporting preparation, including the root-clause finding and the
  disposition of prior candidates and aborted scratch bytes.

The following must exist after Decision A but before separate human
consideration of an offline signature:

- final canonical `PG-P0-CLOSURE-002` payload;
- complete permitted-effects list;
- exact signature-independent source blobs and generator digests;
- independent review of the exact unsigned C3 subject;
- current consumed-decision/replay-state input prepared for C5 verification;
- a self-checking human signing command that exposes no private key;
- signing-time human attestation that revocation state is complete and current
  for the exact key and `PG-P0-CLOSURE-002`;

The following cannot exist until after the human signature:

- final DSSE envelope and signature-bearing record;
- signature-dependent manifest blobs;
- complete proposed C8 tree verification.

The following cannot exist until after C8:

- actual execution commit and tree;

The following cannot exist until after C9:

- actual CAS receipt;
- independent C10 post-execution receipt;
- C11 recognition.

## Human authority decision propositions

### Decision A -- may be considered after the pre-decision evidence is complete

`AUTHORIZE_PREPARATION_OF_PG-P0-CLOSURE-002_FOR_SEPARATE_HUMAN_SIGNATURE`

Meaning: approve the corrected non-circular evidence layering and permit the
maker/checker sequence to freeze C3 for later, separate consideration of a
human offline signature.

This decision does **not** authorize a signature, C8/C9, or mean PG-P0 is
complete.

### Decision B -- may be considered only after C10 passes

`RECOGNIZE_PG-P0-COMPLETE`

Meaning: recognize that the already-executed C8/C9 transition was exactly
authorized, independently verified and recorded.

No pre-execution evidence can honestly support Decision B.

## Required serial sequence

1. Human authority adopts the narrow layering reconciliation.
2. Maker freezes the exact C3 subject.
3. Independent checker accepts the exact unsigned subject.
4. Human attests that revocation state is complete and current for the exact
   key and `PG-P0-CLOSURE-002`.
5. Human separately decides whether to sign and, if approved, signs
   `PG-P0-CLOSURE-002` offline.
6. Independent C5 verifies the signature, authority, revocation and current
   consumed/replay state.
7. Maker performs C6 deterministic construction in an isolated worktree.
8. Independent C7 validates the complete proposed change.
9. Human authors the C8 commit.
10. Human performs C9 expected-old CAS on
   `refs/heads/pg-p0-closure-lineage`.
11. Independent checker issues C10.
12. Human issues C11 recognition.

## Maker disposition

`READY_FOR_INDEPENDENT_REVIEW_OF_THE_PREPARATION_DECISION_SUPPORT`

Not ready for signing. Not ready for C8/C9. PG-P0 remains `ACTIVE`.
