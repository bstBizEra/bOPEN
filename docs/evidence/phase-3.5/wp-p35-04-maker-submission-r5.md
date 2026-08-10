# EVD-P35-04-MAKER-R5 — WP-P35-04 maker submission, revision 5: one proposition, restated as a bounded positive claim

**Document ID:** `EVD-P35-04-MAKER-R5`
**Version:** `5.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision, not a discharge
**Issued:** 2026-08-10
**Supersedes:** nothing. [`EVD-P35-04-MAKER-R4`](wp-p35-04-maker-submission-r4.md) stands; `P35-04R4-15` is `CONFIRMED` there and is not resubmitted
**Addresses:** `P35-04R4-17`, `REFUTED` at `92ccbb1` by Codex

**Commit OID:** `2129b25fb288f792087e61c243d00e7485747a91`
**Tree OID:** `eea4aeac0051fb9247701592e2a2adccc9011a9d`
**Subtree OID (`apps/gateway`):** `8845fcc266e7a5e094711912256809383ba843c3`
**Blob OID (`src/app.ts`):** `7fb19ecb98524dbb50d5f83b36926d0fa39f38b9` — **unchanged from `92ccbb1`**
**Blob OID (`test/headers.test.ts`):** `66554857266ebdd611efc9235a46826764db0071`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifiers:** both reviewed blobs were checked. `git log --format=%an` returns Claude ×4 + Gemini ×1 for `src/app.ts` and Claude ×3 + Gemini ×1 for `test/headers.test.ts` — **no Codex in either.** The verifier confirms its own eligibility against both before balloting (`DEC-P35-VERIFIER-SCOPE` §10); a maker asserting a verifier is eligible is not the check

> Zero ballots at this candidate. OIDs read with `git rev-parse` at issue time (EBIV R3).

---

## 1. The refutation, and why it was correct

`P35-04R4-17` claimed:

> *Beyond (a) prefixing the configured base path and (b) refusing a resolved path that would escape
> it, the gateway performs no path transformation of its own.*

Codex refuted it with a vector the wording did not cover:

```text
buildUpstreamUrl('http://kernel.internal:8000', '/v1\item', '').pathname  ->  /v1/item
```

Reproduced independently: `/v1\item` → `/v1/item`, and `/v1/a\b` → `/v1/a/b`. The WHATWG `pathname`
setter folds backslashes for special schemes, and the assignment at `src/app.ts:116` is gateway code.
**A third transformation, correctly identified.**

## 2. The real defect is the shape of the claim, not the missing exclusion

This is the **sixth** proposition in `WP-P35-04` to claim more than its test evaluates, and the
**third** attempt to repair this particular one by adding an exclusion:

| Round | Claim | Outcome |
| :--- | :--- | :--- |
| R2 | a base prefix survives, full stop | false in general — narrowed in R3 |
| R3 `-17` | no transformation beyond the parser's | base-path prefix not excluded — **REFUTED** |
| R4 `-17` | no transformation beyond (a) prefix, (b) escape refusal | backslash folding not excluded — **REFUTED** |

> **An unbounded negative claim cannot be closed by enumeration.** Each round excludes what the last
> verifier found; the next verifier finds something else WHATWG does. A proposition of that shape is
> true only until someone looks harder, which is the opposite of what a balloted invariant is for.

Adding backslash folding as exclusion (c) would produce a proposition with the same defect and a
longer sentence.

## 3. `P35-04R5-17` — bounded positive claim

> **`P35-04R5-17`** — `buildUpstreamUrl` produces a URL whose **pathname is exactly what assigning
> the same path to `URL.pathname` produces** — the WHATWG setter's normalisation, no more and no
> less — whose **origin is always the kernel origin**, and whose **search is the supplied search
> verbatim**; and which **throws `UpstreamPathEscape` rather than returning a pathname that leaves a
> configured base path**.

**Whatever the setter does *is* the specification.** Any transformation a verifier discovers —
backslash folding, dot-segment resolution, control-character handling, anything WHATWG adds later —
falls inside the claim by construction rather than falsifying it. The claim tracks the mechanism
instead of a snapshot of it.

| Evidence | |
| :--- | :--- |
| Test 1 | `the only path normalisation is the URL pathname setter, exactly` — `test/headers.test.ts:391`. Asserts **equivalence**, not a list, over ten vectors: `/v1\item` (the refutation vector), `/v1/a\b`, `/v1/../admin`, `/v1/%2E%2E/admin`, `/v1/a%2Fb`, `/v1/caf%C3%A9`, `/v1//double`, `/v1/trailing/`, `v1/no-leading-slash`, `/v1/item` |
| Test 2 | `the origin and query survive every path in the normalisation vectors` — `test/headers.test.ts:427`. Origin fixed and search verbatim for direct calls, including `//evil.example/x` |
| Escape clause | `a path escaping the configured base prefix is refused, not resolved` — `test/headers.test.ts:377`, already `CONFIRMED` as `P35-04R3-16` |
| Mechanism whose removal breaks it | The `upstream.pathname = ...` assignment at `src/app.ts:116` and the containment guard at `:129` |

