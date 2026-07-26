# PG-P0 Signing Pass 11 — C2 trust-root approval (APPROVED_PENDING_PROOF_OF_POSSESSION)

**Version:** 0.1
**Status:** Signed operator C2 approval receipt; encoded append-only in this commit
**Operator:** `HUMAN-OPERATOR-001` (identity register `PG-REG-IDENTITY-001`, approved 2026-07-22)
**Signed at:** 2026-07-27T00:00:00+07:00
**Recorded by:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Source:** explicit operator attestation in the current Claude Code session, 2026-07-27 — "As
HUMAN-OPERATOR-001, I approve the trust-root candidate at 8346f33e".

## No-circularity note

This is the **separate C2 approval receipt** required by the closure protocol. It binds the resulting
K4 candidate commit/tree/blob identity (which the candidate file itself does not and cannot contain).
The approved candidate file is **not mutated** by this approval — it remains byte-identical so the
digests bound below stay valid; this receipt is the authoritative statement of the new lifecycle
status.

## C2 binding (exact subject the operator approved)

```yaml
subject:
  parent_commit:          d0a88aa3a2a89acb9cc21b4570adc545195832e5
  candidate_commit:       8346f33e9d10326a2b3a99977495fb4bba99eaa0
  candidate_tree:         42ab3439cb5b304e0a549032eb083e3729c64ec3
  trust_root_blob_oid:    0641b01adce2aa1311a47bdd93ead21241992a5b
  trust_root_raw_sha256:  a6806c1645bcb2f700764ac21009ea58d3cbf8245fdf87540ef6b64b771eebba
  public_key:             83696c1bf3f47fbba21dd40a928e31b7845753364f6733a00be5c4b27caeb637
  public_key_fingerprint: 87c9cd7ece4790733ef7ca6dc4ebfd0f855d6ca87c2f6a8fb9ba64ee3f70bf1d
  fingerprint_profile:    sha256:rfc8032-ed25519-raw-32
authority:
  authority_basis_ref:    PG-P0-INTERP-002 v0.3 (SIGNING-PASS-10 at 266ca800d1f33c1f03324a36166307dd42c15c21)
  permitted_action:       COMPLETE_PG_P0_SCHEDULE_TRANSITION
  effective_at:           2026-07-27T00:00:00+07:00
  expires_at:             2026-08-21T00:00:00+07:00
  revocation_reference:   docs/00-governance/signing/ (append-only revocation record naming keyid operator-pgp0-completion-1)
activation:
  status:                 APPROVED_PENDING_PROOF_OF_POSSESSION
  proof_event:            first valid C4 Stage-1 mandate signature verified by VERIFY-P0-01 against the bound public key
```

## Signed decision

The operator, as **Engineering Authority**, **approves the PG-P0 completion trust-root candidate** at
commit `8346f33e` (trust-root blob `0641b01a…`, raw SHA-256 `a6806c16…`), authority basis
`PG-P0-INTERP-002 v0.3`. The candidate's lifecycle status advances
`CANDIDATE_PENDING_C2_APPROVAL → APPROVED_PENDING_PROOF_OF_POSSESSION`.

Attestation: *"As HUMAN-OPERATOR-001, holding APPROVE_PROGRAM_REGISTERS and
APPROVE_GOVERNANCE_BASELINE under PG-REG-IDENTITY-001 and acting under the issued PG-P0-INTERP-002
v0.3, I approve the trust-root candidate at 8346f33e binding the digests above. I take
accountability."*

## Boundary — the trust root is NOT yet effective

Approval binds the key to the authority basis but does **not** activate the trust root. Per the
staged-activation protocol (operator research verdict), the trust root becomes `ACTIVE` **only** upon
the first valid C4 Stage-1 mandate signature verified by `VERIFY-P0-01` against the bound public key
(RFC 8032 verification; RFC 4210 proof-of-possession by signing) — proving the operator possesses the
private key. Until then:

- no mandate is accepted; no `SCHEDULE-REGISTER.json` or docket-validator mutation occurs;
- no authoritative ref is moved; PG-P0 is not complete; PG-P1 is not opened; production is not
  authorized. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; `main a908bbea1975ffc52a636765cd9f823dfeb978eb`.

Next: C3 freezes the closure manifest + canonical Stage-1 mandate bytes (sorted `evidence_refs`); C4
is the operator's local signature over those exact bytes; K8–K10 verify and activate.

## Independent verification

The maker (Claude) encoded this approval receipt and does not self-certify. An independent
BST-Codex-Motor exact-SHA review must confirm the bound digests match the K4 candidate exactly, the
candidate file is unmutated, the status transition and non-activation boundary are correctly stated,
and the encoding is additive and passes full validation; a durable receipt is produced per §7 of the
issued interpretation.
