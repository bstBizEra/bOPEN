# BOPEN-TENANT-001 — bOPEN Tenant, Organization Graph, Membership, Context & Isolation Specification v1.0

**Document ID:** `BOPEN-TENANT-001`  
**Version:** `1.0`  
**Status:** Draft — no implementation authority  
**Issued:** 2026-07-12  
**Owner:** bOPEN Architecture Authority  
**Classification:** Internal engineering governance  

## Core distinctions

```text
Tenant != Organization != Legal Entity
Membership != Role != Permission != Entitlement
```

## Candidate tenant states

`draft`, `pending_verification`, `approved`, `provisioning`, `active`, `restricted`, `suspended`, `cancellation_pending`, `terminated`, `retention`, `purged`.

## Candidate membership states

`invited`, `active`, `suspended`, `declined`, `expired`, `revoked`, `left`, `removed`.

## Required decisions

- creation/provisioning transaction boundaries;
- tenant ownership and isolation profile;
- organization graph cardinality;
- invitation and membership state machines;
- active-context selection and propagation;
- tenant switching and session implications;
- support/partner cross-tenant grants;
- suspension, retention and purge behavior.

## DEV-P0-01 executable draft baseline

The first development-readiness contracts are:

- `bopen://schemas/tenancy/membership/0.1.0-draft`;
- `bopen://schemas/tenancy/active-context/0.1.0-draft`;
- `bopen://schemas/tenancy/tenant-ownership/0.1.0-draft`;
- `docs/06-contracts/acceptance/multitenant-dev-readiness.acceptance.json`.

They establish testable boundaries without resolving the required decisions above or granting production implementation authority. Membership contains no role, permission, or entitlement; active context accepts only server or trusted-service validation sources; and cross-tenant access must deny at both API and database layers.
