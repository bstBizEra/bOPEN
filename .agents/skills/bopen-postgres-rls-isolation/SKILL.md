---
name: bopen-postgres-rls-isolation
description: >-
  Design review and verify PostgreSQL row-level security for tenant-owned data including schemas migrations roles context functions policies bypass analysis and cross-tenant tests.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.postgres.rls.isolation
  version: "0.1.0"
  owner: bopen-platform-security
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN PostgreSQL RLS Isolation

## Purpose

Make Tenant isolation enforceable at the database layer with default deny least-privilege roles and repeatable negative evidence.

## Use this skill when

- Creating or altering a tenant-owned table
- Writing or reviewing RLS policies
- Changing database roles pools or context functions

## Do not use this skill when

- Using application filters as the only control
- Running the app as table owner or BYPASSRLS
- Claiming isolation without cross-tenant tests

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`design`, `migration-review`, `policy-review`, `test-plan`, `incident-analysis`

## Procedure

1. **Classify tables.** Identify tenant-owned platform-global shared-reference and derived data.
2. **Define context.** Use transaction-local validated Tenant and Principal settings.
3. **Enable enforcement.** Enable and where required force RLS.
4. **Write policies.** Define USING and WITH CHECK per command and role.
5. **Harden roles.** Separate migration and runtime roles and prevent bypass.
6. **Test.** Cover same-Tenant cross-Tenant missing-context and forged-context cases.
7. **Inspect performance.** Validate indexes and plans without weakening policy.

## Mandatory controls

- Every tenant-owned table is registered and covered.
- Policies never rely only on caller-provided Tenant IDs.
- INSERT and UPDATE use WITH CHECK.
- Runtime roles cannot bypass RLS.
- Tests prove default deny and cross-Tenant denial.

## Output contract

- RLS design or review
- Policy and role recommendations
- Database negative-test matrix
- Coverage inventory and gaps

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
