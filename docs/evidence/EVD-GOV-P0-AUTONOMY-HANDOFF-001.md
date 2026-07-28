# EVD-GOV-P0-AUTONOMY-HANDOFF-001 — Bounded Claude/Codex Collaboration

**Document ID:** EVD-GOV-P0-AUTONOMY-HANDOFF-001
**Version:** 0.1-draft
**Status:** Draft; advisory only; independent review pending
**Source:** Read-only inspection of the Gov P0 control surfaces and the isolated handoff worktree
**Recorded at:** 2026-07-24T03:42:18+07:00
**Agent ID:** BST-Codex-Motor (bounded handoff maker subagent)
**Work package:** Gov P0 autonomy handoff (preparation/review only)
**Governing references:** `Roadmap.md`; `Master_Standards.md`; `AGENTS.md`; `docs/work-packages/SKEL-P0-01.md`; `docs/00-governance/agent-governance.md`; `docs/00-governance/agent-role-catalog.md`; `docs/templates/handoff-template.md`

## Purpose and bounded outcome

This record describes a safe operating pattern for Claude and Codex to collaborate on
bounded Gov P0 work items. “Autonomous together” means that the agents may decompose,
implement, test, inspect and hand off work without pausing for a human at every
mechanical step. It does not delegate human authority, widen an accepted work package,
or make a draft contract, evidence record or exact-SHA verdict effective.

The current phase is `PG-P0 ACTIVE` with preparation and independent review in scope;
the `SKEL-P0-01` work package remains **proposed; not accepted**. `Roadmap.md` records
production implementation, migration, merge, release and runtime as unauthorized.

## Exact substrate and custody

| Field | Observed value |
|---|---|
| Worktree | `C:\laragon\www\bopen-worktrees\gov-p0-autonomy-handoff` |
| Branch | `codex/GOV-P0-autonomy-handoff` |
| Exact base / current HEAD | `29949f460345a55b8f8079cad802d6ca85cbe46e` |
| Exact base tree | `463901cf45f3d264a392484a95dfaad139be7339` |
| Base ancestry check | `git merge-base --is-ancestor 29949f460345a55b8f8079cad802d6ca85cbe46e HEAD` → exit `0` |
| Initial custody | Clean worktree before this draft artifact was written |
| Changed file in this handoff | `docs/evidence/EVD-GOV-P0-AUTONOMY-HANDOFF-001.md` only (uncommitted draft) |

The handoff must be exchanged by exact worktree and branch. A receiver must not infer
that a mutable workspace, another branch, or a short SHA is the candidate. The maker
must state the final candidate SHA and tree after committing; the checker must reproduce
from that exact SHA in a fresh, short-path checkout.

## Collaboration protocol

1. **Orchestrator / parent:** bind one work item, exact base SHA, expiry, allowed paths,
   prohibited paths, maker, checker, evidence destination and rollback before spawning a
   subagent. A subagent is a bounded worker, not a new authority.
2. **Claude maker:** work only in the assigned isolated worktree; implement the accepted
   preparation scope; keep contract shells `status: draft`; run the required checks; and
   hand off the exact candidate SHA, tree, commands, results and residual risks. Claude
   may not self-accept the work package or promote a draft.
3. **Codex checker:** use a different vendor/session and author none of the reviewed
   bytes. Fetch or open the exact candidate in a fresh clean worktree, verify ancestry,
   scope, append-only controls, negative tests and the complete validation chain, then
   issue `ACCEPT_EXACT_SHA` or `REJECT_EXACT_SHA` with file/line findings. A technical
   acceptance is evidence only.
4. **Evidence handoff:** the maker and checker records are append-only evidence tied to
   exact commits. A receiver acknowledges custody of the bounded work only; it does not
   approve architecture, accept a work item, pass PG-G0, or authorize execution.
5. **Human gate:** only the attributable Human Engineering Authority may accept the
   work package or authorize any later implementation, merge, release, deployment,
   activation or runtime action. Those actions require their own bound authority and
   evidence; silence, agent consensus or green tests cannot substitute for them.

## Separation and fail-closed controls

- Maker and checker identities, sessions and worktrees must remain distinct. If the
  maker equals the checker, exact base is missing, or provenance is unavailable, the
  checker must reject rather than conditionally accept.
