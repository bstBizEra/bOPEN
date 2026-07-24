# SKEL-P0 Autonomous Engineering Loop

**Status:** Draft; preparation/review only
**Work item:** SKEL-P0-CONST-01

The loop permits autonomous mechanical coordination while stopping before
authority-bearing actions:

```text
Inspect -> Understand -> Plan -> Divide -> Execute -> Verify -> Review
-> Evidence -> Handoff -> Operator decision -> (new bounded cycle)
```

## Entry gate

Before dispatch, the Director records project/phase, work-item ID, owner/expiry,
maker, checker, exact base SHA/tree, allowed/prohibited paths, tests, evidence
destination and rollback. Missing or mismatched authority stops the loop.

## Mechanical autonomy allowed

Agents MAY inspect, plan, create isolated worktrees, implement within allowed paths,
run tests, create draft evidence, perform independent review and send a structured
handoff. Worktrees are retained through evidence and closure decisions.

## Hard stops

The loop MUST stop for wrong ancestry, dirty custody, scope creep, maker/checker
collision, failed required validation, missing provenance, tenant/security
uncertainty, stale manifests, or attempted draft-to-active promotion. Human
Authority is required for acceptance, stable use, merge, push, release, deployment,
activation, runtime flags, secret/plugin enablement and protected-ledger changes.

## Handoff minimum

Every handoff includes exact repository/branch/worktree, base/head/tree SHAs,
changed files, commands and exit codes, tests, evidence paths, findings, residual
risk, blocked items, rollback, `authorization_required`, and advisory status.

## Learning loop

Repeated work MAY produce a draft skill proposal and evaluation case. No skill is
published, registered as effective, or treated as permission without independent
review and approval.
