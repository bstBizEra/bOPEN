# Capability, Event and Audit Analysis

## Capability

The permission resource list provides a useful inventory of administrative surfaces, but it is not a product/module capability registry.

bOPEN requires:

```text
Product -> Module -> Feature -> Action -> Resource Type
```

with version, dependency, event, entitlement and agent-tool contracts.

## Events

Invitation creation/removal and member creation emit Svix events. Team creation initializes a webhook application. This demonstrates integration-event placement near lifecycle changes.

bOPEN must add:
- canonical event envelope;
- transactional outbox;
- schema/version registry;
- idempotency and deduplication;
- correlation and causation IDs;
- replay and dead-letter governance;
- tenant and actor attribution.

## Audit

Audit calls are made for selected lifecycle actions through Retraced. bOPEN should treat external audit viewers as adapters while owning the audit-event contract and durable evidence store.

## Decision proposal

Adopt the rule that material membership/tenant changes emit both integration and audit evidence. Redesign the underlying event and audit contracts.
