# Source Register

**Register date:** 2026-07-22

## Internal controlling and informative artifacts

| Source | Role in this package |
|---|---|
| BOPEN-SYS-001 — bOPEN Final System Design v0.1 | Architecture baseline: global principal, membership, active context, modular-monolith P0, RLS, modules, events, audit, portals, provider seams, and exit posture |
| BOPEN-P0-001 — bOPEN P0 Implementation Control v0.1 | Entry/exit gates, work packages, evidence, negative testing, recovery, supply-chain, and conformance controls |
| Multi-Tenant Portal Research | User/tenant/platform contexts, membership and tenant state machines, portal capabilities, and identity/tenant separation |
| bOPEN Platform Kernel Research | Principal/party/tenant/organization separation, capability packages, industry packs, isolation profiles, and commercial/event kernels |
| bOPEN Open-Source Research Lab Plan | Clean-room research method and comparative study boundaries |
| Skills for bOPEN Architecture research | Skill/tool/capability/workflow separation, bOPEN manifest, registry, evaluation, runtime binding, and provenance model |

## External format and evaluation sources

| Source | URL | Use |
|---|---|---|
| Agent Skills specification | https://agentskills.io/specification | Portable directory, `SKILL.md`, frontmatter, optional directories, progressive disclosure, and validation constraints |
| OpenAI: Build skills | https://developers.openai.com/codex/build-skills | Codex/ChatGPT skill discovery, `.agents/skills`, optional `agents/openai.yaml`, invocation policy, and distribution guidance |
| OpenAI: Skills in API | https://developers.openai.com/cookbook/examples/skills_in_api | Versioned bundle and ZIP upload model; skill/tool/system-prompt boundary |
| OpenAI: Testing Agent Skills Systematically with Evals | https://developers.openai.com/blog/eval-skills | Outcome, process, style, efficiency, and activation evaluation pattern |
| Model Context Protocol 2025-11-25 | https://modelcontextprotocol.io/specification/2025-11-25 | Separation of resources, prompts, and tools |

## Architecture research references

| Source | URL | Research area |
|---|---|---|
| PostgreSQL Row Security | https://www.postgresql.org/docs/current/ddl-rowsecurity.html | Default-deny row policies and database enforcement |
| Keycloak Organizations | https://www.keycloak.org/docs/latest/server_admin/index.html | Multi-organization membership and active organization context |
| Logto Organization Experience | https://docs.logto.io/end-user-flows/organization-experience | Organization membership, invitations, and provisioning |
| ZITADEL Organizations and Delegation | https://zitadel.com/docs/guides/manage/console/organizations-overview | B2B organization isolation and delegated administration |
| OpenFGA documentation | https://openfga.dev/docs/fga | Relationship-based authorization patterns |
| CloudEvents | https://cloudevents.io/ | Portable event-envelope concepts |
| OpenFeature | https://openfeature.dev/ | Provider-neutral feature-flag evaluation seam |
| AWS SaaS Lens | https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html | Pool, silo, and bridge isolation patterns |

External sources are informative unless an approved bOPEN artifact explicitly adopts them. Versions and current behavior must be reverified before material use.
