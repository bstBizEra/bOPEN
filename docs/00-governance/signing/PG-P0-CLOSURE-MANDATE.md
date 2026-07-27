# PG-P0 Closure Mandate - Stage-1 signed completion mandate (C4/C5)

**Version:** 0.1
**Status:** Signed operator mandate; the DSSE envelope carries the operator's Ed25519 signature.
**Operator:** HUMAN-OPERATOR-001 (identity register PG-REG-IDENTITY-001, valid 2026-07-22 .. 2026-08-21).
**Signed at (verification time):** 2026-07-27T00:00:00+07:00
**Recorded by:** Claude (BST-SA Motor worker agent; maker) - recorded the operator-supplied signature;
did not create it.
**Authorizing actions (both held by HUMAN-OPERATOR-001):** APPROVE_PROGRAM_REGISTERS (the
SCHEDULE-REGISTER transition) and APPROVE_GOVERNANCE_BASELINE (the docket validator expected-state
extension), as scoped by PG-P0-INTERP-002 v0.4 (issued via SIGNING-PASS-12).
**Bound closure manifest:** docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST.json,
content SHA-256 = 7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a
(git blob OID ead29e9de3b88cd371bc5d969bdf9b6e6fb67cad; frozen at commit
27e70fa82e5ae5573658dbb0ca10f622fe232f56, operator-confirmed).

## Signed decision

The operator, as Engineering Authority, mandates the single sanctioned PG-P0 schedule transition
ACTIVE -> COMPLETE defined by the bound closure manifest, and authorizes the coordinated docket
validator expected-state extension per PG-P0-INTERP-002 v0.4 section 5. The decision is carried by the
DSSE envelope below (payload = the RFC 8785 canonical Stage-1 mandate; signed with keyid
operator-pgp0-completion-1 over the DSSE pre-authentication encoding).

decision_id: PG-P0-CLOSURE-001. operation: COMPLETE_PHASE. phase_id: PG-P0.
predecessor.schedule_digest: e80f7b9390d86a7627d6d14bd683296f2314189d145791971fb8aeb2a8d9f1cf.
authorized successor digest: 1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863.
mandate digest: 0f34a306ad63bb3457c1fdda3d3c9185bd99636314dc3008f2dc6ebc9acaf92c.
PAE SHA-256: bd5113a6edf87e03d8a80d60da41f430afbe8c7fe0e6a1e59c8352c221863d41.

## DSSE signed mandate envelope

The machine-verifiable envelope is `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.dsse.json`
(payloadType application/vnd.bopen.phase-completion-mandate+json; signatures[0].keyid
operator-pgp0-completion-1). VERIFY-P0-01 verifies it against the effective trust root (operator public
key 83696c1bf3f47fbba21dd40a928e31b7845753364f6733a00be5c4b27caeb637).

## Maker verification note (not the independent check)

The maker computed, on receipt of the operator's SIGNATURE_B64:
`verify_ed25519(operator_public_key, PAE, signature) = True` and
`verify_transition(...) = VERIFIED / VERIFIED_EXACT` (signer_identity HUMAN-OPERATOR-001, signer_keyid
operator-pgp0-completion-1). This establishes proof of possession, which advances the trust root
lifecycle APPROVED_PENDING_PROOF_OF_POSSESSION -> ACTIVE. This maker note is advisory; the independent
BST-Codex-Motor C5 check is authoritative.

## Boundary

This mandate authorizes ONLY the single sanctioned transition (schedule PG-P0 ACTIVE->COMPLETE + the
precedent-following docket expected-state extension + the required test delta, all per the bound
manifest's permitted_effects). It does NOT move any authoritative ref (C9 is the operator's expected-old
CAS commit), complete PG-P0 by itself (recognition is C11 after the post-execution receipt), open PG-P1
(stays NOT_READY), or authorize production. PG-P0 remains ACTIVE until C11; main a908bbe.
