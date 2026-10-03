# Security and Tenancy Control Model

## Trust boundaries

At minimum, model these boundaries:

1. user/client to edge/API;
2. authentication provider to bOPEN session/context resolver;
3. application service to database and RLS;
4. module to platform service;
5. event producer to outbox and broker;
6. agent/skill runtime to tool gateway;
7. platform operator/support actor to tenant resources;
8. bOPEN to external provider.

## Tenant context

The context resolver MUST:

- derive the authenticated principal from trusted identity evidence;
- resolve candidate tenant or workspace from the route/request;
- verify active membership or explicit delegated/support grant;
- check tenant and membership lifecycle state;
- bind a context identifier to the request, transaction, audit, and event envelope;
- clear or replace database session variables safely between pooled connections;
- fail closed on missing, ambiguous, expired, or inconsistent context.

Never trust a tenant header, URL slug, token claim, or agent argument in isolation.

## Database controls

For tenant-owned pooled tables:

- include immutable tenant ownership or a provable tenant relationship;
- enable and force RLS where applicable;
- define policies for every required command;
- default deny when no policy applies;
- prevent application roles from bypassing RLS;
- prevent connection-pool context leakage;
- test direct ID access, joins, aggregates, background jobs, exports, caches, and event consumers across tenants;
- maintain migration checks that fail when a tenant table lacks expected policy coverage.

RLS is defense in depth. Service-layer authorization remains required.

## Authorization

Every decision SHOULD include:

```text
principal
role/grant
scope
resource
requested action
active tenant/workspace context
entitlement state
policy conditions
time and lifecycle state
approval state
```

Support and platform access MUST use explicit, time-bounded, audited grants. Impersonation MUST be exceptional, visible, approved, and non-repudiable.

## Agent, tool, and skill controls

- The agent is a principal.
- The skill is a procedure.
- The tool is an interface.
- The tool gateway authorizes each invocation.
- Skill metadata is never the source of permission.
- Credentials are resolved at runtime and never stored in a skill package.
- Tool input and output are schema-validated and classified.
- Network and filesystem access are deny-by-default or allowlisted.
- Step, token, tool-call, duration, and monetary budgets are bounded.
- External publication and material state changes require the configured approval.

## Non-waivable negative tests

The following must fail safely:

- missing tenant context;
- wrong tenant context;
- inactive tenant or membership;
- principal from tenant A referencing tenant B resource ID;
- entitled tenant with unauthorized principal;
- authorized principal with missing entitlement;
- service/agent grant outside effective time or scope;
- support access without a current grant;
- stale context reused after membership revocation;
- pooled connection retaining a previous tenant's database session state;
- indirect cross-tenant leakage through search, cache, export, analytics, events, logs, or error messages;
- a skill or prompt requesting elevated permission;
- a reference document instructing the agent to ignore policy.

Allowed cross-tenant disclosure count: zero.
