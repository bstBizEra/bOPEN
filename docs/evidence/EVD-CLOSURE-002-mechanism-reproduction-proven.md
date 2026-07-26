# EVD-CLOSURE-002 — Independent reproduction of the coordinated closure mechanism: PROVEN

**Version:** 0.1
**Status:** Durable evidence record of an independent checker reproduction (maker-persisted; verdict
content from the checker's review output)
**Persisted:** 2026-07-27
**Persisted by:** Claude (BST-SA Motor worker agent) — maker; did not author the verdict
**Runtime pointer (non-anchor):** review task `bec7h8b9m`
**Checker:** BST-Codex-Motor (authored none of the reviewed bytes)
**Review subject:** closure-package draft `d8cf7abd152492d9f77984296971521b88341859` (INTERP-002
v0.1 + trust-root v2), reproduction executed from accepted head
`73912e483cc9f4b5bc107f84564b955c9a335ca4`

## Verdicts

- `mechanism_reproduction:` **PROVEN**
- `INTERP_002_draft (v0.1):` **REJECT_EXACT_SHA** — single inaccuracy (evidence-order, below);
  superseded by v0.2 (`6d139f8d`), whose content later received `ACCEPT_EXACT_SHA`
  (EVD-CLOSURE-001).

## What the checker reproduced (applied-and-committed standard)

In a scratch worktree from `73912e4`, the checker independently applied the coordinated closure —
`SCHEDULE-REGISTER.json` PG-P0 `ACTIVE → COMPLETE` (with `planned_end`, decision ref, evidence refs)
**plus** the docket-validator expected-state extension (`P0_COMPLETED_AT`,
`P0_COMPLETE_DECISION_REF`, `P0_COMPLETE_EVIDENCE_REFS`; PG-P0 branch → COMPLETE shape) — committed
it (scratch commits `44b20f0…`, canonicalization fix `9c70d5c…`), and ran the full validation chain:

- **All 11 validation components passed**, including `validate_pg_g0_authority_docket.py --check`,
  manifest `--check`, clean-room, secrets, supply-chain, and skeleton checks.
- A direct call of the docket validation function returned **zero errors**.
- **Fail-closed drift preserved:** additionally flipping PG-P1 failed with
  `signed register transformation differs from signed outcome:
  docs/00-governance/registers/SCHEDULE-REGISTER.json`.

## Material finding (carried forward)

The sanctioned `evidence_refs` example in the draft was written in narrative order, but the docket
validator canonicalizes with `sorted(...)`; the checker's literal application failed until the
register's `evidence_refs` were in canonical **sorted order**. Consequence for execution (closure
steps C3/C6): the frozen closure manifest and the executed successor bytes MUST list `evidence_refs`
in canonical sorted order. The sanctioned *set* is unaffected. Disposition of the issued v0.2 text
(clarification erratum vs corrected v0.3 re-issuance) is an operator decision, pending.

## Trust-root v2 (same review)

Structurally complete (all required binding fields); public-key and fingerprint placeholders
non-hex; **no private-key material**; secret scan passes. Caveat: `VERIFY-P0-01` is not present in
the `d8cf7abd` checkout (it lives in the integrated base' `52bd96ec` lineage); runtime enforcement
is certified there, not in that draft checkout.

## Status effect

None. This record is technical evidence for acceptance condition `PROVEN_MECHANISM` only. It signs
nothing, issues nothing, and completes no phase. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not
authorized.
