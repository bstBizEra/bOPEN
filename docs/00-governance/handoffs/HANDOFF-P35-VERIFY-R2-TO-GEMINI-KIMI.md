# HANDOFF-P35-VERIFY-R2-TO-GEMINI-KIMI — Second verifier seat, and the four packages nobody has looked at

**Status:** **Active — issued 2026-08-01; §2 revised same day after Gemini ruled**

> **Revision, 2026-08-01 — read this before §2.** Gemini has since cast 49 ballots (`adc97fc`).
> That changes both asks:
>
> - **`WP-P35-04` now holds quorum** (codex + gemini at `88e6ed2`). It no longer needs a seat —
>   except for `P35-04R-15` and `P35-04R-16`, added after Gemini's run and **still unballoted**.
> - **`WP-P35-01`..`03` now have one verifier each, not zero.** **Kimi is the second seat**, and
>   the only remaining route to quorum on those three.
>
> Correcting a claim that reached this repository twice: `check_ballot_attribution.py` reported
> *"2 verifiers toward a quorum of 2 — PASS"* for the whole phase while three of four candidates
> had one verifier each. It counted per phase, not per work package. Fixed in `fbd8a99`; it now
> reports per candidate and names every shortfall. **Do not read a phase-level PASS as quorum.**
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Gemini / Antigravity, **or** Kimi — either alone is useful
**Supersedes:** [`HANDOFF-P35-VERIFY-TO-GEMINI-KIMI`](HANDOFF-P35-VERIFY-TO-GEMINI-KIMI.md), stood down 2026-07-30 and stale in every particular
**Governing standards:** [`BOPEN-GOV-EBIV-001`](../BOPEN-GOV-EBIV-001.md) §3, §5, §6, §7; [`BOPEN-GOV-IDENT-001`](../BOPEN-GOV-IDENT-001.md)

---

## 1. Why the previous handoff cannot be used

It was issued 2026-07-30 and predates the SSRF discovery and repair, the `WP-P35-04` R2 reissue,
`WP-P35-05a` entirely, and Codex's ballots. Dispatching it would point you at commits that are
superseded or defective.

Codex caught exactly that mistake on 2026-07-31: it verified the anchors in its handoff before
ruling, found `WP-P35-04` pointed at a commit containing an unauthenticated SSRF, and refused to
ballot. **Verify every anchor below with `git rev-parse` before you rule.** If one is stale, say
so and stop — that is a correct outcome, not a failure to deliver.

## 2. What you are being asked for, in priority order

### 2.1 `WP-P35-04` — complete the quorum *(highest value)*

14 admissible ballots exist from Codex (`0d12332`). `BOPEN-GOV-EBIV-001` §6.1 requires **two**
independent verifiers to confirm; there is one. `check_ballot_attribution.py` currently reports:

```text
phase-3.5: 14 ballot(s), 1 attributable verifier(s) toward a quorum of 2
quorum NOT MET — a confirmation cannot be realized.
```

**You are the second seat.** You are eligible: Claude wrote the code, Codex ruled on it, neither
is you.

| Field | Value |
| :--- | :--- |
| Submission | [`EVD-P35-04-MAKER-R2`](../../evidence/phase-3.5/wp-p35-04-maker-submission-r2.md) **including §6A** |
| Commit | `88e6ed2b4f2ab80a6b8ef0e8d570f761d8725b4b` |
| Tree | `39da471ae01ade3e3ee619f788d99fabbe1fde3d` |
| `apps/gateway` subtree | `485f6b3f0814274700cabcf5d5a38943dd6c4e43` |
| Propositions | `P35-04R-01`..`14`, **plus `15` and `16` added 2026-08-01** |
| Suites | canonical 433/433, gateway 43/43 |

**Do not read Codex's ballots before forming your own view.** §3.1 requires verifiers to be blind
to each other; sequential verifiers who can see prior verdicts count as one. `ballots.jsonl` is in
the tree — read it after you have committed your own, if at all.

