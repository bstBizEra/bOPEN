-- Migration: 005_lifecycle_audit_and_rollout.sql
-- Description: Durable storage for the Phase 2 lifecycle audit envelope, and the tenant-scoped
--              feature rollout and rate limiting that finding F-7 requires.
-- Version: 1.0.0
-- Work package: BOPEN-P35-001
-- Governing artifacts: BOPEN-P1-001-EXECUTION-PLAN §10.2; BOPEN-ENT-001; AGENTS.md §8, §14
-- Rollback: 005_lifecycle_audit_and_rollout.down.sql
--
-- =============================================================================
-- 1. lifecycle_events — the envelope BOPEN-P1-001 §10.2 specifies
-- =============================================================================
-- `AuditDispatcher.emit_lifecycle_event` produces this envelope and every Phase 2 module emits
-- it: invitation, membership, SCIM, context switching, delegation. Established by executing all
-- eight call sites and capturing 26 events — one key set, thirteen keys, no conditional branch.
--
-- Until now it went nowhere. The dispatcher appends to a Python list, so every Phase 2 audit
-- record is lost on restart and differs per worker. An audit trail that does not survive the
-- process it describes is not an audit trail.
--
-- §10.2 names these fields exactly. `contracts/schemas/audit-event.json` describes a different
-- envelope with `status`/`timestamp`/`actor_id`, which appear in neither §10.2 nor
-- `event-envelope.md`. That conflict is raised as DEC-P35-AUDIT-ENVELOPE and is NOT resolved
-- here: this table implements the specified envelope, and if the decision later converges the
-- two, a further migration merges them. Storing the specified shape is not prejudging the
-- decision — it is implementing the specification that already exists.

CREATE TABLE IF NOT EXISTS lifecycle_events (
    event_id            UUID PRIMARY KEY,
    event_type          VARCHAR(64) NOT NULL,
    event_version       INTEGER NOT NULL DEFAULT 1,
    occurred_at         TIMESTAMPTZ NOT NULL,
    correlation_id      VARCHAR(64) NOT NULL,
    causation_id        VARCHAR(64) NULL,

    -- Not always a principal. Observed values include `anonymous`, `security_control`,
    -- `expiry_scheduler`, `scim_directory` and a bare directory identifier. A foreign key to
    -- principals(id) would therefore reject legitimate events, so there is deliberately none —
    -- recorded here so a later reader does not add one and break the denial paths.
    actor_principal_id  VARCHAR(128) NOT NULL,

    -- Two columns rather than one, and this is the design decision in this table.
    --
    -- The producer emits the literal strings `unknown` and `scoped` in the tenant position on
    -- paths that run before a tenant is resolved — a failed SSO assertion, for instance. Putting
    -- those in an identifier column is the same class of error as `mem_<uuid>` in a UUID column,
    -- which is already an open finding against membership-transition.json.
    --
    -- So the identifier column is a real UUID and nullable, and the sentinel moves to its own
    -- column where it is a fact about scope rather than a fake identifier.
    tenant_id           UUID NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    tenant_scope        VARCHAR(16) NOT NULL DEFAULT 'tenant',

    subject_type        VARCHAR(64) NOT NULL,
    subject_id          VARCHAR(128) NOT NULL,
    outcome             VARCHAR(16) NOT NULL,
    reason_code         VARCHAR(64) NOT NULL,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- §10.2's vocabulary, enforced by the producer as AuditContractError and enforced again
    -- here. Two enforcement points is not redundancy: the producer guards the code path that
    -- exists today, the constraint guards every path that will exist later.
    CONSTRAINT chk_lifecycle_outcome CHECK (outcome IN ('success', 'deny', 'failure')),

    CONSTRAINT chk_lifecycle_version CHECK (event_version > 0),

    CONSTRAINT chk_lifecycle_scope CHECK (tenant_scope IN ('tenant', 'unknown', 'scoped')),

    -- A scope of `tenant` requires an identifier; anything else forbids one. Without this the
    -- two columns could disagree, and a row claiming tenant scope with a null identifier would
    -- be invisible to every policy while looking tenant-owned.
    CONSTRAINT chk_lifecycle_scope_agrees_with_id CHECK (
        (tenant_scope = 'tenant' AND tenant_id IS NOT NULL)
        OR (tenant_scope <> 'tenant' AND tenant_id IS NULL)
    ),

    -- An empty correlation identifier defeats the purpose of carrying one.
    CONSTRAINT chk_lifecycle_correlation CHECK (length(correlation_id) > 0),

    CONSTRAINT chk_lifecycle_reason CHECK (length(reason_code) > 0)
);

-- ON DELETE RESTRICT on the tenant reference, matching migration 003's treatment of
-- audit_events: deleting a tenant must not silently erase the record of what it did. Retention
-- and purge are governed decisions, not a side effect of a foreign key.

CREATE INDEX IF NOT EXISTS idx_lifecycle_events_tenant_time
    ON lifecycle_events (tenant_id, occurred_at DESC) WHERE tenant_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_lifecycle_events_correlation
    ON lifecycle_events (correlation_id);

