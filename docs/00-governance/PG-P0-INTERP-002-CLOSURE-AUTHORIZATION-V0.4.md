# PG-P0-INTERP-002 v0.4 (DRAFT) — Closure authorization: §4 evidence-refs de-circularization

**Version:** 0.4
**Status:** Draft; ineffective — for human re-issuance against this exact text
**Supersedes:** v0.3 (issued via SIGNING-PASS-10 at `266ca800d1f33c1f03324a36166307dd42c15c21`;
v0.3 text digest `15c01709219e575d76435a57d09967cdc3e5fb6af2a39c9a49e81d1a24f45d64`). Upon human
re-issuance against this v0.4 text, the v0.3 issuance is superseded. The v0.3 file and SIGNING-PASS-10
are preserved byte-faithfully in this lineage as history.
**Scope of the v0.4 change — §4 ONLY.** During C3 preparation the exact `VERIFY-P0-01` /
docket contract revealed that v0.3 §4's sanctioned successor `evidence_refs` set included the
`<post-execution receipt>`. That receipt (closure step C10, evidence layer 3) attests the C8 execution
commit and therefore cannot exist inside the bytes committed at C8; the docket's evidence-ref
existence check would fail at execution. v0.4 corrects §4 so the successor's `evidence_refs` reference
only execution-time-available evidence, and the post-execution receipt attests the result externally
(true layer-3 separation, per §3). **Everything else is unchanged from v0.3** — the §1–§2 authority-scope
finding and dual-action basis, §3 evidence layers, §5 validator extension, §6 C0–C11, §7 durable
receipts, §8 acceptance rule.
**Effect on prior C-step artifacts (unchanged and still valid):** because §1–§2 authority and the
trust-root mechanism are untouched, the trust-root candidate (`8346f33e`) and the operator's C2
approval (SIGNING-PASS-11 at `5b19fd13`) remain valid; re-issuing v0.4 re-affirms the same authority
basis. Only the C3 successor-bytes definition changes.
**Interpretation id:** `PG-P0-INTERP-002`
**Owner / accountable authority:** Engineering Authority
**Maker:** Claude (BST-SA Motor worker agent)
**Independent checker:** BST-Codex-Motor (exact-SHA review; durable receipt required)

## 0. Consolidated execution lineage (operator hard check)

This interpretation is authored on the **accepted integrated base'
`52bd96ecc66ae910942ce0c245858cfcb8fc20fa`** (Gate-1-accepted via SIGNING-PASS-8), which **contains
`tools/verify_phase_transition.py` (VERIFY-P0-01) and its 27-test suite in-tree** — satisfying the
requirement that VERIFY-P0-01 exist in the exact execution lineage ("exists in another base" is
insufficient). All governing closure records are carried into this lineage byte-faithfully; the v0.4
successor descends from the C2 approval receipt (`294f8177`), which itself descends from the trust-root
candidate (`8346f33e`), SIGNING-PASS-10 (v0.3 issuance), and EVD-CLOSURE-001..005. The closure
execution (C3–C10) proceeds on this lineage only.

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

## 4. The single sanctioned schedule mutation (v0.4: execution-time evidence_refs, canonical sorted)

Only the PG-P0 entry changes (schema `additionalProperties: false` — no new fields):
- `status`: `ACTIVE` → `COMPLETE`
- `planned_end`: `null` → `<closure-effective-time>`
- `rebaseline_decision_ref` → `<closure mandate signing record>#signed-decision`
- `evidence_refs` → **the canonical sorted list** `sorted({
  "docs/00-governance/signing/SIGNING-PASS-8.md",     # Gate-1 acceptance of the integrated base
  "docs/00-governance/signing/SIGNING-PASS-10.md",    # v0.3 authority issuance (superseded by v0.4 re-issuance, retained as the lineage authority record)
  "<closure mandate signing record>"                  # the C4 closure decision (the mandate's own signing record), which exists at C8
  })`

