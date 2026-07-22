# bOPEN Domain Glossary

| Term | Normative meaning | Must not be confused with |
|---|---|---|
| Platform | The bOPEN-operated technical and governance environment | Product |
| Product | User-facing composition of modules and experiences | Tenant |
| Module | Installable or activatable package that exposes capabilities | Feature flag |
| Feature | Bounded product behavior | Entitlement |
| Capability | Registered action/resource contract | Tool or skill |
| Principal | Actor that can act | Party |
| User | Human principal account | Person party |
| Party | Real-world person or organization | Authenticated user |
| Tenant | Isolation, policy, and commercial boundary | Company or organization |
| Organization | Business structure | Tenant |
| Legal entity | Legally recognized organization | Tenant |
| Membership | Principal-to-tenant relationship | Role assignment |
| Role | Named bundle or decision input for authorization | Job title |
| Permission | Allowed action in scope | Entitlement |
| Entitlement | Tenant right or capacity to consume | Permission |
| Active context | Server-validated tenant/workspace/resource execution context | Client header |
| Resource | Governed domain or platform object | Capability |
| Action | Operation attempted on a resource | Workflow |
| Tool | Callable interface to perform or inspect an operation | Skill |
| Skill | Reusable procedure and supporting files | Permission or agent |
| Agent | Governed principal/runtime that plans or acts | Skill |
| Workflow | Durable stateful orchestration with recovery | Prompt |
| Prompt | Request or parameterized message | Policy |
| Policy | Non-bypassable decision constraint | Instruction |
| RLS | PostgreSQL row-level enforcement | Complete authorization system |
| RBAC | Role-based authorization | Tenant isolation |
| ReBAC | Relationship-based resource authorization | RLS replacement |
| Entitlement meter | Usage/capacity control | Billing invoice |
| Domain event | Business fact owned by a module | Audit event |
| Audit event | Security/compliance record of action and outcome | Domain event |
| Outbox | Transactional handoff for asynchronous publication | Message broker |
| Evidence | Verifiable result supporting a control or decision | Assertion |
| ADR | Record of one material architecture decision | Full system design |
