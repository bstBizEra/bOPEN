# bOPEN Agent Alignment & Context Register v1.0

**Document ID:** `BOPEN-GOV-ALIGN-001`  
**Version:** `1.0`  
**Status:** Operational  
**Issued:** 2026-07-29  
**Owner:** Architecture Authority  
**Classification:** Canonical Agent Session, Memory & Backlog Baseline  

---

## 1. Quick Context for AI Agents (Gemini, Claude, Codex, Kimi)

Every AI agent starting a session in bOPEN **must** read this single section to orient itself:

```text
Repository: bOPEN (Open Business Platform Kernel)
Current Phase: Phase 3 — Capability & Commercial Entitlement Kernel
Current Gate: DEC-P3-ENTRY Authorized via Evidence-Driven Gate Realization (AGENTS.md §19.6)
Primary Workspace: c:/laragon/www/bopen (Single-Workspace Policy)
Active Implementation Authority: BOPEN-P3-001 Authorized for Implementation (WP-P3-02..WP-P3-06)
```

---

## 2. Canonical Source-of-Truth Directory

| Concern | Primary Document / Path | Description |
| :--- | :--- | :--- |
| **Product Roadmap** | [`docs/01-product/roadmap.md`](../01-product/roadmap.md) | 5 Strategic Phases (Phase 0 to Phase 4). |
| **Backlog Register** | [`docs/work-packages/WORK-PACKAGE-REGISTER.md`](../work-packages/WORK-PACKAGE-REGISTER.md) | Active & proposed work packages (`BOPEN-P3-001`). |
| **Current Document Status** | [`docs/DOCUMENT-STATUS.md`](../DOCUMENT-STATUS.md) | Status of all normative specs and implementation gates. |
| **Phase 3 Execution Spec** | [`docs/work-packages/BOPEN-P3-001-EXECUTION-PLAN.md`](../work-packages/BOPEN-P3-001-EXECUTION-PLAN.md) | Specs for Phase 3 execution (Capability -> Entitlement -> Metering -> Outbox -> RLS). |
| **Platform Glossary** | [`docs/GLOSSARY.md`](../GLOSSARY.md) | Domain terminology (`Principal`, `Tenant`, `Membership`, `Context`, `Capability`, `Entitlement`). |
| **Change History** | [`docs/CHANGELOG.md`](../CHANGELOG.md) | Audit trail of session updates. |
| **Multi-Agent Rules** | [`AGENTS.md`](../../AGENTS.md) & [`docs/00-governance/multi-agent-orchestration.md`](multi-agent-orchestration.md) | Operating rules & single-workspace policy. |

---

## 3. Session & Memory Protocol for AI Agents

Whenever an AI agent starts or resumes work:

1. **State Discovery**: Read [`docs/00-governance/AGENT-ALIGNMENT.md`](AGENT-ALIGNMENT.md) and [`docs/DOCUMENT-STATUS.md`](../DOCUMENT-STATUS.md).
2. **Work-Package Binding**: Bind the user's task to an accepted work package ID from [`WORK-PACKAGE-REGISTER.md`](../work-packages/WORK-PACKAGE-REGISTER.md).
3. **Execution**: Perform changes directly in the primary workspace. Never spin up isolated Git worktrees or create `/HANDOFF-*.md` in root.
4. **Session Log**: At task completion, update [`docs/CHANGELOG.md`](../CHANGELOG.md) and run:
   ```bash
   python tools/generate_document_manifest.py
   python tools/validate_repository.py
   python tools/check_clean_room.py
   python tools/check_authority_bootstrap.py
   ```
