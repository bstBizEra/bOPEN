---
name: bopen-phase-closure
description: Close a governed bOPEN program phase (schedule register ACTIVE to COMPLETE) through the maker, independent-checker and human-authority sequence with a signed Stage-1 mandate. Use when a phase transition, phase completion or signed mandate is in scope, and before proposing any authority-matrix change. Do not use for release or production authorization.
---

# bOPEN Phase Closure

Use for a governed phase transition. Derived from the PG-P0 closure. This skill does not
grant apply, merge, release or deployment authority.

## Authority model

- Maker (agent) prepares; independent checker verifies exact SHAs; the human authors every
  attributable decision in chat and the maker encodes it append-only afterwards.
- The maker never self-certifies. Every maker artifact gets an independent exact-SHA review
  persisted as a durable receipt (see `bopen-evidence-envelope`).
- A key is not authority. A trust root binds identity, role, `authority_basis` (a pre-existing
  effective mandate), permitted actions, validity and revocation.
- Staged activation: candidate -> approved-pending-proof-of-possession -> ACTIVE only on the
  first valid human signature (RFC 8032 verification; RFC 4210 proof of possession by signing).
- Evidence never substitutes for the signature. If asked to close "on evidence, without the
  human", refuse: completion requires both a signed exact subject and an effective trust root.
- Trust applied-and-committed reproduction over ad-hoc tests. Never report a result as proven
  from an uncommitted check, and never certify a relayed verdict you did not read yourself.

## Preconditions

1. Run `bopen-governance-check` - it owns authority scope, expiry and maker/checker separation.
2. Confirm the phase, the signed decision under which you are acting, and the exact base commit.

## Authority-basis rule, phase-transition specifics

`bopen-governance-check` establishes that authority must cover every changed component. For a phase
transition the components are: the schedule register, the docket validator's expected state, the
signing record, the derived manifests, and the ref move. Additionally:

1. Scope an existing held action through an authoritative interpretation; state
   `interpretation_expands_authority: false`.
2. Registers are usually `additionalProperties: false`. Put authority metadata in the signing record
   and receipt, never in the register.

## Coordinated change (load-bearing)

The transition is ONE commit containing: the register successor; the docket expected-state
extension recording the new signed outcome; the closure signing record; the required test delta;
and both regenerated document manifests. Applying the register alone, or the validator alone,
FAILS by design. Never split a closure into incremental commits.

Add anti-self-validation checks to the validator extension: it must confirm the closure record
exists, is tracked, names the authorizing actions and the manifest digest, and that evidence refs
resolve - not merely that the constants now expect the new state.

## Three evidence layers

1. Pre-execution manifest: exact predecessor and successor digests, permitted and prohibited effects.
2. Execution commit: exactly the approved bytes; parent equals the approved baseline.
3. Post-execution receipt: binds the resulting commit and tree. It must NOT appear in the
   successor's `evidence_refs` - that circularity fails the evidence-existence check at commit time.
   Successor refs list only execution-time-available artifacts, in canonical `sorted()` order.

## Sequence

```
C0  Freeze baseline commit, tree and blob digests
C1  Authority-scope finding verified; interpretation issued against exact text
C2  Human keygen offline; only public key and fingerprint enter the repo; approve the candidate
C3  Freeze the closure manifest and the canonical mandate payload; self-test with a throwaway key
C4  Human signs the DSSE pre-authentication encoding locally; returns only the signature
C5  Independent checker verifies authority, signature, scope and digests; durable receipt
C6  Apply exact bytes in an isolated clean worktree at the approved parent
C7  Positive, negative, drift and full-regression validation
C8  Human commits the coordinated transformation
C9  Human moves the authoritative ref with expected-old compare-and-swap
C10 Independent post-execution receipt (never embedded in the commit it attests)
C11 Recognition. Declaratory and append-only: no register mutation (the register is already
    terminal after C8, and any further edit would need a second docket-pinned change)
```

Acceptance: proven mechanism + authority scope verified + trust root effective + exact subject
signed + independent acceptance + valid post-execution receipt.

## Human-only acts

Offline keygen; the signature over the mandate; the compare-and-swap apply commit. Prepare
everything around them, hand over an exact self-checking command, and wait for real output.
"Approve to proceed" is not a signature.

## Stop conditions

- an agent would generate, receive or hold a private key;
- a register mutation without an authority-scope finding and a docket expected-state extension;
- a maker artifact without an independent receipt;
- a `--check` failure "fixed" with `--write` (see `bopen-windows-toolchain`);
- a signing record whose stated prerequisites the executed closure does not satisfy, with no
  signed reconciliation - escalate to the human; byte checks will not detect it.
