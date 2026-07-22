---
name: bopen-github-actions-hardening
description: >-
  Review or author secure GitHub Actions workflows covering permissions untrusted input privileged triggers action pinning secrets artifacts caches OIDC and self-hosted runners.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.github.actions.hardening
  version: "0.1.0"
  owner: bopen-platform-security
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN GitHub Actions Hardening

## Purpose

Protect the bOPEN software supply chain from workflow injection excessive token authority and mutable dependencies.

## Use this skill when

- Editing workflow files
- Reviewing pull_request_target workflow_run or issue_comment
- Locking down GITHUB_TOKEN and actions

## Do not use this skill when

- General application-code review
- Auto-applying critical workflow changes without review
- Assuming parsed YAML is safe

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`review`, `author`, `harden`, `incident-analysis`

## Procedure

1. **Map triggers.** Classify caller trust and token or secret privilege.
2. **Find injection.** Inspect run blocks for attacker-controlled expression interpolation.
3. **Check privileged execution.** Ensure privileged workflows never execute untrusted fork code.
4. **Audit permissions.** Deny by default and grant minimum scopes per job.
5. **Pin actions.** Require full commit SHA for third-party actions.
6. **Protect secrets and artifacts.** Review logging checkout credentials outputs caches and handoffs.
7. **Report.** Provide severity exact location and corrected YAML for critical and high findings.

## Mandatory controls

- Never use write-all without explicit justification.
- No mutable branch references for third-party actions.
- Untrusted data is passed through environment variables not pasted into shell.
- Prefer OIDC over long-lived cloud credentials.
- Self-hosted runners require a documented trust boundary.

## Output contract

- Workflow security report
- Severity summary and exact findings
- Corrected YAML proposals
- Residual-risk checklist

Every output distinguishes evidence, inference, assumption and recommendation. Use `schemas/output.schema.json` for structured output.

## Failure handling

- Missing authoritative evidence: issue `decision-required` or `incomplete`; never invent facts.
- Failed mandatory or cross-Tenant control: issue `fail` and identify the blocker.
- Unsafe requested behavior: refuse the unsafe step and preserve the governing boundary.
- Tool or dependency failure: report exactly what ran, what failed and which evidence is unavailable.

## Completion evidence

1. Identify source scope or repository revision.
2. Record checks and important negative cases.
3. List residual risks and required reviewers.
4. Never claim `APPROVED`, `SIGNED`, `PUBLISHED` or production-ready without corresponding evidence.

## References

- `references/bopen-invariants.md`
- `references/control-checklist.md`
- `references/output-contract.md`
- `references/examples.md`
- `policies/execution-policy.yaml`
- `bopen.skill.yaml`
