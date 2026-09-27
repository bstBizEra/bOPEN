# bOPEN Governance and Multi-Agent Delivery Pack v0.1

This repository-ready pack establishes the governance, agent operating model, goals,
schedule, skills, delivery loop, module allocation, evidence controls, and harness
adapters for the bOPEN BST multi-tenant platform program.

## Current approved bootstrap authority

`BOPEN-BOOT-001` v1.0 is the currently approved authority for repository bootstrap,
documentation controls, clean-room research separation, validation, and governed
architecture work. It does **not** authorize production implementation of the bOPEN
kernel.

The governance and delivery pack introduced here, including `BOPEN-GOV-001`, is
**PROPOSED / NO IMPLEMENTATION AUTHORITY** until independently reviewed and approved.
Proposed goals, schedules, agent models, loops, skills, technology choices, and design
artifacts are planning inputs only and do not replace `BOPEN-BOOT-001`.

## Production implementation gate

Production kernel implementation remains prohibited until all of the following are true:

1. BOPEN-RES-001 Gate G7 passes.
2. Applicable normative artifacts are approved.
3. A bounded implementation work package is accepted.
4. Required contracts and acceptance tests exist.

## Start here

1. Read `BOPEN-BOOT-001.md` for the approved bootstrap boundary.
2. Read `AGENTS.md`.
3. Review `docs/00-governance/BOPEN-GOV-001_v0.1.md` as a proposed operating model.
4. Confirm artifact status before relying on `GOALS.md`, `SCHEDULE.md`, or other pack files.
5. Select the applicable workflow from `LOOP.md` only within approved bootstrap scope.
6. Select skills from `SKILLS.md`; skills support work but do not grant authority.
7. Register the work item and isolated worktree before mutation.
8. Produce an evidence envelope before requesting acceptance.

## Pack structure

```text
AGENTS.md                         Canonical repository instructions
CLAUDE.md                         Claude Code adapter
.agents/ANTIGRAVITY.md            Antigravity-compatible team adapter
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
override `BOPEN-BOOT-001`, `AGENTS.md`, approved security and tenant-isolation controls,
approved ADRs, or release authority. Proposed artifacts, including `BOPEN-GOV-001`, do
not grant implementation, acceptance, promotion, deployment, or release authority.
