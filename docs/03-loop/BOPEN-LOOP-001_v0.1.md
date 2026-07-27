# LOOP.md — bOPEN Governed Delivery and Learning Loop v0.1

**Status:** Draft; advisory only

## Primary delivery loop

```text
GOAL
→ INTAKE
→ CLASSIFY
→ REQUIREMENTS
→ DESIGN
→ ARCHITECTURE DECISION
→ PLAN
→ AUTHORIZE
→ ISOLATED IMPLEMENTATION
→ VERIFY
→ EVIDENCE
→ INDEPENDENT REVIEW
→ ACCEPT
→ RELEASE DECISION
→ OBSERVE
→ LEARN
→ IMPROVE OR PROMOTE
```

## Work-item state machine

```text
PROPOSED
→ TRIAGED
→ SPECIFIED
→ READY
→ AUTHORIZED
→ IN_PROGRESS
→ REVIEW
→ VERIFICATION
→ ACCEPTED
→ RELEASED
→ OBSERVED
→ CLOSED
```

Terminal or holding states:

```text
BLOCKED
REJECTED
CANCELLED
QUARANTINED
SUPERSEDED
REMEDIATION_REQUIRED
```

## Micro-loop for each implementation task

1. **Orient:** read context receipt and current repository state.
2. **Predict:** declare intended changes, risks and expected test results.
3. **Act:** make the smallest authorized change.
4. **Check:** run static, unit, contract and applicable isolation checks.
5. **Compare:** compare outcome with prediction and requirements.
6. **Correct:** remediate within scope; otherwise stop and escalate.
7. **Evidence:** record commands, results, diff and residual findings.
8. **Handoff:** send structured output to the independent checker.

## Failure-to-learning loop

```text
Failure or unexpected outcome
→ Failure Evidence Envelope
→ Redaction and validation
→ Reproduction
→ Root-cause analysis
→ Noise or verified lesson
→ Knowledge artifact
→ Test / ADR / runbook / skill candidate
→ Evaluation
→ Reject, quarantine or promote
```

Do not promote a lesson solely because an agent reported it. Require reproducibility,
evidence and an accountable human or checker decision.

## Loop performance indicators

- cycle time from authorized to accepted;
- blocked time by cause;
- first-pass verification rate;
- rework rate;
- escaped defects;
- change failure rate;
- evidence completeness;
- reusable capability yield;
- skill evaluation pass rate.
