# BOPEN-AGENT-TEAM-001 - Multi-Agent Delivery Operating Model

**Version:** 0.1
**Status:** PROPOSED_NON_EFFECTIVE
**Owner:** Governance Lead
**Updated:** 2026-07-28
**Purpose:** Define a proposed Codex and Claude delivery model without granting
authority, activation or phase-transition rights.

## Operating principle

The agent team is an execution and assurance system. It may improve delivery
throughput and evidence quality while preserving human accountability, least
privilege, separation of duties and fail-closed governance.

This proposal is not an authority source. Existing effective authority,
identity, phase-gate, signing and ref-movement controls remain controlling.

## Team cells

| Cell | Suggested composition | Output |
| --- | --- | --- |
| Coordination | One phase coordinator | Dependency DAG, package registry and gate packet |
| Implementation | One maker per independent package | Candidate and maker receipt |
| Verification | One independent checker per package | Reproduced validation and technical disposition |
| Integration | One integration maker plus independent checker | Governed successor candidate and integration receipt |
| Assurance | Evidence steward and optional red-team checker | Evidence index, negative tests and dissent register |
| Authority | Named accountable humans | Effective decisions and phase-state transitions |

An agent may fill different roles across different packages, but must not be
maker and decisive checker for the same candidate.

## Codex-Claude rotation

| Work | Maker | Checker |
| --- | --- | --- |
| Package A | Codex | Claude |
| Package B | Claude | Codex |
| Integration | Agent that authored the minority of inputs, where practical | Other model family or fresh independent checker |
| Remediation | Agent not responsible for the finding, where practical | Original or fresh independent checker |

Model-family rotation reduces correlated error but does not establish
independence by itself. Evidence must record actual authorship, context
exposure, runtime and tooling.

## Work-package contract

Every package should state:

```yaml
work_package_id: WP-<phase>-<sequence>
phase_id: <roadmap-phase>
status: PROPOSED|AUTHORIZED|IN_PROGRESS|VERIFYING|TECHNICALLY_ACCEPTED|BLOCKED|CLOSED
base_commit: <40-hex>
base_tree: <40-hex>
allowed_paths: []
allowed_operations: []
maker: <bound-agent-identity>
checker: <independent-bound-agent-identity>
dependencies: []
acceptance_commands: []
evidence_required: []
risk_class: LOW|MEDIUM|HIGH|CRITICAL
expires_at: <RFC3339>
revocation_channel: <registered-channel>
completion_condition: <deterministic-statement>
```

No mutation begins until the package is authorized by the effective mechanism
for the current phase.

## Delegation

A delegated task must include:

- objective and non-objectives;
- exact inputs and expected outputs;
- read/write boundary;
- applicable controls;
- validation commands;
- evidence location;
- stop and escalation conditions.

Subagent output remains untrusted until independently reviewed. A conversational
summary cannot satisfy a gate.

## Integration ownership

The integration maker:

1. starts from the recorded governed base;
2. imports only technically accepted exact candidates;
3. verifies source blob or patch digests;
4. reconciles shared files once;
5. regenerates manifests deterministically;
6. runs complete validation;
7. records the successor commit and tree;
8. submits the integrated candidate for independent review.

Technical acceptance of disconnected branches is not integrated readiness.

## Indicators

| Indicator | Definition |
| --- | --- |
| First-pass technical acceptance | First-review accepts divided by submissions |
| Evidence completeness | Schema-valid, resolvable receipts divided by required receipts |
| Reproducibility | Checker results matching maker results |
| Rework rate | Packages requiring remediation divided by reviewed packages |
| Integration conflict rate | Shared-file conflicts divided by integration batches |
| Escaped defect rate | Post-acceptance defects attributable to accepted packages |
| Governance exceptions | Unauthorized or out-of-scope attempts; target zero |

Indicators inform improvement and never override gate or authority criteria.

## Activation

Adoption requires an applicable human governance decision, registration in the
controlled document set, manifest regeneration and independent review. Until
then this artifact is advisory.
