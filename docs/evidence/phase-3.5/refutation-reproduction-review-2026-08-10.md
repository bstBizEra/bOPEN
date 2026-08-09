# Reproduction review of the five undischarged refutations — 2026-08-10

> **THIS IS NOT A DISCHARGE, AND NOT A BALLOT.** `BOPEN-GOV-EBIV-001` §6.2 discharges a refutation
> only by a failed reproduction recorded against a **successor candidate**. No successor candidate
> exists for any of the five below, no ballot was cast, and nothing here changes any verdict. It
> records what the probes do at `ebb4dcc` so the operator can see which refutations are closable and
> which are not.

**Working tree:** `ebb4dcc` · **Independent runner:** Codex (read-only, no file changed, no ballot
cast, no commit) · **Also run by:** Claude — the maker of part of the surrounding work, whose results
carry no verdict weight under EBIV §8 and are recorded only because they agree.

---

## 1. Result

| Proposition | Candidate | Reproduces at `ebb4dcc`? | Probe exit | Nature |
| :--- | :--- | :--- | :--- | :--- |
| `P35-04R-16` | `88e6ed2` | **No** | `1` | Fixed — containment check refuses the escape |
| `P35-05aR3-02` | `e559d1d` | **No** (unit level only — see §3) | `1` | Fixed — `float()` replaces truncating `int()` |
| `P35-04R-15` | `88e6ed2` | **Yes** | `0` | **Code defect, unresolved** — awaits an operator decision |
| `P35-04R3-15` | `1b39a30` | **Yes** | `0` | Proposition overclaims; behaviour intended |
| `P35-04R3-17` | `1b39a30` | **Yes** | `0` | Proposition overclaims; behaviour intended |

Both runners obtained identical exit statuses and identical observations on all five. Exit statuses
were read from the probe process, not from a surrounding pipeline — a distinction that has produced a
false claim in this repository before.

## 2. The two that no longer reproduce

**`P35-04R-16`** — `buildUpstreamUrl('http://kernel.invalid/base', '/../../admin', '')` no longer
returns `/admin`. It throws:

```
UpstreamPathEscape: resolved path /admin escapes the configured base path /base
```

Mechanism: the containment check at `apps/gateway/src/app.ts:129`, which refuses a resolved pathname
that does not remain at or below the configured base path.

**`P35-05aR3-02`** — an assertion with integer `iat` and `exp = iat + 300.9` is now refused with
`reason == "lifetime_exceeds_ceiling"`. Mechanism: `subject_assertion.py:265` computes
`float(exp) - float(iat)` instead of truncating both sides with `int()`. The comment above that line
cites this refutation and records the outcome plainly:

> *"The proposition was right and the code was wrong. Worth recording, because the previous seven
> refutations in this repository were the other way round."*

## 3. The limitation on `P35-05aR3-02`, stated rather than buried

The original probe was `tools/probes/run_wp_p35_05a_r3_codex.ps1`. **It was not run.** It creates
principals, tenants, memberships, contexts, resources and audit rows in PostgreSQL, which the
read-only boundary of this review forbids, and its hard-coded Python path no longer exists on this
machine.

What was run instead: a generated EdDSA assertion passed directly to
`platform_kernel.subject_assertion.verify_subject_assertion`, with the regression checking 300.1,
300.9 and 300.99 seconds and an exact-300-second acceptance control.

**This is a unit-level result, not an end-to-end HTTP + PostgreSQL rerun.** It is strong evidence and
it is not the same evidence. Any discharge ballot should either run the original probe or state the
substitution explicitly.

## 4. The three that still reproduce, and why they are not one problem

### 4.1 `P35-04R-15` — a live behaviour, and not closable by an agent

`/v1/../admin` and `/v1/%2E%2E/admin` both still reach the injected kernel as `/admin`, status 200.
The `/v1` prefix does not confine the proxy.

The independent runner classified this **code defect / unresolved authorization-boundary behaviour**
and stated the reason it cannot be closed here:

> The architectural repair cannot be selected by an agent. `DEC-P35-GATEWAY-PREFIX-CONFINEMENT`
> remains `Proposed` and awaits the Architecture/Security Authorities' decision between `/v1`
> confinement and a deliberate catch-all contract.

**Choosing between confining the proxy and declaring it deliberately open is the judgement itself.**
An agent that picked either would be substituting for the decision, not implementing it. This
refutation stays open until that decision is disposed.

### 4.2 `P35-04R3-15` and `P35-04R3-17` — the propositions overclaim; the code is right

Neither is repairable by changing code, because neither behaviour is wrong:

- **`P35-04R3-15`** claims percent-encoding reaches the kernel byte-identical. Ordinary encodings —
  `/a%2Fb`, `/café` — are preserved, which was the repair's purpose. Encoded **dot segments** are
  normalised before the handler sees the URL, and the proposition does not exclude them.
- **`P35-04R3-17`** claims the gateway applies no path transformation of its own. A configured `/base`
  is prefixed. That transformation is intentional and is separately claimed by `P35-04R3-02`, but
  `R3-17` as written does not exclude it.

The repair is to **write the propositions correctly and ballot them at a new candidate**. The original
refutations remain true of `1b39a30` permanently; EBIV does not retract a refutation because a later
proposition is better worded.

## 5. What would actually close each

| Proposition | To close it |
| :--- | :--- |
| `P35-04R-16` | A successor candidate, a maker submission, and a ballot by an eligible verifier recording the failed reproduction |
| `P35-05aR3-02` | The same, plus either the original end-to-end probe or an explicit record of the unit-level substitution (§3) |
| `P35-04R3-15`, `P35-04R3-17` | Corrected propositions, balloted at a new candidate. The old ballots stay `REFUTED` |
| `P35-04R-15` | **An operator decision on `DEC-P35-GATEWAY-PREFIX-CONFINEMENT` first.** Nothing an agent does closes this one |

## 6. One tool defect surfaced

`tools/governance_state.py` lists `aa2a74b2` under `BLOCKED BY REFUTATION`. Both of its refuted
propositions — `P35-D3b-05` and `P35-D3b-08` — are `CONFIRMED` at successor `7fcd86c`, which is
disposed. The entry is stale. The cause is the limitation already recorded in that tool: it aggregates
by **candidate** and does not bind disposition scope to proposition scope. Third occurrence of that
limitation producing a misleading row.

---

Recorded advisory-only by Claude (Motor). Confers no verdict, no discharge, no implementation,
approval, merge, release or production authority.
