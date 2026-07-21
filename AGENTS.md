# agents.md — bOPEN Antigravity Team Adapter

Canonical authority: `AGENTS.md` and `docs/00-governance/BOPEN-GOV-001_v0.1.md`.

## Team

- Governance Lead
- Product and Requirements Analyst
- Platform Architect
- Security and Tenant-Isolation Architect
- Backend Maker
- Portal and Experience Maker
- Test and Conformance Verifier
- Evidence Auditor
- Release Coordinator

## Operating pipeline

```text
/intake
→ /specify
→ /architecture
→ /authorize
→ /implement
→ /verify
→ /evidence
→ /review
→ /release-readiness
```

Use `.agents/skills/` for reusable procedures and `.agents/workflows/` for pipeline
commands. Generated plans, screenshots, browser recordings and task lists are supporting
artifacts; they are not acceptance evidence until linked to requirements and checked.

Every agent must inherit the same tenant-isolation, credential, worktree, maker–checker,
evidence and release constraints defined in root `AGENTS.md`.
