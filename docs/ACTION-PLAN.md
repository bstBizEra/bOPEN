# bOPEN Action Plan

**Document ID:** `BOPEN-GOV-ACTION-001`
**Version:** `1.0.0`
**Status:** Live — regenerate the state table when any row changes
**Issued:** 2026-07-31
**Owner:** Engineering Authority
**Companion documents:** [`BOPEN-P36-001`](work-packages/BOPEN-P36-001-EXECUTION-PLAN.md) (what to build), [`ENGINEERING-LOOP`](08-engineering/ENGINEERING-LOOP.md) (how to build it)

---

## 1. What this is

The execution plans say *what* is built and the engineering loop says *how*. This says **what
happens next, in what order, and what is stopping each one**.

One rule governs it: a row moves only when the thing blocking it has an outcome recorded, never
because it has been waiting a long time.

## 2. Standing state, 2026-07-31

| | Count |
| :--- | :--- |
| Work packages implemented | 5 (`WP-P35-01`..`04`, `05a`) |
| Independent ballots cast | **14** — all on `WP-P35-04`, from **1 verifier of 2 required** |
| Phases authorized | 0, 1, 2, 3, 3.5; 3.6 partial |
| Phases verified | **none** — quorum unmet on every package |
| Canonical suite | 433/433 against PostgreSQL |
| Gateway suite | 31/31 |
| Governance checks | 6/6 pass |

**Read the second row before the fifth.** Green suites are maker self-assessment and carry no
verdict weight under `BOPEN-GOV-EBIV-001` §8. Nothing in this repository has been verified by
anyone who did not write it.

## 3. Critical path

The single most valuable action is not on any execution plan.

### A-01 — Seat a verifier *(blocking everything downstream)*

| | |
| :--- | :--- |
| **Why first** | Five implemented work packages cannot be completed, and Phase 4 cannot open, until an independent verifier rules. No amount of further code changes this |
| **Who** | Gemini or Kimi for `WP-P35-01`..`03` — Claude authored them and Codex is remediating, so §20.3 disqualifies both. Codex for `WP-P35-04` and `05a`, which it did not touch |
| **Blocked by** | Gemini/Kimi seats for `WP-P35-01`..`03` remain available. `WP-P35-04` has one verifier of two. `WP-P35-05a`: `AUTH-D1` is accepted; Claude must remediate it, while `AUTH-D3` still needs authority disposition before a successor submission |
| **Risk if deferred** | Verification debt compounds. Each new package adds to a queue nobody has started, and the eventual reviewer faces a body of work too large to probe honestly |

**Codex completed preflight and must not ballot the stale candidates.** The original handoff is
on HOLD under `EVD-P35-CODEX-PREFLIGHT-001`; independence remains intact for a maker-issued
successor.

### A-02 — Security and Privacy review of `DEC-P35-CONTROL-PLANE`

| | |
| :--- | :--- |
| **Why** | Gates the whole of Phase 3.6. `BOPEN-P36-001` cannot start |
| **Must resolve** | `D-CP-003` enumerated one cross-table policy (`principals_read` -> `memberships`); decide its plane/projection shape. Then resolve **F-2** personal data, **F-3** audit placement, and retention |
| **Who** | Security Authority, Privacy Authority |
| **Blocked by** | Nothing. Available today |

### A-03 — Assign a maker to `WP-P35-06`

Accepted and specified since 2026-07-31, unassigned. Alternation suggests Codex or Claude; either
keeps the other eligible as checker.

## 4. Sequenced actions

| # | Action | Owner | Gate | State |
| :--- | :--- | :--- | :--- | :--- |
| A-01 | Cast ballots on `WP-P35-01`..`05a` | Gemini / Kimi / Codex | current exact-commit maker submission | **Gemini/Kimi available for 01-03; Codex HOLD for 04/05a** |
| A-02 | Security + Privacy review of `DEC-P35-CONTROL-PLANE` | Security, Privacy | none | **available now** |
| A-03 | Assign maker to `WP-P35-06` | Engineering | none | **available now** |
| A-04 | Plane assignment register (D-16) | `WP-P36-01` maker | A-02 | blocked |
| A-05 | Cross-plane integrity design + probes (D-17) | `WP-P36-01` maker | A-04 | blocked |
| A-06 | Placement recording and resolver (D-18, D-19) | `WP-P35-06` maker | A-03, A-05 | blocked |
| A-07 | Control-plane credential boundary (D-21) | `WP-P36-02` maker | A-02, A-06 | blocked |
| A-08 | Telemetry normalisation + PII register (D-22, D-23) | `WP-P36-02` maker | A-07 | blocked |
| A-09 | Migration uniformity + disclosure (D-20, D-24) | `WP-P36-03` maker | A-06 | blocked |
| A-10 | Ratify `D-P35-004`..`D-P35-018` | designated authorities | none | **available now** |
| A-11 | Enterprise IdP federation `WP-P35-05b` | unassigned | A-10 (incl. `D-P35-014`) | blocked |
| A-12 | Decide rebalancing before tenant count makes it costly | Architecture | A-06 | not yet urgent, will become so |

## 5. What is deliberately not being done

Recorded so that absence reads as a decision rather than an oversight.

| Not doing | Why |
| :--- | :--- |
| More implementation ahead of verification | Five unverified packages is already too many. Adding a sixth increases the debt, not the progress |
| Go event microservices | Deferred pending measured throughput, `DEC-P35-RUNTIME` §5 |
| Rebalancing between placements | Out of scope for `WP-P35-06`; named in A-12 so it is not forgotten |
| Business-content analytics | Needs the consent mechanism in `DEC-P35-CONTROL-PLANE` §5 tier 3, which needs a buyer to justify building |
| Phase 4 | Not authorized. Blocked on Phase 3.5 admissible evidence, which blocks on A-01 |

## 6. Review cadence

This document is reviewed when a gate clears, not on a calendar. A row whose gate has cleared and
which has not moved is the signal that something is wrong with the plan rather than with the
schedule.

## 7. Authority

Planning artefact. Confers no implementation, approval or production authority. Rows referencing
unratified decisions remain blocked regardless of their position in the table.
