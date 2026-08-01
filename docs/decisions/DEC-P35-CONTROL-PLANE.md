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

> **Corrected 2026-07-31 — this section as first drafted forbade what the platform requires.**
> It prohibited "free-text content — names, addresses" without distinguishing *tenant business
> content* from *platform-owned identity*. `BOPEN-PRD-P35-002` F-2 then established that
> `principals.email` is globally unique and therefore cannot be sharded, so the control plane
> must hold it or the platform cannot register a principal at all. The prohibition below is now
> scoped to its actual target. The error is left visible because a rule that forbids the thing
> it depends on is the kind that gets quietly ignored rather than fixed.

The boundary runs between **tenant business content** and **platform-owned relationship data** —
not between "sensitive" and "not sensitive". Both sides can contain personal data; only one side
belongs to the tenant.

| Prohibited | Reason |
| :--- | :--- |
| Any row from a tenant's business tables | The property this decision exists to protect |
| Field values from those tables, even hashed or truncated | A hash of a business value is still that value's identity, and it makes cross-tenant joins possible |
| Free-text content originating in tenant business data — notes, descriptions, documents, customer names | Unbounded in what it may reveal, and it is the tenant's, not the platform's |
| Query text containing literals | A slow-query log carrying `WHERE customer = 'Acme'` moves business data into telemetry |
| Cross-tenant joins of any kind | Structurally impossible under dedicated placement; must remain impossible in the control plane |

### 4.1 Platform-owned identity is permitted, bounded and declared

The control plane holds the principal registry, including `principals.email`. This is not an
exception grudgingly made — a principal exists **before** it belongs to any tenant
(`BOPEN-TENANT-001` invariant 1), so it was never tenant-owned data. Global email uniqueness is
what makes one principal reachable across many tenants, which is the platform's function.

It is nonetheless personal data, and is therefore subject to:

- an enumerated register of every personal-data column the control plane holds
  (`BOPEN-PRD-P35-002` `PRD-P35B-PII-001`);
- a stated justification per item, naming the platform function that fails without it;
- Privacy Authority review of that register, not of this sentence.

**The test to apply:** *would this value exist if the tenant had never been created?* A principal's
email would — the principal may belong to several tenants or none. A customer name in a tenant's
invoice would not. The first is platform-owned; the second is the tenant's and does not cross.

### 4.1 The one that needs care

**Row counts are metadata; row-count *patterns* can be business intelligence.** Knowing a tenant
holds 40,000 invoices is capacity planning. Tracking that number daily across competitors in one
industry is market data the platform was never given permission to derive.

Recommended constraint: aggregates leave the control plane only as **platform-wide** figures or
as **the tenant's own** figures returned to that tenant. Per-tenant series are retained for
operations and are not an input to commercial analysis without consent under §5.

## 5A. Disposition 2026-08-01 — tier 3 permitted under per-tenant opt-in consent

> **Operator disposition.** Business-content analytics is permitted for **all tenants**, of any
> placement, **under explicit opt-in consent**. Default is off. Consent is revocable.
> §5 below is retained; this section governs its tier 3.

### 5A.1 What this does and does not authorize

**Authorized:** deriving insight from tenant business content — rows, field values, document
content — **for tenants that have opted in**, for the purpose of improving the system and
platform.

**Not authorized, and unchanged:** reading business content of a tenant that has not opted in.
Absence of consent is not consent. §4's prohibitions apply in full to every non-consenting
tenant, which after a default-off launch is every tenant.

### 5A.2 The constraint that makes this enforceable rather than promised

**Consent must not be implemented by giving the control plane credentials on tenant databases.**

If the control plane holds credentials, it can read *every* tenant — and the boundary for
non-consenting tenants degrades from a structural property to a policy the platform promises to
honour. That would silently repeal `PRD-P35B-CRED-001`, which is the mechanism the entire privacy
claim rests on.

The direction is therefore fixed: **consented content is pushed outward from the tenant plane,
never pulled by the control plane.** A tenant that has not consented has no push configured, and
the platform has no route to its data even if its code asked. Consent becomes a capability the
tenant grants, not a check the platform performs on itself.

This is the same reasoning as §6 and it survives the disposition intact.

### 5A.3 What must exist before any content is read

Each is a mechanism, not a statement of intent.

