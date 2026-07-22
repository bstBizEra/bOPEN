---
name: bopen-audit-evidence
description: >-
  Design validate and review audit events evidence envelopes correlation actor context decision reasons redaction retention and conformance evidence for privileged and security-relevant actions.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.audit.evidence
  version: "0.1.0"
  owner: bopen-security-and-assurance
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN Audit and Evidence

## Purpose

Create trustworthy minimally disclosed and reviewable evidence of what was attempted decided and changed.

## Use this skill when

- Adding a privileged or security-relevant action
- Designing audit and evidence semantics that will feed a separately packaged evidence envelope
- Reviewing audit completeness redaction or retention

## Do not use this skill when

- Logging secrets or full sensitive payloads
- Treating mutable logs as the only audit record
- Allowing actors to alter history

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`audit-design`, `evidence-input-contract`, `coverage-review`, `retention-review`, `incident-support`

## Procedure

1. **Classify record.** Decide whether action needs audit operational log evidence or all three.
2. **Define envelope.** Capture event actor Principal effective Tenant scope resource decision time and correlation.
3. **Minimize data.** Store identifiers and governed summaries and redact secrets.
4. **Protect integrity.** Use append-oriented storage restricted roles and tamper evidence.
5. **Link evidence.** Attach tests artifacts approvals logs hashes and reviewers.
6. **Define retention.** Apply Tenant security legal and incident requirements.
7. **Verify coverage.** Test success denial failure support access and replay.

## Mandatory controls

- Audit and evidence are immutable to the subject actor.
- Security-relevant denials are audited.
- Decision reason and policy version are captured.
- Secrets and unnecessary personal data are prohibited.
- Evidence includes source method result hash reviewer and timestamp.

## Output contract

- Audit schema and catalog
- Evidence input contract and validation criteria
- Coverage and retention matrix
- Integrity findings

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
