# EVD-P35-04-MAKER-R6 — WP-P35-04 maker submission, revision 6: the fourth attempt at one proposition

**Document ID:** `EVD-P35-04-MAKER-R6`
**Version:** `6.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision, not a discharge
**Issued:** 2026-08-10
**Supersedes:** nothing. [`EVD-P35-04-MAKER-R5`](wp-p35-04-maker-submission-r5.md) stands, including the correction recorded in its §4
**Addresses:** `P35-04R5-17`, `REFUTED` at `2129b25` by Codex on two independent grounds

**Commit OID:** `fc0eb7775f8738e1a37526d4ce21185754c43c48`
**Tree OID:** `a001c0ce6ac1b19e1757476dbfebb009122885d9`
**Subtree OID (`apps/gateway`):** `5b3964319f5bed9baeb45388932f39da1d38260e`
**Blob OID (`src/app.ts`):** `7fb19ecb98524dbb50d5f83b36926d0fa39f38b9` — **unchanged since `92ccbb1`**
**Blob OID (`test/headers.test.ts`):** `115eb702280d1c50b2cd579bba54e80f6df9fe28`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifiers:** `git log --format=%an` shows no Codex on either reviewed blob. The verifier confirms this itself before balloting (`DEC-P35-VERIFIER-SCOPE` §10)

> Zero ballots at this candidate. OIDs read with `git rev-parse` at issue time (EBIV R3).

---

## 1. Both refutation grounds, reproduced

**Ground 1 — the base-path operation the claim omitted.**

```text
buildUpstreamUrl('http://kernel.internal:8000/base/', '/v1/item', '').pathname  ->  /base/v1/item
new URL('http://kernel.internal:8000/base/').pathname = '/v1/item'              ->  /v1/item
```

**Ground 2 — "search verbatim" is false.**

```text
'?a=1&b= '  ->  '?a=1&b=%20'      the search setter normalises
'?a=1&b=%20', '?x', '?a=%2F', '?a=1&a=2', ''  ->  unchanged
```

One counter-example falsifies "verbatim", and there is one. *(Codex reported 4 of 5 supplied searches
normalised; an independent 6-vector sample found 1 of 6. The samples differ; the verdict does not, and
the maker's smaller number is recorded rather than the verifier's larger one being repeated.)*

**Why R5's test could not catch either.** Its equivalence compared against `path` rather than
`basePath + path`, and **every vector used an origin with no base path**. A test that never configures
a base cannot observe the base join. The claim and the test disagreed, and the test was the one that
got written first.

## 2. Seventh occurrence, fourth attempt, and the honest shape of that

| Round | Claim about path transformation | Outcome |
| :--- | :--- | :--- |
| R2 | a base prefix survives, full stop | false in general |
| R3 `-17` | no transformation beyond the parser's | base-path prefix not excluded — **REFUTED** |
| R4 `-17` | no transformation beyond (a) prefix, (b) escape refusal | backslash folding not excluded — **REFUTED** |
| R5 `-17` | pathname equals assigning **`path`** to the setter | base join and search normalisation omitted — **REFUTED** |
| R6 `-17` | *below* | — |

R5 was supposed to end this by replacing an unbounded negative with a bounded positive. **The form was
right and the content was still wrong**: Codex's ballot records that *"the relational setter bound is
falsifiable and is not itself a tautology"*, so the reason R5 failed is not the shape of the claim but
that the maker wrote a reference the implementation does not use.

That distinction matters, because the R5 → R6 change is small. If it fails again, the shape is not
what needs revisiting.

## 3. `P35-04R6-17`

> **`P35-04R6-17`** — `buildUpstreamUrl(base, path, search)` returns exactly the URL produced by:
> assigning `basePath + path` to `URL.pathname`, then `search` to `URL.search`, on a fresh `URL(base)`
> — where `basePath` is `base`'s pathname with trailing slashes stripped. Both setters' normalisation
> applies unchanged and is part of the result. **The single departure** is that a resolved pathname
> which leaves a non-empty `basePath` raises `UpstreamPathEscape` instead of being returned.

| Evidence | |
| :--- | :--- |
| Test 1 | `buildUpstreamUrl is exactly two setter assignments and a containment check` — `test/headers.test.ts:391`. Compares full `href` over **3 bases × 8 paths × 6 searches = 144 combinations**. Bases: none, `/base`, `/base/`. Includes `/v1\item` (the vector that refuted R4) and `?a=1&b= ` (the vector that refuted R5) |
| Test 2 | `dot segments reaching buildUpstreamUrl directly are refused, not silently contained` — `test/headers.test.ts:438`. Asserts the departure with a base, **and** asserts that with no base the setters apply unchanged and `/../../admin` returns `/admin` |
| Mechanism | The two assignments at `src/app.ts:116`–`117` and the containment guard at `:129` |

## 4. Mutation check — two mutations, failing tests **named**

R5's §4 inferred which tests failed from a count and named the wrong ones. That is corrected in
[R5 §4](wp-p35-04-maker-submission-r5.md) and not repeated here:

```text
unmutated                             71 tests / 71 pass / 0 fail   exit 0

