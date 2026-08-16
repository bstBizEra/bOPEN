# Objective — bOPEN as a multi-tenant management kernel that runs itself

**Status:** **ADVISORY OBJECTIVE.** Not a roadmap amendment, not a phase authorization, not a gate.
`docs/01-product/roadmap.md` and `AGENTS.md` §20.2 remain the normative statements of phase and gate.
**Set by:** operator directive, 2026-08-17 — *"develop current scope of bOPEN as the multi-tenant
management Kernel until all modules are working autonomously and smoothly."*
**Drafted by:** Claude (agent, Motor role). Every number below is derived from the repository or the
running system; the derivation is named so each can be re-checked.

---

## 1. The goal, stated so it can be failed

> Every module in the current kernel scope runs **unattended**: it is entered under a recorded
> decision, verified by an agent that did not build it, accepted by the Completion Authority,
> deployed by a pipeline, observed while running, and recoverable without a person reading source.

"Smoothly" is not a feeling. Per module it means all six:

| | Criterion | How it is checked |
| ---: | :--- | :--- |
| 1 | Schema forces tenant isolation | `ENABLE` + `FORCE ROW LEVEL SECURITY`, verified against the live catalogue |
| 2 | Evidence survives tenant deletion | `ON DELETE RESTRICT` on **every** FK path, probed by attempting the delete |
| 3 | Contract exists **and an instance is validated against it** | `tools/check_contract_conformance.py` — a baseline entry is a debt record, not coverage |
| 4 | Invariants balloted by a non-maker | `BOPEN-GOV-EBIV-001` §6.1 or §6.5, zero live refutations |
| 5 | Runs without a human path fix | installable artifact; no hand-assembled `PYTHONPATH` |
| 6 | Failure is visible and reversible | health signal, alert, and a rehearsed rollback |

**Today no module satisfies all six.** Criteria 1, 2 and 4 are met broadly; 3 is partial; 5 and 6 are
met nowhere.

## 2. Where the kernel actually is

Measured, not asserted:

```text
migrations applied        22 of 22          tables 40, ENABLE+FORCE RLS on 40 of 40
canonical suite           685 tests, 685 pass, 0 fail, exit 0
dispositions recorded     17 work packages
  CONFIRMED_UNDER_TWO_AGENT_PROFILE   16
  BLOCKED_ACCEPTED_WITH_KNOWN_DEFECTS  1   (WP-P35-04 gateway, 2 refutations)
deployable units          apps/gateway · services/platform-kernel · packages/kernel-core · 3 SDKs
contract schemas          17 frozen
```

**Criterion 1 and 2 are the strongest thing this repository has.** Every tenant-scoped table forces
RLS, and evidence tables refuse tenant deletion on *both* the `tenant_id` path and the parent-entity
path — verified by attempting real deletions inside rolled-back savepoints.

## 3. Gate zero — the objective cannot start where the specification says work is prohibited

`AGENTS.md` §20.2 calls itself *"the single operative statement of gate state"* and lists:

```text
| Phase 4 — Foundations and satellite products | NOT AUTHORIZED | blocked pending Phase 3.5 |
```

`DEC-P4-ENTRY` records **MILE-4.1 and MILE-4.2 AUTHORIZED on 2026-08-03**, and the manifest records
both as disposed, along with UOM, Workflow, ContactPoint and Location.

`AGENTS.md` §1 places `AGENTS.md` above a `DEC`. **A strict reader must conclude that most of the
modules this objective is about were built under a closed gate.** Amending §20.2 is a specification
amendment — outside agent authority (§20.3 item 6, EBIV §2) and `CONSTITUTIONAL_REQUIRED` under §31.1.

**This is the first thing to fix, and only the operator can fix it.** Nothing below is safe to call
progress while it stands.

## 4. The remaining kernel work, and a correction to how large it is

Phase 3.6 — hybrid placement and the control plane — is the last structural kernel phase.
`roadmap.md` states its hard part:

> *"twelve foreign keys currently reference `tenants` or `principals` and cannot survive a split
> across databases, because PostgreSQL cannot enforce a foreign key across them."*

**Twelve is stale.** Counting `REFERENCES tenants(` and `REFERENCES principals(` across the 23
forward migrations gives **46** occurrences; the live catalogue carries **30 foreign keys to
`tenants`** alone (13 `RESTRICT`, 17 `CASCADE`) plus those to `principals`. The roadmap sentence was
written 2026-07-31, before migrations 018–022 added UOM, ContactPoint, Location, Notification and the
cascade remediation.

The raw count double-counts migration 022's drop-and-re-add, so the true figure sits between the live
30-plus and the textual 46 — **and either way the problem is roughly three times the size the roadmap
states.** Sizing the last kernel phase from a number that predates five migrations is how a phase
gets entered on a wrong estimate.

Phase 3.6 is additionally **blocked at entry** on Security and Privacy review of
`DEC-P35-CONTROL-PLANE`, which holds two unanswered questions: that the control plane must hold
personal data to function, and where audit records carrying business identifiers should live.

## 5. The one live defect in a shipped module

`P35-04R-15` — the gateway does not confine to `/v1`:

```text
/v1/../docs          -> kernel saw /docs
/v1/../openapi.json  -> kernel saw /openapi.json
```

The interactive API documentation and the full OpenAPI schema are reachable through the gateway. This
is why `WP-P35-04` is the one package disposed `BLOCKED_ACCEPTED_WITH_KNOWN_DEFECTS`.

**No agent can close it.** `DEC-P35-GATEWAY-PREFIX-CONFINEMENT` is `Proposed`, and choosing between
confining the proxy and declaring it a deliberate catch-all *is* the decision.

## 6. Ordered path

**Reserved to the operator — nothing below moves without these:**

1. **§20.2** — reconcile the gate statement with `DEC-P4-ENTRY`. Gate zero.
2. **`DEC-P35-GATEWAY-PREFIX-CONFINEMENT`** — closes the only live defect in a shipped module.
3. **Two dispositions** — Notification Stage 1 and `WP-P35-08`, both drafted, both on the EBIV §6.5 route.
4. **`DEC-P35-CONTROL-PLANE`** — unblocks Phase 3.6 entry.

**Agent work, in dependency order, once the above allow it:**

5. **Criterion 5 — make the kernel installable.** No `pyproject.toml` or `setup.py` exists anywhere;
   four `sys.path` entries are hand-assembled in `tools/run_tests.py`. Repository-root paths sit
   outside the delegation envelope, so this needs an envelope widening or an operator merge.
6. **Criterion 3 — close contract coverage.** Instance validation, not baseline entries. The
   thirteen-of-sixteen state the baseline documents is the gap.
7. **Phase 3.6 identity work** — replace cross-database foreign keys with something enforced, sized
   against the corrected count in §4, not against twelve.
8. **Criterion 6 — deployment, observability, rollback.** `.github/workflows/` holds governance jobs
   and no deployment pipeline; `09-operations/backup-recovery.md`, `deployment.md`, `observability.md`
   and `service-level-objectives.md` are three-line shells.

## 7. What would make this objective complete

Not "all modules work." That is unfalsifiable. Instead:

> **Every module in `docs/evidence/*/manifest.json` satisfies all six criteria in §1, with the check
> for each recorded and re-runnable, and zero live refutations across the corpus.**

At that point the kernel is a multi-tenant management kernel that runs itself. Until then it is a
verified codebase that a person still has to run.

Recorded advisory-only. Confers no phase authorization, entry gate, disposition, merge, release or
production authority.
