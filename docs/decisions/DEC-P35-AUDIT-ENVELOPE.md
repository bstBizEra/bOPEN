# DEC-P35-AUDIT-ENVELOPE — Which audit envelope is the contract

**Decision ID:** `DEC-P35-AUDIT-ENVELOPE`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16 (two approved artifacts conflict)**
**Issued:** 2026-07-30
**Owner:** Architecture Authority & Engineering Authority
**Governing artifacts:** `BOPEN-P1-001-EXECUTION-PLAN` §10.2; `docs/06-contracts/events/event-envelope.md`; `contracts/schemas/audit-event.json`; `contracts/schemas/lifecycle-event.json`
**Raised by:** Claude (agent, Cortex/Motor roles) — advisory only

---

## 1. The conflict

Two audit envelopes exist in this repository. Both are produced by live code. Only one was ever
given a schema, and it is not the one the governing work package specifies.

| | `AuditDispatcher.dispatch` | `AuditDispatcher.emit_lifecycle_event` |
| :--- | :--- | :--- |
| Schema | `contracts/schemas/audit-event.json` | **none, until `lifecycle-event.json` was authored 2026-07-30** |
| Outcome field | `status` ∈ {SUCCESS, DENIED, ERROR} | `outcome` ∈ {success, deny, failure} |
| Time field | `timestamp` | `occurred_at` |
| Actor field | `actor_id` | `actor_principal_id` |
| Emitted by | the Phase 1 authorization path | **every Phase 2 module** — invitation, membership, SCIM, context switching, delegation |

`BOPEN-P1-001-EXECUTION-PLAN` §10.2 specifies the audit envelope field by field:

```
event_id, event_type, event_version, occurred_at, correlation_id, causation_id,
actor_principal_id, tenant_id, subject_type / subject_id,
outcome  ( success, deny, or failure ),
reason_code, policy_version, metadata, integrity_version
```

That is the lifecycle envelope, named exactly. `status`, `timestamp` and `actor_id` appear in
neither §10.2 nor `event-envelope.md`.

**So the finding inverts the obvious reading.** The producer that had no contract is the one
conforming to the specification. `audit-event.json` — the frozen schema — is the artifact that
deviates from the work package it was supposed to implement.

## 2. How this was established

Not by reading. A probe drove all eight call sites of `emit_lifecycle_event` through their real
public APIs and captured 26 events across five modules. Every event carried the same thirteen
keys; there is one dict literal and no conditional branch. `event_type` and `outcome` are
producer-enforced against closed vocabularies, raising `AuditContractError` otherwise.

`contracts/schemas/lifecycle-event.json` was then authored to describe what the code actually
emits — enumerating where the producer is strict, documenting where it is loose. `subject_type`
is the case that decided the approach: eight observed values and no producer validation, so
enumerating them would have produced a schema stricter than its own producer, which is the exact
defect this work exists to remove.

## 3. Three consequences that are not the main conflict

**`reason_code` is specified and the schema omits it.** `AuditDispatcher.dispatch` emits it;
`audit-event.json` forbids it through `additionalProperties: false`. It is a surplus of exactly
one field — asserted by set difference, not claimed. §10.2 lists it, and
`docs/06-contracts/policies/authorization-decision.schema.json` puts it in `required`. A
`DENIED` audit record with no reason code cannot answer the question an audit exists to answer.
The omission is in the schema.

**`policy_version` and `integrity_version` are specified and nothing emits them.** §10.2 requires
`policy_version` for authorization events. It appears in no Python file in the repository, and
`contracts/schemas/authorization-decision.json` also requires it. The evaluator has no versioned
policy to report. This is a gap in the implementation, not in either schema.

**`causation_id` is dead surface.** Always `null`. No caller in either package passes it. §10.2
specifies it as "links event to command or prior event". Whether it is unimplemented or abandoned
is not recorded in any ADR. It is typed nullable-and-required in the new schema because the
producer always writes the key, and a test will fail the day someone populates it.

## 4. Options

**Option A — amend `audit-event.json` to match §10.2.**
Rename `status` → `outcome`, `timestamp` → `occurred_at`, `actor_id` → `actor_principal_id`; add
`reason_code`. The two envelopes converge on the specification. Requires changing
`AuditDispatcher.dispatch` and every consumer of its output. It is the only option that leaves
one envelope.

**Option B — keep both, contract both.** *(the current state after 2026-07-30)*
`audit-event.json` describes the authorization envelope; `lifecycle-event.json` describes the
Phase 2 envelope. Cheapest, and honest about what exists. Cost: two vocabularies for one idea
persist, and every consumer must know which envelope it is reading.

**Option C — amend §10.2 to match `audit-event.json`.**
Rejected on the evidence: §10.2 is echoed by `event-envelope.md` and the policies schema, and the
lifecycle envelope already implements it across five modules. Changing the specification to match
the one artifact that disagrees with it inverts the source-of-truth hierarchy in `AGENTS.md` §4.

## 5. Recommendation

**Option A, sequenced after Phase 2 persistence.**

The envelopes should converge, because `{SUCCESS, DENIED, ERROR}` and `{success, deny, failure}`
are not a rename — `ERROR` has no mechanical counterpart, and `failure` is emitted by nobody
today. Any unification is a semantics decision that must be made deliberately rather than by
search-and-replace.

Sequencing matters. Phase 2 currently holds all of its state in memory and writes no audit rows
to the database at all, so converging the envelopes now would rewrite a producer whose output is
not yet durable. Convergence is cheaper and safer once Phase 2 events are persisted, because at
that point there is one writer and one table to migrate rather than a moving target.

Until then Option B stands as the recorded interim, with the divergence pinned by an executable
test in both directions so a third vocabulary cannot appear silently.

## 6. What is not being claimed

No code was changed to produce this record. Neither schema was edited. The new
`lifecycle-event.json` describes an existing producer and does not alter it.

This is a decision request. It does not resolve the conflict, and no agent has the authority to.

## 7. Provenance

Established 2026-07-30 by executing the producers rather than reading them. Advisory only —
`execution_authority: false`, `approval_authority: false`.
