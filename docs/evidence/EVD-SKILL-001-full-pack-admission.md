# EVD-SKILL-001 — Full skills pack admission evidence

**Document ID:** EVD-SKILL-001  
**Version:** 0.2
**Status:** Candidate evidence  
**Owner:** bOPEN Skills Authority  
**Updated:** 2026-07-22  
**Work item:** BOPEN-SKILL-P0-001  
**Governing artifacts:** BOPEN-BOOT-001; BOPEN-SKILL-001; BOPEN-SKILL-REGISTRY-001  
**Repository branch:** `codex/BOPEN-SKILL-P0-001-admission`
**Recorded at:** `2026-07-22T18:57:58+07:00`  
**Agent ID:** `Codex /root`

## Source

Source directory:

`C:\Users\ounkh\Downloads\bopen-full-skills-pack-0.1.0\bopen-full-skills-pack-0.1.0`

| Source artifact | SHA-256 |
| --- | --- |
| `SHA256SUMS` | `8af2082d79688ca1187b89796afb92966c7644082c75bff531359d19fb95d93f` |
| `PACK-MANIFEST.yaml` | `e1862762a731ef06a17c2fe1354617aa4cfe310170fb12e258e4a24d42ca99d8` |
| `validation-report.json` | `2f133d3f338b2fa4c73e716b3a29555b24ffb992a1cdeb413010b68faf6915d6` |
| `static-eval-report.json` | `7b79ef530d6f7388dabf1ba2f3412f536d3b6b19d1a2b1088f88825b2a24db78` |
| `test-report.json` | `e88500349a4b010b2bae0d8da792832a5c9486af0c23a2f95b6fbd84330ab700` |
| `requirements.lock` | `9fbfc0a2c0c14dd4bb1a7b2b4dcf9ed1b489c72df73fa44065520107303ef559` |
| `supply-chain/sbom.spdx.json` | `cbb58b996a110f9c1a39904d8f5398b87c15ded1dd6c5dec2705aa080b3ae816` |

The source pack is structurally validated but unsigned, uncommitted, not independently model-evaluated and not production-authorized.

## Duplicate and overlap disposition

- Preserved the richer existing `bopen-architecture`; the incoming collision was not copied.
- Reconciled `bopen-threat-model` as a successor candidate and retained confused-deputy coverage plus human Security Authority residual-risk acceptance.
- Admitted 20 non-colliding incoming packages.
- Preserved 12 existing-only specialist packages and the two reconciled collisions, producing 34 total registered skills.
- Kept audit design separate from evidence-envelope packaging.
- Kept Git delivery as an explicit-only orchestrator over Git governance, worktree and evidence specialists.
- Kept portal-context UX separate from runtime portal and tenant-isolation verification.
- Kept P0 conformance as an explicit-only evidence composer, not a self-authorizing gate.

## Admission state

Every registry entry is:

```yaml
state: candidate
activation: inactive
production_authorized: false
```

Transactional, repository-harness, authoring/admission, release-readiness and P0-gate skills are `explicit_only`. All harness metadata disables implicit invocation. Installation provides shared discovery; it does not confer tool, mutation, approval, activation, gate, release or deployment authority.

The registry binds every inactive entry to its exact `package-sha256` digest. The
13 pre-existing packages are honestly identified as local working-tree snapshots,
not as content from the Git base commit; the reconciled threat-model package is
identified as a merged candidate. A future activation requires an exact committed
revision and a separate independently checked activation decision.

## Verification

| Check | Result |
| --- | --- |
| Skill format validation | 34/34 PASS |
| Packaged skill unit suites | 22/22 PASS |
| Closed registry validation | PASS, 34 entries |
| Registry governance tests | 8/8 PASS, including forged-activation mutation cases |
| Full governance tests | 13/13 PASS |
| Repository validation | PASS |
| `npm run validate` | PASS |
| `npm run validate:skills` | PASS |
| Package validators and architecture static evaluation | PASS |
| Cross-harness discovery adapters | Codex, Claude Code, Antigravity and Copilot PASS |
| Workflow eligibility resolver | Correctly DENY while dependencies are inactive |

## Independent advisory review

| Review lane | Verdict | Scope |
| --- | --- | --- |
| Security and supply chain | SUPERSEDED_PENDING_REVIEW | The 0.1 review is superseded by the 0.2 remediation candidate |
| Duplicate, overlap and routing | APPROVE_NOT_EFFECTIVE | Overlaps bounded for inactive candidate admission; activation precision remains unevaluated |
| Validation and fail-closed behavior | PENDING_EXACT_COMMIT_REVIEW | Re-run against the committed 0.2 remediation candidate |

These are independent technical advisory verdicts. They do not activate a skill,
approve publication, pass a program gate, authorize merge or permit deployment.

## Residual risks and next decisions

- Incoming per-skill validators are mostly structural or keyword-based and do not prove runtime semantics.
- Pack provenance and retained SBOM are unsigned; the final external license remains unresolved.
- Package-test dependencies are pinned in `.agents/requirements.lock`; package suites and static evaluation now run in CI.
- Incoming reports are not closed-world checksum-bound.
- Model-level trigger and negative-trigger evaluation remains required before activation.
- Existing legacy skills without package suites remain `package_validation: not_run`.
- This candidate-admission validator categorically refuses activation or promotion. No skill may move from inactive candidate until a separate independently approved activation mechanism verifies an exact committed source and immutable decision evidence.

## 0.2 remediation candidate

The successor branch `codex/BOPEN-SKILL-P0-001-remediation-v2` updates
`io.bizera.bopen.architecture` from candidate version `0.1.0` to `0.1.1`.
The bounded remediation makes authority resolution fail closed, replaces
approval-shaped output values with recommendation-only dispositions, removes
wildcard Python and destructive Make declarations, contains generated outputs,
blocks candidate release packaging, and enforces closed-world checksum coverage.

The `0.1.1` candidate SBOM, provenance statement and release manifest now share
the same version and bind a 60-file static inventory. Package validation rejects
version drift, inventory omissions/additions, per-file hash or size drift, source
tree digest drift and provenance-subject drift. The architecture suite contains
9 unit tests, including a negative supply-chain drift test, and the package
validator reports 37 passing checks.

The registry binds version `0.1.1` to package digest
`ff954ce6bac850c6eb68c2d3166a7ab2a64c462853dff283a6ea6ca1fc6b4dff`.
This remains candidate evidence and confers no activation, gate, merge, release,
publication or deployment authority.
