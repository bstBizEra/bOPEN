# HANDOFF-P35-BALLOTS-TO-CODEX — Cast ballots on `WP-P35-04` and `WP-P35-05a`

**Status:** Active — issued 2026-07-31
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Codex Agent IDE
**Action:** `A-01` in [`ACTION-PLAN`](../../ACTION-PLAN.md) — the critical path
**Governing standards:** [`BOPEN-GOV-EBIV-001`](../BOPEN-GOV-EBIV-001.md) §3, §4, §5, §6, §7; [`BOPEN-GOV-IDENT-001`](../BOPEN-GOV-IDENT-001.md)

---

## 1. Why you, and why this is the only thing that matters right now

Five work packages are implemented. **Zero ballots have been cast in this repository, ever.**
Nothing can be completed and Phase 4 cannot open until an agent that did not write the code rules
on it. No amount of further implementation changes that — it makes it worse, by lengthening the
queue.

You are eligible for `WP-P35-04` (API gateway) and `WP-P35-05a` (kernel authentication boundary).
Claude authored both and you did not touch either. You are **not** eligible for `WP-P35-01`..`03`:
Claude authored them and you are assigned to remediate them, so §3 excludes you on both counts.
Those need Gemini or Kimi.

## 2. Your first act, before reading any code

```bash
git config user.name  "Codex (BST-SA Motor)"
git config user.email "codex@bst.local"
```

`check_ballot_attribution.py` binds `verifier_id` to the git author of the commit that introduces
the ballot line. A ballot committed under the wrong identity does not count toward quorum — not
as a punishment, but because a ballot whose author cannot be established carries no evidence
about who cast it, which is the only thing §3 needs from it.

**Never commit under the operator's identity.** 29 commits already carry that defect and are
recorded as unattributable.

## 3. What you are ruling on

| Submission | Propositions | Commit |
| :--- | :--- | :--- |
| [`EVD-P35-04-MAKER`](../../evidence/phase-3.5/wp-p35-04-maker-submission.md) | `P35-04-01` .. `P35-04-12` | `c03cd4f423d6afa9ee1441e340f5720f184db08c` |
| [`EVD-P35-05A-MAKER`](../../evidence/phase-3.5/wp-p35-05a-maker-submission.md) | `P35-05a-01` .. `P35-05a-11` | `b11e2e8a976a7a5f7469361331a2fe0ddec699bd` |

Each proposition names one invariant, one commit, one test, and the mechanism whose removal makes
that test fail. That is the shape you are meant to attack.

## 4. Your job is to refute, not to confirm

`BOPEN-GOV-EBIV-001` §6.1 is asymmetric on purpose: confirming needs a majority of at least two
verifiers, but **one `REFUTED` ballot carrying a reproducible probe blocks**, however many
confirmations oppose it. A reproducible demonstration is not outvoted by assertions.

So the valuable outcome is a defect, not a rubber stamp. Default to scepticism. Specifically:

- **Do not trust the maker's tests.** They were written by the same agent that wrote the code.
  Write your own probes.
- **Attack the stated limitations first.** `EVD-P35-05A-MAKER` §5 admits no replay protection —
  `jti` is checked but never stored. Prove the window is real and measure it. §5 also admits the
  module's own claim type-check is unreachable. Check whether that leaves a gap PyJWT does not
  cover.
- **Check what the propositions do not claim.** `P35-05a-11` says behaviour is unchanged with no
  authenticator configured. Nothing claims other endpoints are authenticated — verify whether
  `POST /v1/tenants` mints an owner membership without an assertion.
- `EVD-P35-04-MAKER` §6 admits no end-to-end path was proven; the gateway suite injects the
  upstream. Run a real request through gateway → kernel → PostgreSQL and see whether the
  composition holds.

## 5. Running the checks

**Source the environment first.** An unsourced shell produced 9 failures and 18 errors on
2026-07-31 that were misread as a missing database; the database was present and the suite green.
A check reporting `CANNOT RUN` is not a pass.

```bash
set -a; . ./.env.local; set +a
python tools/run_tests.py                       # 433 expected
cd apps/gateway && node --test "test/*.test.ts" # 31 expected
```

## 6. Ballot format

One JSON object per line in `docs/evidence/phase-3.5/ballots.jsonl`. Per §7:

```json
{
  "ballot_id": "blt_<hex12>",
  "proposition_id": "P35-04-03",
  "commit_oid": "<40-hex, read with git rev-parse — never typed>",
  "tree_oid": "<40-hex, read with git rev-parse>",
  "verifier_id": "codex",
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

Rules that will void your work if missed:

- `probe_command` and `probe_exit_code` are **mandatory** on `CONFIRMED` and `REFUTED`. A ballot
  without a runnable probe is inadmissible under R1.
- `independent_of_maker: false` voids the ballot.
- **One commit must not introduce ballots for two different verifiers.** Commit your own ballots
  alone.
- OIDs are read with `git rev-parse`, never transcribed.

Then:

```bash
python tools/check_ballot_attribution.py   # must PASS before you report
python tools/check_evidence_anchors.py
```

## 7. What your ballots will and will not establish

Two packages ruled on by one verifier does **not** confirm them. §6.1 needs a minimum of two
verifiers to confirm, and §6.3 says fewer than two escalates to the Completion Authority and
never auto-passes. Your ballots move these packages from *"nobody has looked"* to *"one
independent agent has looked and here is what they found"*, and the operator decides on that
basis.

That is a real and large improvement over the current state, and it is not a completion. Please
do not describe it as one.

## 8. If you find nothing

Say so plainly, with the probes you ran. A `CONFIRMED` ballot backed by real attempted refutation
is worth something. A `CONFIRMED` ballot backed by rerunning the maker's tests is worth nothing
and will be caught by `refutation_attempted`.

## 9. Provenance

Issued by Claude (agent, Motor role) on 2026-07-31 under operator instruction. Claude is the
maker of both packages under review and has no standing to influence the verdict; this document
exists to give you the artifacts and the format, not the answer.

```text
execution_authority: false
approval_authority: false
```
