---
name: bopen-module-boundary-review
description: >-
  Review modular-monolith package boundaries dependency direction domain ownership public contracts data access and future extraction seams whenever modules or service boundaries change.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.module.boundary.review
  version: "0.1.0"
  owner: bopen-architecture-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Module Boundary Review

## Purpose

Keep P0 cohesive and evolvable without premature microservices or product-domain contamination of platform core.

## Use this skill when

- Adding or reorganizing a bounded Module
- Reviewing circular dependencies or shared database access
- Evaluating later service extraction

## Do not use this skill when

- Splitting by technical layer alone
- Moving industry semantics into platform Modules
- Allowing direct writes across Module-owned tables

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`boundary-review`, `dependency-review`, `extraction-readiness`, `package-design`

## Procedure

1. **Inventory Modules.** List ownership capabilities data and public interfaces.
2. **Map dependencies.** Build a directed graph and identify cycles or shared internals.
3. **Check ownership.** Separate platform foundation product and industry responsibilities.
4. **Check data access.** Require owner-mediated writes and explicit read contracts.
5. **Check events.** Use versioned contracts for asynchronous coupling.
6. **Assess extraction.** Record seams but retain modular monolith unless justified.
7. **Report.** Classify violations remediation and ADR needs.

## Mandatory controls

- Dependency direction is explicit and acyclic where practical.
- No product Module writes another Module's tables directly.
- Shared utilities contain no hidden domain policy.
- Provider adapters sit behind owned interfaces.
- Service extraction requires operational evidence.

## Output contract

- Module map and dependency graph
- Boundary findings and ownership table
- Public contract recommendations
- Extraction-readiness notes

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
