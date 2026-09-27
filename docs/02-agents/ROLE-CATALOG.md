# Agent Role Catalog and Suggested Harness Placement

| Role | Default lead | Secondary/checker | Human accountability |
|---|---|---|---|
| Governance Lead | Claude | Codex evidence scan | Program Authority |
| Requirements Analyst | Claude | Codex feasibility review | Product Authority |
| Domain Architect | Claude | Codex schema feasibility | Architecture Authority |
| Platform Architect | Claude | Codex implementation review | Architecture Authority |
| Security Architect | Claude | Codex static checks | Security Authority |
| Tenant-Isolation Verifier | Claude or dedicated verifier | Codex test execution | Conformance Authority |
| Backend Maker | Codex | Claude review | Module owner |
| Database/Migration Maker | Codex | Claude + verifier | Data Authority |
| Portal Maker | Antigravity + Codex | Claude design review | Product/Design owner |
| Browser/E2E Verifier | Antigravity | Codex test review | Test owner |
| CI/Automation Maker | Codex/Copilot | Claude review | Delivery owner |
| Evidence Auditor | Claude | Codex hash/index generation | Conformance Authority |
| Release Coordinator | Registered harness | Claude readiness review | Human Release Authority |

Assignment is based on operating policy and task shape, not a claim that a harness is
universally superior.
