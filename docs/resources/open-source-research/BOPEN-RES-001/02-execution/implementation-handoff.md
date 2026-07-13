# Clean-Room Implementation Handoff

## Permitted contents

- approved bOPEN requirements;
- bOPEN domain definitions;
- versioned API/event/module contracts created independently;
- approved ADRs;
- bOPEN threat model;
- acceptance tests written in bOPEN terminology;
- non-functional requirements and exit gates.

## Excluded contents

- BoxyHQ source code;
- copied Prisma schema/migrations;
- copied permission tables;
- copied UI or route structures;
- copied tests;
- upstream secrets/configuration;
- unreviewed snippets or screenshots containing source.

## Initial requirements suitable for handoff after approval

1. A principal may hold multiple tenant memberships.
2. Tenant provisioning creates an initial owner membership atomically or compensates on failure.
3. Invitation acceptance creates membership only after token, identity, tenant and policy validation.
4. Active context is server validated for every tenant-scoped request.
5. Membership status, role assignment, entitlement and authorization are distinct.
6. API credentials identify a governed non-human principal.
7. Material membership and tenant changes emit auditable, versioned events.
8. Entitlement decisions are independent from user authorization.
