# Event Envelope

Required candidate fields:

```text
event_id, event_type, event_version, occurred_at
platform_id, tenant_id, context_id
principal_id, actor_type
resource_type, resource_id
correlation_id, causation_id
schema_version, data, metadata
```

Usage and audit events may extend this envelope but have separate schemas and retention rules.

The first draft audit-event schema for authorization outcomes is `docs/06-contracts/events/audit-event.schema.json`.
