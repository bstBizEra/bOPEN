# EVD-SKEL-002 — SKEL-P0-01 Exact-SHA Checker Review

**Verdict:** `REJECT_EXACT_SHA`
**Checker:** BST-Codex-Motor (independent checker of record)
**Reviewed candidate SHA:** `d4fe0d1bcce237a6f373b23784b881cf654b7c6f`
**Candidate tree:** `2a72b69baadaa3b257005e2b5abbafb886021a2f`
**Actual parent:** `9a80f9d042f1ed176c9939bae57953443d0c5964`
**Required parent:** `29949f460345a55b8f8079cad802d6ca85cbe46e`
**Review timestamp:** 2026-07-24 (Asia/Vientiane)
**Review workspace:** fresh detached worktrees `C:\bopen-check2` and `C:\bopen-check3`; initial status clean.

## Ranked findings

1. **P0 — wrong governed base (exact-SHA prerequisite failure).** `docs/work-packages/SKEL-P0-01.md:59` records base `9a80f9d`, and `git rev-list --parents -n 1 d4fe0d1` confirms that parent. `git merge-base --is-ancestor 29949f4 d4fe0d1` exited `1`. The candidate is therefore not descended from the governed PG-P0 ACTIVE substrate and is ineligible for acceptance.
2. **P0 — destructive scope/governance replacement.** Relative to required parent, `git diff --shortstat` reports `437 files changed, 2273 insertions(+), 33069 deletions(-)`, including deletion of `AGENTS.md`, governance registers, signing passes, dockets/binding inventories, and prior validation surfaces. This is not an additive skeleton and can erase immutable governance controls.
3. **P0 — governed validation does not pass at the exact SHA.** In a clean checkout, `pnpm validate` reached the root `build` and then `lint`, but failed at `python3 -B tools/validate_skeleton.py --mode lint` because `python3` was unavailable (exit non-zero). The exact required `python -m unittest discover -s tests -p 'test_*.py'` ran `0` tests and exited `5`. `python tools/validate_skeleton.py` (using the available Python launcher) reported `58` baseline findings, including every payload manifest entry mismatch and `ledger does not bind current manifest/payload`, exit `1`. The custom `tests/run_harness.py` also failed its full-validation test (10 tests, 1 failure).
4. **P0 — manifest is environment-dependent and stale.** `tools/validate_skeleton.py:64` hashes working-tree bytes directly, while the candidate deletes `.gitattributes`. With `core.autocrlf=true`, `apps/AGENTS.md` was `1345` bytes / SHA `ac67da...`, versus manifest `1328` bytes / SHA `82d664...`; the validator consequently rejects the checkout. No LF normalization or repository eol policy binds the hash.
5. **P1 — contract traceability cannot be independently resolved.** Contract shells such as `contracts/draft/tenant.contract.json:20-31` point to `artifact:BOPEN-TENANT-001`, but the candidate deletes the normative platform drafts that define that artifact. The checker cannot establish the required 1:1 trace to a named normative draft in the candidate tree.
6. **P1 — maker provenance is not attributable from the exact object.** `docs/evidence/EVD-SKEL-001.md:48` claims a Claude maker environment, but commit metadata identifies `BizEra <ounkhamvilay@gmail.com>` and the candidate has no model/session receipt binding the bytes to Claude. Independent checker identity is separate, but maker attribution remains unverifiable.

## Exact commands and results

```text
git status --short --branch                 => clean detached worktree at start
git rev-list --parents -n 1 d4fe0d1         => d4fe0d1 9a80f9d...
git merge-base --is-ancestor 29949f4 d4fe0d1 => exit 1
pnpm validate                                => exit non-zero at python3 lint step (python3 unavailable)
python -m unittest discover -s tests -p 'test_*.py' => Ran 0 tests; NO TESTS RAN; exit 5
python tools/validate_skeleton.py           => FAIL (58 baseline findings); exit 1
py -3 tests/run_harness.py                  => 10 tests, 1 failure (manifest/validator); exit 1
```

## Adversarial fail-closed checks

- Injected executable `apps/runtime.py`; `py -3 tools/validate_skeleton.py --mode lint` denied it with `[business_logic] apps\\runtime.py: Python AST contains executable/import/definition nodes` and exit `1`.
- Changed `contracts/draft/tenant.contract.json` control status from `draft` to `active`; validator denied it with `[contracts] tenant.contract.json invalid status` and exit `1`.

## Control disposition

| Control | Result |
|---|---|
| Required ACTIVE parent | **FAIL** |
| Exact SHA/tree binding | **FAIL** (tree recorded above; package manifest/ledger mismatch) |
| SKELETON-ONLY scope | **FAIL** (governed substrate deletions) |
| Draft contract shells | **BLOCKED/FAIL** (promotion denial works; normative sources absent) |
| Fail-closed runtime guard | **PASS** (adversarial denial observed) |
| Fail-closed draft promotion guard | **PASS** (adversarial denial observed) |
| Portability/LF hashing | **FAIL** |
| Maker/checker provenance | **BLOCKED** (maker receipt not attributable) |
| Production/merge/push/release/deploy authority | **UNAUTHORIZED** |

## Required remediation

Rebuild from parent `29949f460345a55b8f8079cad802d6ca85cbe46e`; preserve all governed files and immutable PG-G0 state; make additions strictly additive; regenerate and verify manifest/ledger in a clean short-path checkout; add LF normalization (`.gitattributes` or equivalent validator normalization); ensure `python -m unittest discover` discovers the complete suite; include attributable Claude maker/session provenance; then submit a new exact SHA for a fresh independent review.

## Required status

```yaml
truth_status: rejected_exact_sha
authority_status: advisory_only
implementation_status: candidate_rejected
risk_class: P0-governance-and-reproducibility
self_certification:
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

This record is technical checker evidence only. It does not accept for production, merge, push, release, deployment, activation, or self-authorize any subsequent action. Final disposition remains with the attributable Human Engineering Authority.
