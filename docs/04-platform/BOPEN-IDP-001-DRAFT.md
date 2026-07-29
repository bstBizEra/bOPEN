# BOPEN-IDP-001 — Enterprise SSO, Identity Provider & Token Specification v1.0

**Document ID:** `BOPEN-IDP-001`  
**Version:** `1.0`  
**Status:** Superseded — no implementation authority  
**Superseded by:** [`BOPEN-IDP-001.md`](BOPEN-IDP-001.md) — Enterprise Identity, Federation, Provisioning, and Session Claims Standard v1.0 (Approved for Phase 2 implementation, 2026-07-29)  
**Issued:** 2026-07-29  
**Owner:** Security & Architecture Authorities  
**Classification:** Internal engineering governance  

> **Superseded notice.** This draft is retained for provenance only. It carries no
> implementation authority and must not be cited as a governing artifact. The approved
> replacement is [`BOPEN-IDP-001.md`](BOPEN-IDP-001.md), adopted under work package
> [`BOPEN-P2-001`](../work-packages/BOPEN-P2-001-EXECUTION-PLAN.md) WP-P2-01.

---

## 1. Executive Summary

bOPEN provides a multi-tenant Enterprise Single Sign-On (SSO) and Identity Provider (IdP) integration layer supporting SAML 2.0 and OpenID Connect (OIDC) protocols.

---

## 2. SSO Architecture & Domain Routing

```text
User Login Request (email: alice@acme.com)
  └── Domain Extractor ("acme.com")
       └── Tenant IdP Lookup (Acme Corp -> Okta / Azure AD via BoxyHQ / Keycloak)
            └── SAML 2.0 / OIDC Authentication Flow
                 └── Issue bOPEN Validated Session JWT Token
```

---

## 3. JWT Session Token Claim Standard

bOPEN session tokens MUST contain these mandatory claims:

| Claim Key | Meaning | Example |
| :--- | :--- | :--- |
| `sub` | Authenticated Principal ID | `usr_98f12a3b` |
| `tid` | Active Tenant ID Boundary | `tnt_45a11c00` |
| `oid` | Optional Active Organization ID | `org_12e34f56` |
| `mid` | Active Membership ID | `mem_88a99b22` |
| `roles` | Active Context Roles | `["tenant_owner"]` |
| `scopes` | Granted Capability Scopes | `["tenant:read", "bFleet:access"]` |
| `iss` | Token Issuer | `https://auth.bopen.io` |
| `iat` | Issued At Timestamp (Epoch) | `1785200000` |
| `exp` | Expiration Timestamp (Epoch) | `1785203600` |

---

## 4. SCIM 2.0 User Provisioning Protocol

Tenant user provisioning follows the SCIM 2.0 standard (`/scim/v2/Users`, `/scim/v2/Groups`):
* Creating a user via SCIM automatically provisions a `Principal` record and creates an `invited` or `active` `Membership` for the target tenant.
* Deactivating a SCIM user immediately transitions tenant membership to `revoked` and revokes active session context tokens.
