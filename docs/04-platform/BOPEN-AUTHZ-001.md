# BOPEN-AUTHZ-001 — bOPEN Authorization & Policy Specification v1.0

**Document ID:** `BOPEN-AUTHZ-001`  
**Version:** `1.0`  
**Status:** Approved for Phase 1 implementation  
**Issued:** 2026-07-29  
**Owner:** Security & Architecture Authorities  
**Classification:** Normative Specification  

---

## 1. Authorization Rules

1. **Deny-by-Default**: Every request without explicit policy match returns `DENY`.
2. **Context Binding**: Authorization decisions require `principal_id`, `tenant_id`, `active_membership_id`, `action`, and `resource_id`.
3. **Audit Correlation**: Every decision emits a structured decision log matching `contracts/schemas/authorization-decision.json`.