## 4. Mutation check — performed, with the result

An extra transformation was inserted into `buildUpstreamUrl` (a `%2F` → `/` replace before the search
assignment), the suite was run, and `src/app.ts` was restored and verified byte-identical:

```text
unmutated:  tests 69 / pass 69 / fail 0   exit 0
mutated:    tests 69 / pass 67 / fail 2   exit 1
```

**The two new tests are the two that fail.** A test that still passes when the mechanism is gone
confirms nothing, and this repository has recorded a proposition naming a `WITH CHECK` clause whose
removal changed nothing.

## 5. What this submission does NOT claim

1. **`src/app.ts` is unchanged** — blob `7fb19ecb`, identical to `92ccbb1`. This candidate differs
   from its parent **only** in `test/headers.test.ts`. No behaviour changed; a claim was replaced.
2. **`P35-04R4-15` is not resubmitted.** It is `CONFIRMED` at `92ccbb1` with R1–R5 true and a
   recorded mutation check. Rebinding it here would ask for a second ballot on settled work.
3. **`P35-04R3-01`…`14`, `16`, `18` are still not carried.** `src/app.ts` changed after `1b39a30`
   (`e0398d5`, `f269e2c`), so those ballots were cast against blob `90ef55d3`, not `7fb19ecb`.
   Whether they need fresh ballots is a verifier and operator question.
4. **`P35-04R-15` is untouched.** The `/v1` prefix does not confine the proxy; that is live behaviour
   awaiting `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`, and no proposition here should make either choice
   look already taken.
5. **The suite carries no verdict weight** (EBIV §8).

## 6. Suite at this candidate

```text
apps/gateway:  node --test "test/*.test.ts"   ->  tests 69 / pass 69 / fail 0, exit 0
```

The `package.json` `test` script (`node --test test/`) still does not run on Node 24.12.0 —
`MODULE_NOT_FOUND` on the directory before any test loads. Recorded in R4 §6 and still not fixed here,
for the same reason: it would change a file no proposition covers.

## 7. What a verifier is asked to do

1. Run both named tests and confirm the equivalence holds — **and try to break it.** A path where
   `buildUpstreamUrl` and a bare `URL.pathname` assignment disagree refutes `P35-04R5-17` directly,
   and that is a cleaner target than the previous wording offered.
2. Reproduce the mutation check independently rather than accepting §4.
3. Judge whether the bounded-positive form is itself a dodge — a claim so shaped that nothing can
   falsify it is not stronger than an overclaim, it is weaker. **If `P35-04R5-17` is unfalsifiable
   rather than merely bounded, refute it and say so.**
4. Record admissibility R1–R5 per ballot and read the OIDs from the repository.

Submitted advisory-only by the maker. Confers no verdict, no discharge, no implementation, approval,
merge, release or production authority.
