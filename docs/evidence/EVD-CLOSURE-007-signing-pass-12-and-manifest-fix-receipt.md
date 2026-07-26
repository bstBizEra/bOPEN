# EVD-CLOSURE-007 — Durable checker receipt: SIGNING-PASS-12 issuance + legacy-manifest housekeeping

**Version:** 0.1
**Status:** Durable independent-review receipt (maker-persisted verbatim per issued PG-P0-INTERP-002 §7)
**Persisted:** 2026-07-27
**Persisted by:** Claude (BST-SA Motor worker agent) — maker; did not author the receipt content
**Runtime pointers (non-anchor):** review tasks `bizrdstut` (initial, REJECT on pre-existing manifest
staleness) and `bsad7ar0b` (re-review after housekeeping fix, ACCEPT)

## Checker receipt (verbatim)

```yaml
receipt:
  subject_commit: 425178acffbdba3952f636bfeb084af0d710d9d6
  subject_tree: bbb4aa083e259c8c174dfbc2865271e867c741d5
  parent: 1837521609dd3ac1ab6e6dbd9d62a38818ae402a
  bound_v04_sha256: f4948f9034a04ebcc3926b58f8d1bc1d94e190c15a6019e09e451a37d6992d8e
  checker: BST-Codex-Motor
  independent: true
  tools: Python 3.13, pnpm 11.9.0, Git
  test_results_sha256: 29a3fd71112b23d4c29b1104a9e741fce419a8a0111be81918324754668a1e0c
  timestamp: 2026-07-27T03:00:07+07:00
  verdicts:
    signing_pass_12_issuance: ACCEPT_EXACT_SHA
    manifest_housekeeping: ACCEPT
self_certification:
  maker: Claude Opus 4.8
  maker_self_certification: false
  checker_authored_commits: 0
  checker_independent: true
```

## Findings (summarized)

- Default and canonical document-manifest `--check`: both PASS at HEAD; `pnpm validate`: PASS; full
  test discovery 189/189 PASS.
- **Pre-existing-staleness independently confirmed:** the default `generate_document_manifest.py
  --check` FAILS at the accepted head `73912e4` and at base' `52bd96ec` — proving the manifest
  staleness predates all closure work and is not part of the canonical `pnpm validate` gate.
- Housekeeping scope: exactly the three intended files (CHANGELOG + both manifests); protected-surface
  and issuance diffs both 0 lines; Claude-only authorship.
- **SP-12 issuance intact:** binds v0.4 blob `f4948f90…`; C2 trust-root candidate blob `0641b01a…`
  unchanged. No new finding.
- Boundary: `PG-P0 ACTIVE`; trust root `APPROVED_PENDING_PROOF_OF_POSSESSION`; no register/validator
  mutation; no mandate signed or accepted.

## Note on manifest regeneration order (operational)

The tool-default manifest `docs/DOCUMENT-MANIFEST.json` **indexes** the `GOV-P0-02` manifest (names
differ, so it is not excluded), while `GOV-P0-02` excludes the default. Both must be regenerated
GOV-P0-02-first, default-last. All subsequent closure commits regenerate both, in that order.

## Status effect

None. Technical evidence only; the v0.4 re-issuance remains the accountable human authority's act.
`PG-P0 ACTIVE`; `PG-P1 NOT_READY`; production not authorized.
