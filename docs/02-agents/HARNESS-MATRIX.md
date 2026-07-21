# Harness Matrix

## Codex

Use for:

- bounded implementation and refactoring;
- migrations and repository-wide mechanical changes;
- unit/contract test scaffolding;
- CI scripts and build repair;
- module scaffolding and documentation synchronization;
- worktree-based parallel execution.

Required adapter: root `AGENTS.md`. Repository skills live under `.agents/skills/`.

## Claude Code

Use for:

- requirements and architecture;
- threat modeling and policy review;
- cross-file analysis;
- independent code/evidence checking;
- complex defect and root-cause reasoning;
- conformance report preparation.

Required adapter: `CLAUDE.md`, `.claude/rules/`, and approved `.claude/agents/`.

## Antigravity

Use for:

- agent-first portal prototypes;
- visual and browser-visible verification;
- UI workflows and interaction artifacts;
- orchestrated pipelines using `.agents/workflows/`;
- multi-agent demonstrations in isolated workspaces.

Required adapter: `agents.md`, `.agents/skills/`, `.agents/workflows/`.

## GitHub Copilot or repository-native agents

Use for:

- issue/PR-oriented bounded tasks;
- CI diagnosis;
- code suggestions and review support;
- low-risk repository automation.

Required adapter: `.github/copilot-instructions.md` and root governance.

## Other harness admission

Before use, record:

- instruction discovery mechanism;
- tool, network and sandbox model;
- secret handling;
- repository write behavior;
- subagent/handoff support;
- logging and evidence capability;
- kill/stop control;
- version and owner.

Unknown harnesses remain read-only until evaluated.
