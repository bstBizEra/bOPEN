# EVD-CLOSURE-015 - Independent adversarial fail-proof of the PG-P0 apply pipeline

**Version:** 0.1
**Status:** Durable independent-checker receipt (maker-persisted verbatim per issued PG-P0-INTERP-002 section 7).
**Class:** Independent BST-Codex-Motor adversarial review. Pre-apply evidence; authorizes nothing.
**Persisted:** 2026-07-27 by Claude (BST-SA Motor worker, maker; did not author the receipt content).
**Runtime pointer (non-anchor):** review task bepj19liv.
**Subject:** the C6-C9 apply pipeline at parent `01ddb750aa719e0b3faf935418a001e907fb9e37`.

## Verdict: PIPELINE_FAILS_CLOSED

All nine negative cases were rejected; the happy-path control succeeded. No required-fail case passed.
All mutating work was performed in a disposable `git clone` (`C:/b-fpclone`, deleted); the operator's
private key was neither requested nor used.

**Artifact binding (decisive):** the review binds
`PATCH_SHA256 = 1A9FF63B949058D9B13653E134F5CF2DF1B7650611467B2ADFEBECBD499D88BE`. The maker independently
recomputed the SHA-256 of the on-disk apply patch and confirmed it MATCHES, so the artifact that was
adversarially proven is byte-identical to the artifact the operator applies.

| # | Case | Result | Failing gate / exact error |
|---|---|---|---|
| 1 | Forged signature | rejected | `SIGNATURE_INVALID: no valid signature from a trusted key` |
| 2 | Swapped payload | rejected | `SIGNATURE_INVALID` |
| 3 | Wrong key | rejected | `SIGNATURE_INVALID` |
| 4 | Missing mandate | rejected | `FileNotFoundError: ...PG-P0-CLOSURE-MANDATE.dsse.json` (gate fails; not skipped) |
| 5 | Tampered patch | rejected | `SUCCESSOR_MISMATCH: proposed successor != authorized recomputation`; docket stale |
| 6 | Wrong parent / CAS | rejected | `cannot lock ref ...: is at c090ff1... but expected 01ddb750...`; branch remained at the other value |
| 7 | Validator-only apply | rejected | docket: `PG-G0 authority readiness report is stale` |
| 8 | Schedule-only apply | rejected | docket: `PG-G0 authority readiness report is stale` |
| 9 | Reversed manifest order | rejected | `manifest snapshot stale: docs/DOCUMENT-MANIFEST.json` |
| 10 | Happy-path control | accepted | `VERIFIED: VERIFIED_EXACT`; commit + CAS succeeded IN THE CLONE ONLY |

Cases 7 and 8 independently confirm that the coordinated change cannot be split: the schedule mutation and
the docket validator extension must land in one commit. Case 6 confirms compare-and-swap protection. For
cases 1-5 and 7-9 no commit was created and no ref moved.

## Checker receipt (verbatim)

```text
SUBJECT: Adversarial fail-proof review of PG-P0 apply pipeline at parent 01ddb750aa719e0b3faf935418a001e907fb9e37
PATCH_SHA256: 1A9FF63B949058D9B13653E134F5CF2DF1B7650611467B2ADFEBECBD499D88BE
CHECKER_IDENTITY: BST-Codex-Motor
INDEPENDENCE_BASIS: Independent checker; scratch clone only; operator private key neither requested nor used
COMMANDS_TOOLS: Git clone --no-hardlinks; git apply; Python 3.13 validators; tools/verify_phase_transition.py; manifest generators/checks; docket, repository, contract, program-control, identity, clean-room, secret, supply-chain and skeleton validators; unittest discovery; Git commit and compare-and-swap update-ref
VERDICT: PIPELINE_FAILS_CLOSED
TIMESTAMP: 2026-07-27
ADVISORY_ONLY: true
EXECUTION_AUTHORITY: false
APPROVAL_AUTHORITY: false
READY_FOR_OPERATOR_REVIEW: true
```

## Source-repository integrity

`pg-p0-closure-lineage` remained `01ddb750aa719e0b3faf935418a001e907fb9e37`; `main` remained
`a908bbea1975ffc52a636765cd9f823dfeb978eb`. The clone was deleted.

## Status effect

None. Pre-apply evidence that the apply pipeline refuses to commit under tampered conditions. It is not
an apply, not an acceptance, and not a production authorization. `PG-P0 ACTIVE`; `PG-P1 NOT_READY`.
