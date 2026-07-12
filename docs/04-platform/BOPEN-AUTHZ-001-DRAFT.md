# BOPEN-AUTHZ-001 — bOPEN Authorization, Scope, Delegation & Policy Specification v1.0

**Document ID:** `BOPEN-AUTHZ-001`  
**Version:** `1.0`  
**Status:** Draft — no implementation authority  
**Issued:** 2026-07-12  
**Owner:** Security and Architecture Authorities  
**Classification:** Internal engineering governance  

## Decision input

Principal, tenant, active context, action, resource, scope, role/grant relationships, conditions, capability state, entitlement state and request risk context.

## Decision output

`ALLOW` or `DENY`, reason code, policy version, evaluated scope, obligations, correlation ID and audit metadata.

## Rules

- deny by default;
- explicit precedence;
- no UI-only enforcement;
- support access is time-bound and auditable;
- cross-tenant access requires explicit grant;
- agent tool access is separate from human role assignment;
- RLS enforces tenant isolation and does not replace authorization.
