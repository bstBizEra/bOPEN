# Research Scope

## Primary question

How does BoxyHQ implement the enterprise SaaS lifecycle, and which patterns should bOPEN adopt, adapt, reject or defer?

## Mandatory questions

- What object is the global user identity?
- What creates a team and owner membership?
- How is team membership stored and made unique?
- How are invitations issued and accepted?
- How is active team context selected and validated?
- Which checks prevent cross-team access?
- How are roles translated into permissions?
- Where do SSO and directory sync intersect with team membership?
- How are audit records and webhooks produced?
- How are API keys scoped?
- How does subscription state affect product access, if at all?
- What does BoxyHQ not model that bOPEN requires?

## Required negative-space analysis

The study must document absent or insufficient abstractions, including generic principal, tenant lifecycle, isolation profile, organization graph, scoped role assignment, policy conditions, entitlement types, capability registry, domain event contract, agent principal and industry-pack contracts.
