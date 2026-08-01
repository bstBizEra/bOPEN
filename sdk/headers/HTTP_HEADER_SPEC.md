# bOPEN Standard Client HTTP Header Specification v1.1

**Version:** `1.1`
**Amended:** 2026-08-01 by `DEC-P35-AUTH-CLOSURE` `AUTH-D1` (ACCEPTED, option 3)

All client applications, satellite products (bPro, bFleet, PropTech, bERP, LDM), and AI agents interacting with the bOPEN Platform Kernel MUST send these HTTP headers:

| Header Name | Required? | Authority | Meaning & Format | Example |
| :--- | :---: | :--- | :--- | :--- |
| `Authorization` | **Mandatory** | **Authoritative** | Signed context access token. The **only** header that establishes identity | `Bearer eyJhbGciOi...` |
| `X-Correlation-ID` | **Mandatory** | none | Request tracking GUID for cross-service tracing. Max 64 characters; refused, never truncated | `corr_12345678-abcd-ef01-2345-6789abcdef01` |
| `X-Tenant-ID` | Optional | **non-authoritative** | Cross-check only. On the bearer path the tenant comes from the signed `tid` claim; a disagreeing header is refused | `tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c` |
| `X-Context-ID` | Optional | **non-authoritative** | Reference only. **Possession of a context identifier confers no authority** | `ctx_99f11a22-33b4-44c5-55d6-66e77f88a99b` |
| `X-Capability-Version` | Optional | none | Requested capability contract API version | `1.0.0` |

## Authority rule (v1.1)

**A header cannot create authority. Only a verified signature can.**

Headers may *narrow* or *cross-check* a signed claim — `X-Tenant-ID` disagreeing with the token's
`tid` is refused — but no combination of headers, absent a valid `Authorization` bearer token,
authorizes a protected operation.

### What changed from v1.0, and why

v1.0 listed `X-Context-ID` as an optional identifier without stating its authority, and the kernel
accepted it *in place of* a token. Two independent agents reproduced the consequence on
2026-07-31: a tenant member presenting another member's `X-Context-ID`, with no token and no
signature, obtained `200 ALLOW` and acted as that member. The identifier was also published to
every member of the tenant through `GET /v1/audit-events`, so obtaining one required no attack at
all.

Possession of an identifier is not authentication. `AUTH-D1` disposed this: protected endpoints
are bearer-only. The normative basis is OWASP ASVS 5.0 §6.8.2 — signature presence and integrity
must always be validated, and unsigned or invalid assertions rejected.

**No automatic fallback occurs after token verification fails.** A rejected token is a refusal,
never a downgrade to header-asserted identity.

### Legacy profile

A `X-Context-ID`-only path remains available **for test and local development only**, is disabled
by default, is separately named, and cannot be enabled on a production profile. It is not a
supported client contract and will be removed.
