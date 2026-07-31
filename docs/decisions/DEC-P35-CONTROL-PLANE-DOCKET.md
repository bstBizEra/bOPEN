# DEC-P35-CONTROL-PLANE-DOCKET — Security and Privacy review surface for the control-plane boundary

**Document ID:** `DEC-P35-CP-DOCKET-001`
**Version:** `1.0.0`
**Status:** **Proposed — awaiting Security and Privacy Authority disposition**
**Issued:** 2026-08-01
**Owner:** Architecture Authority
**Required concurrence:** **Security Authority, Privacy Authority**, Engineering Authority, Product Authority
**Resolves:** action `A-02` in [`ACTION-PLAN`](../ACTION-PLAN.md) — the gate on all of Phase 3.6
**Source record:** [`DEC-P35-CONTROL-PLANE`](DEC-P35-CONTROL-PLANE.md)
**Findings:** [`BOPEN-PRD-P35-002`](../02-requirements/BOPEN-PRD-P35-002.md) F-2, F-3, F-6

---

## 1. Purpose

`BOPEN-P36-001` cannot begin until `DEC-P35-CONTROL-PLANE` is reviewed, and that review turns on
two questions the PRD found and could not answer: what personal data the control plane may hold
(F-2), and where audit records carrying business identifiers live (F-3). A third (F-6) has since
been found that blocks the plane assignment itself.

This docket presents one bounded review surface. It decides nothing.

## 2. Live baseline, 2026-08-01

| Item | State | Consequence |
| :--- | :--- | :--- |
| `DEC-P35-CONTROL-PLANE` | Proposed, §4 corrected 2026-07-31 | No collection is authorized |
| `DEC-P35-TENANCY-MODEL` §8 | **Approved** — hybrid placement | Placement model settled; boundary content is not |
| `BOPEN-P36-001` | Proposed, entry blocked | Blocked by this docket |
| Retention mechanism | **None exists** in any of 9 migrations | De facto retention for every column is *forever* |
| Security-monitoring design | **None exists** — no SIEM, no detection catalogue | "Capability lost" is assessed against a capability never specified |

## 3. Docket

### 3.1 `D-CP-001` — Control-plane personal data (F-2)

**Question.** What is the complete, bounded set of personal data the control plane may hold?

**Finding.** `principals` is forced into the control plane by a global unique constraint on
`email`, so the control plane necessarily holds personal data. Four items were found that carry
personal data with **no platform function that fails without them**:

| Item | Finding |
| :--- | :--- |
| `principals.email` as a stored plaintext value | The unique constraint drives dedup. The **value** is never used as a lookup key anywhere — no `WHERE email`, no `find_by_email`. Authentication binds by issuer+subject; SSO binds by `(connection, issuer, subject)`; `context_service` actively refuses email claims; `D-P35-010` forbids indexing it as an identity key |
| `principals.email NOT NULL` for non-human types | The `type` vocabulary is `human, service, application, device, agent`. Four of five are not people and are compelled to carry an email address |
| `usage_outbox.principal_id` | Billing aggregates per tenant. No code path reads this column for a billing decision |
| `audit_events.payload`, `lifecycle_events.metadata` | Unbounded JSONB, `NOT NULL DEFAULT '{}'`, **no writer exists** for either. A column with no writer and no bound crosses a boundary by default, because nobody argued about it |

**Also found — a register built on column types will not catch everything.** Five caller-supplied
free-text fields are length-validated only: `correlation_id` (64), `idempotency_key` (128),
`subject_id` (128), `updated_by` (128), `actor_principal_id` (128). `PRD-P35B-PII-001`'s test
compares columns "of a personal-data type"; these are `VARCHAR` and will pass. **A register the
Privacy Authority reads as complete, when the test cannot see half the intake channels, is worse
than no register** — it converts an unknown risk into a believed-absent one.

**Options.**

| | Disposition | Benefit | Cost |
| :--- | :--- | :--- | :--- |
| A | Declare and bound; no schema change | Cheapest; ships with the split | Ratifies the four unjustified items as baseline; apertures stay open |
| **B** | **Declare, bound, and remove what has no function** *(recommended)* | Genuine minimisation — removal is the only technique that reduces what is held. Makes erasure representable | One migration; ~a week |
| C | B plus keyed pseudonymisation of email | A control-plane disclosure yields no addresses | Platform can never contact its own users — no breach notice, no recovery. **Pepper can never be rotated**, since rotation needs plaintext you no longer hold |
| D | B plus a tokenisation vault | Keeps reversibility; real chokepoint with its own audit | New component on the registration critical path; highest-value target in the deployment |

**Recommended: B.** C and D relocate or obscure; only removal removes. C's cost lands precisely
on the thing that cannot be foreseen — contacting a user about a security incident — and is
irreversible. If encryption at rest is wanted for that column, **column-level encryption with a
rotatable key is strictly better than a hash**: it keeps both reversibility and rotation.

**Bind the erasure decision to this one.** Migration 009 left `audit_events.principal_id ON
DELETE SET NULL` explicitly open, naming two readings with opposite fixes. It is the same question
from the other end: if the control plane holds personal data, what happens when the person asks
for it back. `principals.status` has no CHECK constraint and no erased value, so **there is
currently no way even to record that a principal was erased.**

### 3.2 `D-CP-002` — Audit placement (F-3)

**Question.** `audit_events` carries `action`, `resource_type` and `resource_id`. Where does it live?

