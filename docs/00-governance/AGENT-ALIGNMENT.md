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
Current Phase: Phase 3.5 — Runtime Realization, CLOSING
Current Gate: DEC-P35-RUNTIME Approved (Option C); DEC-P35-TWO-AGENT-QUORUM Approved 2026-08-02 (Option B)
Primary Workspace: c:/laragon/www/bopen (Single-Workspace Policy)
Team: Claude + Codex (two-agent profile in force — EBIV §6.5)
Rule: an engine that edits a package cannot vote on it (EBIV §3). Record your row before writing
Verification State (2026-08-02):
  WP-P35-01..03  CONFIRMED_UNDER_TWO_AGENT_PROFILE (one verifier + operator disposition; rerun-evidence risk on record)
  WP-P35-04      BLOCKED_ACCEPTED_WITH_KNOWN_DEFECTS (two standing refutations; gateway usable)
  WP-P35-05a R4  AWAITING one Codex ballot at 119f2d8 — the only open engineering item in the phase
  Phases 1-3     IMPLEMENTED_UNVERIFIED (not re-verified under EBIV)
Next: Codex ballots WP-P35-05a R4; then Phase 3.5 fully disposed and Phase 4 entry opens
```

Read [`AGENTS.md`](../../AGENTS.md) §20.2 and §22 before starting. Authorization to write code
is not a verdict on code already written.

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
