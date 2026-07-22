---
name: bopen-portal-context-ux
description: >-
  Design and review Platform Console My bOPEN User Portal Tenant Portal and work surfaces with explicit contexts Tenant switching stale-session handling route protection and authorization-failure UX.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.portal.context.ux
  version: "0.1.0"
  owner: bopen-experience-authority
  lifecycle: CANDIDATE
  risk-class: SKR2
---

# bOPEN Portal Context UX

## Purpose

Make active operating context visible and safe so users cannot silently or accidentally act in the wrong Tenant or platform scope.

## Use this skill when

- Designing personal Tenant or platform routes
- Implementing Tenant switching or invitations
- Reviewing context indicators deep links or denials

## Do not use this skill when

- Relying on route names as backend authorization
- Mixing personal identity into Tenant administration
- Hiding context changes

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`information-architecture`, `flow-review`, `route-review`, `tenant-switch`, `error-ux`

## Procedure

1. **Classify surface.** Assign each page to user Tenant platform partner security billing or agent context.
2. **Define routes.** Use explicit route families and server-side guards.
3. **Expose context.** Display active Tenant and make switching intentional.
4. **Design transitions.** Handle invitations Tenant creation switching suspension and removal.
5. **Protect deep links.** Resolve Resource and Tenant together and never silently switch authority.
6. **Design failures.** Distinguish unauthenticated no Membership no Entitlement disabled Module and unauthorized.
7. **Test.** Cover stale tabs back navigation multiple Tenants forged URLs and revocation.

## Mandatory controls

- /my is personal context Tenant routes are Tenant context and /platform is platform context.
- Backend policy is authoritative.
- Tenant switch invalidates or reloads scoped data and caches.
- Personal identity data is not Tenant-owned.
- Errors avoid resource-existence leaks.

## Output contract

- Portal capability and route map
- Context-switch sequence
- Guard and error matrix
- UX conformance tests

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
