# AGENTOPS-P0-01 — Agent Engineering Control Plane and Model Routing (Proposal)

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Authorization source:** None yet. This proposal is **not** authorized by SIGNING-PASS-5, whose PG-P0 opening covers repository skeleton, draft contract shells, test-harness scaffolding and documentation. Execution requires a separate operator decision and binding into `SCHEDULE-REGISTER` `PG-P0.work_item_refs`.
**Accepted by/at:** Pending attributable Human Engineering Authority disposition
**Proposal author:** Claude (BST-SA Motor worker agent; `claude-opus-4-8`)
**Independent checker:** BST-Codex-Motor (must review the exact final SHA if this package is ever executed)
**Phase:** PG-P0 (candidate work item; not yet bound)
**Expiry:** 2026-08-21T00:00:00+07:00

## Why this package exists

Two external candidates delivered agent-operations content under the SKEL-P0-01 name:

- **SKEL-P0-01-A1** — dual-agent engineering control plane (43 files under `docs/agent-operations/`).
- **SKEL-P0-01-A2** — adaptive dual-provider model routing, stability and delivery control.

Both were reviewed and found **out of scope for SKEL-P0-01**, which is a repository *skeleton* package (zones, draft contract shells, package roots, test harness, skeleton validator). A1/A2 govern *how the agents operate* — meta-tooling, not the bOPEN platform skeleton. A1 was additionally built on the repository Initial commit rather than the governed PG-P0 substrate, and A2 amends A1 and presupposes A1 files that do not exist on the governed base.

This package re-homes that content so it can be authorized, built and reviewed on its own merits without contaminating the skeleton candidate.

**Source-input provenance:** A1's build report attributes its bytes to OpenAI GPT-5.6 Pro and records the declared Claude maker attribution as unverified; A2 arrived in the same delivery lineage. This proposal document is authored by Claude (`claude-opus-4-8`). No claim is made that any Claude or Codex runtime performed a maker or checker role it did not perform.

## Objective

Establish a governed, **disabled-by-default** agent engineering control plane and model-routing layer for the Claude–Codex maker/checker operating model — documentation, descriptors and fail-closed validators only, with no runtime activation.

## In scope

1. **Control plane (from A1):** project memory and rules; context scoping and compaction checkpoints; inspect-first plan mode; permission classes and checkpoints; reusable skill playbook; deterministic hook descriptors; **disabled** MCP tool and plugin catalogs; isolated specialist subagent profiles; Claude/Codex disjoint ownership with role switching; worktree, handoff and routine descriptors; bounded learn/skill-candidate loop.
2. **Model routing (from A2):** provider/profile aliases (`FAST`/`BUILD`/`DEEP`/`CONFORMANCE`); approved model registry binding each alias to an exact model ID, revision, configuration digest, tool set and context digest; job/risk classification; routing policy; model scorecard; run receipts; failover and escalation rules with bounded repair loops.
3. **Validators:** `tools/validate_agent_controls.py` and `tools/validate_model_routing.py`, dependency-free and LF-normalized (no raw-byte hashing), added to the `pnpm validate` chain **without removing or reordering any existing governance validator**.
4. **Negative tests** for every fail-closed rule (see acceptance criteria).
5. **Documentation and traceability:** work package, evidence, traceability manifest, append-only documentation-ledger entries with the document manifest rebound in the same commit.

## Out of scope

Production business logic; database migrations; enabling any MCP server, plugin, provider adapter, live endpoint or credential; runtime activation; merge, release or deployment; changes to signed PG-G0 outcomes, dockets, registers or root-control surfaces; modification of the SKEL-P0-01 candidate bytes; treating any model, agent or peer review as an approving authority.

## Allowed paths

`docs/agent-operations/**`, `tools/validate_agent_controls.py`, `tools/validate_model_routing.py`, `tests/**` (guard and negative tests only), `docs/` (status, manifest, evidence, work-package and changelog surfaces), `package.json` (validate-chain extension only).

## Prohibited paths

`docs/00-governance/registers/**` and `docs/00-governance/signing/**` (read-only), signed dockets and binding inventories, the five root-control surfaces (`Roadmap.md`, `Backlog.md`, `Master_Standards.md`, `Progress_Log.md`, `Recap_Today.md`), `research/upstream/`, secrets, and any **active** root `CLAUDE.md`/`AGENTS.md` adapter that would auto-activate agent behavior on checkout (templates only).

## Dependencies and sequencing

1. Operator authorization and binding into `SCHEDULE-REGISTER` `PG-P0.work_item_refs`.
2. SKEL-P0-01 accepted first (independent Codex exact-SHA receipt **and** Human Engineering Authority acceptance). This package must branch from the accepted substrate — never from an unaccepted candidate.

## Acceptance criteria

- Every artifact additive, `draft` and **disabled**; no signed byte changes; all catalogs disabled with zero live endpoints, credentials or enabled plugins; no active root adapter file.
- Full governed `pnpm validate` chain (all existing validators intact, plus the two new ones) and the complete test suite pass at the exact candidate SHA on a clean worktree.
- Negative tests deny, at minimum: enabled plugin; active root MCP configuration; inline MCP endpoint; overlapping module write paths; **same-provider maker and checker**; checker profile below the artifact's risk level; `FAST` profile on high-risk or final-conformance work; model/version change after candidate-SHA freeze; silent fallback or missing superseding receipt; final reviewer that authored bytes or repaired modules; and **claims of Claude/Codex execution without attributable run receipts**.
- Maker and checker are different providers, each with truthful attributable run receipts.
- Independent checker accepts the exact final SHA; two fresh non-authoring conformance reviewers where A2's final gate applies.
- Human Engineering Authority acceptance recorded before the control plane is treated as operative.

## Risks and rollback

Risk: agent-operations descriptors mistaken for active configuration. Control: mandatory `disabled` status, fail-closed validators, templates never placed at active root paths. Risk: scope creep back into the skeleton. Control: this package is separately bound; SKEL-P0-01 bytes are out of its allowed paths. Risk: model routing used to justify weaker review. Control: model confidence is never acceptance evidence; deterministic validators and exact-SHA checks decide. Rollback: revert the isolated candidate branch; no signed, runtime or skeleton state is touched.

## Completion record

Pending. This proposed record does not accept itself and grants no execution authority.