| Requirement | Why |
| :--- | :--- |
| **Consent record** — tenant, scope, terms version, granting principal, timestamp | "The tenant agreed" must name *who*, *to what*, and *when*, or it cannot be shown later |
| **Authority to consent is checked** | An `active` membership is not authority to give away a tenant's data. The role permitted to consent must be named |
| **Revocation, honoured retroactively** | Revocation that leaves derived models trained on the data is revocation in name only. The retention and re-derivation obligation must be stated **before** the first model exists, not after |
| **Per-tenant provenance in every derived artifact** | If tenant X revokes, you must be able to answer which aggregates, models and reports contain its contribution. Unanswerable later if not recorded from the start |
| **Disclosure the tenant can inspect** | Pairs with `PRD-P35B-DISCLOSE-001`: a tenant can see its placement, what is held, and its own consent state |
| **Default-off proven by test** | A negative probe showing a non-consenting tenant's content is unreachable — refused by construction, not by an `if` |

### 5A.4 Cost recorded honestly

This is the most expensive of the four options considered. It buys the widest data, and it
obliges the platform to build consent capture, revocation, provenance tracking and retroactive
re-derivation — none of which exist. **Option "derived metrics only" required none of them**, and
would have supplied capacity, adoption, performance and cost analytics from metering and
schema-level counts already being collected.

The disposition is the operator's and is recorded as made. The cost is recorded beside it so that
a later reader can see it was chosen rather than stumbled into, and so that a decision to descope
later is available on the evidence rather than on regret.

### 5A.5 Concurrence

**Security and Privacy Authority concurrence is NOT recorded.** This section creates a new data
flow out of tenant boundaries, which is the category §8 already marks as requiring review. The
*choice* is the operator's; the *mechanism* in §5A.3 must be reviewed before implementation.
Docketed as `D-CP-005`.

## 5B. Correction 2026-08-01 — the requirement is frequency, flow and reports, not content

> **§5A over-scoped the requirement and is narrowed here.** §5A is retained under the extend-only
> rule and **must not be read as the current disposition**. §5B governs.

### 5B.1 What was actually asked for

*"Frequency data, flow and report."* Not business content. §5A was drafted from a broader reading
and would have obliged the platform to build consent capture, revocation, provenance tracking and
retroactive re-derivation — **none of which this requirement needs.**

### 5B.2 All three are already permitted, and none touches business content

| Requirement | Derived from | Business content needed? |
| :--- | :--- | :--- |
| **Frequency** — API call volume, feature and capability invocation counts, error rates, quota consumption | `usage_meter_balances`, `usage_outbox`, `rate_limit_counters`, audit outcome counts | **No** |
| **Flow** — which capabilities follow which, journeys, funnels, drop-off, abandonment | `audit_events` **shape**: `action`, `resource_type`, `occurred_at`, `correlation_id` | **No** |
| **Report** — platform-wide aggregates, and a tenant's own figures returned to it | the above, aggregated | **No** — §5 tiers 1 and 2 |

Every one sits inside §3 as already drafted. **No amendment to §4 is required, and §5 tier 3 is
not engaged.**

### 5B.3 What this removes

**All six mechanisms in §5A.3 are withdrawn as unnecessary**: consent record, authority-to-consent
check, retroactive revocation, per-tenant provenance in derived artifacts, consent disclosure, and
the default-off consent probe.

`D-CP-005` is **withdrawn**. Business-content analytics is **not** authorized for any tenant, by
consent or otherwise. If it is ever wanted, §5 tier 3 and §5A remain on the record as the analysis
of what it would cost — but nothing is being built toward it.

That is the whole benefit of the correction: the platform gets the analytics that were actually
wanted, and `O-1` stays a structural property rather than a policy with an exception in it.

### 5B.4 The one thing flow analytics does constrain

Flow needs the **shape** of audit events — `action`, `resource_type`, timing, correlation — and
**not** `resource_id`, which is the column naming the tenant's business object.

That is precisely the split `D-CP-002` option 3 recommends: the full record stays tenant-side as
the authoritative one, and a control-plane projection carries everything except `resource_id` and
`payload`. **This requirement therefore does not merely tolerate that disposition, it depends on
it** — a tenant-side-only audit record (`D-CP-002` option 1) would make platform-wide flow
analysis impossible.

`D-CP-002` should be disposed with that dependency on the record.

**Prerequisite unchanged:** `P-1` still binds. `action` and `resource_type` are free text today,
so a caller can put business content in them. They must be closed vocabularies before any
projection carries them, or "no business content crosses" is a hope rather than a property.

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
