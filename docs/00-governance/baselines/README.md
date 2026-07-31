# Architecture Baselines

**Document ID:** `BOPEN-GOV-BASELINE-001`
**Version:** `1.0.0`
**Status:** Operational
**Issued:** 2026-07-31
**Owner:** Architecture Authority
**Governed by:** [`AGENTS.md`](../../../AGENTS.md) §23

---

## 1. What this is

A baseline is an immutable capture of the architecture **before** a major change to it, so that
the prior design can be read, compared and restored after the change lands.

The mechanism is an annotated git tag, not a copied directory. A tag is content-addressed: it
names an exact tree by hash, cannot drift, costs no disk, and can be verified against the object
database years later. A `backup/` folder is a second copy that silently diverges, and after two
of them nobody knows which was real.

```bash
git tag -l 'arch-baseline/*'                       # list baselines
git show arch-baseline/<name>                      # read what it captured and why
git diff arch-baseline/<name>..HEAD -- docs/decisions/   # what changed since
git checkout arch-baseline/<name>                  # restore, read-only
```

## 2. When a baseline is required

Before a change that alters any of the following, per `AGENTS.md` §23:

- the tenant isolation mechanism;
- an approved normative artifact (`BOPEN-*-001`) or an ADR of record;
- the technology selection in `BOPEN-ARCH-TECH-001`;
- a blueprint layer's technology or its presence;
- a data-flow boundary — what may leave a tenant, a process or the platform.

A change confined to one work package's implementation does not need one. The test is whether a
future reader would need the *previous* design to understand a decision, not whether the diff is
large.

## 3. Register

| Baseline | Commit | Captured | Superseded by |
| :--- | :--- | :--- | :--- |
| [`arch-baseline/2026-07-31-rls-option-c`](#31-2026-07-31--rls-with-option-c-sharding) | `9e26c0b` | 2026-07-31 | `DEC-P35-TENANCY-MODEL` §8 — Option D hybrid |

### 3.1 `2026-07-31` — RLS with Option C sharding

**Commit:** `9e26c0b55eb1505eafbf252eec8f9ff2745749d8`
**Tree:** `014fb1418c38be4d2e7344e19fd54141dbac2dce`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`

**Architecture at this point:**

| Concern | State |
| :--- | :--- |
| Tenant isolation | Single shared schema, PostgreSQL row-level security, **16 tables** under policy, `FORCE ROW LEVEL SECURITY` |
| Scaling model | `DEC-P35-TENANCY-MODEL` §7 — Option C, shard tenants across instances, RLS retained per shard |
| Evidence | **38 isolation tests** executed against live PostgreSQL; canonical suite 433/433 |
| Layer 1 — gateway | Built — `apps/gateway`, Hono + Zod, 31 tests |
| Layer 2 — identity | Authentication boundary built (`subject_assertion.py`); federation blocked |
| Layer 3 — kernel | Built — FastAPI 0.121 + Pydantic 2.12, 11 routes |
| Layer 4 — persistence | Executed — 9 migrations, psycopg3 |
| Layer 5 — events | Deferred, 0 Go files |
| Verification | `IMPLEMENTED_UNVERIFIED` across all work packages, **zero ballots** |

**Why it was superseded:** the operator stated a tenant-privacy requirement — one database per
tenant, no cross-tenant data accessible. §7 had recorded its driver as *load, not isolation*, and
recorded in terms that an isolation driver would change the answer. It did.

**What the successor keeps:** row-level security survives as the mechanism for the shared
trial-tier pool, so the 16 policy-bearing tables and all 38 isolation tests retain their meaning.
That is the principal reason Option D was chosen over Option B — no evidence is discarded to gain
the isolation.

## 4. What a baseline is not

It is not a substitute for the decision record that explains the change, nor for the extend-only
rule. Superseded text stays in place and marked; the baseline exists so the *whole tree* around
that text can still be read, not so the text can be deleted.

It is also not a backup of data. Tenant data recovery is a separate concern and is not addressed
here.
