# Phase 4 (MILE-4.2) — readiness & authorization-sequencing map

**Document ID:** `MAP-P4-READINESS`
**Version:** `1.0.0`
**Status:** **Advisory planning — authorizes nothing.** A Motor synthesis of where Phase 4 stands and a *recommended* authorization sequence. Every foundation build and every promotion remains an operator decision recorded in `DEC-P4-ENTRY` before build.
**Issued:** 2026-08-06
**Author:** Claude (agent, Motor role) — advisory only, no approval authority
**Purpose:** give the operator one place to see disposed vs. gated, per-foundation readiness and remaining prerequisites, and a recommended order — so an authorization decision is informed, not inferred.

---

## 1. Disposed (ratified) — the built platform

- **Kernel + hybrid tenancy (Option D) — complete.** Shared RLS pool (trial/free) · dedicated-DB provisioning + usable dedicated tenant (Option A) · verified trial→paid migration, with the `tenant_session` freeze at the single write chokepoint.
- **Six MILE-4.2 foundations disposed** (each: authorize-before-build → tests-first → migration+forced-RLS → repo → endpoints → EBIV R2 trace → maker submission → independent Codex ballot → operator disposition):

| Foundation | Keystone defended |
| :--- | :--- |
| Party (`BOPEN-PARTY-001`) | tenant-scoped party graph |
| Money | integer minor units, exact — never float |
| Workflow | state machine + append-only history |
| UOM | dimension-safe (kg+m refused), exact Decimal |
| Party ContactPoint (`BOPEN-PARTY-002`) | resolver never falls back to `principals.email` |
| Location (`BOPEN-LOC-001`) | coordinate validity + provider distrust ("HTTP 200 ≠ accepted") |

## 2. Gated foundations — readiness & remaining prerequisites

| Foundation | Research | Review | Design prep produced | Remaining before authorization | Gate |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Notification** | ✅ | ✅ | worker/queue ADR (DRAFT, under Codex review) · provider/channel ADR (DRAFT) · privacy/threat model (DRAFT) | `BOPEN-NOTIFY-001` spec · test/refusal matrix · migration/rollback plan — **PAUSED** pending the ADR review; then freeze all + record `DEC-P4-ENTRY` authorization. Dependency `NOTIFY-D-01` (ContactPoint) **cleared**. | gated |
| **Document** | ✅ | ✅ | — | `BOPEN-DOC-001` + successor artifacts (grant model, scanner-fail-closed, migration, test matrix); `DEC-P4-ENTRY` authorization | gated |
| **Calendar** | ✅ | ✅ | — | civil-time/tzdb supply-chain ADR (the new external-data dependency) · `BOPEN-CAL-001` + successor artifacts; `DEC-P4-ENTRY` authorization | gated |
| **Asset** | ~67% (RETURN FOR REVISION) | — | — | research revised past the open Medium strict-checker finding **first**, then review, then the above | gated |

## 3. Open governance items

- **`AGENTS.md` §24 (reasoning/Refusal-Matrix standards)** and **§25 (governed engineering loop)** — recorded **PROPOSED / NOT IN FORCE**; awaiting an explicit operator authorization (with Git provenance) to become normative. They grant no authority.
- **AI authority-parity bundle** — **REJECTED 2026-08-06**, fail-closed retained (`38083e5`). Resolved; EBIV §2 keeps Completion Authority a human/named-authority role, not an agent role.
- **Codex advisory review of the two Notification ADRs** — in flight (read-only sandbox). Its findings gate the remaining Notification prep.

## 4. Recommended authorization sequence (Motor recommendation — the operator decides)

1. **Notification** — closest to ready: its dependency is cleared and its design corpus is nearly complete. *Path:* the Codex ADR review clears (or its gaps are revised) → freeze the remaining prep (spec, test/refusal matrix, migration plan) → record the `DEC-P4-ENTRY` authorization → governed build. It also builds the kernel's first async runtime, so it is the highest-value **and** highest-new-surface slice.
2. **Calendar** *or* **Document** — both reviewed and well-bounded. Calendar continues the Thai/Lao locale thread and needs its tzdb ADR first; Document unblocks the attachment/content-grant flows Notification references. Either is a clean request-driven build (no new runtime surface).
3. **Asset** — after its research is revised past the Medium finding and reviewed.

The proven cadence is one foundation at a time: authorize → build → independent Codex ballot → operator disposition, per the governed loop drafted in `AGENTS.md` §25 (PROPOSED).

## 5. What this map does NOT do

Advisory planning only. It authorizes nothing, promotes nothing, and disposes nothing; it does not supersede `DOCUMENT-STATUS.md` (the authority record). Every build and promotion is the operator's decision.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
