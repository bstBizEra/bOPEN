# bOPEN Engineering Loop

**Document ID:** `BOPEN-ENG-LOOP-001`
**Version:** `1.0.0`
**Status:** Operational
**Issued:** 2026-07-31
**Owner:** Engineering Authority
**Governing artifacts:** `AGENTS.md` §5, §16, §17, §20.3, §21, §23; `BOPEN-GOV-EBIV-001`; `BOPEN-GOV-IDENT-001`
**Companion documents:** [`ACTION-PLAN`](../ACTION-PLAN.md) (what is next), execution plans (what to build)

---

## 1. The loop

One work package, one turn of the loop. It does not begin in the middle and it does not end at a
green test suite.

```text
   ┌─ 1 BIND ──────── work package, governing artifacts, maker seat
   │
   │  2 BASELINE ──── if architecture changes (§23) — tag first, never after
   │
   │  3 SPECIFY ───── contract before implementation (§10)
   │
   │  4 BUILD ─────── smallest coherent change (§5.5)
   │
   │  5 PROBE ─────── negative tests, then mutate to prove they can fail
   │
   │  6 EVIDENCE ──── anchors read from git, never transcribed
   │
   │  7 SUBMIT ────── maker's report — carries no verdict weight
   │
   │  8 VERIFY ────── someone who did not write it ◄── THE LOOP STOPS HERE
   │                                                    IF NOBODY IS SEATED
   │  9 RECORD ────── completion authority, or refutation
   └────────────────► next package
```

**Stage 8 is not a formality and not the last 5% of the work.** A package that reaches stage 7
and stops is not "nearly done" — it is unverified, which is where all five current Phase 3.5
packages sit.

## 2. Stage by stage

### 1 · Bind

Identify the accepted work package ID, the governing artifacts, and your role. If you are Maker,
you are excluded from voting on this package for its lifetime (`BOPEN-GOV-EBIV-001` §3). Check the
role table before writing, not after — the exclusion is earned by authorship and cannot be undone
by intent.

Set your commit identity per repository (`AGENTS.md` §21.1). Never the operator's.

### 2 · Baseline

Only if the change alters architecture — the isolation mechanism, an approved artifact or ADR, the
technology selection, a blueprint layer, or a data-flow boundary. Tag before the change lands
(`AGENTS.md` §23). A baseline taken afterwards captures the thing you were trying to preserve a
copy of, already changed.

### 3 · Specify

For externally observable behaviour, the contract comes first (§10). If a decision is unratified,
**stop and raise a decision request** rather than choosing by implementation default (§16). This
is the stage where most damage is avoidable and where skipping is most tempting.

### 4 · Build

Smallest coherent change. Ask *"is this the defect, or am I adding capability?"* before writing.
Additive is better than invasive: a change that is inert until configured — as `WP-P35-05a` and
`WP-P35-06` both are — makes rollback a configuration edit rather than a revert.

### 5 · Probe

Every security-relevant rule carries a negative test asserting the violating operation is refused
(EBIV R4). Then **mutate the mechanism and confirm the test fails.**

```bash
# 1. break it deliberately
# 2. run the suite — it must go red
# 3. restore, re-verify green
```

A test that passes with the mechanism removed measures nothing. This is the cheapest quality
check in the loop and the one most often skipped, because a green suite feels like completion.

### 6 · Evidence

Anchors are read from git, never typed:

```bash
git rev-parse HEAD                 # commit OID
git rev-parse HEAD^{tree}          # tree OID
python tools/check_evidence_anchors.py
```

An evidence record bound to an object that does not resolve cannot be re-verified, which defeats
its purpose. This has already happened once here, in Phase 3, and the check exists because of it.

Record limitations in the submission — replay windows, unreachable code paths, untested
compositions. A limitation you disclose is a finding; one a verifier discovers is a defect in
your report as well as in the code.

### 7 · Submit

Report per `AGENTS.md` §17: work-package IDs, files changed, contracts changed, checks and
results, evidence path, residual risks, decisions still required.

Offer **falsifiable propositions**: one invariant, one commit, one named test, and the mechanism
whose removal makes that test fail. A verifier's job is to try to break these, and vague claims
cannot be broken — which reads as strength and is the opposite.

### 8 · Verify

An agent that authored any part of the artifact, including its tests, may not vote. Verifiers are
blind to each other; sequential verifiers who can read prior verdicts count as one.

One `REFUTED` ballot carrying a reproducible probe blocks, and is discharged only by a failed
reproduction — never by re-assertion.

### 9 · Record

Completion authority records the outcome only after admissibility and unresolved-refutation
checks. A quorum verifies; it never authorizes. Production activation, specification amendment and
permission widening remain outside agent authority regardless of vote.

## 3. Required checks

Every package, every time. Source the environment first — most of these silently do nothing
without it.

```bash
set -a; . ./.env.local; set +a

python tools/run_tests.py                    # canonical suite
python tools/validate_repository.py
python tools/check_clean_room.py
python tools/check_authority_bootstrap.py
python tools/check_evidence_anchors.py
python tools/check_ballot_attribution.py
python tools/check_contract_conformance.py
cd apps/gateway && node --test "test/*.test.ts"
```

A check that reports `CANNOT RUN` is not a pass. On 2026-07-31 an unsourced shell produced 9
failures and 18 errors that were read as a missing database and reported as a blocker; the
database was present and the suite was green. **Verify the environment before believing a
failure.**

## 4. Stop conditions

Stop and raise a decision request (`AGENTS.md` §16) when a required artifact is absent, two
approved artifacts conflict, tenant ownership is ambiguous, authorization precedence is undefined,
a clean-room boundary is crossed, a destructive migration lacks recovery, industry logic would
enter the kernel, or scope exceeds the accepted package.

Stopping is a result. This repository's failure mode is not agents refusing too often — it is
work proceeding past a question that was never answered.

## 5. Anti-patterns, each observed here

| Anti-pattern | What it costs |
| :--- | :--- |
| Building ahead of the checker | Stacking on an unreviewed parent risks invalidating both |
| Reporting a green suite as completion | Maker self-assessment carries no verdict weight (EBIV §8) |
| Transcribing evidence anchors | An unresolvable OID makes the claim unverifiable |
| Reading a spec instead of querying the database | Reading migrations gave 5 foreign keys; the database had 12 |
| Trusting one query's empty result | `information_schema` filters by ownership; `pg_catalog` did not |
| Bundling unrelated work into one commit | Misattributes both halves; split the hunks |
| Deleting superseded text | Extend-only. Mark it superseded and record why |
| Assuming a check passed because it exited quietly | `CANNOT RUN` is not a pass |

## 6. Authority

Process document. Confers no implementation, approval or production authority. Where it and
`AGENTS.md` disagree, `AGENTS.md` governs and this document is the defect.
