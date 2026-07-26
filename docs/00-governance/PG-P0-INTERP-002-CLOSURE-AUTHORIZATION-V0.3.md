# PG-P0-INTERP-002 v0.3 (DRAFT) — Closure authorization: sorted-refs correction + consolidated execution lineage

**Version:** 0.3
**Status:** Draft; ineffective — for human re-issuance against this exact text
**Supersedes:** v0.2 (issued via SIGNING-PASS-9 at `32271aa2d86f707a77415ce1d6492bbefb905307`;
v0.2 text digest `aa679b1e38a7b5a248c7e01695db33d45f0e73f36969ad8517b0bafe1ec1aea6`). Upon human
re-issuance against this v0.3 text, the v0.2 issuance is superseded. The v0.2 file and SIGNING-PASS-9
are preserved byte-faithfully in this lineage as history. Reason for supersession: the independent
mechanism reproduction (EVD-CLOSURE-002) proved the coordinated closure but found the v0.2 §4
`evidence_refs` example written in narrative order, while the docket validator canonicalizes with
`sorted(...)`. A signed exact-text blob must not carry a known ordering ambiguity, even though the
authorized *set* is unchanged.
**Interpretation id:** `PG-P0-INTERP-002`
**Owner / accountable authority:** Engineering Authority
**Maker:** Claude (BST-SA Motor worker agent)
**Independent checker:** BST-Codex-Motor (exact-SHA review; durable receipt required)

## 0. Consolidated execution lineage (operator hard check)

This v0.3 is authored on the **accepted integrated base' `52bd96ecc66ae910942ce0c245858cfcb8fc20fa`**
(Gate-1-accepted via SIGNING-PASS-8), which **contains `tools/verify_phase_transition.py`
(VERIFY-P0-01) and its 27-test suite in-tree** — satisfying the requirement that VERIFY-P0-01 exist
in the exact execution lineage ("exists in another base" is insufficient). All governing closure
records are carried into this lineage byte-faithfully from their source commits: SIGNING-PASS-8 +
issued PG-P0-INTERP-001 (from `d6252de1`), SIGNING-PASS-9 + v0.2 text + trust-root v2 draft (from
`32271aa2`), EVD-CLOSURE-001/002 (from `52359dc4`). The closure execution (C3–C10) proceeds on this
lineage only.

## 1. Authority-scope finding (unchanged from v0.2; independently confirmed sound in EVD-CLOSURE-001)

```yaml
authority_scope_finding:
  effective_actions: [APPROVE_PROGRAM_REGISTERS, APPROVE_GOVERNANCE_BASELINE]  # both held by HUMAN-OPERATOR-001 (valid to 2026-08-21, unrevoked)
  authority_basis: "PG-REG-IDENTITY-001 bindings of both pre-existing actions (matrix v0.2.0, approved)"
  authorized_subjects:
    schedule_register: true          # one of the seven program registers (DEC-0013 definition)
    docket_validator: true           # governance-baseline machinery (DEC-0013 precedent); the signed
                                     # decision names the exact files/diff (SIGNING-PASS-5 / 29949f46 precedent)
    closure_authorization_record: true  # the decision's own append-only encoding (SIGNING-PASS precedent)
    derived_regeneration: true       # deterministic validator outputs, enumerated in the closure manifest
    authoritative_ref_update: true   # HUMAN act per DEC-0014, expected-old compare-and-swap
  interpretation_expands_authority: false
```

## 2. Interpretation (to be re-issued by the accountable human authority against this exact text)

> The PG-P0 completion transition is authorized by **two pre-existing effective actions jointly**:
> **(a)** `APPROVE_PROGRAM_REGISTERS` scopes to the single sanctioned `SCHEDULE-REGISTER.json`
> mutation `PG-P0: ACTIVE → COMPLETE` (§4); **(b)** `APPROVE_GOVERNANCE_BASELINE` scopes to the
> precedent-following extension of `tools/validate_pg_g0_authority_docket.py`'s encoded signed
> outcome (§5), with the signed decision naming the exact files and diff. The closure signing record
> and the enumerated derived regenerations are the decision's own encoding. The authoritative ref
> update is the operator's human act under DEC-0014, protected by expected-old compare-and-swap.

## 3. Three evidence layers (unchanged)

1. **Pre-execution closure manifest** — exact predecessor digests, exact successor byte digests for
   every file the closure may change, permitted effects; its SHA-256 is bound into the Stage-1 mandate.
2. **Authorized execution commit** — exactly the approved schedule successor, validator successor,
   signing record, and enumerated derived bytes; parent must equal the approved baseline commit.
3. **Post-execution closure receipt** — binds the resulting commit/tree/register/evidence digests;
   **must not be embedded in the commit it attests**. PG-P0 is recognized `COMPLETE` only after this
   receipt passes independent verification.

## 4. The single sanctioned schedule mutation (CORRECTED: canonical sorted refs)

Only the PG-P0 entry changes (schema `additionalProperties: false` — no new fields):
- `status`: `ACTIVE` → `COMPLETE`
- `planned_end`: `null` → `<closure-effective-time>`
- `rebaseline_decision_ref` → `<closure signing record>#signed-decision`
- `evidence_refs` → **the canonical sorted list** `sorted({ <closure signing record>,
  <post-execution receipt>, "docs/00-governance/signing/SIGNING-PASS-8.md" })`

