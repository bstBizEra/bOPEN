# SKEL-P0-01-A2 — Adaptive Dual-Provider Model Routing, Stability and Delivery Control

**Version:** 0.1
**Status:** Proposed; disabled; not accepted
**Parent:** SKEL-P0-01-A1 — dependency unresolved on the governed lineage
**Work package:** SKEL-P0-01
**Phase:** PG-P0 preparation/review only
**Owner:** Engineering Authority
**Maker:** BST-Codex-Motor
**Independent checker:** Claude, fresh read-only exact-SHA review required
**Issued:** 2026-07-24
**Source:** Operator-supplied `SKEL-P0-01-A2_Model_Routing_Recommendation.md`
**Source SHA-256:** `f00d302bbd16e11ef15dd5d386ffc6d2d41b056a10bd78ff60dcbd8a7f7dbb56`
**Source bytes:** 13665
**Candidate base:** `ca92c7c9796824213fa68db280131bc87e6b2cfb`
**Evidence:** EVD-SKEL-003

## Disposition

Record the supplied recommendation as a governed A2 amendment proposal. It is documentation-only, disabled and non-effective. It does not install a provider, select a live model, enable MCP or plugins, grant tool access, modify runtime configuration, accept SKEL-P0-01, or authorize merge, release, deployment or activation.

The supplied A1 delivery bundle identifies base `9a80f9d042f1ed176c9939bae57953443d0c5964`, parent candidate `f900c69c64f89981313a49a642ef4430888430f7` and A1 candidate `6d0cdced9a76957961d7424920dfad91268a41f6`. Those objects are not the governed PG-P0 skeleton lineage used here. A1 therefore remains an unresolved dependency and MUST NOT be imported, promoted or treated as accepted by this A2 record.

## Objective and routing order

Amend the proposed Claude–Codex operating model so each provider uses an evaluated, approved model profile suited to the job while preserving exact-SHA review, deterministic verification, attribution, maker/checker separation and human authority.

```text
Task and risk classification
  -> provider suitability
  -> approved model profile
  -> exact model/version/configuration binding
  -> bounded execution
  -> deterministic verification
  -> cross-provider review
  -> exact-SHA delivery evidence
```

Optimization order is authority and safety eligibility, capability/tool compatibility, quality and defect containment, stability and repeatability, latency, then cost. Speed MUST NOT override safety, quality, tenancy, authorization or evidence gates.

## Normative rules

1. Provider, exact model, agent identity and role MUST be distinct fields.
2. Durable controls MUST use governed aliases such as `claude.fast`, `claude.build`, `claude.deep`, `codex.fast`, `codex.build`, `codex.deep` and `codex.conformance`.
3. Every run MUST bind its alias to an exact provider model ID, revision, configuration digest, tool catalog, context-pack digest and source SHA.
4. Silent substitution, downgrade and provider failover are prohibited. A change requires a checkpoint and a superseding run receipt.
5. A faster or less expensive model MAY be selected only after mandatory capability, risk, compatibility and quality floors pass.
6. Maker/checker separation MUST remain cross-provider. A checker reviews a frozen exact SHA read-only and MUST NOT repair maker bytes.
7. Model confidence is not acceptance evidence. Deterministic validators, tests, manifests, negative tests and exact-SHA checks decide deliverability.
8. A model, tool or skill never grants permission. Tenant context, permission, tool grants and human authority remain external controls.
9. High-risk work MUST NOT use a fast profile as maker or final checker.
10. Model mappings MUST be promoted, suspended or revoked through evaluation evidence, not preference.

## Governed profiles

| Profile | Intended work | Mutation | Prohibited use |
|---|---|---:|---|
| `FAST` | Inventory, search, classification, collation, formatting and guardable mechanical work | Read-only by default | Architecture authority, security decisions, promotion, final conformance |
| `BUILD` | Code, schemas, validators, tests, refactors, package wiring and operating docs | Assigned worktree only | Unreviewed high-risk security or governance disposition |
| `DEEP` | Architecture, authorization, tenant isolation, threat analysis and difficult cross-module review | Assigned maker worktree or read-only checker | Low-value bulk work eligible for a lower profile |
| `CONFORMANCE` | Fresh final exact-SHA review and delivery verdict | Read-only only | Repair, candidate authorship or human approval |

## Default module ownership

