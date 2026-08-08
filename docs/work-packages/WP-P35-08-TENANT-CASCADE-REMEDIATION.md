# WP-P35-08 — Append-only evidence survives tenant deletion

**Work package ID:** `WP-P35-08`
**Version:** `1.0.0`
**Status:** **DRAFT — entry gate NOT recorded. No build is authorized by this document.**
**Issued:** 2026-08-08
**Owner:** Engineering & Security Authorities
**Governing:** [`DEC-P4-NOTIFY-TENANT-CASCADE`](../decisions/DEC-P4-NOTIFY-TENANT-CASCADE.md) §6, §7; `AGENTS.md` §8, §14, §23, §25.1; `BOPEN-GOV-EBIV-001`

---

## 1. Why this exists

Eleven tables across four foundations declare `tenant_id REFERENCES tenants(id) ON DELETE CASCADE`
while relying on an `ON DELETE RESTRICT` parent edge to make their evidence append-only. PostgreSQL
performs foreign-key actions with row security bypassed, so the tenant edge reaches the row first
and the RESTRICT edge is never consulted.

Reproduced live on the notification tables (Codex, ballot `bd42b2e`): the tenant delete **succeeded**
and `notification_attempt` and `notification_receipt` went to zero rows.

The operator selected Option 2 (`DEC-P4-NOTIFY-TENANT-CASCADE` §7): make the tenant edge `RESTRICT`,
applying the pattern `audit_events` and `lifecycle_events` already use.

## 2. Scope

**In scope** — one migration, `022_evidence_survives_tenant_deletion.sql`, plus its `.down.sql`,
altering the `tenant_id` foreign key from `CASCADE` to `RESTRICT` on:

| Foundation | Tables |
| :--- | :--- |
| Workflow (013/014) | `workflow_history` |
| Party ContactPoint (019) | `party_contact_points`, `party_contact_point_verification_events` |
| Location (020) | `location_address_versions`, `location_geometry_observations`, `location_external_identifiers`, `location_relationships`, `location_history` |
| Notification (021) | `notification_dispatch`, `notification_attempt`, `notification_receipt` |

Plus negative tests in `tests/isolation/`, and traceability rows.

**Out of scope** — each needs its own decision:

- Option 3 (separating evidence retention from tenant lifetime). Not foreclosed; see §7.1 of the DEC.
- Any tenant-offboarding or archival capability. This package makes deletion **refuse**; it does not
  provide the path that would make deletion possible again.
- The mutable parent rows (`workflow_instances`, `parties`, `locations`, `notifications`) — only the
  append-only evidence tables are in scope.
- Correcting `NOTIFY-S1-ISO-WRITE-01`, the row a verifier marked `INADMISSIBLE`.

## 3. Keystone invariant

> A tenant that holds append-only evidence cannot be deleted. Deletion is **refused loudly**, never
> silently satisfied by destroying the evidence.

## 4. Refusal Matrix

Written before implementation; each must be shown to fail when its mechanism is removed.

| # | Input | Required behaviour |
| :--- | :--- | :--- |
| R-1 | Delete a tenant holding rows in **any** of the 11 tables | **Refused**, one case per table — 11 probes, not one |
| R-2 | Delete a tenant holding **no** evidence rows | **Permitted.** The fix must not make tenant deletion impossible in general |
| R-3 | Direct delete of the parent (dispatch, instance, location, contact point) with evidence present | Still refused — the existing RESTRICT edges are unchanged |
| R-4 | Direct `UPDATE`/`DELETE` on an evidence row from a tenant session | Still reaches zero rows — the append-only policies are unchanged |
| R-5 | Ordinary tenant-scoped reads and writes across all four foundations | Unchanged. The migration alters a delete action, nothing else |
| R-6 | `022...down.sql` applied | Restores `CASCADE` exactly, leaving no residue |
| R-7 | A **new** append-only table added later with `tenant_id ON DELETE CASCADE` | **Reported by a structural check.** Without this the same defect returns with the next foundation |

