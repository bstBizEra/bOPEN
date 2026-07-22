---
name: bopen-event-outbox-contract
description: >-
  Design and review versioned domain events event envelopes transactional outbox writes delivery retries idempotency dead letters and replay governance for WP-07 and asynchronous integration.
license: Internal-Evaluation
metadata:
  canonical-id: io.bizera.bopen.event.outbox.contract
  version: "0.1.0"
  owner: bopen-integration-authority
  lifecycle: CANDIDATE
  risk-class: SKR3
---

# bOPEN Event and Transactional Outbox Contract

## Purpose

Keep business state and event publication consistent traceable and recoverable across failures.

## Use this skill when

- Publishing a domain or integration event
- Adding an outbox dispatcher or consumer
- Designing retry dead-letter or replay behavior

## Do not use this skill when

- Publishing directly after commit without durable intent
- Using an event as authorization
- Changing event meaning without a version

## Authority boundary

This Skill is a procedure. It does not grant tools, permissions, credentials, Tenant context, Entitlement, approval or exception. Revalidate each tool call and tenant-sensitive action through bOPEN policy.

## Inputs

- Requested mode and bounded task scope.
- Applicable repository paths, source artifacts and constraints.
- Known authority, Tenant sensitivity, risk and requested output format.

## Supported modes

`event-design`, `outbox-review`, `consumer-contract`, `replay-plan`, `incident-analysis`

## Procedure

1. **Classify event.** Separate domain fact integration event command and telemetry.
2. **Define schema.** Use stable event type version and bOPEN envelope.
3. **Write atomically.** Persist aggregate change and outbox record in one transaction.
4. **Dispatch.** Claim publish and mark delivery with bounded retries and observability.
5. **Consume idempotently.** Deduplicate and revalidate privileged Tenant authority.
6. **Handle failure.** Define dead-letter quarantine compensation and operator action.
7. **Govern replay.** Authorize scope record replay metadata and prevent duplicate effects.

## Mandatory controls

- Event ID type version Tenant actor resource correlation causation and time are explicit.
- Payload is a fact not a database-row dump.
- Consumers are idempotent.
- Replay is an audited privileged operation.
- Schema compatibility is tested.

## Output contract

- Event contract and examples
- Outbox schema and transaction design
- Consumer failure and idempotency rules
- Replay and recovery runbook

Every output distinguishes evidence, inference, assumption and recommendation. Use `schemas/output.schema.json` for structured output.

## Failure handling

- Missing authoritative evidence: issue `decision-required` or `incomplete`; never invent facts.
- Failed mandatory or cross-Tenant control: issue `fail` and identify the blocker.
- Unsafe requested behavior: refuse the unsafe step and preserve the governing boundary.
- Tool or dependency failure: report exactly what ran, what failed and which evidence is unavailable.

## Completion evidence

1. Identify source scope or repository revision.
2. Record checks and important negative cases.
3. List residual risks and required reviewers.
4. Never claim `APPROVED`, `SIGNED`, `PUBLISHED` or production-ready without corresponding evidence.

## References

- `references/bopen-invariants.md`
- `references/control-checklist.md`
- `references/output-contract.md`
- `references/examples.md`
- `policies/execution-policy.yaml`
- `bopen.skill.yaml`
