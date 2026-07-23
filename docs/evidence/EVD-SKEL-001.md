# EVD-SKEL-001 — bOPEN Repository Skeleton Evidence

**Version:** 0.1  
**Status:** Draft evidence; not an acceptance record  
**Work package:** `SKEL-P0-01`  
**Owner:** Engineering Authority  
**Generated at:** 2026-07-24T01:39:14+07:00  
**Base commit:** `9a80f9d042f1ed176c9939bae57953443d0c5964`  
**Candidate branch:** `agent/skel-p0-01-repository-skeleton`

## Scope evidence

- Original root `README.md` bytes are preserved.
- All new repository content is within the work package's structural, contract, test, validator, documentation, or validate-chain scope.
- No research upstream, signed docket, binding inventory, governance register, root-ledger genesis, secret, migration, runtime configuration, or deployment surface is present.

## Structural evidence

- Nine populated top-level zones have README and scoped `AGENTS.md` controls.
- Eleven one-to-one contract shells are version 0.1.0, `status: draft`, non-stable, and semantically open.
- Two private typed package roots are version `0.0.0-draft.1` and expose no runtime entry point.
- Five future test tiers include a fail-closed placeholder guard.

## Validation commands

```text
python3 -B tools/validate_skeleton.py
python3 -B tests/run_harness.py
npm run build
npm run lint
npm test
npm run validate
pnpm validate
```

## Observed result

| Command | Result |
|---|---|
| `python3 -B tools/validate_skeleton.py` | **PASS** — 8 control groups, 0 findings |
| `python3 -B tests/run_harness.py` | **PASS** — 10 tests, 0 failures |
| `npm run build` | **PASS** — both empty typed package roots verified |
| `npm run lint` | **PASS** — both package manifests plus 6 lint-mode control groups |
| `npm test` | **PASS** — 10 guard/validator tests plus both package emptiness tests |
| `npm run validate` | **PASS** — complete build → lint → test → full skeleton-validation chain |
| `pnpm validate` | **Environment-limited rerun pending** — the repository pins `pnpm@11.17.0` and exposes the same `validate` lifecycle, but no pnpm executable or package-registry network was available in the maker environment. The exact-SHA checker must execute this entrypoint. |

**Maker environment:** Node.js `v22.16.0`; npm `10.9.2`; Python `3.13.5`.

The fail-closed behavior was also exercised against a temporary injected runtime file: all five tiers denied the candidate without a tier-marked negative test, and a marker for one tier did not satisfy another tier.

## Exact-tree binding

`docs/manifests/SKEL-P0-01.package-manifest.json` binds each payload path, byte count, and SHA-256. `docs/ledgers/repository-change-ledger.ndjson` appends a hash-chained preparation entry that binds the manifest and payload digests. The ledger explicitly is not root governance.

The Git commit SHA cannot be embedded in the same commit without self-reference. The independent checker must therefore obtain the exact candidate SHA from the branch/PR head, verify that its tree matches the manifest, and record the disposition externally or in a later authorized append.

## Pending external gates

- Independent checker acceptance by BST-Codex-Motor at the exact final SHA.
- Attributable Human Engineering Authority acceptance.
- Any later implementation, activation, publication, release, or production authorization.