| Round | Claude maker / Codex checker | Codex maker / Claude checker |
|---:|---|---|
| 1 | M01 Project Memory and Rules — `claude.build` or `claude.deep` | M06 Deterministic Hooks — `codex.build` |
| 2 | M02 Context Scope and Compact — `claude.deep` | M07 MCP Tools and Live-Data Control — `codex.build`, or `codex.deep` when security-sensitive |
| 3 | M03 Inspect-First Plan Mode — `claude.build` | M08 Plugin Bundles and Validators — `codex.build` |
| 4 | M04 Permission and Checkpoints — `claude.deep` | M10 Agent-Team Manifests and Coordination Guards — `codex.build` |
| 5 | M05 Reusable Skills Playbook — `claude.deep` | M11 Worktrees and Routines — `codex.build` |
| 6 | M09 Isolated Specialist Design — `claude.deep` | M12 Goal→Verify→Repeat→Learn Automation — `codex.build` or `codex.deep` |

The split MAY change only through an approved scorecard with maker/checker separation re-established before writes.

## Review and integration controls

Each maker freezes its exact SHA. The other provider reviews read-only at an eligible profile. Findings return to the original maker, who alone repairs its worktree. The same reviewer rechecks the corrected exact SHA. Both modules pass before integration.

I01 semantic control-plane integration is normally Claude maker with Codex checker. I02 deterministic repository integration is normally Codex maker with Claude checker.

The final gate requires fresh, read-only BST-Codex-Conformance and BST-Claude-Conformance reviews of the same SHA. Neither reviewer may have authored candidate bytes or repaired modules. Human Engineering Authority acceptance remains separate.

## Deterministic procedure

1. Inspect repository, rules, scope, authority and candidate state.
2. Classify job type, risk, mutation class, context size and tool requirements.
3. Query the approved registry for eligible provider/profile bindings.
4. Reject routes without current evaluation, required tools, context or risk level.
5. Rank eligible routes by quality, stability, latency and then cost.
6. Freeze provider, exact model, configuration, tools, context digest, worktree and source SHA.
7. Emit a model-run receipt before mutation.
8. Execute within step, time, tool-call and repair-loop budgets.
9. Run deterministic checks.
10. Freeze the candidate SHA and hand off cross-provider.
11. Record review, repair, recheck and final evidence.

## Failover

- FAST ambiguity or mandatory-check failure: use BUILD from a checkpoint with a new receipt.
- BUILD failing two bounded repairs: escalate to DEEP and stop the unbounded loop.
- Security, tenancy, authorization or supply-chain concern: escalate immediately to DEEP and add negative tests.
- Provider outage/tool incompatibility: stop and require an explicit assignment update.
- Maker failover: record mixed authorship or restart from the last clean SHA and appoint a fresh checker.
- Exact model unavailable: stop and issue a superseding receipt; never substitute silently.
- Critical policy or cross-tenant violation: quarantine the candidate and suspend the route.

## Delivery and scorecard

A deliverable requires complete artifacts, passing deterministic and negative checks, zero unresolved critical/high findings, a frozen SHA, exact-SHA manifest/evidence, accepted cross-provider review, documented rollback, model/configuration attribution and explicit pending human acceptance where applicable.

Each provider/profile binding MUST record its exact model/revision, job/risk classes, tool/context compatibility, evaluation digest, pass and defect-escape rates, schema/provider/tool failures, duration/tool/context metrics, review finding rate, evaluation time and lifecycle status. Any cross-tenant disclosure or unauthorized mutation immediately suspends the route.

## Proposed repository additions

Future authorized implementation may add draft model routing, registry, job classification, policy, scorecard, run receipt, failover and evaluation artifacts under `docs/agent-operations/models/`, plus `tools/validate_model_routing.py` and `tests/unit/test_model_routing.py`. This A2 record does not create or enable them.

A future validator MUST reject missing exact bindings, unapproved routes, FAST high-risk/final work, same-provider maker/checker, under-qualified checkers, silent fallback, post-freeze model drift, authoring final reviewers, missing digests, unbounded retries, cost-first routing and unattributed execution claims.

## Entry and exit gates

A2 remains `draft`, `disabled` and `planned-not-executed` until:

1. a governed-lineage A1 candidate is prepared and independently accepted;
2. exact provider/model bindings exist in an approved registry;
3. representative evaluations run for both providers;
4. routing and failover validators pass;
5. attributable maker/checker receipts exist;
6. both fresh final conformance reviewers accept one exact final SHA; and
7. Human Engineering Authority records acceptance.

## Change note

**Reason:** Introduce evidence-based model selection without weakening dual-provider review.
**Benefit of old phase:** A1’s conceptual dual-agent separation established useful maker/checker and exact-SHA controls.
**Expected outcome:** A governed, provider-neutral routing layer selects the smallest eligible model while deterministic evidence and human authority remain decisive.