**Normative rule (the v0.3 correction):** the executed successor's `evidence_refs` array MUST be in
canonical ascending lexicographic order — exactly `sorted(...)` of the sanctioned set — matching the
docket validator's canonicalization. Any narrative ordering in examples is non-normative; the
`sorted(...)` rule governs. The frozen closure manifest (C3) MUST list the final concrete paths in
this canonical order. PG-P1..PG-C0 remain `NOT_READY` byte-identically.

## 5. Validator extension with anti-self-validation checks (unchanged)

Constants `P0_COMPLETED_AT`, `P0_COMPLETE_DECISION_REF`, `P0_COMPLETE_EVIDENCE_REFS` (a set; the
expected-state builder applies `sorted(...)`); PG-P0 branch → `COMPLETE` shape. Beyond constant
equality the extended check MUST require: the closure signing record exists, is tracked, non-empty,
and names both authorizing actions + the closure-manifest SHA-256; every evidence ref exists and is
tracked; the schedule successor equals the exact expected bytes with all existing unrelated-drift
checks fully in force; the signer's identity-register binding was effective and unrevoked at
`P0_COMPLETED_AT`. Cryptographic verification (DSSE/Ed25519 vs the effective trust root) is performed
by `VERIFY-P0-01` — present in this lineage (§0) — and by the independent checker.

## 6. Corrected closure sequence (binding; C1 re-executes for v0.3)

```
C0  Freeze full baseline commit/tree + relevant blob digests          [this lineage's head]
C1  Authority-scope finding verified + interpretation issued          [re-issue against v0.3 exact text]
C2  Operator keygen offline; public key + fingerprint into trust root; approve
C3  Freeze the closure manifest + exact successor bytes (schedule §4 sorted refs, validator §5)
C4  Human signs the Stage-1 closure mandate (binds manifest SHA-256; single-use decision id)
C5  Independent checker verifies authority, signature, scope, digests -> durable receipt
C6  Apply exact bytes in an isolated clean worktree (HEAD == approved parent; tree clean)
C7  Positive, negative, drift and full-regression validation (mandatory test list of v0.2 §6, unchanged)
C8  Commit the coordinated transformation (execution commit, layer 2)
C9  Move any authoritative ref with expected-old compare-and-swap (human act)
C10 Independent post-execution closure receipt (layer 3; separate commit)
C11 Recognize PG-P0 COMPLETE only after that receipt passes
```

## 7. Durable review receipts (unchanged)

Immutable receipts in `docs/evidence/` binding subject commit+tree, closure-manifest SHA-256, checker
identity + independence basis, commands and tool versions, test-results SHA-256, validation results,
verdict, signed-at, and (once the trust root is effective) a detached signature. Runtime ids are
pointers, never trust anchors.

## 8. Acceptance rule (unchanged, verbatim)

```
PROVEN_MECHANISM + AUTHORITY_SCOPE_VERIFIED + TRUST_ROOT_EFFECTIVE + EXACT_SUBJECT_SIGNED
+ INDEPENDENT_ACCEPT_EXACT_SHA + POST_EXECUTION_RECEIPT_VALID  =  PG-P0 COMPLETE
```

Status of conditions at v0.3 authoring: `PROVEN_MECHANISM` ✓ (EVD-CLOSURE-002);
`AUTHORITY_SCOPE_VERIFIED` ✓ (§1; EVD-CLOSURE-001); remaining four pending C2–C10.

## Non-authorization

This draft grants no authority, issues nothing by itself, mutates no register/schema/docket/
validator, signs no mandate, and completes no phase. Gate 1 and PG-P0 closure do not implicitly open
PG-P1. It is content staged for the accountable human authority to re-issue against this exact text.
`PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized; `main` `a908bbe`.

## Issuance record — 2026-07-27

**Outcome:** RE-ISSUED / EFFECTIVE, against the exact v0.3 text.
**Issued by:** `HUMAN-OPERATOR-001` (Engineering Authority, DIRECT), holding both scoped actions
(`APPROVE_PROGRAM_REGISTERS`, `APPROVE_GOVERNANCE_BASELINE`) per `PG-REG-IDENTITY-001`.
**Attestation:** "As HUMAN-OPERATOR-001, I re-issue PG-P0-INTERP-002 against v0.3 at a210e8a4."
**Issued at:** 2026-07-27T00:00:00+07:00
**Exact-text binding:** commit `a210e8a41f8975351890f6f673e6b82bc458870b`, v0.3 file SHA-256
`15c01709219e575d76435a57d09967cdc3e5fb6af2a39c9a49e81d1a24f45d64`; independent review receipt
`EVD-CLOSURE-003` (`ACCEPT_EXACT_SHA`, no finding).
**Supersedes:** the v0.2 issuance (SIGNING-PASS-9 at `32271aa2`), preserved as history.
**Recorded in:** `docs/00-governance/signing/SIGNING-PASS-10.md`

The interpretation above is hereby effective with its bounds, corrections, consolidated execution
lineage, C0–C11 sequence, and six-condition acceptance rule in full. The immutable "Draft;
ineffective" header reflects authoring-time status and is preserved unchanged per the extend-only
principle; this issuance record is the authoritative current state. C1 is complete on this lineage;
C2–C11 remain, each separately gated. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
