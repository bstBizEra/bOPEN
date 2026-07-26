# Authority Interpretation (DRAFT) — `ACCEPT_EVIDENCE` scope for accepting an integrated preparation base

**Version:** 0.1
**Status:** Draft interpretation; ineffective — for issuance by the accountable human authority
**Interpretation id:** `PG-P0-INTERP-001`
**Owner / accountable authority:** Engineering Authority (accountable for `ACCEPT_EVIDENCE`)
**Issued:** 2026-07-25
**Maker:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Independent checker:** BST-Codex-Motor (must review the exact final SHA)

## Purpose

Resolve the Gate-1 authority-basis gap **without mutating any register**. Earlier disposition
required that `ACCEPT_EVIDENCE` "must not be silently treated as equivalent without an explicit
scope mapping," and offered two safe options: (1) add a dedicated `ACCEPT_INTEGRATED_BASE` action,
or (2) obtain an authoritative interpretation that `ACCEPT_EVIDENCE` permits accepting this exact
preparation baseline. Option 1 was pursued but is **blocked**: adding an authority action mutates the
live `AUTHORITY-MATRIX.json` and `AUTHORITY-IDENTITY-REGISTER.json`, which the terminal PG-G0
authority docket validates against its signed substrate (any change fails
`validate_pg_g0_authority_docket.py --check` with "differs from signed outcome" / "current identity
registry drift"). This draft provides the **Option-2 explicit scope mapping** so `ACCEPT_EVIDENCE`
can be used attributably — and, because it adds no action and changes no register, it does not
disturb the terminal PG-G0 docket.

## Interpretive question

Does the `ACCEPT_EVIDENCE` action (`evidence_acceptance`; accountable Engineering Authority; no
required concurrence; `self_approval_allowed: false`; `evidence_required: true`; `expiry_required:
false`), which `HUMAN-OPERATOR-001` holds, permit **accepting a specific, byte-reviewed integrated
preparation base** — identified by exact commit + tree — as the frozen baseline for subsequent
governed decisions, on the strength of independent exact-SHA review evidence?

## Proposed ruling (to be issued by the accountable human authority)

> **YES, bounded.** `ACCEPT_EVIDENCE` covers accepting a specific integrated preparation base
> identified by its exact commit and tree, on the strength of independent exact-SHA review evidence,
> as the frozen baseline for subsequent governed decisions. Such an acceptance is an
> *evidence_acceptance*: the operative act is accepting that the independent review evidence
> (each carrying an `ACCEPT_EXACT_SHA` verdict) establishes the base as a faithful, byte-reviewed
> work product — not the grant of any new authority, phase transition, or register change.

**Applies to:** `ACCEPT_EVIDENCE` acceptance of the integrated preparation base
`52bd96ecc66ae910942ce0c245858cfcb8fc20fa` (tree `2aab11dd9b895a38b1d41de2281778bca3cdc776`, parent
`73912e483cc9f4b5bc107f84564b955c9a335ca4`), whose faithfulness is established by the independent
reviews `b3j5vmwa4` (base') and `bwvaoowr0` (package `e74b797f`), both `ACCEPT_EXACT_SHA`.

## Scope mapping rationale

- The action `ACCEPT_EVIDENCE` is `evidence_acceptance`; accepting an integration base *on the
  strength of independent review evidence* is squarely evidence acceptance, not a distinct action.
- `evidence_required: true` is satisfied (two independent `ACCEPT_EXACT_SHA` receipts + verified
  byte-equivalence of the integrated blobs).
- No required concurrence; `self_approval_allowed: false` is honoured (the maker of the reviewed
  candidates does not accept; the human authority does).
- It requires no register mutation, so it is compatible with the terminal PG-G0 authority docket.

## Bounds and exclusions (this interpretation is narrow)

- It authorizes accepting a **preparation baseline as verified evidence** only. It does **not**
  broaden `ACCEPT_EVIDENCE` to authorize phase completion, register mutation, gate-contract
  activation, trust-root establishment, mandate signing, merge to `main`, opening `PG-P1`, or
  production. Those remain their own separately-gated decisions.
- It is specific to a base whose faithfulness is established by independent **exact-SHA** review; it
  is not a general licence to accept arbitrary artifacts under `ACCEPT_EVIDENCE`.
- It supersedes nothing signed and changes no register, schema, docket, or signing pass.

## Application (human authority; not performed here)

1. The accountable Engineering Authority (`HUMAN-OPERATOR-001`) issues this interpretation
   (append-only), and then issues an `ACCEPT_EVIDENCE` decision accepting `52bd96ec`, citing this
   interpretation as the explicit authority basis. Both are recorded append-only; independent
   exact-SHA review confirms the encoding.
2. No matrix/identity/schema/docket change occurs; the PG-G0 docket is undisturbed.
3. The `ACCEPT_INTEGRATED_BASE` action proposal, its `APPROVE_GOVERNANCE_BASELINE` change-package,
   and the associated incorporation are **withdrawn from the active path** (retained as historical
   evidence of the blocked Option-1 route).

## Non-authorization

This draft grants no authority, issues no interpretation by itself, accepts no SHA, mutates no
register/schema/docket, and completes no phase. It is content staged for the accountable human
authority to issue. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized; `main` `a908bbe`.

## Issuance record — 2026-07-27

**Outcome:** ISSUED / EFFECTIVE.
**Issued by:** `HUMAN-OPERATOR-001` (Engineering Authority, DIRECT), accountable for `ACCEPT_EVIDENCE`.
**Attestation:** "As HUMAN-OPERATOR-001, I issue PG-P0-INTERP-001 and ACCEPT_EVIDENCE for 52bd96ec."
**Issued at:** 2026-07-27T00:00:00+07:00
**Recorded in:** `docs/00-governance/signing/SIGNING-PASS-8.md`

The interpretation above is hereby effective, with its stated bounds and exclusions in full. It was
issued together with the `ACCEPT_EVIDENCE` acceptance of the integrated base `52bd96ec`
(SIGNING-PASS-8, Signed decision 2). The immutable header "Draft interpretation; ineffective" reflects
authoring-time status and is preserved unchanged per the extend-only principle; this issuance record
is the authoritative current state.
