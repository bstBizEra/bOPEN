# PG-P0-INTERP-002 v0.2 (DRAFT) — Closure authorization, authority-scope finding, and mechanism for PG-P0 `ACTIVE → COMPLETE`

**Version:** 0.2 (supersedes v0.1 at `d8cf7abd152492d9f77984296971521b88341859`, which based the whole
closure on `APPROVE_PROGRAM_REGISTERS` alone — corrected per the operator research verdict
`APPROVE_WITH_MATERIAL_CORRECTIONS`)
**Status:** Draft; ineffective — for human issuance against this exact text
**Interpretation id:** `PG-P0-INTERP-002`
**Owner / accountable authority:** Engineering Authority
**Issued (draft):** 2026-07-27
**Maker:** Claude (BST-SA Motor worker agent)
**Independent checker:** BST-Codex-Motor (exact-SHA review; durable receipt required)

## 1. Authority-scope finding (correction 1 — produced BEFORE issuance)

Verified against the effective matrix, identity register, and Git history:

```yaml
authority_scope_finding:
  effective_actions:
    - APPROVE_PROGRAM_REGISTERS   # program_register_approval; held by HUMAN-OPERATOR-001 (valid to 2026-08-21)
    - APPROVE_GOVERNANCE_BASELINE # governance_baseline_approval; held by HUMAN-OPERATOR-001 (valid to 2026-08-21)
  authority_basis: "PG-REG-IDENTITY-001 bindings of both pre-existing actions (matrix v0.2.0, approved)"
  authorized_subjects:
    schedule_register: true          # SCHEDULE-REGISTER.json is one of the seven program registers
                                     # (DEC-0013's own definition of APPROVE_PROGRAM_REGISTERS scope)
    docket_validator: true           # NOT covered by APPROVE_PROGRAM_REGISTERS (it is source code, not a
                                     # register). Covered by APPROVE_GOVERNANCE_BASELINE: the validator is
                                     # governance-baseline machinery (DEC-0013 precedent: governance
                                     # schemas/machinery adopted under this action), PROVIDED the signed
                                     # decision names the exact validator files and diff — the
                                     # SIGNING-PASS-5 precedent, whose execution note explicitly
                                     # authorized "any docket/readiness surface the validators require",
                                     # under which 29949f46 changed SCHEDULE-REGISTER.json AND
                                     # validate_pg_g0_authority_docket.py together.
    closure_authorization_record: true  # a signing record is the decision's own append-only encoding
                                        # (SIGNING-PASS-1..8 precedent); its authority is the decision it records
    derived_regeneration: true       # deterministic validator outputs (readiness reports, manifest);
                                     # no authority content; must be enumerated in the closure manifest
    authoritative_ref_update: true   # a HUMAN act: per DEC-0014 (verifier + human apply), the operator's
                                     # own commit/ref move IS the authoritative apply, protected by
                                     # git update-ref compare-and-swap; no agent performs it
  interpretation_expands_authority: false  # both actions pre-exist and are held; this interpretation
                                           # only scopes them to one bounded transition
```

**Consequence:** the closure decision must be issued under **both** actions jointly (concurrences of
both collapse to the operator under the approved solo-operator disclosure). No new action is created;
no action authorizes its own creation.

## 2. Interpretation (to be issued by the accountable human authority against this exact text)

> The PG-P0 completion transition is authorized by **two pre-existing effective actions jointly**:
> **(a)** `APPROVE_PROGRAM_REGISTERS` scopes to the single sanctioned `SCHEDULE-REGISTER.json`
> mutation `PG-P0: ACTIVE → COMPLETE` (§4); **(b)** `APPROVE_GOVERNANCE_BASELINE` scopes to the
> precedent-following extension of `tools/validate_pg_g0_authority_docket.py`'s encoded signed
> outcome (§5), with the signed decision naming the exact files and diff. The closure signing record
> and the enumerated derived regenerations are the decision's own encoding. The authoritative ref
> update is the operator's human act under DEC-0014, protected by expected-old compare-and-swap.

## 3. Three evidence layers (correction 3 — no circular signing)

1. **Pre-execution closure manifest** (frozen before signing): exact predecessor digests (schedule,
   validator, registers), exact successor byte digests for every file the closure may change,
   permitted effects, and nothing else. Its SHA-256 is bound into the Stage-1 mandate.
2. **Authorized execution commit**: contains exactly the approved schedule successor, validator
   successor, signing record, and enumerated derived bytes — nothing else. Its parent must equal the
   approved baseline commit.
3. **Post-execution closure receipt** (separate, subsequent): binds the resulting commit/tree, the
   register state, and the evidence digests. It attests the execution commit and therefore **must not
   be embedded in the commit it attests**. PG-P0 is recognized `COMPLETE` only after this receipt
   passes independent verification.

## 4. The single sanctioned schedule mutation (unchanged from v0.1)

Only the PG-P0 entry changes (schema `additionalProperties: false` — no new fields; authority
metadata lives in the signing record and receipt, not the register):
`status: ACTIVE → COMPLETE`; `planned_end: null → <closure-effective-time>`;
`rebaseline_decision_ref → <closure signing record>#signed-decision`;
`evidence_refs → [<closure signing record>, <post-execution receipt>, docs/00-governance/signing/SIGNING-PASS-8.md]`.
PG-P1..PG-C0 remain `NOT_READY` byte-identically.

