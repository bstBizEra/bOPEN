# EVD-P35-04-MAKER-R3 — WP-P35-04 Maker Submission, revision 3 (API Gateway)

**Document ID:** `EVD-P35-04-MAKER-R3`
**Version:** `3.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-01
**Supersedes:** [`EVD-P35-04-MAKER-R2`](wp-p35-04-maker-submission-r2.md) at `88e6ed2…`, **blocked** by two refutations
**Discharges:** `P35-04R-15` (partially — see §3), `P35-04R-16` (guard added; probe validity is a verifier question)

**Commit OID:** `1b39a30bfde007c65b88685b5102650de4f9e54c`
**Tree OID:** `d1348383bc45ca723d28be38960f65e05fb4be97`
**Subtree OID (`apps/gateway`):** `516a65a4df0542f514f4b6fb11f0a40f4c34bb88`
**Blob OID (`src/app.ts`):** `90ef55d31e5584acf3c5d6dbe912faac17b9dc56`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifiers:** Codex, Gemini
**Suites:** gateway 47/47; canonical 433/433

> Zero ballots at this candidate. All OIDs read with `git rev-parse` at issue time (EBIV R3, `A-07`).

---

## 1. Why revision 3 exists

R2 was **blocked** by the first two refutations this repository has produced. `P35-04R-15` and
`P35-04R-16`, both offered by the maker expecting exactly that verdict, were refuted by Gemini
with reproducible probes (`8041701`). EBIV §6.1 makes one such ballot blocking; §6.2 allows
discharge only by fixing until the probe fails to reproduce, or by an independent verifier
demonstrating the probe invalid.

R2's confirmations for `P35-04R-01`..`14` are not disturbed by this revision — they were cast at
`88e6ed2…`, which remains reachable. **They do not carry forward.** This is a new candidate and
needs its own ballots.

## 2. What changed

| Change | Reason |
| :--- | :--- |
| Request target read from `new URL(c.req.url).pathname`, not `c.req.path` | `c.req.path` runs `decodeURI`; `/v1/a%2Fb` reached the kernel as `/v1/a/b`, inventing a segment boundary from an encoded slash |
| `buildUpstreamUrl` throws `UpstreamPathEscape` on base-prefix escape | Closes the latent hazard `P35-04R-16` exercised |
| 4 tests added (43 → 47) | One of them asserts a **known defect** deliberately — see §3.2 |

## 3. The honest position on `P35-04R-15`

That proposition conflated two transformations. **Only one was ours.**

### 3.1 Percent-decoding — fixed, and claimable

`/v1/a%2Fb` and `/v1/caf%C3%A9` now reach the kernel byte-identical. This is a real defect
repaired, and `P35-04R3-15` below claims it.

### 3.2 Dot segments — unachievable at this layer, and therefore not claimed

`/v1/../admin` still reaches the kernel as `/admin`. The WHATWG URL parser resolves dot segments
when the `Request` object is constructed — before Hono, before this code. The original target is
unrecoverable here.

**No proposition in this submission claims otherwise.** Restating `P35-04R-15` as worded would be
offering a claim the maker knows to be false, which is worse than the prose limitation it was
written to escape.

Instead:

- `test/headers.test.ts` asserts the normalisation **deliberately**, so the limitation cannot
  drift unnoticed in either direction;
- `P35-04R3-17` claims the *bounded* truth — that the gateway introduces no transformation of its
  own beyond what the parser already applied;
- the residual architectural question is raised as a **decision**, not left as a proposition:
  see §6.

## 4. The honest position on `P35-04R-16`

Gemini's probe called `buildUpstreamUrl('http://…/base', '/../../admin', '')` **directly**.
Measured through the real gateway with the same base:

```text
/../../admin        ->  /base/admin
/v1/../../admin     ->  /base/admin
/%2e%2e/%2e%2e/admin->  /base/admin
```

Every path stays contained, because dot segments are normalised before the handler runs. **No
request path can put the function in the state the probe exercises**, and the proposition is
worded *"no **request path** can cause the upstream path to escape…"*.

**The maker does not rule on this.** §6.2 reserves invalidating a probe to an independent
verifier, demonstrated rather than asserted. It is put to the verifiers as `P35-04R3-18`, which
asks the question directly rather than assuming the answer. The guard was added regardless.

## 5. Propositions

`P35-04R3-01`..`14` are `P35-04R-01`..`14` carried unchanged to this candidate. They require
fresh ballots.

| ID | Proposition | Test |
| :--- | :--- | :--- |
| `P35-04R3-01` | No request path can move the upstream request off the kernel origin | `"//evil.example/x" cannot move…` + 4 vectors |
| `P35-04R3-02` | A base path prefix survives **for paths the parser leaves intact** | `an ordinary path under a base prefix is still allowed` |
| `P35-04R3-03`..`06` | Response framing: `content-encoding`, `content-length`, `Set-Cookie`, `Connection` | `response header handling`, `Connection-named headers…` |
| `P35-04R3-07`..`14` | Header contract, identifier acceptance, non-echo, status passthrough | as R2 |
| **`P35-04R3-15`** | **Percent-encoding in the request target reaches the kernel byte-identical** | `percent-encoding reaches the kernel as sent` |
| **`P35-04R3-16`** | **A path escaping the configured base prefix is refused, not resolved** | `a path escaping the configured base prefix is refused…` |
| **`P35-04R3-17`** | **The gateway applies no path transformation of its own beyond those the URL parser applies before any handler runs** | `KNOWN LIMITATION: dot segments are resolved before this code runs` |
| **`P35-04R3-18`** | **No request path can reach `buildUpstreamUrl` with an unnormalised dot segment** | verifier to construct; §4 records the maker's measurement, not a verdict |

**`P35-04R3-02` is narrowed on purpose.** R2's version claimed a base prefix survives, full stop;
its test used a path with no dot segments and the claim was false in general. The wording now
matches what the test checks — which is the defect that recurred three times in this package.

## 6. Raised, not resolved — dot-segment normalisation at the platform edge

`/v1/../admin` reaching the kernel as `/admin` is real and unfixable in this component. Whether
it *matters* is an architecture question this submission cannot answer:

- does any ingress or deployment authorize on the raw request target, expecting the gateway to
  forward it intact?
- does any kernel route take a path parameter that may legitimately contain an encoded `..`?

If either is yes, the mitigation belongs upstream of the gateway or in the kernel's routing — not
here. **Recommend a decision record.** Left as a proposition it would be refuted forever by a
verifier correctly reproducing behaviour nobody can change at this layer.

## 7. Residual risks

Carried from R2 §6.2 and unchanged: no end-to-end path executed (the suite injects the upstream);
no timeout on the upstream fetch; no TLS; dependencies pinned but not hash-verified.

## 8. What revisions 1 and 2 teach about this one

R1: 31 tests, 3 mutation probes, a critical SSRF in the gap between its propositions.
R2: 43 tests, 28 confirmations, two refutations in the gap.
R3: 47 tests. **That is not evidence it is correct.** It is the same kind of evidence, one
iteration later, and the only thing that has ever found a defect here is someone independent
attacking a claim the maker was willing to state plainly.

## 9. Authority

A maker's submission. EBIV §8: a passing suite is a self-assessment carrying **no verdict weight**.
Quorum needs two verifiers (§6.1); fewer escalates and never auto-passes (§6.3).

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