**Two propositions are offered expecting `REFUTED`.** §6A.3: `P35-04R-15` (path fidelity) and
`P35-04R-16` (base-path containment) are both believed false by the maker and are offered so the
defects can be balloted rather than sitting in prose where no verdict can reach them. Refute them
with your own probe; do not take the maker's word.

**One existing proposition is disclosed as overclaiming.** §6A.2: `P35-04R-02` asserts a base path
prefix survives, and its test only exercises a path with no dot segments. It is false in general.
Codex confirmed it, correctly, on what it asserts. Form your own view on whether that warrants
`REFUTED` or `INADMISSIBLE`.

### 2.2 `WP-P35-01`..`WP-P35-03` — nobody has ever looked

Zero ballots. These are the oldest unverified packages in the repository and the seat has been
empty since 2026-07-30. **Claude authored them and Codex is assigned to remediate them, so §3
excludes both. Only you can rule on these.**

| Package | Submission | Commit |
| :--- | :--- | :--- |
| `WP-P35-01` persistence + tenant sessions | [`maker-submission.md`](../../evidence/phase-3.5/maker-submission.md) | verify with `git rev-parse` before ruling |
| `WP-P35-02` kernel HTTP surface | [`wp-p35-02-maker-submission.md`](../../evidence/phase-3.5/wp-p35-02-maker-submission.md) | as above |
| `WP-P35-03` signed context token | [`wp-p35-03-maker-submission.md`](../../evidence/phase-3.5/wp-p35-03-maker-submission.md) | as above |

`WP-P35-01` carries the **tenant isolation** claim — 38 tests executing against live PostgreSQL.
It is the single most consequential unverified assertion in this repository: if isolation does not
hold, it does not hold across every future product at once.

### 2.3 `WP-P35-05a` — excluded

Codex's `HOLD_FOR_DECISION` stands; `AUTH-D1` and `AUTH-D3` are with the authorities. Do not
ballot it.

## 3. What this repository has learned about how to attack it

Offered because it is the fastest route to a real defect, not to steer your verdict.

**Every defect found here so far lived in the gap between a proposition and its test.** Three
instances in two days:

1. Revision 1's path test — fixture had no `.` or `%`, and a critical unauthenticated SSRF hid
   behind it through 31 passing tests and three mutation probes.
2. §6.1 path normalisation — reproduced, but no proposition claimed path fidelity, so an
   adversarial ballot could not touch it.
3. `P35-04R-02` — true for its fixture, false in general.

**So: read each proposition, then read the test it names, and ask what the words claim that the
test does not check.** That question has found something every time it has been asked here.

### 3.1 What a probe has to be — the bar, stated because the last run sat below it

`probe_command` is the field that decides whether a ballot carries evidence. Measured across the
63 ballots cast so far, there are two tiers, and the record should be able to tell them apart:

| Tier | Example | What it establishes |
| :--- | :--- | :--- |
| **Independent probe** | Codex's 90 hostile path/search combinations; Gemini's 14 hand-written `node --eval` one-liners against `buildUpstreamUrl` | An independent agent constructed an attack and it failed |
| **Named-test rerun** | `python -m unittest tests/isolation/test_rls_database_behavior.py`, used as the probe for 13 separate ballots | The maker's named test passes at this commit |

Both are legitimate; **only the first is refutation.** EBIV §8 holds that a maker's passing suite
carries no verdict weight, and a probe that *is* the maker's suite transmits that same absence of
weight into a ballot. 32 of Gemini's 49 ballots sit in the second tier.

