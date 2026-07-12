# Risk Register

| ID | Risk | Impact | Control | Owner | Status |
|---|---|---|---|---|---|
| RSK-001 | Upstream source copied into bOPEN | License/coupling | Clean-room policy and path validation | Research Authority | Open |
| RSK-002 | Agents invent tenant/authorization semantics | Security/rework | AGENTS hierarchy and decision stop conditions | Architecture Authority | Controlled |
| RSK-003 | Cross-tenant data leakage | Critical | DB isolation, deny tests and security review | Security/Data Authorities | Open |
| RSK-004 | Entitlement conflated with authorization | Revenue/security | Separate contracts and ADR-0008 | Product/Architecture | Controlled |
| RSK-005 | Premature microservices | Complexity | Modular-monolith proposal and extraction criteria | Architecture | Open |
| RSK-006 | bOPEN naming conflict | Brand/legal | Codename status and clearance | Product/Legal | Open |
| RSK-007 | Unclear open-source license | Legal/commercial | All-rights-reserved bootstrap and legal strategy | Legal | Open |
| RSK-008 | Documentation diverges from code | Governance | Same-change updates and traceability validation | Engineering | Open |
| RSK-009 | Local bootstrap history and GitHub stable `main` history diverge | Release/source integrity | DEC-0006 option 1 approved; reconcile through protected branch and pull request; prohibit force-push | Engineering | Controlled |
| RSK-010 | Local bGitea `origin` repository is not yet verified | Local collaboration blocked or pushed to wrong repo | Confirm or create local bGitea repository before configuring `origin` or pushing work branches | Engineering | Open |
| RSK-011 | Private GitHub repository cannot enable branch protection on the current account plan | Stable review controls cannot be enforced on GitHub | Keep repository private; resolve DEC-0008 through bGitea enforcement or account upgrade; do not treat draft PR/CI alone as protection | Engineering | Open |
