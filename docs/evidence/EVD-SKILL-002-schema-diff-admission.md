# EVD-SKILL-002 — bOPEN Schema Diff Skill Admission

**Status:** Quarantined / Not admitted  
**Work package:** BOPEN-SKILL-P0-002  
**Skill:** `bopen-schema-diff` v0.1.0  
**Source:** `C:\Users\ounkh\Downloads\bopen-schema-diff-0.1.0\bopen-schema-diff`  

## Scope

The package is admitted for bounded repository/worktree analysis, migration-risk
classification, RLS and tenant-isolation review, and evidence generation. It does
not authorize production migration application, credential acquisition, RLS
disablement, database grants, activation, release, or deployment.

## Validation evidence

| Check | Result |
|---|---|
| `python scripts/validate_package.py` | 134 passed, 0 warnings, 0 errors |
| `python scripts/run_static_evals.py` | 21/21 passed |
| Independent unit-test lane | 11/11 passed; local shell lacked `pytest` |
| Source package checksum manifest | Present; package source remains bound to `UNBOUND-SOURCE-REVISION` |

The static suite includes destructive-change, privilege, RLS, tenant-isolation,
credential, and production-mutation negative cases. Passing a negative case means
the skill correctly blocks the unsafe input; it does not approve that input.

## Admission disposition

Independent security and supply-chain review returned **NO-GO**. The package is
quarantined for remediation and must not be installed as an admitted or invocable
skill. Findings include:

- fail-open `SAFE/PASS` results for unsupported or empty SQL and incomplete
  destructive/RLS detection;
- raw DSN exposure in process arguments and unrestricted adapter arguments;
- PATH-resolved, unpinned external tools and non-immutable dependencies;
- arbitrary output overwrites without approved-root or symlink-safe controls;
- stale/incomplete SBOM and checksum closure, unsigned placeholder provenance,
  unbound source revision, and `allow_implicit_invocation: true` conflicting with
  the deny-by-default execution policy.

## Lifecycle and authority

```yaml
state: quarantined
activation: inactive
production_mutation: prohibited
authority_effect: none
pg_g0_effect: none
```

Independent technical review, human activation, and any production use remain
separate decisions. The current bOPEN G0 authority boundary remains in force.

## Residual risks

- Full unit-test execution requires the environment's approved Python test
  dependency to be installed or supplied through an authorized isolated runtime.
- The package manifest source revision is unbound until a later immutable release
  process supplies an exact source revision and digest-bound publication record.
- Optional external engines (Atlas, pg-schema-diff, Prisma) were not invoked.
