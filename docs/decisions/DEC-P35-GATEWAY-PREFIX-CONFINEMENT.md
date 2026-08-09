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

---

## 8. Independent re-check 2026-08-09 — §4 understated the exposure

§7 said this conclusion was one agent's and should be checked before being relied on. It was checked
by Codex. **The governance conclusion holds; the severity assessment does not.**

### 8.1 Confirmed

- `P35-04R-16` is discharged for the corrected successor behaviour — a failed reproduction, and it
  does not retroactively make `88e6ed2` unrefuted; its historical ballot stands.
- `P35-04R-15` **remains undischarged**.
- The code comment's technical reasoning is **correct** — Codex drove a bare Hono handler behind the
  real Node adapter and observed both literal and percent-encoded dot segments arriving already
  normalised as `/admin`. *"Nevertheless, that establishes why the behavior occurs; it does not make
  the `P35-04R-15` reproduction fail. The source comment and the 'KNOWN LIMITATION' test therefore
  cannot discharge the ballot."*

### 8.2 Corrected — the maker undercounted what is reachable

§4 said three routes exist outside `/v1`. **There are seven.** `FastAPI(...)` is constructed at
`api.py:999` with no `docs_url`, `redoc_url` or `openapi_url` override anywhere in the file, so its
four default documentation endpoints are live:

| Route | Status in §4 |
| :--- | :--- |
| `/health`, `/readiness`, `/.well-known/jwks.json` | counted |
| `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc` | **missed** |

Verified independently: there is no `docs_url`/`redoc_url`/`openapi_url` anywhere in `api.py`.

**So §4's claim that there is "no evidence of anything being reachable today that should not be" was
wrong.** The kernel's OpenAPI schema and interactive documentation are reachable through the
catch-all proxy right now, and **no governing artifact says whether they should be public.**

Codex also notes `/readiness` performs a database query and its failure path returns
`detail=f"persistence unavailable: {type(exc).__name__}"` — exception-type disclosure on an
unauthenticated endpoint. Confirmed at `api.py`.

### 8.3 Fail-open confirmed empirically

Codex forwarded a hypothetical `/future-private` kernel path and it returned the injected upstream's
200, reachable through **both** `/future-private` and `/v1/../future-private`. No repository
deployment, ingress, Nginx, Traefik or reverse-proxy manifest adds path confinement; the runtime
binds to `127.0.0.1` by default, which limits network exposure but not paths.

**The structural risk is confirmed fail-open for future root routes**, not merely theoretical.

### 8.4 A test asserts the opposite

Codex found a test that **intentionally asserts the dot-segment behaviour as a "KNOWN LIMITATION"**.
That is the re-assertion of §3 encoded as a passing test — the strongest form the argument has taken,
and still not a failed reproduction.

### 8.5 Effect on the options

Option 1 (confine to `/v1`) now has a larger blast radius than §6 implied: `/health`, `/readiness`,
JWKS **and the four documentation endpoints** are reachable through the gateway today, and confining
would stop all seven. Whether each *should* remain reachable is now part of the decision rather than
a detail.

The maker's assessment ran in the direction that made the finding look smaller. Recorded.