**For `WP-P35-01` in particular this matters more than anywhere else.** Its invariants are the
tenant isolation claims — `INV-TENANT-ISOLATION-01/02`, `INV-TENANT-DENY-DEFAULT-01/02`,
`INV-TENANT-WRITE-01/02`, `INV-TENANT-FORCE-RLS-01`. Rerunning
`test_rls_database_behavior.py` shows Claude's tests pass. **Write your own SQL.** Open a
tenant-scoped session, try to read another tenant's rows directly, try to write across the
boundary, try it as the table owner to test `FORCE ROW LEVEL SECURITY`, try with
`app.current_tenant_id` unset. If isolation does not hold, it does not hold across every future
product at once, and it is the single claim in this repository least able to afford a rerun in
place of a probe.

Second: **do not trust maker tests.** Claude wrote the implementations *and* their tests. A green
suite is a maker self-assessment carrying no verdict weight (§8).

Third: **the stated limitations are where the maker already knows it is weak.** `WP-P35-05a`'s
replay window, `WP-P35-04` §6.2's absent end-to-end path, `WP-P35-01`'s isolation claims. Start
there.

## 4. Identity — do this before anything else

Neither of you has a commit identity in this repository yet. `agent-identity-register.json`
already reserves them:

```bash
git config user.name  "Gemini (BST-SA Motor)"     # or: Kimi (BST-SA Motor)
git config user.email "gemini@bst.local"          # or: kimi@bst.local
```

`check_ballot_attribution.py` binds `verifier_id` to the git author of the commit introducing the
ballot line, and refuses unregistered identities. **A ballot under the wrong identity does not
count toward quorum** — not as punishment, but because it carries no evidence about who cast it.

Never commit under the operator's identity; 29 commits already carry that defect.

## 5. Ballot format and checks

One JSON object per line in `docs/evidence/phase-3.5/ballots.jsonl`, per §7:

```json
{
  "ballot_id": "blt_<hex12>",
  "proposition_id": "P35-04R-15",
  "commit_oid": "<read with git rev-parse — never typed>",
  "tree_oid": "<read with git rev-parse>",
  "verifier_id": "gemini",
  "verifier_lens": "<your angle of attack>",
  "independent_of_maker": true,
  "verdict": "CONFIRMED | REFUTED | ABSTAIN | INADMISSIBLE",
  "probe_command": "<the exact command you ran>",
  "probe_exit_code": 0,
  "probe_observation": "<what you observed, factually>",
  "refutation_attempted": true,
  "admissibility": { "R1": true, "R2": true, "R3": true, "R4": true, "R5": true },
  "issued_at": "<ISO8601>"
}
```

`probe_command` and `probe_exit_code` are mandatory on `CONFIRMED` and `REFUTED` — a ballot with
no runnable probe is inadmissible under R1. `independent_of_maker: false` voids it. **One commit
must not introduce ballots for two verifiers**; commit your own alone.

```bash
set -a; . ./.env.local; set +a          # sourcing matters: an unsourced shell produced
python tools/run_tests.py               # 9 failures and 18 errors that were a missing env,
cd apps/gateway && node --test "test/*.test.ts"   # not a missing database
python tools/check_ballot_attribution.py          # must PASS before you report
```

A check reporting `CANNOT RUN` is **not** a pass.

## 6. What your ballots establish

On `WP-P35-04`: with your ballots the quorum reaches two, and confirmation becomes *possible* —
though §6.1 also requires a strict majority of admissible non-abstaining ballots, and a single
`REFUTED` with a reproducible probe blocks regardless of how many confirmations oppose it.

On `WP-P35-01`..`03`: one verifier, so §6.3 escalates to the Completion Authority rather than
confirming. Moving those from *"nobody has looked"* to *"one independent agent has looked"* is
still the largest single improvement available in this repository.

**A `REFUTED` ballot with a reproducible probe is worth more to us than a `CONFIRMED` one.** The
maker has shipped a critical SSRF behind a green suite once already this week.

## 7. Provenance

Issued by Claude (agent, Motor role) on 2026-08-01. Claude is the maker of every package listed
and has no standing to influence any verdict. §3 tells you where the maker believes it is weak; it
does not tell you what to conclude.

```text
execution_authority: false
approval_authority: false
```
