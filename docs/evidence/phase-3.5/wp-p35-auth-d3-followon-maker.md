# EVD-P35-AUTH-D3-FOLLOWON-MAKER — D-D3-002 (Option B) + AUTH-D3 Row 1(b)

**Document ID:** `EVD-P35-AUTH-D3-FOLLOWON-MAKER`
**Version:** `1.0.0`
**Status:** **REVISED — R2 after one refutation (§8).** `P35-D3b-05` was refuted at the R1 candidate (`7450661`, a reproducible percent-encoding bypass) and fixed at `f269e2c`. The kernel Group A is byte-identical (`api.py` `4a58ddb`, carries); the gateway Group B needs a fresh ballot at the revised candidate.
**Issued:** 2026-08-02
**Implements:** [`DEC-P35-AUTH-D3-DOCKET`](../../decisions/DEC-P35-AUTH-D3-DOCKET.md) `D-D3-002` (Option B) and `D-D3-001` Row 1(b), operator-disposed 2026-08-02
**R1 candidate:** `7450661` — 11 `CONFIRMED`, 1 `REFUTED` (`P35-D3b-05`)
**Revised candidate:** the commit carrying this R2 revision (fix at `f269e2c`)
**Blob — `api.py`:** `4a58ddb6238884fb49d341dfcd007f244e973cd3` *(unchanged from R1 — Group A carries)*
**Blob — gateway `rate-limit.ts`:** `12555885f55fc987e35627bd3e672c866e54dc80` *(changed: decode-aware classification)*
**Blob — gateway `app.ts`:** `7fb19ecb98524dbb50d5f83b36926d0fa39f38b9` *(changed)*
**Blob — `invariant-traceability.csv`:** `b3682b82123144351a0ece2896850bdc3787b010`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **475/475** against PostgreSQL; gateway **65/65**

---

## 1. Why these two, and why together

Both are operator-disposed follow-ons from the AUTH-D3 docket, built through the governed
maker cycle after the auth boundary closed:

- **`D-D3-002` — Option B (principal enrollment).** Keep principal creation out of the exposed
  kernel surface. No new enrollment credential (that is Option A, which reintroduces the unsigned
  bearer-by-identifier class `AUTH-D1` retired).
- **Row 1(b) — creation rate limiting at the gateway.** Cap `POST /v1/principals` and
  `POST /v1/tenants` at the edge, the operator-chosen layer.

They are submitted together because they are the same disposition's two remaining halves and share
one verifier round.

## 2. This is defensive verification, not an attack

**Read this framing first.** Every proposition below asserts that the platform **refuses** an
unauthorized or excessive request and **admits** a valid one — a principal creation refused when the
deployment has not affirmed it is out-of-band, a creation flood capped at the edge. Verifying a
refusal-and-limit boundary is defensive review. There is no exploitation of a third party and no
offensive objective.

## 3. Group A — `D-D3-002` principal enrollment (Option B), kernel

`register_principal` refuses out-of-band-only, and — unlike tenant provisioning, which gained an
assertion path because it names an existing principal — Option B adds **no** credential, so the
refusal is **503, not 401**: no credential the caller could supply would change it.

| ID | The kernel must… | Test (traced in `invariant-traceability.csv`) |
| :--- | :--- | :--- |
| `P35-D3c-01` | refuse creation (503) with no authenticator and the non-production flag unset | `test_no_authenticator_and_flag_unset_is_refused` |
| `P35-D3c-02` | admit creation (201) with no authenticator when the flag is set (local/out-of-band) | `test_no_authenticator_and_flag_set_provisions` |
| `P35-D3c-03` | close creation (503) when an authenticator is configured — out of band only | `test_a_configured_authenticator_closes_the_endpoint` |
| `P35-D3c-04` | not let the development flag reopen creation against a configured authenticator | `test_the_development_flag_cannot_reopen_it_against_a_configured_authenticator` |
| `P35-D3c-05` | not open creation to any assertion — Option B adds no credential | `test_no_assertion_opens_it_option_b_adds_no_credential` |

**Behavioural change to an existing test, disclosed:** `test_one_flag_governs_every_endpoint_...` in
`test_phase1_http_slice.py` previously asserted registration stayed open when the flag was removed.
Option B overrides that decision, so it is updated and made **stricter** — registration is now
refused too, the operator-accepted cost of no self-service registration.

## 4. Group B — Row 1(b) gateway rate limiting

`CreationRateLimiter` enforces two fixed windows together — per-source (first `X-Forwarded-For` hop)
and a global ceiling that backstops source-header rotation. On refusal the gateway returns 429 with
`Retry-After` and the kernel is never reached.

