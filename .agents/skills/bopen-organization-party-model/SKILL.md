---
name: bopen-organization-party-model
description: >-
  Design and review Party Person Organization Legal Entity business-role and organization-graph models whenever customer supplier employee partner branch company or real-world relationship data is introduced.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.organization.party.model
  version: "0.1.0"
  owner: bopen-foundation-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Organization and Party Model

## Purpose

Prevent authentication users and tenant boundaries from being overloaded as real-world business entities.

## Use this skill when

- Modeling people or organizations
- Designing legal entities branches or relationships
- Linking a Party to an optional Principal

## Do not use this skill when

- Treating every person as a user
- Equating Tenant Organization and Legal Entity
- Embedding industry semantics in the generic kernel

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`domain-model`, `relationship-graph`, `migration`, `conformance-review`

## Procedure

1. **Identify entities.** Classify Person Organization Legal Entity and Party forms.
2. **Separate concepts.** Distinguish Principal Party Tenant and Organization.
3. **Model roles.** Represent customer supplier employee and partner contextually.
4. **Model graph.** Define parent subsidiary branch manages partner and temporal relationships.
5. **Link identity optionally.** Allow Party Person to link to a Principal without requiring one.
6. **Scope to tenant.** Define tenant-owned shared and external records.
7. **Verify history.** Preserve effective dates mergers role changes and audit.

## Mandatory controls

- Party may exist without login identity.
- Tenant is a security and commercial boundary not automatically a company.
- Organization and Legal Entity are not synonyms.
- Relationships have type scope and effective dates.
- Tenant-owned Party data is RLS protected.

## Output contract

- Party and organization model
- Relationship taxonomy and temporal rules
- Identity-linking contract
- Migration and conformance findings

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
