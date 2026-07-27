# bOPEN Governance and Multi-Agent Delivery Pack v0.1

This repository-ready pack establishes the governance, agent operating model, goals,
schedule, skills, delivery loop, module allocation, evidence controls, and harness
adapters for the bOPEN BST multi-tenant platform program.

## Controlling baseline

- BOPEN-SYS-001 — bOPEN Final System Design v0.1
- BOPEN-P0-001 — bOPEN P0 Implementation Control v0.1
- BOPEN-GOV-001 — bOPEN Governed Platform, Product, Module and Delivery Operating Model v0.1

## Start here

1. Read `AGENTS.md`.
2. Read `docs/00-governance/BOPEN-GOV-001_v0.1.md`.
3. Confirm the active goal in `GOALS.md`.
4. Confirm the authorized phase and dates in `SCHEDULE.md`.
5. Select the applicable workflow from `LOOP.md`.
6. Select only approved skills from `SKILLS.md`.
7. Register the work item and isolated worktree before mutation.
8. Produce an evidence envelope before requesting acceptance.

## Pack structure

```text
AGENTS.md                         Canonical repository instructions
CLAUDE.md                         Claude Code adapter
agents.md                         Antigravity-compatible team adapter
GOALS.md                          Program goals and measurable outcomes
SCHEDULE.md                       Gate-based target schedule
LOOP.md                           Governed engineering and learning loop
SKILLS.md                         Skill policy and approved skill catalog
MODULES.md                        Module registry and harness allocation

docs/00-governance/               Normative governance and authority
docs/01-program/                  Goal, roadmap, schedule and scorecards
docs/02-agents/                   Agent roles, harness matrix and handoffs
docs/03-loop/                     Loop, state machine and review protocol
docs/04-skills/                   Skill lifecycle and machine-readable registry
docs/05-modules/                  Module contract, allocation and ownership
docs/06-evidence/                 Evidence envelope and verification matrix
docs/07-technology/               Technology baseline and freeze controls
docs/08-design/                   Product and design-system governance
docs/09-operations/               Session, worktree and cadence runbooks
docs/registers/                   Machine-readable control registers

.agents/skills/                   Cross-harness Agent Skills
.agents/workflows/                Antigravity workflow definitions
.claude/agents/                   Claude Code specialist subagents
.claude/rules/                    Claude path- and topic-scoped rules
.github/copilot-instructions.md    GitHub Copilot adapter
templates/                        Work item, decision and module templates
```

## Authority rule

Harness-specific files are adapters. They may narrow scope but may not weaken or
override `AGENTS.md`, BOPEN-GOV-001, security policy, tenant-isolation controls,
approved ADRs, or release authority.
