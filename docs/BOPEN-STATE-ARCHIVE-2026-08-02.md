# bOPEN State Archive — 2026-08-02

**Document ID:** `BOPEN-GOV-ARCHIVE-001`
**Version:** `1.0.0`
**Status:** Milestone checkpoint — Phase 3.5 closure, pending final `WP-P35-05a` R4 disposition
**Issued:** 2026-08-02
**State archived:** as of `79530b1`, the last substantive-work commit; `WP-P35-05a` R4 ballot in flight by Codex
**Tag sits on:** the commit that adds this record (adds no code or state), tagged `milestone/phase-3.5-closure-2026-08-02`

> A single resumable snapshot: where bOPEN stands, what is proven, what is open, and how to
> continue. This is a checkpoint, not a completion — one ballot and several authority decisions
> remain, listed in §5.

---

## 1. What bOPEN is

An independently governed multi-tenant, multi-industry **platform kernel**. It owns platform
concerns — principals, tenancy, authorization, entitlement, events, audit — and forbids industry
semantics in the kernel. Industry products compose on top across a network boundary.

**Seven phases:** 0 Govern · 1 Kernel slice · 2 Membership/SSO · 3 Entitlement · 3.5 Runtime
realization · 3.6 Tenant privacy · 4 Foundations & products.

## 2. What is built and running

The kernel went from an in-process specification model to a service callable across a network
boundary. Verified against live PostgreSQL, canonical suite **465/465**, gateway **47/47**.

| Blueprint layer | State |
| :--- | :--- |
| 1 · API gateway (Hono + Zod) | Built — `apps/gateway`, header contract at the edge |
| 2 · Identity | Authentication boundary built (`subject_assertion.py`); federation (`05b`) deferred |
| 3 · Kernel core (FastAPI + Pydantic v2) | Built — 11 routes |
| 4 · Persistence (PostgreSQL + RLS + psycopg3) | Executed — 9 migrations, 16 tables under RLS |
| 5 · Event microservices (Go) | Deferred pending measured throughput |

## 3. Phase 3.5 closure state (this archive's subject)

Disposed under the **two-agent profile** (`BOPEN-GOV-EBIV-001` §6.5, ratified 2026-08-02): one
independent verifier plus operator disposition confirms, labelled `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.

| Candidate | Commit | Verdict |
| :--- | :--- | :--- |
| `WP-P35-01` persistence + tenant sessions | `6ce069e` | `CONFIRMED_UNDER_TWO_AGENT_PROFILE` — note (a) |
| `WP-P35-02` kernel HTTP surface | `a969bb5` | `CONFIRMED_UNDER_TWO_AGENT_PROFILE` — note (a) |
| `WP-P35-03` signed context token | `767cb81` | `CONFIRMED_UNDER_TWO_AGENT_PROFILE` — note (a) |
| `WP-P35-04` API gateway | `1b39a30` | `BLOCKED_ACCEPTED_WITH_KNOWN_DEFECTS` — two standing refutations; gateway usable |
| `WP-P35-05a` auth boundary | `119f2d8` (R4) | **`AWAITING_BALLOT`** — Codex balloting in flight at archive time |

**Note (a):** the single verifier for `01`..`03` reran maker tests for a large share of its ballots,
so tenant isolation rests on rerun evidence under a one-verifier rule. Recorded, not hidden.

**Note on `WP-P35-04`:** the SSRF, response-desync, cookie and connection-header defects are fixed
and the gateway is usable; the two refutations (`R3-15` dot-segment normalisation, `R3-17` base-path
prefixing) are unresolvable at that layer and stand permanently.

## 4. What was found and fixed — the record that matters

Every serious defect came from adversarial work, never from counting confirmations:

- **Unauthenticated SSRF** in the gateway (caller chose the upstream host, bearer token exfiltrated) — subagent sweep. Fixed.
- **Privilege escalation** — a tenant member acting as owner via an unsigned `X-Context-ID` the kernel published. Reproduced by two engines. Closed by `AUTH-D1`.
- **Auth boundary defects** — 500-not-503 on malformed PEM, a signature-validity status oracle, an unbounded replay window, an integer-truncation lifetime bypass (the first refutation to find a *code* defect, not a wording one). All fixed or bounded.
- **Eight commits under the wrong git identity** — disclosed in `AGENTS.md` §23.0, not rewritten.
- **AUTH-D3 exposure measured** — a complete unauthenticated path to an owner token exists, but tenant isolation holds throughout: unbounded in volume, bounded in blast radius.

## 5. Open — how to resume

### Authority decisions (operator/authority only)

| Decision | Effect when made |
| :--- | :--- |
| Dispose `WP-P35-05a` R4 (after Codex ballot) | Phase 3.5 fully closed → **Phase 4 entry opens** |
| `DEC-P35-AUTH-D3-DOCKET` | Closes the last auth hole; Row 1 mitigations need no enrollment decision |
| `DEC-P35-CONTROL-PLANE-DOCKET` (`D-CP-001/002/004`, `memberships` plane) | Unblocks Phase 3.6 |
| `DEC-P35-VERIFIER-REASSIGN` | Cleans the maker/verifier role record for `01`..`03` |

### The one engineering action in flight

`WP-P35-05a` R4 ballot — Codex, at `119f2d8`. When it lands: verify from repository objects,
then operator disposition under the §6.5 profile.

### Deferred by decision, not oversight

Go event microservices; rebalancing between placements; the analytics collector (frequency/flow/
reports need no business content); `WP-P35-05b` BoxyHQ federation. Two things the analytics
deferral must **not** sweep along: `P-1` (close `action`/`resource_type` vocabularies) and
`D-CP-002` (audit placement) — both cheap now, unrecoverable later.

## 6. How to pick the work back up

1. Read [`AGENTS.md`](../AGENTS.md) §20.2 (gate) and §6.5 of [`BOPEN-GOV-EBIV-001`](00-governance/BOPEN-GOV-EBIV-001.md) (two-agent profile).
2. Read [`ACTION-PLAN`](ACTION-PLAN.md) §3 for the live critical path and [`AGENT-ALIGNMENT`](00-governance/AGENT-ALIGNMENT.md) for the orientation register.
3. Every agent: `git config user.email` before the first commit — the shared config has been switched between runs and caused misattribution (`AGENTS.md` §23.0).
4. Source `.env.local` before any check; a `CANNOT RUN` is not a pass.
5. Verdicts are per candidate commit, never per phase — ballots bind to commits.

## 7. Governance posture

The apparatus earned its cost this session: `check_evidence_anchors` caught evidence bound to a
non-existent commit; `check_ballot_attribution` caught eight misattributed commits and, once fixed,
a per-phase-vs-per-candidate quorum miscount; the refutation rule caught a critical SSRF and an
integer-truncation bypass that all confirmations had missed. The two-agent profile preserves the
half that works — one reproducible refutation blocks — while conceding only the second verifier a
two-agent team cannot supply.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