R-7 is the row that decides whether this package fixes an instance or a class. The defect has
already recurred four times, including inside `014`, the migration written to teach the lesson.

## 5. Roles

| Role | Assigned |
| :--- | :--- |
| Maker | Claude — excluded from voting for this package's lifetime (EBIV §3) |
| Independent verifier | **Codex** — `git blame` across all five migrations and both extended files shows Claude only; Codex authored nothing on this surface and is eligible under both readings of §3 |
| Completion Authority | Operator — not an agent role |

## 6. Sequence

1. **Baseline** (§23) — tag before the change lands. This alters an isolation mechanism across four
   disposed foundations; if any step of it is wrong, the tag is the way back.
2. Write the §4 negative tests; observe them fail.
3. Implement the smallest migration that turns them green.
4. Mutate each mechanism; confirm the matching test goes red.
5. Register traceability **before** dispatch — an unregistered proposition yields `R2:false` and
   wastes the run.
6. Serialized canonical suite at the candidate, in a clean tree.
7. Maker submission anchored to an exact commit and tree.
8. Codex ballot, defensively framed, gated on blob identity rather than checkout equality.
9. Operator disposition.

## 7. Risks specific to this package

1. **It touches four disposed foundations at once.** A defect here reaches further than any single
   foundation's work did. That is the argument for one migration and one careful verification rather
   than four hurried ones — and the argument for the §23 baseline being taken seriously.
2. **The shared database already holds data.** `ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT`
   revalidates existing rows; the migration must be checked against a populated database, not only
   an empty one.
3. **Tenant deletion becomes conditional**, and no archival path exists. Any existing test or tool
   that deletes a tenant as cleanup will begin to fail. That is the intended behaviour, but it must
   be found deliberately rather than discovered as a broken suite.
4. **R-2 is the safety valve.** A migration that made *all* tenant deletion impossible would satisfy
   R-1 completely and be wrong.

## 8. Acceptance criteria

- Every §4 row has a named executed test, and each fails when its mechanism is removed.
- All 11 tables probed individually for R-1 — a single representative table is not sufficient.
- R-2 demonstrated: a tenant with no evidence is still deletable.
- Full canonical suite green at the candidate, run serialized in a clean working tree.
- The down migration restores the prior state and is exercised, not merely written.
- No change to any RLS policy, grant, or table definition beyond the named foreign-key actions.

## 9. Authority

Draft work package. Confers no implementation, approval, merge, release or production authority.
**An entry gate must be recorded before any code is written** (`AGENTS.md` §25.1 step 0).

---

## 10. Amendment 2026-08-08 — entry gate GO

> **Change note (extend-only).** Recorded **before** any code is written, per `AGENTS.md` §25.1
> step 0 and §3.1.

| Field | Value |
| :--- | :--- |
| **Decision** | **Entry gate GO.** `WP-P35-08` is bound as the accepted work package for the tenant-cascade remediation |
| **Scope** | Exactly §2. Option 3, archival paths, tenant-offboarding capability and the mutable parent rows remain out of scope |
| **Baseline** | `arch-baseline/2026-08-08-pre-tenant-cascade-restrict`, tagged **before** the change (§23) |
| **Roles** | Maker: Claude (excluded from voting, EBIV §3). Independent verifier: Codex — eligibility checked before assignment (§7.3 of the DEC). Completion Authority: operator |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Engineering & Security Authorities |
| **Decision timestamp** | 2026-08-08 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

Acceptance authorizes the build described in §2 and nothing beyond it. It does not dispose any
foundation, does not reopen the three existing dispositions (§7.2 of the DEC), and does not
authorize a tenant-offboarding or archival capability.

The status line above remains **DRAFT** in its original text for provenance; this amendment
supersedes it. The operative status is **ACCEPTED — entry gate GO 2026-08-08**.
