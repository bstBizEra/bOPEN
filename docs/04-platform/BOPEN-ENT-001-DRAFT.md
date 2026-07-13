# BOPEN-ENT-001 — bOPEN Entitlement, Usage & Commercial Kernel Specification v1.0

**Document ID:** `BOPEN-ENT-001`  
**Version:** `1.0`  
**Status:** Draft — no implementation authority  
**Issued:** 2026-07-12  
**Owner:** bOPEN Architecture Authority  
**Classification:** Internal engineering governance  

## Entitlement types

- boolean;
- static value;
- capacity;
- seat;
- metered allowance;
- time-bound promotional/admin grant.

## Separation

Subscription and payment state feed entitlement policy but do not directly equal authorization. Feature flags govern rollout, not commercial rights.

## Required contracts

Entitlement decision, balance/limit, usage event, aggregation, plan version, tenant override and suspension/degradation policy.
