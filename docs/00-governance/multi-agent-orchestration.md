# Multi-LLM & Agent Orchestration Specification v1.0

**Document ID:** `BOPEN-GOV-AGENT-001`  
**Version:** `1.0`  
**Status:** Approved for agent operations  
**Issued:** 2026-07-29  
**Owner:** Engineering Authority & Architecture Authority  
**Classification:** Internal engineering governance  

---

## 1. Overview & Purpose

The bOPEN multi-tenant platform kernel relies on high-assurance engineering governance across multiple AI agent runtimes and Large Language Models (LLMs)—including **Gemini**, **Claude**, **Codex**, **Kimi**, and **DeepSeek**.

This specification outlines the standard operating procedures, model role specializations, and single-workspace coordination protocols required to prevent worktree fragmentation, handoff deadlocks, and governance drift.

---

## 2. Core Operational Rules

### 2.1 Single-Workspace Execution Principle
* All participating AI agents—regardless of model family or agent framework—shall operate directly within the primary repository workspace (`c:/laragon/www/bopen`) on a designated target branch.
* Spawning uncoordinated parallel Git worktrees (e.g. `C:/b-c8`, `.claude/worktrees/`, `bopen-worktrees/`) is **prohibited** unless an explicit multi-workspace decision is authorized.
* All agents share a single working tree and build target to prevent context fragmentation.

### 2.2 Model Specialization Matrix

| Model / Agent Engine | Strategic Role | Primary Responsibilities |
| :--- | :--- | :--- |
| **Gemini (Antigravity)** | Lead Architect & System Auditor | Architectural synthesis, multi-domain planning, system-wide audits, and compliance verification. |
| **Claude** | Senior Refactorer & Test Engineer | Large-scale code refactoring, complex unit/integration test design, and contract schema authoring. |
| **Codex** | Precision Implementer & Tooling | Low-level logic implementation, script execution, CI validation, and verifier maintenance. |
| **Kimi / DeepSeek** | Research Analyst & Documentarian | Upstream source analysis, long-context documentation audit, clean-room findings synthesis. |

---

## 3. Workflow & Handoff Rules

1. **No Root Handoff Pollutants**: Agents must **never** commit or create untracked coordination files at the repository root (e.g., `/HANDOFF-*-TO-CODEX.md`).
2. **Governed Handoff Records**: All state changes and handoffs between agents or humans must be recorded directly in governed artifacts:
   - `docs/CHANGELOG.md`
   - `docs/DOCUMENT-MANIFEST.json`
   - `docs/evidence/`
3. **Mandatory Validation Gate**: Before ending any turn or declaring a task complete, every agent MUST execute:
   ```bash
   python tools/validate_repository.py
   python tools/check_clean_room.py
   ```
4. **Anti-Deadlock Rule**: If an automated verifier or test fails during an agent-to-agent transition, the current agent must resolve the underlying cause or present an explicit decision request to the human user rather than looping through infinite repair cycles.

---

## 4. Traceability & Evidence

Every change executed by an agent must update `docs/DOCUMENT-MANIFEST.json` using `python tools/generate_document_manifest.py` to maintain total auditability across all LLM contributions.
