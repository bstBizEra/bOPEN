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

## 2. Standing state, 2026-08-02

| | Count |
| :--- | :--- |
| Work packages implemented | 5 (`WP-P35-01`..`04`, `05a`) |
| Independent ballots cast | **123** across candidates |
| Phases authorized | 0, 1, 2, 3, 3.5; 3.6 partial |
| Phase 3.5 | **CLOSING** — 01-03 `CONFIRMED_UNDER_TWO_AGENT_PROFILE`, 04 accepted-with-defects, 05a R4 awaits one ballot |
| Canonical suite | 465/465 against PostgreSQL |
| Gateway suite | 47/47 |
| Governance checks | 6/6 pass |

**What "confirmed" means here is weaker than it sounds, by design.** Under the two-agent profile
(EBIV §6.5) a confirmation is one independent verifier plus operator disposition, not two blind
verifiers — recorded as `CONFIRMED_UNDER_TWO_AGENT_PROFILE` so the difference is never silent.
The single verifier for `WP-P35-01`..`03` reran maker tests for many of its ballots, so tenant
isolation in particular rests on rerun evidence. Green suites remain maker self-assessment with
no verdict weight (§8).

## 3. Critical path

### A-01 — Verify Phase 3.5 *(largely COMPLETE, 2026-08-02)*

Once the single most valuable action; now nearly discharged. `DEC-P35-TWO-AGENT-QUORUM` Option B
(EBIV §6.5) resolved the structural blocker — with a two-agent team, one verifier plus operator
disposition confirms.

| Package | State |
| :--- | :--- |
| `WP-P35-01`..`03` | **`CONFIRMED_UNDER_TWO_AGENT_PROFILE`** — Gemini verifier + operator disposition |
| `WP-P35-04` | **Accepted with known defects** — two standing refutations, gateway usable |
| `WP-P35-05a` R4 | **The one remaining action:** a Codex ballot at `119f2d8` |

**Only `WP-P35-05a` R4 is still open.** After that ballot and its disposition, A-01 is complete
and Phase 4 entry opens (its condition was `WP-P35-01`..`03`, now disposed). The verification-debt
risk that made this "blocking everything" has been discharged rather than deferred.

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
| A-01 | Verify Phase 3.5 | Codex + operator | §6.5 profile | **DONE except `WP-P35-05a` R4 — one Codex ballot at `119f2d8`** |
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
| Business-content analytics | **Not authorized at all.** `DEC-P35-CONTROL-PLANE` §5B: the requirement is frequency, flow and reports, none of which touch business content. `D-CP-005` withdrawn |
| The analytics collector agent, dashboards, flow reports | **Deferred until bOPEN is finished** (operator, 2026-08-01). These consume data; building them before there is a stable platform to consume from is the wrong order |
| Phase 4 | Not authorized. Blocked on Phase 3.5 admissible evidence, which blocks on A-01 |

**Two things the analytics deferral does NOT cover**, because they decide whether the data will
exist and be safe to read when the collector is finally built:

- **`P-1` — closing the `action` and `resource_type` vocabularies.** Free text today. Deferring
  it lets tenants accumulate arbitrary values in audit rows, and migration 009's principle means
  those rows cannot be edited to fix it. Historical rows would have to be excluded rather than
  cleaned.
- **`D-CP-002` — where audit lives.** Placement, not analytics. If hybrid placement lands first,
  audit goes somewhere by default, and moving it later is a migration across N databases.
  Cross-tenant visibility is annihilated by dedicated placement rather than relocated, so a
  projection that does not exist from the first tenant leaves the collector with no history.

Both are cheap now and unrecoverable later. Neither is new scope: `P-1` is already a
prerequisite in `DEC-P35-CONTROL-PLANE-DOCKET` §3.2 and `D-CP-002` is already docket row 3.

## 6. Review cadence

This document is reviewed when a gate clears, not on a calendar. A row whose gate has cleared and
which has not moved is the signal that something is wrong with the plan rather than with the
schedule.

## 7. Authority

Planning artefact. Confers no implementation, approval or production authority. Rows referencing
unratified decisions remain blocked regardless of their position in the table.
