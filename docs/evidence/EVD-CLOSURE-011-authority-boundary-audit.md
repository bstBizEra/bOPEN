# EVD-CLOSURE-011 - Advisory maker-side audit: authority-boundary review

**Version:** 0.1
**Status:** Advisory governance audit (maker-side). NOT an independent-checker receipt.
**Class note:** Produced by a Claude worker sub-agent (immune lane), maker-side. It identifies risks and
confirms the authority discipline; it weakens no gate, authorizes nothing, and does not substitute for
independent BST-Codex-Motor verification (EVD-CLOSURE-001..008).
**Persisted:** 2026-07-27 by Claude (BST-SA Motor worker, maker). **Runtime pointer (non-anchor):** a13c04c6.
**Subject:** closure lineage HEAD `1f885049` (branch pg-p0-closure-lineage).

## Verdict: DISCIPLINE_HELD

1. **No agent self-authorization - PASS.** Every signing record (SIGNING-PASS-8..12) casts HUMAN-OPERATOR-001 as the authorizing actor and Claude only as recorder/maker, each with a first-person operator attestation and a non-self-certification clause. Zero instances of an agent "approving/authorizing"; no approval encoded without a human attestation.
2. **Human acts attributable - PASS.** INTERP-001 issuance (SP-8), INTERP-002 v0.3 (SP-10), v0.4 re-issuance (SP-12), C2 trust-root approval (SP-11) each cite HUMAN-OPERATOR-001 + the held action(s) + PG-REG-IDENTITY-001 and bind exact digests. The maker did not invent the authority basis.
3. **Trust root not prematurely effective - PASS.** Effective status APPROVED_PENDING_PROOF_OF_POSSESSION (never ACTIVE); public_key is real 64-hex; NO private-key material anywhere (check_secrets.py PASS); activation gated on the C4 signature. (Note: the candidate JSON literally still reads CANDIDATE_PENDING_C2_APPROVAL by digest-stability design; the advanced status lives authoritatively in the SP-11 receipt.)
4. **Independent verification of every maker artifact - PASS.** Each maker artifact has a matching BST-Codex-Motor durable receipt (EVD-CLOSURE-001..008) with an ACCEPT verdict; the reality of the review is evidenced by two initial REJECTs (EVD-007 pre-existing manifest staleness; EVD-008 cp1252 0x97 byte) accepted only after fixes. No maker artifact self-certified.
5. **Nothing merged / no ref abuse - PASS.** main `a908bbe` unchanged; the closure lineage shares no common ancestor with main (disjoint history off base' `52bd96ec`), so it physically cannot fast-forward production; no agent moved an authoritative ref; the only planned ref move (C9) is explicitly the human's expected-old CAS commit.
6. **Scope containment - PASS.** INTERP-002 v0.4 and the closure manifest's prohibited_effects forbid PG-P1..PG-C0 changes, matrix/identity/schema changes, agent ref-moves, and opening PG-P1 / authorizing research or production. PG-P1 stays NOT_READY (mandate invariant).
7. **Remaining human-only acts - CONFIRMED.** (a) C4 - the Ed25519 Stage-1 mandate signature (proof of possession; the sole event that flips the trust root to ACTIVE); (b) C9 - the expected-old compare-and-swap authoritative ref move. No agent can hold the key or perform either.

Advisory notes (not violations): the trust-root JSON status vs. receipt status distinction (design), and the disjoint-history property (stronger than "not merged").

```yaml
self_certification:
  agent_id: claude-immune
  certification_scope: advisory_only
  independent_of_maker: false
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

Status effect: none. Advisory confirmation that the maker/checker/human discipline held. `PG-P0 ACTIVE`;
`PG-P1 NOT_READY`; production not authorized.
