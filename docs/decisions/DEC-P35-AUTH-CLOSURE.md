# DEC-P35-AUTH-CLOSURE - Close the remaining kernel authentication paths

**Decision ID:** `DEC-P35-AUTH-CLOSURE`  
**Version:** `0.2.0`
**Status:** Partially decided - `AUTH-D1` accepted; `AUTH-D3` pending
**Issued:** 2026-08-01  
**Owner:** Security Authority and Architecture Authority  
**Required concurrence:** Engineering Authority and Product Authority  
**Raised from:** `EVD-P35-CODEX-PREFLIGHT-001`  
**Governing artifacts:** `BOPEN-IDP-001` sections 12 and 14; `BOPEN-AUTHZ-001`;
`HTTP_HEADER_SPEC.md`; `DEC-P35-IDP-SPLIT`; `AGENTS.md` sections 8-10 and 20.3

---

## 1. Scope and label clarification

The operator instruction names auth decisions `D1` and `D3`, but no controlled repository
artifact defined those labels. This record defines them explicitly as `AUTH-D1` and `AUTH-D3`
instead of guessing silently.

This document records the operator's `AUTH-D1` disposition and retains the technical
recommendation for `AUTH-D3`. The `AUTH-D1` disposition does not decide `AUTH-D3`, amend a frozen
contract by itself, verify an implementation, or authorize production activation.

## 2. AUTH-D1 - What authenticates protected kernel requests?

### Question

May `X-Context-ID` plus `X-Tenant-ID` continue to authorize protected operations without a signed
bearer token after WP-P35-05a introduces a configured authenticator?

### Observed behavior

With a configured authenticator and no Authorization header, the legacy path returned
`200 ALLOW` from `/v1/authorize`. The path validates that a context row exists, but it does not
authenticate the caller presenting the identifier.

### Options

1. Keep the legacy path indefinitely. Compatible, but treats possession of a context identifier
   as a credential and contradicts the mandatory bearer header in `HTTP_HEADER_SPEC.md`.
2. Prefer bearer but retain legacy fallback in production. Easier migration, but the weaker path
   remains the effective security boundary.
3. Require a verified bearer token for every protected endpoint. Retain `X-Context-ID` only as a
   non-authoritative reference where a contract still needs it.

### Decision - option 3 accepted 2026-08-01

**Option 3 is accepted.** A protected endpoint must derive principal, tenant, membership, and context
from a verified signed token, then re-read the stored context for revocation and current state.
Headers may narrow or cross-check signed claims; they cannot create authority.

The normative basis is [`DEC-P35-AUTH-CLOSURE-RESEARCH`](DEC-P35-AUTH-CLOSURE-RESEARCH.md)
section 2: OWASP ASVS 5.0 section 6.8.2 requires signature presence and integrity to be validated
and unsigned or invalid assertions to be rejected. `AUTH-D1` therefore does not depend on how
initial enrollment is solved under `AUTH-D3`.

The compatibility transition must be explicit:

- default production behavior fails closed without a bearer token;
- no automatic fallback occurs after token verification failure;
- any temporary legacy profile is test/local only, separately named, disabled by default, and
  cannot be enabled on a production profile;
- the gateway and kernel enforce the same rule;
- removal includes negative tests proving a valid context ID alone receives `401` and performs no
  protected read, write, authorization decision, or audit enumeration.

## 3. AUTH-D3 - Which unauthenticated identity mutations remain public?

### Question

When a kernel authenticator is configured, may callers without a verified assertion still create
principals and provision tenants with an owner membership?

### Observed behavior

With a configured authenticator and no assertion, `POST /v1/principals` and `POST /v1/tenants`
both returned `201`.

### Constraint

The current subject assertion names an existing bOPEN `principal_id`. It cannot authenticate
initial principal enrollment because that identifier does not exist yet. Reusing email as the
identity key is prohibited by `DEC-P35-AUTH-BOUNDARY` and `BOPEN-IDP-001`.

### Options

1. Leave both endpoints public. Preserves self-service but permits unauthenticated platform-state
   creation and third-party owner binding.
2. Apply the current subject assertion to both endpoints. Works for tenant provisioning by an
   existing principal but cannot correctly solve initial enrollment.
3. Split enrollment from authenticated provisioning: define a purpose-bound enrollment proof for
   principal creation, and require an authenticated existing principal or separately authorized
   provisioning service for tenant creation.

### Recommendation

**Adopt option 3.** Until the enrollment proof contract exists, production principal registration
fails closed or remains outside the exposed kernel surface. Tenant provisioning requires:

- a verified authenticated principal whose identifier equals `owner_principal_id`; or
- a separately authenticated service principal with an explicit tenant-provisioning capability.

Neither route may infer authority from email equality, a caller-supplied owner ID, network
location, or the existence of a context identifier. Principal creation, tenant creation, owner
membership creation, and audit/outbox effects must retain their required transaction boundaries.

### Enrollment-credential recursion risk still requiring disposition

The annex identifies a viable self-naming enrollment credential, but it also identifies the
security recursion plainly: the credential is an unsigned bearer-by-identifier mechanism, the
same class of authority that `AUTH-D1` retires from protected endpoints.

Codex's recommendation is that this risk is acceptable only as a separately named enrollment
trust domain with all of these controls: CSPRNG generation, at least 112 bits of entropy, a hard
10-minute lifetime, single-use atomic consumption, local out-of-band transfer rather than email,
explicit enrollment-only authorization, and no durable credential after redemption. A generic,
long-lived, reusable, emailed, or protected-endpoint fallback token is not acceptable.

The authorities must decide whether that bounded exception is acceptable. Until they do,
principal enrollment remains closed or outside the exposed production kernel surface. This
pending decision does not reopen the legacy `X-Context-ID` authorization path disposed by
`AUTH-D1`.

## 4. Implementation sequencing if ratified

1. Amend or version `HTTP_HEADER_SPEC.md` and the affected API contracts before code.
2. Add failing negative tests for the two reproduced probes.
3. Introduce the enrollment-proof contract without embedding an IdP in the kernel.
4. Make protected endpoints bearer-only and tenant provisioning assertion/capability-bound.
5. Remove or isolate the legacy context-authentication branch.
6. Re-run the live PostgreSQL, gateway, contract, clean-room, evidence-anchor, and authority
   checks.
7. Issue a new maker submission at an exact commit and hand it to an eligible independent
   verifier.

## 5. Decision record

| Field | Value |
|---|---|
| `AUTH-D1` | **ACCEPTED 2026-08-01 - option 3.** Protected endpoints are bearer-only; `X-Context-ID` is non-authoritative |
| `AUTH-D3` | Pending authority disposition; Codex recommends proof-bound enrollment and authenticated provisioning |
| Disposition source | Operator instruction, recorded 2026-08-01 |
| Implementation effect | `AUTH-D1` remediation may proceed inside authorized `WP-P35-05a`; contracts and negative tests precede code |
| Remaining authority decision | `AUTH-D3` only - accept or reject the bounded enrollment-credential recursion risk |
| Production activation | Not authorized |

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