A: add `%2F` -> `/` before search     71 tests / 68 pass / 3 fail
     buildUpstreamUrl is exactly two setter assignments and a containment check
     percent-encoding reaches the kernel as sent
     the only path normalisation is the URL pathname setter, exactly

B: remove the base join               71 tests / 68 pass / 3 fail
     a base path prefix is preserved rather than discarded
     an ordinary path under a base prefix is still allowed
     buildUpstreamUrl is exactly two setter assignments and a containment check
```

Both mutations kill Test 1. `src/app.ts` was restored and verified byte-identical after each.

## 5. What this submission does NOT claim

1. **No source changed.** `src/app.ts` is blob `7fb19ecb`, unchanged since `92ccbb1`. Three
   submissions in a row have altered only a claim and its test.
2. **R5's two tests are left in place.** They pass, and what they assert is true of the no-base case
   they exercise. They are subsumed by Test 1, not contradicted by it. `P35-04R5-17` remains
   `REFUTED` at `2129b25` permanently.
3. **`P35-04R4-15` is not resubmitted** — `CONFIRMED` at `92ccbb1`.
4. **`P35-04R3-01`…`14`, `16`, `18` are still not carried.** `src/app.ts` changed after `1b39a30`
   (`e0398d5`, `f269e2c`); those ballots were cast against blob `90ef55d3`.
5. **`P35-04R-15` is untouched** — live behaviour awaiting `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`.
6. **The suite carries no verdict weight** (EBIV §8).

## 6. Suite

```text
apps/gateway:  node --test "test/*.test.ts"   ->  tests 71 / pass 71 / fail 0, exit 0
```

`package.json`'s `test` script still does not run on Node 24.12.0 (`MODULE_NOT_FOUND` on the
directory). Recorded in R4 §6, still unfixed, same reason: no proposition covers it.

## 7. What a verifier is asked to do

1. **Try a base or search the 144 combinations miss.** A non-special scheme base, a base with a query
   or fragment, an empty `path`, a path that is only `..`, a search containing a `#`, control
   characters, `%00`. One divergence refutes `P35-04R6-17` outright.
2. **Reproduce the mutation check and name the failing tests yourself** rather than accepting §4 —
   that is precisely where the previous submission was wrong.
3. **Say whether four rounds on one proposition is a signal the proposition should be dropped.**
   `P35-04R3-02` and `-16` already claim the base-path behaviours separately, and
   `P35-04R4-15` claims the encoding behaviour. If `-17` adds nothing those three do not already
   cover, the correct outcome may be to retire it rather than confirm a fourth wording. **A verifier
   saying so would be more useful than a confirmation.**
4. Record admissibility R1–R5 and read the OIDs from the repository.

Submitted advisory-only by the maker. Confers no verdict, no discharge, no implementation, approval,
merge, release or production authority.
