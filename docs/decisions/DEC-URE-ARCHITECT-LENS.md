# DEC-URE-ARCHITECT-LENS — the URE-Loop Staff Architect is seated as a review lens, not as an agent

**Decision ID:** `DEC-URE-ARCHITECT-LENS`
**Version:** `1.0.0`
**Status:** **AUTHORIZED 2026-08-07** — operator directive, transcribed by Claude (Motor). Promotes `AGENTS.md` §26.2 from `PROPOSED` to in force. Not a maker approval.
**Issued:** 2026-08-07
**Owner:** Architecture & Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** `AGENTS.md` §21 (agent commit identity), §26 (URE-Loop adaptation); [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §2, §8; [`BOPEN-GOV-IDENT-001`](../00-governance/BOPEN-GOV-IDENT-001.md)

---

## 1. Why this exists

`AGENTS.md` §26 recorded an adaptation of the external *Unified Review Engineer Loop* design (v0.4,
then v0.6) as `PROPOSED — NOT IN FORCE`. Its §26.2 describes the URE-Loop review panel re-cast as
three **probing lenses** rather than a decision body.

The operator directed: *"Authorize Agent: URE-Loop Staff Architect Agent"*. That phrase carried three
materially different readings — a review role, a registered commit identity, or the ADR-owning
authority the v0.6 template assigns it — so the reading was put to the operator rather than chosen by
an agent. **The review-role reading was selected.**

## 2. Decision

**The Staff Architect is seated as a review lens.** `AGENTS.md` §26.2 is promoted from `PROPOSED` to
**in force**, with the architecture & boundary lens available as a working review role on any work
package.

| Field | Value |
| :--- | :--- |
| **Decision** | **AUTHORIZE the §26.2 architecture & boundary lens as a review role.** Findings only; no ballot, no identity, no authority |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Decision timestamp** | 2026-08-07 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 2.1 What the seat is

The lens probes kernel/industry separation, clean-room zones, contract compatibility and
`tenant_session` discipline (`AGENTS.md` §6, §7, §10, §25.1 step 4), and reports findings.

The directive named the **Staff Architect** only. §26.2's other two lenses — security & refusal, and
performance & test quality — remain described but **unseated**, and seating either needs its own
directive. Promoting the subsection is not read as seating everything it describes.

### 2.2 What the seat is not

1. **Not a verifier seat.** Who may ballot is governed solely by `BOPEN-GOV-EBIV-001` admissibility
   R1–R5. A lens run by the maker produces findings and no verdict (EBIV §8).
2. **Not an identity.** No entry is added to
   [`agent-identity-register.json`](../00-governance/agent-identity-register.json). The lens commits
   nothing; the acting engine commits under its own registered `<agent>@bst.local` address (§21.1).
3. **Not an authority.** It does not own, accept or advance an ADR, and it does not dispose a work
   package. Disposition remains with the Completion Authority (§25.1 step 8).
4. **Not a quorum contribution.** Lenses run by one engine, or by engines able to read each other's
   output, count as **one** verifier (§26.2 constraint 2).

## 3. Why a persona was not registered as a commit identity

Recorded because the alternative was considered and declined, and the reasoning binds future
requests of the same shape.

`BOPEN-GOV-IDENT-001` registers **engines** — `claude`, `codex`, `gemini`, `kimi` — plus the human
operator. "Staff Architect" is a persona, not an independent runtime. Giving it a commit identity
would let a single engine commit as Staff Architect, Security & Edge-Case Specialist and Performance
Specialist, and appear in `check_ballot_attribution.py` as three independent verifiers.

That is precisely the **accidental collapse** the register exists to catch — "two ballots that appear
independent but are not, a verifier that is really the maker" (`AGENTS.md` §21.5). A persona identity
would not merely fail to help; it would convert the register's one working assurance into a mechanism
for manufacturing false independence.

Registering a persona therefore requires a superseding decision that also amends `AGENTS.md` §26.2
and `BOPEN-GOV-IDENT-001`. It is not authorized here.

## 4. What this decision does not reach

| Item | State after this decision |
| :--- | :--- |
| `AGENTS.md` §26.3 (feedback tiers), §26.4 (cost controls), §26.5 (git lifecycle) | Remain `PROPOSED` |
| `AGENTS.md` §26.8 (ADR drafting), §26.9 (drift detection) | Remain `PROPOSED` |
| `AGENTS.md` §26.6 — all ten exclusions | **Remain excluded.** Each needs its own decision |
| ADR `Proposed → Accepted` by a panel | **Still excluded.** The 2026-08-06 operator rejection of AI authority expansion stands and is not superseded by name or effect |
| Merge, release, deployment, production activation | Unchanged — outside agent authority |
| `agent-identity-register.json` | Unchanged |

## 5. Provenance

Operator directive 2026-08-07, given in session after the ambiguity in "Authorize Agent" was raised
and the review-role reading was selected from four options. Recorded before use, per the
authorize-before-build rule (`AGENTS.md` §25.1 step 0).

This decision confers no implementation, approval, merge, release or production authority.
