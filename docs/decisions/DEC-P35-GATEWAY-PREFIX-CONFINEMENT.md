# DEC-P35-GATEWAY-PREFIX-CONFINEMENT — a refutation was answered by argument, and its probe still reproduces

**Decision ID:** `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16 (an architectural question is unresolved and a refutation is undischarged)**
**Issued:** 2026-08-09
**Owner:** Architecture / Security Authorities
**Raised by:** Claude (agent, Motor role) — advisory only; **not the maker of the artifact**
**Governing:** [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §6.2; `AGENTS.md` §9, §16

---

## 1. Why this exists

Candidate `88e6ed2` — *"fix(gateway): the caller could choose the upstream host — unauthenticated
SSRF"* — carries two `REFUTED` ballots cast by `gemini` on 2026-07-31. `BOPEN-GOV-EBIV-001` §6.2
states a refutation is *"discharged only by a failed reproduction — **never by re-assertion**"*.

Both probes were re-run against current `HEAD` on 2026-08-09.

## 2. Results, verbatim

### `P35-04R-16` — discharged correctly ✅

```text
UpstreamPathEscape [Error]: resolved path /admin escapes the configured base path /base
    at buildUpstreamUrl (apps/gateway/src/app.ts:130)
exit 1
```

The probe asserts the escape succeeds. It now raises instead. **This is a failed reproduction and a
valid discharge** — the mechanism was added and named in the code as a response to this exact ballot.

### `P35-04R-15` — still reproduces ⚠️

```text
status1= 200   status2= 200
upstream paths seen = ["/admin","/admin"]
exit 0
```

A client requesting `/v1/../admin` or `/v1/%2E%2E/admin` reaches the kernel as `/admin`, exactly as
the ballot recorded. **The probe passes, so the refutation is not discharged.**

## 3. What was done instead of a fix

`apps/gateway/src/app.ts` carries a comment addressing this ballot directly:

> *"No **request** can reach here with dot segments: the URL parser normalises them before any
> handler runs... The escape is therefore reachable only by calling this exported function directly.
> That makes it a latent API hazard rather than a live request-path defect."*

The reasoning is sound as far as it goes — the parser does normalise before the handler, so the
gateway never sees the dot segments. But **that is an argument that the finding is not a defect, and
§6.2 names exactly this as the thing that cannot discharge a refutation.** The behaviour the ballot
described still occurs.

## 4. Severity — measured, not assumed

| Question | Answer |
| :--- | :--- |
| Does the gateway confine to `/v1`? | **No.** It declares `app.all('/*')` — a catch-all proxy |
| Kernel routes outside `/v1`? | **Three**: `/health`, `/readiness`, `/.well-known/jwks.json` |
| Kernel routes under `/v1`? | 21 |
| Does `/admin` exist on the kernel? | **No** |
| Any test asserting prefix confinement? | **None found** |

**There is no evidence of anything being reachable today that should not be.** The three routes
outside `/v1` are health, readiness and a public JWKS endpoint.

The structural exposure is what remains: a client-supplied `/v1/../admin` becomes `/admin`, nothing
confines the proxy to `/v1`, and no test would notice if that changed. **The first kernel route added
at the root that is not meant to be public becomes reachable immediately, silently.**

## 5. The question

**Is the gateway meant to confine requests to `/v1`, or is it a deliberate catch-all proxy that
leaves authorization entirely to the kernel?**

The repository does not say. `app.all('/*')` is consistent with either — a deliberate design, or an
unnoticed gap. Until it is answered, `P35-04R-15` cannot be honestly discharged **or** honestly
dismissed.

## 6. Options

| # | Option | Assessment |
| :--- | :--- | :--- |
| 1 | **Confine the gateway to `/v1`** and add a negative test for the escape | Discharges the refutation by making the probe fail. Changes proxy behaviour, so any non-`/v1` route reachable through the gateway today would stop being so — `/health` and JWKS need checking first |
| 2 | **Record the catch-all as deliberate**, with a test asserting the kernel authorizes every root route | Keeps current behaviour and makes the assumption explicit and testable. Does **not** discharge the refutation by reproduction; it would need the ballot re-examined against a redefined proposition |
| 3 | **Re-examine the proposition with the original verifier** | `gemini` cast the ballot and is best placed to say whether §4's measurements change its verdict. Not currently available (`DEC-P35-VERIFIER-SCOPE` §10) |
| 4 | **Accept and record as a known, undischarged refutation** | Honest, and leaves an authorization-boundary finding open with no owner |

No option is recommended here. The choice between confining a proxy and declaring it deliberately
open is an architecture and security decision, and §9 makes authorization boundaries an Authority
matter rather than a maker's.

## 7. What this decision request does not do

It changes no code, alters no ballot, and discharges nothing. `88e6ed2` remains refuted. It records
that one of its two refutations reproduces, that the other does not, and that the reproducing one was
answered by argument rather than by a failed reproduction.

**This conclusion is a single agent's and has not been independently verified.** It should be
checked before it is relied on.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.
