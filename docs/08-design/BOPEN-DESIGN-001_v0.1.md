# BOPEN-DESIGN-001 — Platform Experience and Module UI Governance v0.1

## Portal surfaces

- Platform Console
- My bOPEN
- Tenant Portal
- Work Portal
- Security Portal
- Billing Portal
- Partner Portal
- Agent Portal
- Developer Portal

## Context routes

```text
/my/*                 Personal user context
/{tenantSlug}/*       Active tenant context
/platform/*           Platform operator context
```

## Design controls

- Always display active tenant context in tenant-scoped work.
- Never imply access based only on hidden navigation.
- Restricted actions show a policy-consistent explanation without revealing sensitive
  authorization internals.
- Tenant branding may alter approved tokens, logos and domains, not security affordances.
- Modules contribute navigation through a registered manifest.
- Meet applicable accessibility requirements for keyboard, contrast, focus, semantics
  and error recovery.
- Show agent actions, pending approvals and human decisions as distinct states.

## Required module design states

Loading, empty, success, validation error, system error, forbidden, not entitled,
module disabled, tenant restricted, tenant suspended, support access active and
read-only degradation.
