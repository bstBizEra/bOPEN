# BOPEN-MOD-001 — Product, Module, Feature & Capability Contracts Specification

**Document ID:** `BOPEN-MOD-001`  
**Version:** `1.0.0`  
**Status:** APPROVED FOR PHASE 3 PLANNING & CONTRACT FREEZE  
**Issued:** 2026-07-29  
**Owner:** Architecture Authority & Engineering Authority  
**Classification:** Normative Architecture & Module Contract Specification  

---

## 1. Executive Summary

bOPEN defines a strict, contract-first capability ontology and module registration pipeline. Platform kernel capabilities, commercial features, and satellite industry products MUST be registered, validated, and published via versioned machine-readable module manifests ([module-manifest.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/module-manifest.schema.json)).

Industry products and satellite packages CANNOT embed custom logic into the platform kernel without registering capabilities under this specification.

---

## 2. Core Ontology Hierarchy

```text
Product (e.g. bPro, PropTech, bFleet)
  └── Module (e.g. mod_practice_mgmt, mod_leasing)
       └── Feature (e.g. feat_time_tracking, feat_lease_agreements)
            └── Capability / Action (e.g. cap_invoice_create, cap_lease_approve)
                 └── Resource (e.g. res_invoice, res_lease)
```

---

## 3. Disambiguated Lifecycles: Global Catalog vs. Tenant Context

To prevent ambiguity between repository-wide module availability and tenant-specific enablement:

### 3.1 Global Catalog Lifecycle
$$\text{registered} \longrightarrow \text{validated} \longrightarrow \text{approved} \longrightarrow \text{available}$$

1. **`registered`**: Module manifest submitted to the repository registry (`contracts/schemas/module-manifest.schema.json`).
2. **`validated`**: Schema validation and dependency resolution pass against repository tooling.
3. **`approved`**: Architecture Authority signs off on the module manifest version.
4. **`available`**: Published to the global capability catalog for tenant subscription.

### 3.2 Tenant Context Lifecycle
$$\text{entitled} \longrightarrow \text{enabled} \longrightarrow \text{configured} \longrightarrow \text{active}$$

1. **`entitled`**: Tenant commercial subscription tier or override includes the module capability ([BOPEN-ENT-001](BOPEN-ENT-001.md)).
2. **`enabled`**: Feature rollout toggle permits deployment to the tenant environment.
3. **`configured`**: Tenant administrator completes required module configuration.
4. **`active`**: Module capabilities are bound to the validated active context and usable.

---

## 4. Server-Validated Active Context Requirement

No client-supplied `X-Tenant-ID` or module request header is trusted without server-side validation. Every module capability invocation MUST accept a **server-validated active context** (`ContextPayload`) containing verified `(sub, tid, mid, cid)`. Client headers that do not match the cryptographically verified context payload are rejected (`DENY_INVALID_CONTEXT`).

---

## 5. Required Contract Schemas

All capability registration and module discovery logic must satisfy these machine-readable contract schemas:
* [module-manifest.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/module-manifest.schema.json)
* [capability-registration.schema.json](file:///c:/laragon/www/bopen/contracts/schemas/capability-registration.schema.json)
