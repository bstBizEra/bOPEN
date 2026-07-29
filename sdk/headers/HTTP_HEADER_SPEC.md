# bOPEN Standard Client HTTP Header Specification v1.0

All client applications, satellite products (bPro, bFleet, PropTech, bERP, LDM), and AI agents interacting with the bOPEN Platform Kernel MUST send these HTTP headers:

| Header Name | Required? | Meaning & Format | Example |
| :--- | :---: | :--- | :--- |
| `X-Tenant-ID` | **Mandatory** | Explicit UUID of the target Tenant boundary | `tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c` |
| `X-Context-ID` | Optional | Explicit validated session context ID | `ctx_99f11a22-33b4-44c5-55d6-66e77f88a99b` |
| `X-Correlation-ID` | **Mandatory** | Unique request tracking GUID for cross-service tracing | `corr_12345678-abcd-ef01-2345-6789abcdef01` |
| `X-Capability-Version` | Optional | Requested capability contract API version | `1.0.0` |
| `Authorization` | **Mandatory** | Standard OAuth 2.0 Bearer JWT session token | `Bearer eyJhbGciOi...` |
