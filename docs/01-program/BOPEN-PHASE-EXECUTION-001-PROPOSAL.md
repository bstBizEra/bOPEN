# BOPEN-PHASE-EXECUTION-001 - Roadmap Execution Addendum

**Version:** 0.1
**Status:** PROPOSED_NON_EFFECTIVE
**Owner:** Program Governance
**Updated:** 2026-07-28
**Applies to:** Proposed execution pattern for each roadmap phase.

## Phase lifecycle

| Stage | Agent activity | Required exit evidence |
| --- | --- | --- |
| 0. Intake | Resolve roadmap baseline, authority, identities, scope and controls | Valid intake receipt |
| 1. Decompose | Build dependency DAG and work-package contracts | Authorized package registry |
| 2. Mobilize | Allocate isolated worktrees and maker/checker roles | Ownership map and clean baselines |
| 3. Implement | Execute independent packages | Candidate commits and maker receipts |
| 4. Verify | Reproduce checks and test negative paths | Independent checker receipts |
| 5. Integrate | Build one successor candidate from accepted exact bytes | Integration receipt and full-suite pass |
| 6. Gate | Assemble phase evidence and recommendation | Exact gate packet |
| 7. Decide | Authorized humans approve, reject, defer or condition | Effective decision receipt |
| 8. Close | Update canonical state and preserve records | Closure record and retained evidence |
| 9. Learn | Extract verified lessons and test skill improvements | Accepted or rejected learning proposal |

This lifecycle does not replace an effective phase-specific closure sequence.
For PG-P0, the authoritative C0-C11 closure controls remain controlling.

## Parallelization gate

A package may run in parallel only when:

- inputs are stable;
- output ownership does not overlap another active maker;
- acceptance is independently testable;
- shared-file integration is assigned to a named integration package;
- failure does not require unrecorded rollback of another package.

Otherwise the work must be sequenced.

## Proposed readiness formula

```text
TECHNICAL_READINESS =
  ScopeValid
  AND AuthorityIntakeValid
  AND AllMandatoryPackagesTechnicallyAccepted
  AND IntegratedCandidateReproduced
  AND EvidenceComplete
  AND NoBlockingDissent
```

`HumanGateDecisionValid` is deliberately excluded from technical readiness and
is required separately for phase completion.

## State meanings

| State | Meaning |
| --- | --- |
| `TECHNICALLY_READY_FOR_GATE` | Technical criteria met; human decision outstanding |
| `TECHNICALLY_COMPLETE_PENDING_AUTHORITY` | Proposed cross-model panel passed; authority action outstanding |
| `CONDITIONALLY_APPROVED` | Human authority approved with recorded conditions |
| `COMPLETE` | Effective closure decision and canonical transition recorded |
| `DEFERRED` | Decision postponed with evidence and resumption criteria |
| `BLOCKED` | Named blocker prevents progress |
| `REJECTED` | Candidate or phase fails requirements |

Only states supported by the effective schedule schema may be written to the
canonical register. Proposal-only readiness labels belong in evidence or
dashboards unless separately adopted.

## Roadmap update rule

An authoritative roadmap or schedule change must reference the exact gate
decision and canonical successor state. Agent summaries may update operational
reports but must not mutate phase status without explicit authority.

## Activation

Adoption requires reconciliation with the effective roadmap and phase-specific
gate, schema review, manifest regeneration and an authorized human decision.
