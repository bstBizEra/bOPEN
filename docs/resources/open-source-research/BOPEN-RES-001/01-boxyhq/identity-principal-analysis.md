# Identity and Principal Analysis

## Strong patterns

- Global user record independent of team.
- Linked provider accounts separated from user.
- Sessions separated from user.
- Email verification and password reset modeled independently.
- Multiple team memberships available from one user.

## Limitations for bOPEN

`User` represents only a human account. bOPEN must support:

- service accounts;
- API clients/applications;
- agents;
- devices;
- system principals;
- credential rotation and revocation;
- principal status independent from membership status;
- principal-to-party linkage.

## API key finding

A team-bound `ApiKey` is useful for tenant-scoped automation, but it does not establish who or what is acting. bOPEN should require:

```text
Service Principal
  -> Credential
  -> Tenant Membership or Grant
  -> Role/Capability Assignment
  -> Session/Token
  -> Audit Actor
```

## Decision proposal

Adopt the global-human-user pattern. Reject the idea that user and API key together are sufficient as the bOPEN principal kernel.

## R1 observations - 2026-07-13

### Observation

- Human `User` remains the sole identity root; no general principal abstraction was observed.
- Identity operations provide metrics but no complete domain-event/audit chain.
- Email canonicalization is not consistently applied before unique lookup/storage.
- Verification, reset, lockout, linked-account and API-key use have substantial negative-test gaps.
- JWT sessions are not invalidated by password reset/change.
- Team API keys are stored by digest, but observed code does not use them as an authentication path or enforce expiry/last-used semantics.

### Inference

bOPEN needs principal, credential, session and audit lifecycles that remain independent from the human-user profile and tenant membership. Identity canonicalization and credential/session revocation require explicit contracts and negative tests.

### Decision status

Research input only. RES-P0-05 trace is complete, but runtime acceptance and G3 remain open.
