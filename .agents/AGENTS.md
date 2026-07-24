# bOPEN Agent Constitution (SKEL-P0 draft)

**Status:** Draft; preparation-only; not an authority grant
**Work item:** SKEL-P0-CONST-01
**Phase:** PG-P0
**Owner:** Engineering Authority
**Checker:** Independent checker required for any implementation candidate

This directory defines runtime-facing role contracts and the SKEL-P0 loop. It is a
procedural contract, not a permission system. Agents remain governed principals;
skills and prompts never grant permission, entitlement, tenant access, approval,
merge, release, deployment, activation, or production authority.

## Non-negotiable controls

- One authorized work item per isolated worktree; record exact base/head/tree SHAs.
- Maker and checker MUST be different vendor/session identities and MUST NOT edit
  each other's worktree or self-accept their own bytes.
- Draft contracts remain `status: draft`; signed registers, dockets, ledgers and
  PG-G0 outcomes are append-only and byte-frozen unless a separately authorized
  work item says otherwise.
- Tenant context, entitlement, authorization, tool calls and approvals are
  independently revalidated. A skill or prompt cannot elevate authority.
- Missing authority, wrong base, dirty custody, scope creep, unavailable evidence,
  failed validation, or provenance gaps are fail-closed stops.
- Production implementation, migration, merge, push, release, deployment, runtime
  activation, secret use and plugin/MCP enablement require attributable Human
  Authority and their own evidence.

## Role and loop contracts

- [TEAM.md](TEAM.md) defines the bounded roles and outputs.
- [LOOP.md](LOOP.md) defines the inspect-plan-build-review-validate-handoff cycle.
- `roles/` contains provider-neutral role prompts.
- `playbooks/` contains repeatable procedures; they do not authorize execution.
- `checkpoints/` contains evidence questions for each lifecycle checkpoint.

The current artifact is a draft preparation surface. It becomes effective only after
an attributable authority accepts the bounded work item and its exact evidence.
