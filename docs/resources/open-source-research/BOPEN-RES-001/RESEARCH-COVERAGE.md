# Research Coverage Matrix

| bOPEN area | BoxyHQ study strength | Planned evidence | Key gap to test |
|---|---:|---|---|
| Platform | Medium | README, routes, integration boundaries | No formal platform control plane |
| Human principal | High | User/account/session schema and auth flows | No principal supertype |
| Service/agent/device principal | Low | API key and integration review | Missing governed non-human identity model |
| Tenant | High analogy | Team schema, creation and settings | Missing tenant states, policy, isolation profile |
| Membership | High | TeamMember schema and lifecycle | Role embedded in membership |
| Invitation | High | Create/fetch/accept/expire/delete paths | Missing explicit status and replay controls |
| Context | Medium | Route/session/access resolver trace | Context may be implicit and team-only |
| Authorization | Medium-high | Role permission map and API guards | No conditions, deny, ReBAC or decision record |
| Entitlement | Low | Subscription and payment integration | No generalized feature/quota entitlement engine |
| Capability | Low | Permission resources and services/features | No versioned capability/module registry |
| SSO/SCIM | Medium-high | SAML Jackson integration trace | External integration owns substantial behavior |
| Audit | Medium-high | Retraced calls and event coverage | Native immutable audit contract absent |
| Events | Medium-high | Svix event emissions | No full domain-event/outbox/replay model |
| API access | Medium | Team-bound API key model | No service-principal lifecycle and scoped grants |
| Data isolation | Low-medium | Query/access paths and tests | No PostgreSQL RLS baseline in observed schema |
| Billing | Medium | Stripe/subscription/service/price records | Commercial state and access gating separation |
| Industry modules | None | Gap analysis | Outside SaaS starter abstraction |
| Multi-industry foundation | None | Gap analysis | Party, asset, location, document kernels absent |