CREATE INDEX IF NOT EXISTS idx_lifecycle_events_type_time
    ON lifecycle_events (event_type, occurred_at DESC);

ALTER TABLE lifecycle_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE lifecycle_events FORCE ROW LEVEL SECURITY;

-- Append-only, by the same construction migration 003 used for audit_events: a SELECT policy
-- and an INSERT policy and no others, so UPDATE and DELETE reach zero rows whatever SQL is
-- issued. Do not add an UPDATE or DELETE policy without an approved ADR.
CREATE POLICY lifecycle_events_read_isolation ON lifecycle_events
    FOR SELECT
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE POLICY lifecycle_events_append_isolation ON lifecycle_events
    FOR INSERT
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- Rows with no tenant — the `unknown` and `scoped` cases — are readable through NEITHER policy,
-- because `tenant_id = NULL` is never true. That is deliberate and it is a limitation worth
-- stating: pre-resolution events are durable and auditable only through an administrative path
-- that does not yet exist. They are not lost, they are not tenant-readable, and the gap is
-- recorded rather than papered over with a policy that would make them visible to whichever
-- tenant asked first.

-- =============================================================================
-- 2. tenant_feature_toggles — finding F-7, first half
-- =============================================================================
-- `FeatureRolloutEvaluator.is_feature_enabled(feature_key, tenant_id)` accepts a tenant
-- identifier and never reads it. The toggle map is process-global, so one tenant's rollout
-- decision applies to every tenant, and the default for an unknown key is `True`.
--
-- That default is the sharper half. A mistyped feature key grants the feature, which inverts
-- the deny-by-default posture asserted everywhere else in this kernel. The table has no default:
-- absence of a row is absence of a decision, and what the evaluator does with that is an
-- application choice this schema does not make for it.

CREATE TABLE IF NOT EXISTS tenant_feature_toggles (
    tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    feature_key  VARCHAR(128) NOT NULL,
    enabled      BOOLEAN NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by   VARCHAR(128) NULL,

    -- Tenant-scoped uniqueness including tenant scope, per AGENTS.md §14. A feature key is
    -- unique within a tenant and meaningless across tenants.
    PRIMARY KEY (tenant_id, feature_key),

    CONSTRAINT chk_feature_key_not_empty CHECK (length(feature_key) > 0)
);

ALTER TABLE tenant_feature_toggles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_feature_toggles FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_feature_toggles_isolation ON tenant_feature_toggles
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- =============================================================================
-- 3. rate_limit_policies and rate_limit_counters — finding F-7, second half
-- =============================================================================
-- `RateLimiter._limits` is keyed on capability alone, so a limit set for one tenant applies to
-- all of them. `_counts` has no timestamp and no expiry: `reset_seconds=60` is a hardcoded value
-- in the response that no code path acts on, so once a tenant reaches its limit it is throttled
-- for the remaining lifetime of the process.
--
-- The counter is keyed on the window start rather than being mutated in place, so a window
-- boundary is a new row rather than a reset that has to be scheduled. Nothing has to run for a
-- limit to expire, which is the property that makes it correct without a background job.

CREATE TABLE IF NOT EXISTS rate_limit_policies (
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    capability_id   VARCHAR(64) NOT NULL,
    max_per_window  INTEGER NOT NULL,
    window_seconds  INTEGER NOT NULL DEFAULT 60,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (tenant_id, capability_id),

    CONSTRAINT chk_rate_limit_positive CHECK (max_per_window > 0),
    CONSTRAINT chk_rate_window_positive CHECK (window_seconds > 0)
);

ALTER TABLE rate_limit_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit_policies FORCE ROW LEVEL SECURITY;

CREATE POLICY rate_limit_policies_isolation ON rate_limit_policies
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

CREATE TABLE IF NOT EXISTS rate_limit_counters (
    tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    capability_id  VARCHAR(64) NOT NULL,
    window_start   TIMESTAMPTZ NOT NULL,
    window_end     TIMESTAMPTZ NOT NULL,
    consumed       INTEGER NOT NULL DEFAULT 0,

    -- The window start is part of the key, so a new window is a new row and an expired window
    -- simply stops being selected. There is nothing to reset and no job to schedule.
    PRIMARY KEY (tenant_id, capability_id, window_start),

    CONSTRAINT chk_counter_window_order CHECK (window_end > window_start),
    CONSTRAINT chk_counter_non_negative CHECK (consumed >= 0)
);

-- A counter that exceeds its policy is not made unrepresentable here, unlike
-- `chk_balance_within_quota` on usage_meter_balances. The limit lives in a different table and
-- a CHECK cannot reference one, so this invariant has to be enforced by the conditional UPDATE
-- that increments the counter. That is a weaker guarantee than quota gets, and saying so is
-- better than implying the two are equally protected.

CREATE INDEX IF NOT EXISTS idx_rate_limit_counters_window
    ON rate_limit_counters (tenant_id, capability_id, window_end DESC);

ALTER TABLE rate_limit_counters ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit_counters FORCE ROW LEVEL SECURITY;

CREATE POLICY rate_limit_counters_isolation ON rate_limit_counters
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
