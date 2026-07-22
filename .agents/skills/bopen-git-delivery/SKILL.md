---
name: bopen-git-delivery
description: >-
  Prepare controlled Git delivery by inspecting scope selecting a branch validating staging intentionally committing pushing and opening a draft pull request only when publication is explicitly requested.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.git.delivery
  version: "0.1.0"
  owner: bopen-platform-engineering
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Git Delivery

## Purpose

Publish reviewed bOPEN changes without hidden scope secret leakage history rewriting or bypassed verification.

## Use this skill when

- The user explicitly asks to commit push or open a PR
- Publishing a validated pack branch
- Preparing a delivery summary

## Do not use this skill when

- Publishing without explicit intent
- Force-pushing protected branches
- Including unrelated or secret files

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`prepare`, `commit`, `push`, `draft-pr`

## Procedure

1. **Resolve context.** Confirm repository remote branch and worktree status.
2. **Inspect scope.** Review diff untracked files generated content and secret risk.
3. **Validate.** Run required tests linters pack checks and architecture gates.
4. **Stage intentionally.** Stage only approved files.
5. **Commit.** Use a precise traceable message.
6. **Push safely.** Push a non-protected branch without force.
7. **Open draft PR.** Summarize change validation risks and reviewer needs.

## Mandatory controls

- Explicit publication intent is mandatory.
- Never amend or force-push shared history without approval.
- No credentials local env files or unrelated artifacts.
- Failed mandatory checks block delivery.
- PR remains draft until review gates pass.

## Output contract

- Delivery readiness report
- Commit and branch details
- Draft PR with validation evidence
- Excluded and unresolved files

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
