# EVD-CLOSURE-012 - Advisory maker-side rehearsal: C6-C8 execution dry-run (EXECUTION_PROVEN)

**Version:** 0.1
**Status:** Advisory execution-rehearsal evidence (maker-side). NOT an independent-checker receipt; NOT
an execution. Produced by a Claude worker sub-agent (motor lane) using ONLY a throwaway Ed25519 key in a
scratch worktree that was destroyed. It authorizes nothing; the operator's real C4 signature and the real
C6-C9 execution remain the sole authority.
**Persisted:** 2026-07-27 by Claude (BST-SA Motor worker, maker). **Runtime pointer (non-anchor):** ac5f948d.
**Subject:** the frozen PG-P0 closure at lineage head; predecessor `e80f7b93...`, authorized successor
`1f8d183e...`, mandate `0f34a306...`, PAE `bd5113a6...`.

## Verdict: EXECUTION_PROVEN

A throwaway dry-run applied the full coordinated closure and every gate passed: committed successor
digest == `1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863`; `validate_pg_g0_authority_
docket.py --check` PASS; both document-manifest `--check` paths PASS; `VERIFY-P0-01 verify_transition`
=> VERIFIED / VERIFIED_EXACT (signer HUMAN-OPERATOR-001); full unittest suite 189 OK (after the test
delta below); PG-P1->ACTIVE drift makes `--check` FAIL then restore PASS. Throwaway key only; scratch
worktree removed; real branch `pg-p0-closure-lineage` unchanged.

## Material finding (drove the C3 manifest re-freeze)

The C3 manifest's original `permitted_effects` omitted a THIRD required file:
`tests/governance/test_program_control_validation.py`. Two of its tests hardcode PG-P0 == ACTIVE and
fail the C7 full-regression unless the closure commit also carries a small test delta (proved green,
189 OK). `tools/validate_program_controls.py` itself needs NO change (its PG-P0 rule is skipped once
COMPLETE; the schedule-window check still passes). The C3 closure manifest has been corrected to add
this permitted effect; the mandate/predecessor/successor/PAE digests are unchanged, so the operator's
C4 signature subject is unaffected.

## The proven, ordered C6-C8 procedure (for the REAL mandate)

- **C6.2 (signature-independent):** apply the single-line PG-P0 schedule mutation (status
  ACTIVE->COMPLETE, planned_end 2026-07-27T00:00:00+07:00, rebaseline_decision_ref +
  evidence_refs[sorted]); confirm RFC8785 digest == `1f8d183e...`.
- **C6.3 (signature-independent):** apply the docket validator extension - new constants
  (P0_COMPLETED_AT / P0_COMPLETE_DECISION_REF / P0_COMPLETE_EVIDENCE_REFS) + the PG-P0 expected branch
  switched to the COMPLETE shape + a new `validate_pg_p0_closure_authorization(root)` implementing the
  INTERP-002 v0.4 §5 anti-self-validation checks (live PG-P0 == COMPLETE shape; PG-P1 stays NOT_READY;
  closure signing record exists/tracked/non-empty and names both actions + the closure-manifest SHA-256;
  every evidence ref exists/tracked; signer identity effective+unrevoked at P0_COMPLETED_AT; no crypto -
  that stays in VERIFY-P0-01), wired after `validate_signed_artifact_transforms(root)`.
- **C6.4 (signature-independent):** apply the test delta to
  `tests/governance/test_program_control_validation.py`.
- **C6.5 (THE one signature-dependent artifact):** create
  `docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md` with the REAL operator DSSE envelope + decision
  text; per §5 it MUST name both authorizing actions and the closure-manifest SHA-256 and carry the
  `#signed-decision` anchor. ASCII-only, UTF-8, LF; git-add (must be tracked before the checks).
- **C6.6 (derived):** regenerate GOV-P0-02 manifest first, then the default manifest.
- **C7:** docket --check + both manifest --check + VERIFY-P0-01 (real envelope/trust root) VERIFIED_EXACT
  + PG-P1-drift negative + full unittest 189 OK.
- **C8:** ONE execution commit = schedule + validator + test delta + mandate record + both manifests.

What differs with the real signature: ONLY the DSSE bytes inside PG-P0-CLOSURE-MANDATE.md (and hence the
two derived manifest entries for that record) - regenerate, never copy the rehearsal's. The schedule
successor bytes, the validator diff, and the test delta are byte-identical regardless of signature.

## Load-bearing note

Because the §5 checks are included, the real PG-P0-CLOSURE-MANDATE.md content is load-bearing for
`docket --check`: it must name both actions and the corrected closure-manifest SHA-256
`7417cc6a7bdffc6cac0b3707be293fb01ec17434f848d831c2383f374cafb33a`. The operator's C4 record authoring
(or the maker's assembly of it around the operator signature) must satisfy this or C7 fails.

```yaml
self_certification:
  agent_id: claude-motor
  certification_scope: advisory_only
  independent_of_maker: false
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

Status effect: none. Rehearsal evidence that C6-C8 is mechanical and validates end-to-end. `PG-P0 ACTIVE`;
`PG-P1 NOT_READY`; production not authorized.