**Finding — `resource_id` is not opaque today.** The column is `VARCHAR(255)`, no CHECK, no
pattern. The `/v1/authorize` boundary applies `max_length` and **no** UUID validation, so a
caller's string is written verbatim. The kernel's own `normalise_id` is applied for the database
read *after* the audit row is written — so `audit_events` can hold
`"acme-corp/2026-Q3-payroll.xlsx"` on a request whose data read the API would then reject.
`action` and `resource_type` are free text on the same path.

**Finding — this is partly an F-1 mitigation.** Two of F-1's twelve broken foreign keys are
`audit_events.principal_id` and `audit_events.tenant_id`. Placing audit (or a projection)
control-plane-side **repairs** them; placing it tenant-side **adds** them to the list.

**Finding — `correlation_id` is a weak join key.** It is supplied by the party being audited, has
no uniqueness constraint, and under `PRD-P35B-CRED-001` the platform cannot execute the join
anyway. "Correlate later via `correlation_id`" operationally means *ask the tenant to query their
own database during an incident, on the database that may be compromised.*

**Options.**

| | Disposition | Cost |
| :--- | :--- | :--- |
| 1 | Tenant-side only | Loses cross-tenant attack detection **permanently and unrecoverably**; audit sits inside its own blast radius; contradicts `DEC-P35-CONTROL-PLANE` §2–§3 as drafted |
| 2 | Whole record centrally | `resource_id` and `payload` cross; violates §4 rows 2–3; reduces `O-1` from a property to a promise |
| **3** | **Dual record — authority tenant-side, projection control-plane-side, no `resource_id`, no `payload`** *(recommended)* | Two records to keep consistent; the AUTHZ-001-conformant record lives where `CRED-001` forbids the platform to read it |
| 4 | 3 plus per-tenant-salted pseudonym of `resource_id` | Recovers cardinality without the value; **requires amending §4**, which forbids hashed field values |

**Recommended: 3.** It concedes exactly what placement was adopted to protect (`resource_id` names
the tenant's object) and preserves exactly what placement destroys — cross-tenant visibility,
which no tenant can see and only the centre can hold. It requires **no amendment to a record that
has not yet had its first review**, which options 2 and 4 both do.

**Two blocking prerequisites, whichever option is chosen:**

- **P-1** — constrain `resource_id` to UUID and `action`/`resource_type` to closed vocabularies
  **before** placement is implemented. Until then every option moves unbounded caller-supplied
  text. Existing rows cannot be edited under migration 009's principle, so historical rows may
  need excluding from any projection rather than cleaning.
- **P-2** — decide `payload` explicitly. It has no writer. An unmentioned column crosses by default.

**Also:** `lifecycle_events` has the identical shape (`subject_id`, `metadata` JSONB) and is also
listed control-plane. The disposition must cover it or explicitly decline to.

### 3.3 `D-CP-003` — Blocking input to plane assignment (F-6)

Migration 007's `principals_read` policy is a **subquery from `principals` into `memberships`**.
Split those across databases and PostgreSQL cannot evaluate it, silently reopening a measured
6,657-row disclosure.

F-1 enumerated foreign keys. **RLS policies with cross-plane dependencies have not been
enumerated at all.** And in the control plane every session is unscoped by construction, so
migration 007's `… IS NULL OR …` branch grants full registry read to every control-plane
connection — converting a stated residual risk into the normal operating mode.

**Required before `PRD-P35B-PLANE-001` can be signed off:** enumerate every RLS policy whose
`USING` or `WITH CHECK` clause references another table, and decide `memberships`' plane with that
in hand. **Recommended disposition: enumerate first, decide after.** No option is offered here
because the input does not exist yet.

### 3.4 `D-CP-004` — Retention

No retention mechanism exists in any of the nine migrations. **De facto retention is forever, for
every column above.** Any period chosen is an improvement.

The schema already states the shape of the answer: `rate_limit_counters` prints its own expiry
(`window_end`) and carries no principal — retention is a **ceiling**, and a cron job suffices.
`audit_events` is append-only by construction with `ON DELETE RESTRICT` on its tenant, because
migration 003 states *"deleting a tenant must not silently erase its audit trail"* — retention is
a **floor**, and deletion must be a governed act.

Advisory periods are tabulated in the F-2 research and are not reproduced here. Two need inputs
this docket cannot supply: whether metering rows are financial records (Finance), and the
erasure question bound to `D-CP-001`.

## 4. Recommended disposition order

1. `D-CP-003` — enumerate cross-plane RLS dependencies. Cheap, and it may change plane assignment.
2. `D-CP-001` — the personal-data register, with erasure bound to it.
3. `D-CP-002` — audit placement, with P-1 and P-2 as prerequisites.
4. `D-CP-004` — retention.

## 5. Ratification record

```text
Docket ID:
Outcome: ACCEPT | REJECT | RETURN_WITH_CONDITIONS
Conditions:
Approver role:
Approver identity:
Decision timestamp:
Evidence or rationale:
```

Silence is not a decision. A row left undecided leaves its dependent work blocked, which is the
intended behaviour.

## 6. Provenance and limits

Findings were produced by two research agents reading the migrations, the decision records and the
kernel source, then reported with their own uncertainty stated. **Neither ran a live probe.**
`BOPEN-PRD-P35-002` §12 records that reading migrations undercounted F-1 by more than half — five
against twelve measured — so the same caution applies here, particularly to F-3's column
classifications and to the claim that `usage_outbox.principal_id` has no reader.

One claim in the F-3 research is flagged unverified by its author and is **not** relied on above:
that the migration-running role holds superuser or `BYPASSRLS`, which would make a tenant-side
audit trail reachable by an attacker inside the tenant database. It warrants a probe before it is
used as an argument.

Prepared by Claude (agent, Motor role) as an advisory review surface.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
