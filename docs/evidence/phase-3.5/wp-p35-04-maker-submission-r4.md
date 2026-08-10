# EVD-P35-04-MAKER-R4 — WP-P35-04 maker submission, revision 4 (API Gateway): two corrected propositions

**Document ID:** `EVD-P35-04-MAKER-R4`
**Version:** `4.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision, and not a discharge
**Issued:** 2026-08-10
**Supersedes:** nothing. [`EVD-P35-04-MAKER-R3`](wp-p35-04-maker-submission-r3.md) stands; this adds two propositions to replace two it got wrong
**Addresses:** `P35-04R3-15` and `P35-04R3-17`, both `REFUTED` at `1b39a30` by Codex

**Commit OID:** `92ccbb1db9adc3008490b826f964087f9da6b739`
**Tree OID:** `f6302cdbd0b90cf17984cea302a52aa89f0b991d`
**Subtree OID (`apps/gateway`):** `a7e83cdf2d7c4258d9dc9050840b098b6d5e3e4f`
**Blob OID (`src/app.ts`):** `7fb19ecb98524dbb50d5f83b36926d0fa39f38b9`
**Blob OID (`test/headers.test.ts`):** `857ee9c6d6f54ad0ef9cfd2bacb73f0089f13007`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifiers:** Codex — `git log --format=%an -- apps/gateway/src/app.ts` returns Claude ×4 and Gemini ×1, no Codex. The verifier confirms its own eligibility before balloting, per `DEC-P35-VERIFIER-SCOPE` §10; a maker asserting a verifier is eligible is not the check

> Zero ballots at this candidate. All OIDs read with `git rev-parse` at issue time (EBIV R3).

---

## 1. What this submission is, and what it is not

**Not a discharge.** `BOPEN-GOV-EBIV-001` §6.2 discharges a refutation only by a **failed
reproduction**. Both refutations below still reproduce at this candidate, verified independently by
Codex on 2026-08-10 and recorded in
[`refutation-reproduction-review-2026-08-10.md`](refutation-reproduction-review-2026-08-10.md). They
reproduce because **the code is correct and the propositions were not.**

`P35-04R3-15` and `P35-04R3-17` remain `REFUTED` against `1b39a30` permanently. Nothing here retracts
them, and no ballot at this candidate should be read as doing so.

**No code changed for this submission.** `apps/gateway/src/app.ts` is untouched. Only the two
propositions are new, and they describe behaviour that already exists and is already tested.

## 2. The defect being repaired, and its history in this package

Both refutations found the same thing: a proposition claiming more than its test checks.

> **From `EVD-P35-04-MAKER-R3` §5, about a third instance:** *"R2's version claimed a base prefix
> survives, full stop; its test used a path with no dot segments and the claim was false in general.
> The wording now matches what the test checks — **which is the defect that recurred three times in
> this package.**"*

These are the fourth and fifth. The pattern is stable enough to name: **a proposition written from
what the author believes the code does, rather than from what the named test evaluates.** Both
corrections below are written from the test outward.

## 3. `P35-04R4-15` — percent-encoding, with the exclusion the old wording omitted

| | |
| :--- | :--- |
| **Refuted wording (`P35-04R3-15`)** | *"Percent-encoding in the request target reaches the kernel byte-identical"* |
| **Why it was refuted** | It does not exclude encoded dot segments. `/v1/%2E%2E/admin` reaches the kernel as `/admin`. Codex: *"The examples `/a%2Fb` and `/caf%C3%A9` are repaired, but the proposition as written is false."* |

**Corrected proposition:**

> **`P35-04R4-15`** — Percent-encoding in the request target reaches the kernel byte-identical **for
> every sequence the WHATWG URL parser preserves. Dot segments — `.` and `..`, percent-encoded or
> not — are excluded: the parser resolves them when the `Request` is constructed, before Hono or any
> gateway code runs, and the original target is unrecoverable at this layer.**

| Evidence | |
| :--- | :--- |
| Positive test | `percent-encoding reaches the kernel as sent` — `test/headers.test.ts:345`. Sends `/v1/a%2Fb` and `/v1/caf%C3%A9`; asserts both arrive byte-identical |
| Exclusion test | `KNOWN LIMITATION: dot segments are resolved before this code runs` — `test/headers.test.ts:361`. Asserts `/v1/../admin` arrives as `/admin` — **it asserts the excluded behaviour on purpose**, so the exclusion cannot change silently in either direction |
| Mechanism whose removal breaks it | `new URL(c.req.url).pathname` at `src/app.ts:207`, replacing `c.req.path`, which ran `decodeURI` |

## 4. `P35-04R4-17` — no transformation, minus the one it does perform

| | |
| :--- | :--- |
| **Refuted wording (`P35-04R3-17`)** | *"The gateway applies no path transformation of its own beyond those the URL parser applies before any handler runs"* |
| **Why it was refuted** | With a configured `/base`, `/v1/item` becomes `/base/v1/item`. Codex: *"That transformation is intentional and separately claimed by R3-02, but R3-17 does not exclude it and therefore still overclaims."* |

**Corrected proposition:**

> **`P35-04R4-17`** — Beyond **(a)** prefixing the configured base path and **(b)** refusing a
> resolved path that would escape it, the gateway performs no path transformation of its own. Changes
> made by the URL parser before any handler runs are not the gateway's; their extent is claimed by
> `P35-04R4-15`.

| Evidence | |
| :--- | :--- |
| Exclusion (a) | `an ordinary path under a base prefix is still allowed` — `test/headers.test.ts:386`. `/v1/authorize` under base `/base` → `/base/v1/authorize`. Separately claimed by `P35-04R3-02` |
| Exclusion (b) | `a path escaping the configured base prefix is refused, not resolved` — `test/headers.test.ts:377`. Separately claimed by `P35-04R3-16` |
| Residual claim | Everything else in `buildUpstreamUrl` — origin, query, and the untouched path — passes through |
| Mechanism whose removal breaks it | The base-path join and the `UpstreamPathEscape` guard at `src/app.ts:129` |

**Note on exclusion (b).** The test's own comment records that this path is *"unreachable from a
request — the parser normalises first — so this closes a latent hazard in an exported function rather
than a live request path."* The exclusion is stated anyway, because `buildUpstreamUrl` is exported and
a caller other than the request handler can reach it.

## 5. What this submission does NOT claim

Stated because the scope of a revision is exactly where a maker's judgement is least trustworthy:

1. **It does not carry `P35-04R3-01`…`14`, `16` or `18` to this candidate.**
   `apps/gateway/src/app.ts` **changed after `1b39a30`** — `e0398d5` added edge rate limiting for
   creation and `f269e2c` closed a percent-encoding bypass of it — so the blob those ballots were cast
   against (`90ef55d3`) is not this one (`7fb19ecb`). Whether they need fresh ballots here is a
   **verifier and operator question**; this submission neither assumes they carry nor asserts they do
   not.
2. **It does not address `P35-04R-15`.** The `/v1` prefix does not confine the proxy; that is a live
   behaviour, not a wording defect, and `DEC-P35-GATEWAY-PREFIX-CONFINEMENT` is still `Proposed`.
   Choosing between confining the proxy and declaring it a deliberate catch-all is the decision
   itself, and no proposition should be written that makes either choice look already taken.
3. **It claims nothing about the suite's verdict weight.** A passing suite carries none (EBIV §8).

## 6. Suite at this candidate

```text
apps/gateway:  node --test "test/*.test.ts"   ->  tests 67 / pass 67 / fail 0, exit 0
```

**The `package.json` `test` script does not run.** `node --test test/` fails on Node 24.12.0 with
`MODULE_NOT_FOUND` on the directory itself, before any test loads:

```text
Error: Cannot find module 'C:\laragon\www\bopen\apps\gateway\test'
```

This is a **script defect, not a test failure** — the same invocation with a glob passes 67/67. It is
recorded here rather than fixed, because fixing it would change a file in this candidate and no
proposition covers it. Raised for a work package of its own.

The canonical Python suite was not re-run for this submission; nothing in it is touched by two
markdown propositions.

## 7. What a verifier is asked to do

1. Confirm `P35-04R4-15` **including its exclusion** — that the positive test preserves encoding and
   that the exclusion test still asserts `/admin`.
2. Confirm `P35-04R4-17` **including both exclusions** — and check that the residual claim is not
   itself an overclaim, which is the failure this revision exists to repair and the one most likely to
   recur inside its own repair.
3. Record admissibility R1–R5 per ballot, and read the OIDs above rather than the prose.
4. **Refute either one if it still claims more than its test evaluates.** Two rounds of this package
   were closed on wording that read well; the third, fourth and fifth were not.

Submitted advisory-only by the maker. Confers no verdict, no discharge, no implementation, approval,
merge, release or production authority.