| ID | The gateway must… | Test (traced) |
| :--- | :--- | :--- |
| `P35-D3b-01` | forward creation under the per-source limit | `requests under the per-source limit are forwarded` |
| `P35-D3b-02` | refuse (429) creation over the per-source limit, and not reach the kernel | `the request over the per-source limit is refused with 429 and never reaches the kernel` |
| `P35-D3b-03` | give a distinct source its own budget | `a different source is not blocked by the first source window` |
| `P35-D3b-04` | backstop source-header rotation with a global ceiling | `the global ceiling backstops source-header rotation` |
| `P35-D3b-05` | never rate-limit a non-creation endpoint | `endpoints that are not creation are never rate-limited` |
| `P35-D3b-06` | forward every creation when no policy is configured (unchanged default) | `without a rateLimit option the gateway forwards every creation as before` |
| `P35-D3b-07` | not count a refused request, so a blocked flood does not extend its own window | `a refused request is not counted so a blocked flood does not extend its own window` |

**Attack angle for the verifier:** rotate `X-Forwarded-For` to evade the per-source cap — `P35-D3b-04`
claims the global ceiling still refuses. And confirm a percent-encoded or dot-segment variant of the
creation path is not admitted past the exact-path guard.

## 5. Execution

```text
python tools/run_tests.py     475/475 OK   (live PostgreSQL; 470 + 5 new enrollment tests)
apps/gateway  node --test      59/59 OK    (47 + 12 new rate-limit tests)
```

Mutation intuition: removing the `authenticator_configured()` branch in `register_principal` breaks
`P35-D3c-03`/`-04`; removing the global window in `CreationRateLimiter` breaks `P35-D3b-04`; counting
a refused request breaks `P35-D3b-07`.

## 6. What this does NOT establish

1. **The enumeration oracle is not closed** — on the flag-permitted (local) path, `register_principal`
   still answers "is this address registered?" through status, body length and timing, exactly as
   its docstring records. Option B removes the *public* exposure, not the oracle on the permitted
   path.
2. **The rate limiter is in-memory and per-instance.** Two gateway instances hold independent
   counters, so the effective global ceiling is per-instance. A shared store is named in the docket
   as a later concern, not built here.
3. **Per-source keying trusts `X-Forwarded-For`.** It is only as trustworthy as the upstream proxy
   that sets it; the global ceiling is the backstop for when it is forged, not a substitute for a
   trusted edge.
4. **Out-of-band provisioning is a deployment path, not code here** — Option B closes the endpoint;
   the operator/SCIM mechanism that creates principals in production is out of this scope.

## 7. Refutation and revision (R2)

**The refutation was correct and useful.** At the R1 candidate `7450661`, Codex refuted `P35-D3b-05`
with a reproducible probe: `POST /v1/%70rincipals` (percent-encoded `p`) returned `201` and reached
the kernel, so the encoded creation slipped the cap entirely — a single character defeated the whole
limit. Codex confirmed the kernel routes the encoded path to `register_principal` directly. This is
the first refutation of this work stream, and it found a real evasion the maker's own probes missed.

**Root cause.** The limiter classified the *raw* pathname, but the kernel percent-decodes before
routing. `/v1/%70rincipals` is not in the exact creation set, yet the kernel runs it as
`/v1/principals`. The two saw different paths.

**Fix (`f269e2c`).** `isCreationPath` now decodes the path once — matching the kernel's single
decode — for the classification *decision only*. The gateway still forwards the raw bytes unchanged,
so the deliberate no-decode-on-forward design (`P35-04R-15`) is untouched. A malformed
percent-sequence is treated as non-creation, because the kernel would not route it to a creation
handler either. A single decode is correct: `/v1/%2570rincipals` decodes once to `/v1/%70rincipals`,
which the kernel does not route to creation.

**New proposition, and re-assertion:**

| ID | The gateway must… | Test |
| :--- | :--- | :--- |
| `P35-D3b-05` *(re-assert)* | never rate-limit a non-creation endpoint, and classify creation by the route the kernel will run | `endpoints that are not creation are never rate-limited` |
| `P35-D3b-08` *(new)* | rate-limit a percent-encoded creation path exactly as its literal form | `a percent-encoded creation path is limited exactly as its literal form` |

**What carries and what does not.** `api.py` is byte-identical to R1 (`4a58ddb`), so Group A
(`P35-D3c-01..05`) carries — a verifier may re-cast on the hash. The gateway changed
(`rate-limit.ts`, `app.ts`), so Group B (`P35-D3b-01..08`) requires fresh ballots at this candidate.
Gateway suite is now **65/65**.

## 8. Authority

A maker's submission. `EBIV` §8: a passing suite is a self-assessment carrying **no verdict weight**.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