## 5. Validator extension with anti-self-validation checks (correction 2)

The expected-state extension (constants `P0_COMPLETED_AT`, `P0_COMPLETE_DECISION_REF`,
`P0_COMPLETE_EVIDENCE_REFS`; PG-P0 branch → `COMPLETE` shape) follows the `29949f46` precedent —
**and must not be self-confirming**. The extended check MUST require, beyond constant equality:

- the closure signing record exists at `P0_COMPLETE_DECISION_REF`'s path and is a tracked, non-empty
  record naming both authorizing actions, the signer identity, and the closure-manifest SHA-256;
- every `P0_COMPLETE_EVIDENCE_REFS` entry exists and is tracked (the docket's existing
  `validate_evidence_refs` pattern);
- the schedule successor equals the exact expected bytes AND no unrelated register/matrix/identity
  state changed (existing drift checks remain fully in force);
- the signer's identity-register binding was effective and unrevoked at `P0_COMPLETED_AT`.

External signature verification (DSSE/Ed25519 against the effective trust root) is performed by
`VERIFY-P0-01` on the mandate and by the independent checker — the docket validator checks the
*governed evidence surface*; `VERIFY-P0-01` checks the *cryptographic authorization*; the independent
receipt checks both against the resulting commit.

## 6. Corrected closure sequence (operator C0–C11, binding)

```
C0  Freeze full baseline commit/tree + relevant blob digests
C1  Authority-scope finding verified (§1) — precondition to issuance
C2  Trust root: operator keygen; replace placeholder with real public key + fingerprint; approve
C3  Freeze the closure manifest + exact successor bytes (schedule §4, validator §5)
C4  Human signs the Stage-1 closure mandate (binds manifest SHA-256; single-use decision id)
C5  Independent checker verifies authority, signature, scope, digests  -> durable receipt
C6  Apply exact bytes in an isolated clean worktree (HEAD == approved parent; tree clean)
C7  Positive, negative, drift and full-regression validation (mandatory test list below)
C8  Commit the coordinated transformation (execution commit, layer 2)
C9  Move any authoritative ref with expected-old compare-and-swap (human act)
C10 Independent post-execution closure receipt (layer 3; separate commit)
C11 Recognize PG-P0 COMPLETE only after that receipt passes
```

**Mandatory decisive-review tests (C7):** original validator accepts the `ACTIVE` baseline;
schedule-only mutation FAILS; validator-only mutation FAILS; missing/invalid closure mandate or
signing record FAILS; wrong parent commit/tree FAILS; missing `planned_end` / decision ref /
evidence ref FAILS; expired or revoked signer FAILS; altered PG-P1 state FAILS; any
production-authority change FAILS; any unrelated register change FAILS; the exact coordinated
successor PASSES; the full validator suite PASSES; the post-execution receipt matches the resulting
commit and tree.

## 7. Durable review receipts (correction 4)

Every decisive review must persist an immutable receipt in `docs/evidence/` binding: subject
commit + tree (full), closure-manifest SHA-256, checker identity + independence basis, commands and
tool versions, test-results SHA-256, authority-validation and subject-digest-validation results,
verdict, signed-at, and (once the trust root is effective) a detached signature. Runtime review ids
(e.g. task ids) are pointers, never trust anchors.

## 8. Acceptance rule (verbatim from the operator verdict)

```
PROVEN_MECHANISM + AUTHORITY_SCOPE_VERIFIED + TRUST_ROOT_EFFECTIVE + EXACT_SUBJECT_SIGNED
+ INDEPENDENT_ACCEPT_EXACT_SHA + POST_EXECUTION_RECEIPT_VALID  =  PG-P0 COMPLETE
```

Until all six hold: `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production `NOT_AUTHORIZED`.

## Non-authorization

This draft grants no authority, issues nothing by itself, mutates no register/schema/docket/
validator, signs no mandate, and completes no phase. Gate 1 and PG-P0 closure do not implicitly
open PG-P1. It is content staged for the accountable human authority to issue against this exact
text. `main` `a908bbe`.

## Issuance record — 2026-07-27

**Outcome:** ISSUED / EFFECTIVE, against the exact v0.2 text.
**Issued by:** `HUMAN-OPERATOR-001` (Engineering Authority, DIRECT), holding both scoped actions
(`APPROVE_PROGRAM_REGISTERS`, `APPROVE_GOVERNANCE_BASELINE`) per `PG-REG-IDENTITY-001`.
**Attestation:** "As HUMAN-OPERATOR-001, I re-issue PG-P0-INTERP-002 against v0.2 at 6d139f8d."
**Issued at:** 2026-07-27T00:00:00+07:00
**Exact-text binding:** commit `6d139f8da13220e07c58ffdeb2c06d842e50a620`, interpretation file
SHA-256 `aa679b1e38a7b5a248c7e01695db33d45f0e73f36969ad8517b0bafe1ec1aea6`.
**Recorded in:** `docs/00-governance/signing/SIGNING-PASS-9.md`

The interpretation above is hereby effective with its bounds, corrections, C0–C11 sequence, and
six-condition acceptance rule in full. The immutable "Draft; ineffective" header reflects
authoring-time status and is preserved unchanged per the extend-only principle; this issuance record
is the authoritative current state. Only C1 is thereby complete; C2–C11 remain, each separately
gated. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