- Allowed work is limited to the accepted package. For `SKEL-P0-01`, this means
  additive skeleton directories, draft shells, guard-test scaffolding, validator
  extension and documentation/evidence surfaces. Agent-operations or a dual-agent
  control plane belongs to a separately proposed `AGENTOPS-P0-01` package and must not
  be bundled here.
- Prohibited mutations include `docs/00-governance/registers/`, signed passes and
  binding inventories, PG-G0 outcomes, runtime/business code, secrets, migrations,
  production configuration, and protected-branch history. Existing ledgers and status
  records remain append-only; no overwrite or history rewrite is implied by a handoff.
- A checker must adversarially prove that kernel-zone business logic and draft-to-active
  promotion are denied by the validator. A passing positive path without these denials
  is insufficient.
- Validators that hash files must bind repository bytes (LF normalization or a
  repository `.gitattributes` policy) so the result is portable across Windows and
  other checkout environments. A line-ending-dependent result is a blocker.

## Required exact-SHA handoff envelope

The maker handoff must include:

- work-package ID and governing requirement/ADR references;
- maker identity/session and explicit statement of bytes authored;
- checker identity/session, independence statement and intended fresh-checkout path;
- exact base SHA, candidate SHA, parent and tree SHA;
- clean-worktree attestation, allowed/prohibited path diff and rollback plan;
- every command, exit code and material output (including skipped/unrun checks);
- manifest/evidence hashes where applicable, negative-fixture results and residual risks;
- `truth_status`, `authority_status`, `implementation_status`, `risk_class` and
  `authorization_required` fields.

The checker disposition must be exactly `ACCEPT_EXACT_SHA` or `REJECT_EXACT_SHA`.
`ACCEPT_EXACT_SHA` means only that the exact bytes satisfy the technical review; it
does not promote, merge, push, release, deploy, activate or authorize runtime use.

## Current status and blocked items

```yaml
truth_status: observed_current_state
authority_status: advisory_only
implementation_status: preparation_only
risk_class: governance_high
authorization_required:
  - Human Engineering Authority must accept the proposed work package before it is treated as a stable base.
  - Independent exact-SHA checker must review the final maker candidate; this draft is not that verdict.
  - Any production implementation, merge, release, deployment, activation or runtime flag requires a separate attributable operator decision.
blocked_items:
  - SKEL-P0-01 Accepted by/at remains pending.
  - Final maker candidate SHA and maker evidence are not supplied in this handoff.
  - Human Engineering Authority disposition is absent.
  - Agent-operations/dual-agent control-plane work is out of scope and requires AGENTOPS-P0-01.
```

## Self-certification boundary

```yaml
self_certification:
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  ready_for_operator_review: true
```

This record does not certify its own work package, accept a candidate, or authorize any
mutation. It is ready only for an operator and an independent checker to review within
the controls above.

## Commands run (read-only / markdown hygiene)

All commands were run from the isolated worktree on 2026-07-24. No repository validator,
test suite, register writer, manifest writer, commit, merge, push, release, deployment or
runtime command was run for this documentation-only handoff.

| Command | Result |
|---|---|
| `git status --short --branch` | `## codex/GOV-P0-autonomy-handoff`; clean before this file was added |
| `git rev-parse HEAD` | `29949f460345a55b8f8079cad802d6ca85cbe46e` |
| `git rev-parse HEAD^{tree}` | `463901cf45f3d264a392484a95dfaad139be7339` |
| `git merge-base --is-ancestor 29949f460345a55b8f8079cad802d6ca85cbe46e HEAD` | exit `0` |
| `git diff --check -- docs/evidence/EVD-GOV-P0-AUTONOMY-HANDOFF-001.md` | exit `0` after writing this file; no whitespace errors |

## Residual risks and rollback

The autonomy pattern can still be misused if a parent omits an exact base, accepts a
mutable path as evidence, conflates checker acceptance with authority, or allows a
subagent to cross the package boundary. These are open governance risks until the
operator accepts a concrete package and a different-session checker records an exact
receipt. The safe rollback before acceptance is to discard this isolated branch/worktree;
no protected, signed, runtime or production state is touched.