**Normative rule (v0.4 — de-circularized).** The successor's `evidence_refs` reference **only
execution-time-available evidence**: artifacts that already exist and are git-tracked at the moment of
the C8 execution commit. The **post-execution closure receipt (C10, evidence layer 3) is NOT a member
of this set** — it attests the resulting commit *externally* and must not be embedded in the bytes it
attests (§3). The array MUST be in canonical ascending lexicographic order — exactly `sorted(...)` of
the sanctioned set — matching the docket validator's canonicalization; any narrative ordering in
examples is non-normative. At C4 the `<closure mandate signing record>` path is fixed and its file is
created together with the mandate, so all three members exist and are tracked before C8; the frozen
closure manifest (C3) MUST list the final concrete paths in canonical order. PG-P1..PG-C0 remain
`NOT_READY` byte-identically.

## 5. Validator extension with anti-self-validation checks (unchanged)

Constants `P0_COMPLETED_AT`, `P0_COMPLETE_DECISION_REF`, `P0_COMPLETE_EVIDENCE_REFS` (a set; the
expected-state builder applies `sorted(...)`); PG-P0 branch → `COMPLETE` shape. Beyond constant
equality the extended check MUST require: the closure signing record exists, is tracked, non-empty,
and names both authorizing actions + the closure-manifest SHA-256; every evidence ref exists and is
tracked; the schedule successor equals the exact expected bytes with all existing unrelated-drift
checks fully in force; the signer's identity-register binding was effective and unrevoked at
`P0_COMPLETED_AT`. Cryptographic verification (DSSE/Ed25519 vs the effective trust root) is performed
by `VERIFY-P0-01` — present in this lineage (§0) — and by the independent checker.

## 6. Corrected closure sequence (binding; C1 re-executes for v0.4)

```
C0  Freeze full baseline commit/tree + relevant blob digests          [this lineage's head]
C1  Authority-scope finding verified + interpretation issued          [re-issue against v0.4 exact text]
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

Status of conditions at v0.4 authoring: `PROVEN_MECHANISM` ✓ (EVD-CLOSURE-002);
`AUTHORITY_SCOPE_VERIFIED` ✓ (§1; EVD-CLOSURE-001); `C1` (v0.3) issued and `C2` trust root approved
(SIGNING-PASS-10, SIGNING-PASS-11; EVD-CLOSURE-003/004/005) — `TRUST_ROOT_EFFECTIVE` still pending C4
proof-of-possession; remaining conditions pending C3–C10 under this corrected text.

## Non-authorization

This draft grants no authority, issues nothing by itself, mutates no register/schema/docket/
validator, signs no mandate, and completes no phase. Gate 1 and PG-P0 closure do not implicitly open
PG-P1. It is content staged for the accountable human authority to re-issue against this exact text.
`PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized; `main` `a908bbe`.

## Issuance record — 2026-07-27

**Outcome:** RE-ISSUED / EFFECTIVE, against the exact v0.4 text.
**Issued by:** `HUMAN-OPERATOR-001` (Engineering Authority, DIRECT), holding both scoped actions
(`APPROVE_PROGRAM_REGISTERS`, `APPROVE_GOVERNANCE_BASELINE`) per `PG-REG-IDENTITY-001`.
**Attestation:** "As HUMAN-OPERATOR-001, I re-issue PG-P0-INTERP-002 against v0.4 at e55012c3."
**Issued at:** 2026-07-27T00:00:00+07:00
**Exact-text binding:** commit `e55012c38d260e15f8f9d713c01db43bcb33059f`, v0.4 file SHA-256
`f4948f9034a04ebcc3926b58f8d1bc1d94e190c15a6019e09e451a37d6992d8e`; independent review receipt
`EVD-CLOSURE-006` (`ACCEPT_EXACT_SHA`, no finding).
**Supersedes (§4 only):** the v0.3 issuance (SIGNING-PASS-10 at `266ca800`), preserved as history;
the C2 approval (SIGNING-PASS-11) and trust-root candidate remain valid.
**Recorded in:** `docs/00-governance/signing/SIGNING-PASS-12.md`

The interpretation above is hereby effective. The immutable "Draft; ineffective" header reflects
authoring-time status and is preserved unchanged per the extend-only principle; this issuance record
is the authoritative current state. C1 is complete on this lineage; C2 trust root remains
`APPROVED_PENDING_PROOF_OF_POSSESSION`; C3–C11 remain, each separately gated. `PG-P0 ACTIVE`;
`PG-P1 NOT_READY`; production not authorized.
