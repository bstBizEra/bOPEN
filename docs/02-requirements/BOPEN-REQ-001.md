# BOPEN-REQ-001 — bOPEN Product Requirements Specification v1.0

**Document ID:** `BOPEN-REQ-001`  
**Version:** `1.0`  
**Status:** Approved for Phase 1 implementation  
**Issued:** 2026-07-29  
**Owner:** Product Authority  
**Classification:** Normative Specification  

---

## 1. High-Level Requirements

1. **Multi-Tenancy**: Support enterprise multi-tenancy with physical data isolation and server-validated active context (`tenant_id`).
2. **First-Class Principal & Membership**: Treat `Principal` as any entity (human, service, device, agent) and `Membership` as an explicit principal-to-tenant relationship state.
3. **Deny-by-Default Authorization**: Require explicit ReBAC/ABAC decision evaluation for every request.
4. **Correlated Security Audit**: Emit structured audit logs capturing actor, tenant, resource, action, status, and correlation ID.
