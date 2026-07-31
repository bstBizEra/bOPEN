# DEC-P35-CONTROL-PLANE — What the platform may know about a tenant it cannot read

**Decision ID:** `DEC-P35-CONTROL-PLANE`
**Version:** `1.0.0`
**Status:** **Proposed — requires Security and Privacy Authority review before implementation**
**Issued:** 2026-07-31
**Owner:** Architecture Authority
**Required concurrence:** Security Authority, Privacy Authority, Engineering Authority, Product Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing artifacts:** [`DEC-P35-TENANCY-MODEL`](DEC-P35-TENANCY-MODEL.md) §8, `BOPEN-TENANT-001`, `AGENTS.md` §7 invariant 11, §8, §13

---

## 1. The tension this resolves

`DEC-P35-TENANCY-MODEL` §8 makes tenant data private by placing each tenant in its own database.
The operator's requirement is that this must **not** blind the platform: it still needs system
performance management, capacity planning, and business analysis.

Those two requirements are compatible, but only if the boundary is drawn explicitly. Drawn
loosely — "the platform may read what it needs" — privacy becomes a promise rather than a
property, and the promise erodes one useful query at a time.

## 2. The split

```text
CONTROL PLANE — one platform-owned database
  tenant registry, placement map, entitlement plans, quotas
  metered usage aggregates, audit events, lifecycle events, rate-limit counters
  operational telemetry: latency, error rates, storage bytes, connection counts
        ▲
        │  ONLY aggregates, counters and metadata cross this line
        │  Tenant business rows NEVER cross it
        │
DATA PLANE — one database per tenant (or a shared RLS pool for trial tenants)
  invoices, orders, assets, documents, parties — the tenant's actual business
```

**The platform can answer** *"tenant X made 1.2M calls this month, holds 40GB, runs at p99 240ms,
is at 82% of quota, and had 14 authorization denials"* — everything needed for capacity planning,
performance work, billing and abuse detection — **without reading one invoice.**

## 3. What may be collected

This list is exhaustive by intent. Anything not named here is outside the boundary and requires
an amendment, not an interpretation.

| Category | Examples | Why it is not tenant data |
| :--- | :--- | :--- |
| **Usage aggregates** | API call counts, storage bytes, quota consumption, metered events | Counts of actions, not their content. Already modelled in `usage_meter_balances` and `usage_outbox` |
| **Operational telemetry** | Query latency, error rates, connection counts, cache hit rates, migration state | Properties of the platform's own execution |
| **Authorization outcomes** | Allow/deny counts, reason codes, denial rates | `BOPEN-AUTHZ-001` already requires these to be audited |
| **Lifecycle events** | Tenant provisioned, suspended, membership changed, plan upgraded | Platform-owned relationship state, not tenant business content |
| **Entitlement state** | Plan tier, feature flags, overage status | Commercial relationship between platform and tenant |
| **Schema-level counts** | Row counts per table, growth rate, index bloat | Cardinality without content — see §4.1 |

## 4. What may **not** be collected

| Prohibited | Reason |
| :--- | :--- |
| Any row from a tenant's business tables | The property this decision exists to protect |
| Field values, even hashed or truncated | A hash of a business value is still that value's identity, and joins across tenants become possible |
| Free-text content — names, notes, addresses, documents | Personal data under most regimes, and unbounded in what it may reveal |
| Query text containing literals | A slow-query log carrying `WHERE customer = 'Acme'` moves business data into telemetry |
| Cross-tenant joins of any kind | Structurally impossible under dedicated placement; must remain impossible in the control plane |

### 4.1 The one that needs care

**Row counts are metadata; row-count *patterns* can be business intelligence.** Knowing a tenant
holds 40,000 invoices is capacity planning. Tracking that number daily across competitors in one
industry is market data the platform was never given permission to derive.

Recommended constraint: aggregates leave the control plane only as **platform-wide** figures or
as **the tenant's own** figures returned to that tenant. Per-tenant series are retained for
operations and are not an input to commercial analysis without consent under §5.

## 5. Business analysis

Three tiers, in increasing order of what they require.

| Tier | Basis | Requires |
| :--- | :--- | :--- |
| **Platform-wide aggregates** | "Median tenant makes 40k calls/month" | Nothing beyond §3 |
| **Tenant's own analytics, returned to them** | Dashboards a tenant sees about itself | Nothing beyond §3 |
| **Anything derived from business content** | "What are tenants selling" | **Explicit, revocable, per-tenant consent**, recorded and auditable |

The third tier is a commercial and legal decision, not a technical setting. A platform that
quietly takes it will eventually have to explain when it started — and the honest answer will be
"from the beginning, in a design document nobody read."

## 6. Why this must be structural, not procedural

`DEC-P35-TENANCY-MODEL` §8 gives dedicated databases. That makes the prohibition in §4
**enforceable rather than merely stated**: the control plane holds no credential for a tenant's
database, so it *cannot* read business rows even if code asked it to.

Recommendation: the control plane connects with a role that has no grant on any tenant database.
Tenant databases push aggregates outward — they are never pulled. A boundary that depends on the
platform choosing not to look is not a boundary.

## 7. Open questions for the reviewing authorities

1. Retention period for per-tenant operational telemetry.
2. Whether a tenant may **see** the telemetry held about it. Recommendation: yes — it is the
   cheapest way to keep the boundary honest.
3. Whether trial tenants in the shared RLS pool are told they are sharing. Recommendation: yes,
   explicitly, since `DEC-P35-TENANCY-MODEL` §8.1 makes it a condition of that placement.
4. Whether the consent mechanism in §5 tier 3 is built now or deferred until a buyer exists.

## 8. Decision and approver

| Field | Value |
| :--- | :--- |
| **Decision** | *Pending* |
| **Approver** | *Not assigned — Architecture Authority* |
| **Security review** | *Not assigned — **required**, this record creates a data flow out of tenant boundaries* |
| **Privacy review** | *Not assigned — **required*** |
| **Agent authority** | Advisory only. `execution_authority: false`, `approval_authority: false` |

No implementation is authorized by this record. It exists so the boundary is decided before code
makes it by default.
