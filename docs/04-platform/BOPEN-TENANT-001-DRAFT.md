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
