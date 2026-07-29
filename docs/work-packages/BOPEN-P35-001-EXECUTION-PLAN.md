# BOPEN-P35-001 — Phase 3.5 Runtime Realization

**Status:** Proposed — pending `DEC-P35-RUNTIME`
**Version:** `1.0.0`
**Issued:** 2026-07-30
**Owner:** Engineering Authority
**Dependencies:** [`DEC-P35-RUNTIME`](../decisions/DEC-P35-RUNTIME.md)
**Governing artifacts:** `BOPEN-ARCH-PLAN-001`, `BOPEN-TENANT-001`, `BOPEN-AUTHZ-001`, `BOPEN-ARCH-001`, `AGENTS.md` §8, §11, §14

---

## Objective

Convert the bOPEN platform kernel from an in-process specification model into a running
multi-tenant service that satellite products can call across a network boundary, with each
architectural layer proven by evidence executed against its real dependency.

The measure of completion is not that more code exists. It is that the isolation guarantee
of `BOPEN-TENANT-001` is enforced by PostgreSQL and demonstrated by a test that would fail
if the policy were removed.

---

## In scope

`WP-P35-01` — **Persistence and tenant-scoped session layer**

- psycopg3 connection management with per-transaction `SET LOCAL app.current_tenant_id`.
- Repository implementations replacing in-memory dictionaries for the Phase 1 entities
  authorized by `AGENTS.md` §3: principal, tenant, membership, context, authorization
  decision, audit event.
- Migration runner with forward and rollback execution.
- Migration `003` adding the context and audit persistence that Phase 1 requires and that
  `001` does not provide.
- RLS conformance suite executed against a live PostgreSQL instance.

`WP-P35-02` — **Kernel HTTP surface**

- FastAPI application exposing the Phase 1 vertical slice and the Phase 3 entitlement
  decision surface.
- Pydantic v2 models generated from or validated against `contracts/schemas/`.
- Request-scoped context binding via `contextvars`.

`WP-P35-03` — **Signed context token**

- Token issuance and verification carrying `sub`, `tid`, `mid`, `roles`, `scopes`.
- Server-side context validation on every request; client-supplied tenant identifiers are
  never trusted (`AGENTS.md` §8).

`WP-P35-04` — **API gateway**

- Hono service validating `X-Tenant-ID`, `X-Context-ID`, `X-Correlation-ID` against
  [`HTTP_HEADER_SPEC.md`](../../sdk/headers/HTTP_HEADER_SPEC.md).
- Zod validation bound to `contracts/schemas/`.

`WP-P35-05` — **Enterprise IdP bridge integration**

- Replace the simulated SSO surface in `idp_bridge.py` with a BoxyHQ Jackson integration
  behind the existing interface.

---

## Out of scope

- Go event microservices (blueprint layer 5). Deferred under `DEC-P35-RUNTIME` §5 pending
  observed throughput. Not cancelled.
- Any Phase 4 business foundation or satellite product surface.
- Amendment of approved normative specifications. This work package implements
  `BOPEN-MOD-001`, `BOPEN-ENT-001`, `BOPEN-TENANT-001` and `BOPEN-AUTHZ-001`; it does not
  change them.
- Rewriting the Phase 1–3 entitlement, capability or membership domain logic. Where that
  logic is correct it is rehosted onto real persistence unchanged. Where the Codex review
  of 2026-07-30 found it defective, the defect is recorded against `WP-P35-01` acceptance
  rather than patched in place, because most of those defects are consequences of the
  in-memory substrate and disappear when it is removed.

---

## Deliverables

| ID | Artifact | Layer |
| :--- | :--- | :--- |
| D-01 | `infrastructure/database/003_phase1_context_audit.sql` + rollback | 4 |
| D-02 | `services/platform-kernel/python/platform_kernel/db.py` — tenant-scoped session | 4 |
| D-03 | `tools/db_bootstrap.py` — idempotent database creation and migration application | 4 |
| D-04 | `tests/isolation/test_rls_database_behavior.py` — executed RLS conformance | 4 |
| D-05 | `requirements.txt` — dependency record per `AGENTS.md` §13 | — |
| D-06 | Repository layer for Phase 1 entities | 4 |
| D-07 | FastAPI kernel application | 3 |
| D-08 | Context token issuer and verifier | 3 |
| D-09 | Hono gateway | 1 |
| D-10 | Jackson IdP integration | 2 |

D-01 through D-05 constitute the first increment and are delivered together.

---

## Acceptance criteria

Each criterion is stated so that it can be failed.

**A-01 — Isolation is enforced by the database.**
With `app.current_tenant_id` set to tenant A, a `SELECT` over a table holding rows for
tenants A and B returns only A's rows, executed against PostgreSQL. Removing the policy
causes the test to fail. Application-level filtering is absent from the test path.

**A-02 — Deny-by-default holds at the database.**
With `app.current_tenant_id` unset or empty, every tenant-scoped table returns zero rows.

**A-03 — Cross-tenant write is refused by the database.**
An `INSERT` or `UPDATE` carrying a `tenant_id` other than the session tenant raises a
policy violation, not a silently accepted row.

**A-04 — `FORCE ROW LEVEL SECURITY` is effective against the owning role.**
The probe runs as the table owner and is still constrained.

**A-05 — Evidence is executed, not simulated.**
No test admitted as evidence for A-01..A-04 may substitute a Python data structure for the
PostgreSQL policy. Absence of a configured database causes the suite to **fail**, never to
pass and never to skip silently.

**A-06 — Migration is reversible.**
`003` applies and rolls back cleanly on a database already carrying `001` and `002`.

**A-07 — Evidence anchoring is machine-emitted.**
Commit and tree OIDs in any evidence manifest produced by this work package are read from
git by a tool. No OID is transcribed by an agent. A manifest whose OIDs do not resolve is
rejected.

---

## Required checks and evidence

| Check | Command |
| :--- | :--- |
| Canonical suite | `python tools/run_tests.py` |
| Repository validation | `python tools/validate_repository.py` |
| Clean-room | `python tools/check_clean_room.py` |
| Authority bootstrap | `python tools/check_authority_bootstrap.py` |
| Database bootstrap | `python tools/db_bootstrap.py --apply` |
| RLS conformance | included in canonical suite, isolation category |

Evidence path: `docs/evidence/phase-3.5/`.
Invariant traceability CSV is mandatory and must name a test ID for every invariant in
`AGENTS.md` §7 that this work package touches.

---

## Risks and rollback

| Risk | Mitigation |
| :--- | :--- |
| Live database becomes a hard test dependency, breaking contributor onboarding | `tools/db_bootstrap.py` provisions a local instance in one command; failure message states the exact remediation |
| A-05 makes the suite fail where it previously passed | Intended. The prior pass state was not evidence of isolation. The transition is recorded rather than smoothed |
| Rehosting Phase 3 logic surfaces further defects | Expected and desirable. Defects surfaced by real execution are the purpose of this work package |
| Migration `003` conflicts with a concurrently authored migration | Migration numbering is claimed in this work package before authoring |

Rollback: `003` has an explicit `down` script. D-02 through D-04 are additive files; the
in-memory path remains until repositories replace it under D-06, so the increment is
reversible by deletion.

---

## Completion record

*Not started. To be completed only against executed evidence meeting A-01..A-07.*

| Role | Assignee |
| :--- | :--- |
| Maker | *unassigned* |
| Independent checker | *unassigned — must not be the maker* |
| Security reviewer | *unassigned* |
| Completion authority | *unassigned* |

Under `DEC-P35-RUNTIME` §5.1 the independent checker may not be the agent that authored the
implementation or its tests.
