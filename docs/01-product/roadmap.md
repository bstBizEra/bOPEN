# Strategic Roadmap

## Phase 0 — Govern and research

Repository bootstrap, clean-room research, requirements and architecture.

## Phase 1 — Platform kernel vertical slice

Human principal, tenant provisioning, owner membership, active context, authorization, audit and isolation.

## Phase 2 — Membership and enterprise onboarding

Invitations, tenant switching, SSO/SCIM boundaries, service principals and delegated access.

## Phase 3 — Capability and entitlement kernel

Module registry, entitlement decisions, usage events and product composition.

## Phase 3.5 — Runtime realization

Persistence on PostgreSQL with enforced row-level isolation, kernel HTTP surface, signed
context token, API gateway and enterprise IdP integration. Turns the kernel from an
in-process model into a service that satellite products can call.

Inserted 2026-07-30 under `BOPEN-P35-001`. `DEC-P35-RUNTIME` approved 2026-07-31, so
implementation is authorized. `WP-P35-01`..`WP-P35-04` and `WP-P35-05a` are implemented and
unverified. Enterprise IdP federation (`WP-P35-05b`) was moved out of this phase by
`DEC-P35-IDP-SPLIT`, because a runtime security fix should not wait on a vendor licensing
question; it remains blocked.

## Phase 3.6 — Tenant privacy and platform observability

Hybrid placement: a dedicated database per tenant by default, a shared row-level-security pool
for trial and free tier. A control plane that carries usage aggregates, operational telemetry,
authorization outcomes and entitlement state — and never a tenant business row.

Inserted 2026-07-31 under `DEC-P35-TENANCY-MODEL` §8, on a tenant-privacy driver. Requirements in
[`BOPEN-PRD-P35-002`](../02-requirements/BOPEN-PRD-P35-002.md); plan in
[`BOPEN-P36-001`](../work-packages/BOPEN-P36-001-EXECUTION-PLAN.md).

The hard part is not placement. It is that twelve foreign keys currently reference `tenants` or
`principals` and cannot survive a split across databases, because PostgreSQL cannot enforce a
foreign key across them. Replacing those with something enforced — not with a convention — is the
work.

Blocked at entry on Security and Privacy review of `DEC-P35-CONTROL-PLANE`, which is where two
open questions belong: that the control plane must hold personal data to function, and where
audit records carrying business identifiers should live.

## Phase 4 — Common business foundation and first product packs

Party, organization, document, location and initial bPro/bFleet compositions.

Blocked until Phase 3.5 reports admissible evidence: these products consume the kernel
across a network boundary, which does not yet exist.
