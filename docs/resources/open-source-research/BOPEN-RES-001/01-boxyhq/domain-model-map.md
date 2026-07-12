# Domain Model Map

| Upstream model | Meaning | bOPEN mapping | Disposition |
|---|---|---|---|
| `User` | Global human application user | Human Principal + User Account | ADAPT |
| `Account` | External auth provider account | Linked Identity | ADAPT |
| `Session` | Authenticated session | Principal Session | ADAPT |
| `VerificationToken` | Account verification token | Verification Challenge | ADAPT |
| `Team` | Shared SaaS organization/team | Tenant candidate | ADAPT |
| `TeamMember` | User-team relationship with role | Membership + embedded role | ADAPT and separate role |
| `Invitation` | Proposed membership via email/link | Membership Invitation | ADAPT |
| `ApiKey` | Team-scoped API credential | Credential for Service Principal | REJECT direct mapping; redesign |
| `Subscription` | Billing subscription record | Tenant Subscription | ADAPT |
| `Service` / `Price` | Stripe-like catalog data | Product/Offer/Price | DEFER to commercial kernel |
| Jackson store models | Enterprise identity backing store | IdP connection/provisioning adapter data | Isolate adapter |

## Cardinality observations

- A user can have multiple team memberships.
- A team can have multiple members and invitations.
- A membership is unique for one team and one user.
- A team may have multiple API keys.
- Subscription records are not visibly related to team through a direct foreign key in the observed schema; the team contains billing identifiers instead.

## bOPEN requirements generated

- one global principal may have zero, one or many tenant memberships;
- membership uniqueness must be enforced;
- tenant billing association must be explicit and auditable;
- credentials must belong to a governed principal, not float as tenant secrets;
- external identity adapter storage must not become the tenant-domain source of truth.
