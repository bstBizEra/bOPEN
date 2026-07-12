# First Platform Kernel Vertical Slice — Draft Execution Specification

## Goal

Validate the minimum bOPEN relationship chain without billing, workflow, agents or industry logic.

```text
Register human principal
  -> provision tenant
  -> create owner membership
  -> establish active tenant context
  -> authorize tenant read
  -> emit correlated audit event
```

## Required before implementation

- approved BOPEN-REQ-001 requirements;
- approved BOPEN-ARCH-001 boundaries;
- approved BOPEN-TENANT-001 lifecycle and isolation;
- approved BOPEN-AUTHZ-001 decision contract;
- approved BOPEN-SEC-001 controls;
- BOPEN-RES-001 G7 pass;
- accepted implementation work package.

## Acceptance scenarios

1. New principal and tenant create exactly one active owner membership.
2. Tenant provisioning failure does not leave an unauthorized active tenant.
3. Principal cannot access a tenant without active membership.
4. Tenant context cannot be forged by changing client input.
5. Cross-tenant read is denied at API and database enforcement layers.
6. Authorization result includes reason and policy version.
7. Audit event identifies actor, tenant, resource, action, result and correlation.

## Executable draft fixture

The draft acceptance fixture is `docs/06-contracts/acceptance/first-vertical-slice.acceptance.json`.

DEV-P0-01 extends the negative multi-tenant boundary through `docs/06-contracts/acceptance/multitenant-dev-readiness.acceptance.json`; it does not expand implementation authority.

This fixture is a contract/test input only. It does not authorize production implementation before the required BOPEN-RES-001 G7 pass, approved normative artifacts and accepted implementation work package.
