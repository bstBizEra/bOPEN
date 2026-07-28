# BOPEN-EVIDENCE-VOTING-001 - Evidence and Technical Review Protocol

**Version:** 0.1
**Status:** PROPOSED_NON_EFFECTIVE
**Owner:** Governance Lead
**Updated:** 2026-07-28
**Purpose:** Define candidate-scoped technical dispositions and evidence
aggregation for a human gate.

## Non-authority rule

In this document, "vote" means a technical recommendation about exact candidate
bytes. It is not organizational authority and must not be treated as a
signature, gate decision, register mutation, ref movement, activation, release
or phase completion.

The effective maker/checker and human-authority model remains controlling.

## Evidence classes

| Class | Evidence | Required characteristics |
| --- | --- | --- |
| E0 | Task and authority intake | Exact source, scope, identity, validity and revocation state |
| E1 | Candidate provenance | Base and candidate commit/tree, patch digest, files and authorship |
| E2 | Deterministic checks | Commands, versions, exit codes and output digests |
| E3 | Independent reproduction | Fresh checker execution against the exact candidate |
| E4 | Negative assurance | Fail-closed, bypass, malformed-input, boundary and rollback tests |
| E5 | Integration fidelity | Accepted input digests, successor base and manifest reproduction |
| E6 | Human gate decision | Attributable authorized decision, conditions and canonical result |
| E7 | Learning record | Verified cause, proposed skill delta and forward-test result |

Evidence is append-only. Corrections reference and supersede prior records
without erasing them.

## Exact-candidate rule

Every review binds:

```text
repository
+ base commit and tree
+ candidate commit and tree
+ patch digest
+ evidence-index digest
```

All governing references must resolve from the candidate tree or an explicitly
authorized immutable external source. A dangling cross-branch reference
requires `ABSTAIN_INSUFFICIENT_EVIDENCE` or `REJECT_TECHNICAL`.

## Reviewer eligibility

A technical reviewer must:

- be bound to an identifiable run;
- disclose model, runtime and tool metadata;
- not have authored the candidate;
- review the exact candidate;
- reproduce mandatory checks;
- disclose material context or dependency conflicts;
- record findings, rationale and residual risks.

Agent count is not independence. Duplicate conclusions or runs sharing
contaminated context do not increase assurance.

## Dispositions

| Disposition | Meaning |
| --- | --- |
| `APPROVE_TECHNICAL` | Exact candidate meets the reviewed technical and evidence criteria |
| `REJECT_TECHNICAL` | Reproducible defect, control violation or acceptance failure exists |
| `ABSTAIN_INSUFFICIENT_EVIDENCE` | Reliable conclusion is not possible from available evidence |

Each disposition expires when candidate bytes or bound evidence change.

## Proposed review panels

- Normal package: one independent technical approval plus all mandatory
  automated checks.
- High-risk package: one Codex reviewer, one Claude reviewer and one
  verification reviewer; at least two approvals, including one from each model
  family.
- Integrated phase candidate: the high-risk panel plus full-suite reproduction
  by the verification reviewer.

These panels are advisory. They apply only when an authorized work package
adopts this proposal. Existing effective checker requirements are not replaced.

Any substantiated blocking rejection prevents technical readiness until a new
candidate is reviewed. An abstention does not count as approval. A numerical
majority cannot cure missing evidence, failed checks, scope violations or
absent authority.

## Dissent and remediation

A finding may be challenged only with new evidence. It must not be outvoted.

Remediation creates a new candidate and:

1. links the rejected candidate and findings;
2. records changed files and patch digest;
3. reruns affected and regression checks;
4. obtains fresh independent dispositions;
5. preserves the original rejection.

## Gate packet

A phase gate packet should contain:

- phase and roadmap baseline;
- authorized package inventory;
- exact accepted candidate list;
- integrated successor commit and tree;
- validation and negative-test index;
- technical-review index and dissent disposition;
- deviations, risks and conditions;
- authority, identity, expiry and revocation evidence;
- proposed human disposition.

The proposed disposition is `TECHNICALLY_READY_FOR_GATE`, never `COMPLETE`,
until the effective human decision and canonical transition exist.

## Activation

This protocol remains non-effective until an authorized governance decision
adopts it and its schemas, templates and validators are independently accepted.
