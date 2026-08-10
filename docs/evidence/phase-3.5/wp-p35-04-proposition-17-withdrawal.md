# WP-P35-04 — `-17` withdrawn after four refutations and a verifier's recommendation to retire it

**Document ID:** `EVD-P35-04-WITHDRAW-17`
**Version:** `1.0.0`
**Status:** **MAKER WITHDRAWAL** — not a disposition, not a discharge, and not a verdict on anything
**Issued:** 2026-08-10
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Basis:** `P35-04R6-17` `REFUTED` at `fc0eb77` by Codex, whose ballot recommends retirement

---

## 1. What is withdrawn

The proposition carried as `P35-04R3-17`, `P35-04R4-17`, `P35-04R5-17` and `P35-04R6-17` — in every
wording, an attempt to state what path transformations `buildUpstreamUrl` performs.

**No successor is submitted. There will be no `-17` at a fifth wording.**

## 2. The four refutations, all correct, all reproduced by the maker

| Wording | What it claimed | Refuted because |
| :--- | :--- | :--- |
| `R3-17` | no transformation beyond the parser's | the configured base-path prefix was not excluded |
| `R4-17` | no transformation beyond (a) prefix, (b) escape refusal | `/v1\item` → `/v1/item`; the setter folds backslashes |
| `R5-17` | pathname equals assigning **`path`** to the setter | the base join was omitted, and `search` is not verbatim |
| `R6-17` | equals assigning **`basePath + path`**, then `search` | empty path: literal gives `/base`, the code gives `/base/` |

Every one was independently reproduced before being accepted. The `R6` divergence:

```text
base 'http://kernel.internal:8000/base'
  path ''      literal basePath+path -> /base      buildUpstreamUrl -> /base/
  path 'v1/x'  literal basePath+path -> /basev1/x  buildUpstreamUrl -> /base/v1/x
```

## 3. The finding that ends the sequence

> **The R6 test computed its reference using the implementation's own conditional-separator
> expression, so it could not diverge on the one point the proposition got wrong.**

The verifier put it precisely: *"the named 144-combination test mirrors the implementation's
conditional separator instead of the stated formula, so it does not evaluate this claim."*

Every earlier round failed because the test checked less than the claim. This round failed because
the test was **written by copying the code**, which makes it tautological exactly where the
proposition was inaccurate. A 144-combination test looked like thoroughness and was thoroughness
about the wrong thing.

That is the eighth proposition in this package whose test did not evaluate its claim, and the only
useful conclusion is not a ninth wording.

## 4. The verifier's recommendation, adopted

From ballot `P35-04R6-17`:

> Retirement is preferable to a fifth attempt: existing propositions cover the security-relevant base
> preservation, escape refusal, and encoding behavior, while this repeated implementation-shaped
> restatement has not added a stable distinct invariant.

**What already covers the behaviour, without `-17`:**

| Invariant | Proposition | Status |
| :--- | :--- | :--- |
| A base path prefix survives for paths the parser leaves intact | `P35-04R3-02` | `CONFIRMED` at `1b39a30` |
| A path escaping the configured base prefix is refused, not resolved | `P35-04R3-16` | `CONFIRMED` at `1b39a30` |
| No request path can move the upstream off the kernel origin | `P35-04R3-01` | `CONFIRMED` at `1b39a30` |
| Percent-encoding reaches the kernel byte-identical, dot segments excluded | `P35-04R4-15` | `CONFIRMED` at `92ccbb1` |

`-17` was a **restatement of the implementation**, not an invariant. Its four wordings each described
how `buildUpstreamUrl` is written rather than what callers may rely on — which is why each one broke
the moment a verifier read the code more carefully than the maker had.

## 5. What is NOT withdrawn, and what does not change

1. **All four refutations stand permanently** against `1b39a30`, `92ccbb1` and `2129b25`. Withdrawal
   is not discharge; EBIV §6.2 discharges only by failed reproduction, and none of these was.
2. **No test is deleted.** The tests written across R5 and R6 pass, are mutation-sensitive, and
   assert true things about `buildUpstreamUrl`. They remain as regression cover with no proposition
   attached — which is the correct relationship, since a test may check more than any invariant
   claims.
3. **No source changed at any point in this sequence.** `src/app.ts` has been blob `7fb19ecb` since
   `92ccbb1`. Four submissions altered only claims and tests.
4. **`P35-04R-15` is untouched.** The `/v1` prefix does not confine the proxy; that is live behaviour
   awaiting `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`, and it is the only genuinely open item in this
   package.

## 6. For the operator

This withdrawal is a maker act with a verifier's recommendation behind it, and it needs no
disposition. It is recorded because **the package's proposition set changed**, and because the reason
is worth having in the record: an invariant that restates an implementation cannot be stabilised by
rewording, and four attempts is enough evidence of that.

If the Completion Authority prefers `-17` retained in some form, the request should name the
**caller-facing guarantee** it wants stated — not the code path — because that is the distinction the
four failures were about.

Recorded advisory-only. Confers no verdict, no discharge, no implementation, approval, merge, release
or production authority.
