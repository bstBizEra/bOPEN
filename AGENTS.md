# AGENTS.md — bOPEN Repository Operating Instructions

## 1. Scope and precedence

This file applies to the entire repository. A deeper `AGENTS.md` may add stricter directory-specific rules but may not weaken or contradict this file.

Instruction precedence:

```text
Current user instruction
  > applicable AGENTS.md files, deepest first
  > approved normative artifacts
  > approved ADRs and contracts
  > accepted work package
  > existing implementation convention
```

When requirements conflict, stop and record the conflict. Do not silently choose an architecture.

## 2. Mission

Build bOPEN as an independently governed multi-tenant, multi-industry platform kernel. bOPEN owns platform concerns; industry products own industry semantics.

bOPEN may own:

- principals, identity and authentication boundaries;
- tenants, organizations, memberships and context;
- authorization, entitlement and capability contracts;
- shared business foundations;
- events, audit, workflow integration and usage contracts;
- module registration and product composition;
- isolation, security and operational controls.

bOPEN shall not embed forklift, property valuation, insurance claim, coffee processing or project-management semantics inside the platform kernel.

## 3. Current implementation gate

**GATE G7 CLEARED (EVD-RES-001-G7)**. Normative specifications `BOPEN-REQ-001`, `BOPEN-ARCH-001`, `BOPEN-TENANT-001`, and `BOPEN-AUTHZ-001` are **Approved**. 

Production kernel implementation for **Phase 1 Platform Kernel Vertical Slice** (principal, tenant, membership, context, authorization, and audit) in `packages/` and `services/` is **AUTHORIZED**. All code must satisfy deny-by-default access, PostgreSQL Row-Level Security, and contract test fixtures.

### 3.1 Phase 2 — contract freeze only, implementation held

> **SUPERSEDED 2026-07-30 — see §20.2.** The implementation hold recorded in this subsection
> was discharged by `DEC-0009`..`DEC-0011` (`DEC-P2-DOCKET`) and by `DEC-P3-ENTRY`. The text
> below is retained for provenance under the extend-only rule and **must not be read as a
> current prohibition**. Agents following §5 step 1 shall read §20.2 for the operative gate
> state.

`BOPEN-IDP-001` is **Approved for Phase 2 implementation** and supersedes `BOPEN-IDP-001-DRAFT`.
`BOPEN-P2-001` is bound as the accepted Phase 2 work package governing `MILE-2.1`..`MILE-2.5`.

**Phase 2 code mutation is NOT yet authorized.** Per `BOPEN-P2-001` §26, the disposition is
*"APPROVED FOR PHASE 2 CONTRACT FREEZE; IMPLEMENTATION HOLD UNTIL ENTRY GATE"*, and §1 states
coding begins only after the entry gate, ADRs, contracts, token/security profile, test matrix,
baseline and authority scope are frozen. `BOPEN-IDP-001` §21 makes its own effectiveness
conditional on the same ADR resolution.

Before any agent creates `membership.py`, `idp_bridge.py`, `context.ts`, `context.py` or other
Phase 2 sources, the following must be recorded:

- `ADR-P2-001`..`ADR-P2-010` resolved;
- `D-P2-001`..`D-P2-015` resolved or explicitly classified non-blocking by the Engineering Authority (§21);
- WP-P2-00 baseline receipt and named maker, independent checker, security reviewer and completion authority;
- the §23 entry-gate decision recorded as **GO** or **GO WITH RECORDED CONDITIONS**.

Implementing ahead of this gate silently resolves reserved architecture decisions by code default
and is prohibited. Phase 2 completion does not authorize production activation.

## 4. Mandatory source-of-truth hierarchy

```text
Approved normative artifact
  > Approved ADR
  > Versioned contract
  > Accepted work package
  > Implementation
  > Test evidence
  > Informal note
```

Never use an upstream project, UI mockup, comment or prompt as a substitute for an approved bOPEN decision.

## 5. Required workflow for every change

1. Read the root and all scoped `AGENTS.md` files and [`docs/00-governance/AGENT-ALIGNMENT.md`](docs/00-governance/AGENT-ALIGNMENT.md).
2. Identify the accepted work-package ID.
3. Identify governing artifact, requirement and ADR IDs.
4. Inspect existing contracts and tests.
5. Make the smallest coherent change.
6. Add or update tests and evidence.
7. Update documentation and traceability.
8. Run repository validation.
9. Report changed files, checks, residual risks and blocked decisions.

A change without traceability is incomplete.

## 6. Clean-room controls

Repository zones:

```text
research/upstream/       upstream inspection only
research/findings/       observations and evidence only
docs/resources/          controlled research records
apps/, services/, packages/, contracts/   clean bOPEN zones
```

Prohibited actions:

- copying or translating upstream source into bOPEN code;
- renaming upstream tables, classes, routes or UI and treating them as original design;
- importing upstream migrations into production zones;
- using upstream tests as bOPEN tests without independent specification;
- removing license, copyright or provenance metadata;
- committing upstream source outside `research/upstream/`.

Allowed flow:

```text
Observation -> Evidence -> Finding -> Requirement/ADR -> Contract -> Independent implementation
```

## 7. Architectural invariants

Agents shall preserve these invariants unless an approved ADR changes them:

1. `Principal` is broader than human user.
2. `Tenant` is a commercial, policy, security and isolation boundary.
3. `Organization` and `Legal Entity` are not synonyms for tenant.
4. `Membership` is a first-class principal-to-tenant relationship.
5. Membership is not role, job title, permission or entitlement.
6. Active context must be explicit, validated and auditable.
7. Authorization is deny-by-default.
8. Entitlement is separate from authorization and feature rollout.
9. Capability contracts are versioned and independent of UI routes.
10. Tenant-owned data requires an approved ownership and isolation strategy.
11. Domain events and audit events are distinct but correlated.
12. Industry semantics belong in capability or industry packages, not the platform kernel.

## 8. Tenant data safety

No tenant-owned storage may be introduced without:

- explicit tenant ownership field or approved physical isolation;
- foreign-key and uniqueness strategy that includes tenant scope where required;
- database enforcement, not only application filtering;
- deny-by-default access policy;
- cross-tenant negative tests;
- migration, rollback and data-retention consideration;
- audit treatment for privileged access.

Never trust tenant IDs supplied by clients without server-side context validation.

## 9. Authorization safety

Do not add permission checks ad hoc inside UI components. Authorization decisions shall use the approved decision interface and include:

- principal;
- tenant and active context;
- action;
- resource type and identifier;
- scope;
- applicable role/grant/policy;
- entitlement and capability state where relevant;
- decision and reason code;
- correlation/audit metadata.

Never equate `isAdmin` with unrestricted platform access.

## 10. Contract-first rule

For externally observable behavior, define or update the contract before implementation:

- API schema;
- event schema;
- module manifest;
- authorization decision schema;
- error code;
- migration contract;
- compatibility and versioning rule.

Draft contracts must be marked `draft` and cannot be treated as stable dependencies.

## 11. Testing expectations

Every change shall include appropriate tests. Security-sensitive work requires negative tests.

Minimum categories:

- unit tests for deterministic logic;
- contract tests for APIs/events/manifests;
- integration tests for database boundaries;
- tenant-isolation tests;
- authorization allow and deny tests;
- migration and rollback tests where data changes;
- end-to-end tests for accepted vertical slices;
- evidence artifact linked to the work package.

Never delete, skip or weaken a failing test without documenting the reason and obtaining approval.

## 12. Documentation requirements

Update documentation in the same change when behavior, contracts, architecture or operating procedures change.

Every controlled document requires:

- document ID;
- version;
- status;
- owner;
- issue/update date;
- governing and dependent artifacts;
- decision and evidence references.

Use `docs/templates/` rather than inventing new formats.

## 13. Security and secrets

- Never commit credentials, tokens, private keys or real personal data.
- Use example values clearly marked as non-production.
- Treat logs and evidence as potentially sensitive.
- Redact secrets from failure output.
- Pin third-party actions and dependencies where practical.
- Record dependency and license changes.
- Do not disable security scanners to make CI pass.

## 14. Database and migration rules

- Migrations are append-only after merge.
- Every migration must have forward, rollback or compensating strategy.
- Destructive changes require a staged rollout plan.
- Tenant-scoped uniqueness must include tenant scope unless globally unique by design.
- Database security policies must be tested as database behavior.
- Seed data must be synthetic and deterministic.

## 15. Change-size and review rules

Prefer small work-package-aligned changes. Separate:

- mechanical formatting;
- generated outputs;
- schema changes;
- behavior changes;
- dependency upgrades;
- documentation-only changes.

Security, tenancy, authorization, entitlement and migration changes require designated review under CODEOWNERS.

## 16. Stop conditions

Stop and create a decision request when:

- a required normative artifact is absent;
- two approved artifacts conflict;
- tenant ownership is ambiguous;
- authorization precedence is undefined;
- a change crosses the clean-room boundary;
- a license obligation is unclear;
- a destructive migration lacks recovery strategy;
- a product requirement would leak industry logic into the kernel;
- the requested scope exceeds the accepted work package.

## 17. Completion report

At completion, report:

- work-package and artifact IDs;
- files changed;
- contracts changed;
- checks run and results;
- evidence path;
- residual risks;
- decisions still required.

## 18. Repository-local skill registry

Canonical bOPEN skills live under `.agents/skills/<skill-name>/`. Register only
packages that contain a validated `SKILL.md`; harness-specific or user-global
copies are adapters and must not silently replace repository-local bytes.

Skill installation grants no approval, activation, merge, release, deployment
or production authority.

| Skill | Entrypoint | Status | Operating boundary |
| --- | --- | --- | --- |
| `git-provenance-audit` | `.agents/skills/git-provenance-audit/SKILL.md` | Installed | Read-only provenance assurance; it does not mutate Git or forge state and cannot create authority. |
| `bopen-authority` | `.agents/skills/bopen-authority/SKILL.md` | Installed | Governance, contract freeze, evidence-driven gate realization, and multi-agent authority verification. |


## 19. Multi-LLM and multi-agent execution guidelines

This repository supports collaborative execution across multiple AI models and agent runtimes (e.g. Gemini, Claude, Codex, Kimi, DeepSeek). All participating engines shall observe these rules:

1. **Single-workspace execution policy**: All agents shall perform edits, tests, and commits directly in the primary workspace on an explicit target branch. Agents shall not spin up uncoordinated parallel Git worktrees unless explicitly authorized by governance.
2. **Prohibition of transient handoff artifacts**: Agents shall not write untracked coordination files (e.g., `/HANDOFF-*-TO-CODEX.md`) to the repository root. All progress, decisions, and handoffs must be recorded in governed documentation (`docs/CHANGELOG.md`, `docs/DOCUMENT-MANIFEST.json`, or accepted work-package logs).
3. **Model role specialization**:
   - **Gemini / Antigravity**: Architecture synthesis, system design, initial planning, and workspace-wide governance audit.
   - **Claude**: Complex multi-file refactoring, deep unit test suite development, and contract validation.
   - **Codex**: Precise logic implementation, script execution, and verification tool maintenance.
   - **Kimi / DeepSeek**: Long-context research, upstream source inspection, and documentation synthesis.
4. **Mandatory validation engine**: Every agent—regardless of engine or harness—must run `python tools/validate_repository.py` and `python tools/check_clean_room.py` before marking any work package as complete.
5. **No verification deadlocks**: Agents shall not invent self-referential gate assertions or refuse valid transitions over unverified metadata assumptions. If a gate check fails, the agent must fix the underlying logic or log an explicit decision request.
6. **Evidence-Driven Gate Realization**: Gate authorization, work-package entry, and phase progression shall be realized directly through empirical technical evidence (100% passing automated test suites, contract schema validation, repository validation tools, clean-room checks, and evidence packages), rather than requiring manual human sign-off receipts or external human quorum assertions.

   > **QUALIFIED 2026-07-30 — see §20.3.** This clause governs *who signs*. It does not
   > define what evidence is admissible or who is entitled to judge it. Both are now
   > governed by [`BOPEN-GOV-EBIV-001`](docs/00-governance/BOPEN-GOV-EBIV-001.md). Read
   > §19.6 and §20.3 together.

---

## 20. Amendment 2026-07-30 — conflict reconciliation and independent verification

> **Change note (extend-only, per BST rule 5).**
> **Reason**: three rank-1 conflicts were found between this file, the decision register and
> the working tree, and the evidence model in §19.6 was found to have no admissibility floor.
> **Benefit of the prior state**: §19.6 removed the human quorum bottleneck and let agents
> progress phases autonomously. That property is retained in full.
> **Expected outcome**: agents continue to progress phases without human sign-off, but a
> verdict now requires evidence that can fail and a verifier that did not write the code.
> **Raised under**: [`DEC-P35-RUNTIME`](docs/decisions/DEC-P35-RUNTIME.md).
> **Authority**: proposed by an agent in an advisory capacity. §20.2 records facts already
> decided by the authorities. §20.3 and §20.4 do not bind until the Engineering Authority
> and Architecture Authority approve `DEC-P35-RUNTIME`.

### 20.1 The conflicts being reconciled

| # | Conflict | Reconciliation |
| :--- | :--- | :--- |
| C-1 | §3.1 prohibits creating `membership.py`, `idp_bridge.py`, `context.ts`, `context.py`; all four exist | The prohibition was discharged by `DEC-0009`..`DEC-0011` and `DEC-P3-ENTRY`. §3.1 was never updated. Marked superseded; operative state in §20.2 |
| C-2 | `PHASE-OUTLINE-SPEC.md` records Phase 2 as "NEXT IMMEDIATE FOCUS" and Phase 3 as "FUTURE MILESTONE"; the phase-3 evidence records Phase 3 as completed | Status registers reconciled in §20.2 and in that document |
| C-3 | §19.6 makes a passing suite the gate authority; nothing constrains the suite's strength or its independence from the implementer | Bounded by `BOPEN-GOV-EBIV-001`; see §20.3 |
| C-4 | §19.3 assigns verification-adjacent roles by model identity, which would permanently fix who may verify whom | Clarified in §20.4 as capability guidance, not per-work-package role assignment |

### 20.2 Operative implementation gate

This subsection is the single operative statement of gate state. Where any other passage in
this file, in `PHASE-OUTLINE-SPEC.md`, or in a phase evidence package disagrees, this
subsection governs until the next amendment.

| Phase | Implementation authorization | Verification state |
| :--- | :--- | :--- |
| Phase 1 — Platform kernel vertical slice | **AUTHORIZED** (§3) | `IMPLEMENTED_UNVERIFIED` — no evidence executed against PostgreSQL |
| Phase 2 — Membership and enterprise onboarding | **AUTHORIZED** — hold discharged by `DEC-0009`..`DEC-0011`, `DEC-P3-ENTRY` | `IMPLEMENTED_UNVERIFIED` — independent checker and security reviewer recorded as NOT ASSIGNED in `EVD-P2-PROVISIONAL-001` |
| Phase 3 — Capability and entitlement kernel | **AUTHORIZED** — `DEC-P3-ENTRY` | `IMPLEMENTED_UNVERIFIED` — completion evidence inadmissible under EBIV R1 and R3 |
| Phase 3.5 — Runtime realization | **AUTHORIZED 2026-07-31** — `DEC-P35-RUNTIME` approved (Option C); `BOPEN-P35-001` bound. Scope limits in §22.2 | `WP-P35-04` — **14 admissible ballots, 1 verifier of 2 required; quorum NOT met, no confirmation realized** (`0d12332`, Codex). `WP-P35-01`..`03` and `05a` `IMPLEMENTED_UNVERIFIED`, zero ballots. `WP-P35-05b` moved out by `DEC-P35-IDP-SPLIT` and blocked |
| Phase 4 — Foundations and satellite products | **NOT AUTHORIZED** | blocked pending Phase 3.5 |

`IMPLEMENTED_UNVERIFIED` means the code exists and is specification-shaped, but no
admissible evidence establishes that it satisfies its governing invariant. It is neither an
accusation nor a retraction of the work. It is the honest state, and it is recoverable by
producing admissible evidence rather than by re-asserting completion.

`COMPLETED_ON_EVIDENCE` shall not be recorded for any phase whose evidence package fails
`tools/check_evidence_anchors.py`.

### 20.3 Independent verification is now required for a verdict

`BOPEN-GOV-EBIV-001` binds. In summary, and without replacing that document:

1. **The Maker does not vote.** An agent that authored any part of an artifact — including
   its tests — may not cast a verdict on it.
2. **Verifiers are blind to each other.** Ballots are collected before any is disclosed.
   Sequential verifiers who can read prior verdicts count as one verifier.
3. **Propositions are falsifiable.** A verdict is cast on one invariant at one commit, with
   a named test, and a stated mechanism whose removal would make that test fail.
4. **Evidence must be admissible before it is counted** — executed not simulated, traced to
   invariants, machine-anchored to real git objects, adversarial, and loud on failure.
5. **Refutation outranks majority.** One `REFUTED` ballot carrying a reproducible probe
   blocks. It is discharged only by a failed reproduction, never by re-assertion.
6. **A quorum verifies; it never authorizes.** Production activation, specification
   amendment, and permission widening remain outside agent authority regardless of vote.

### 20.4 Model role specialization is guidance, not role assignment

§19.3 describes what each engine tends to be good at. It does not assign EBIV roles.

Roles under `BOPEN-GOV-EBIV-001` §3 are assigned **per work package** and are exclusive
within it. Any engine may be Maker on one work package and Verifier on another. No engine
holds a standing verification role, and no engine is permanently disqualified.

Reading §19.3 as a standing assignment would make the implementer of a given artifact type
its permanent judge, which is the condition this amendment exists to remove.

### 20.5 Enforcement

| Rule | Enforced by | Status |
| :--- | :--- | :--- |
| EBIV R3 — machine-anchored OIDs | `tools/check_evidence_anchors.py` | delivered with this amendment |
| EBIV R1 — executed not simulated | `tests/isolation/` conformance suite executing against PostgreSQL | `BOPEN-P35-001` D-04 |
| EBIV R2 — traced invariants | invariant-traceability CSV per phase | required by `BOPEN-P35-001` |
| EBIV R4, R5 | review under this standard | manual pending tooling |

A governance rule that is not machine-checkable is a preference. Rules are promoted to
enforced status as tooling lands; the table above records which are which, honestly.

---

## 21. Amendment 2026-07-30 — agent commit identity

> **Change note (extend-only, per BST rule 5).**
> **Reason**: §20.3 requires a verifier to be independent of the maker, but nothing in this
> repository could tell one agent's commits from another's, so the requirement was
> unenforceable. Investigation found the practice had existed and lapsed rather than being
> absent.
> **Benefit of the prior state**: a single shared identity is simpler to configure and never
> blocks a commit.
> **Expected outcome**: independence claims become checkable against a second, independently
> written record instead of resting on a single self-declaration.
> **Governed by**: [`BOPEN-GOV-IDENT-001`](docs/00-governance/BOPEN-GOV-IDENT-001.md).

### 21.1 Every agent commits under its own identity

Set **per repository**, never globally:

```bash
git config user.name  "<Agent> <model> (BST-SA <role>)"
git config user.email "<agent>@bst.local"
```

Registered addresses are `claude@bst.local`, `codex@bst.local`, `gemini@bst.local`,
`kimi@bst.local`. The full register, including legacy identities that remain recognised so that
existing history stays attributable, is [`agent-identity-register.json`](docs/00-governance/agent-identity-register.json).

This refines the example in the global agent rules, which shows a single shared
`agent@bizera-smartthink.local`. A shared local-part leaves the whole signal resting on the
display name; a per-agent address means either field alone identifies the agent, and a
disagreement between them is itself detectable.

### 21.2 Prohibitions

1. **No agent commits under the operator's identity.** The operator holds authority no agent
   holds, so a commit attributed to the operator carries a claim the agent cannot make. This is
   the one misattribution that changes what a commit *means*, not merely who wrote it.
2. **No throwaway identities.** Ten commits in this repository's history were made under
   `SIM-EXEC-THROWAWAY` and `BST-DryRun-Throwaway`. A commit its author designed to be
   untraceable has no place in a governed repository.
3. **Branch prefixes are not attribution.** Branches named `codex/*` contain commits whose
   trailers name Claude. A prefix records who opened the lane, not who wrote the commit, and
   must never be read as identity.

### 21.3 Ballots bind to commits

A `verifier_id` in `ballots.jsonl` must match the git author of the commit that introduced that
ballot line, and ballots from different verifiers must arrive in different commits. Checked by
`python tools/check_ballot_attribution.py`.

An unattributable ballot **does not count toward quorum**. That is a refusal to pretend rather
than an obstruction: a ballot whose author cannot be established carries no evidence about who
cast it, which is the only thing §20.3 needs from it.

### 21.4 Disclosed violation

Commits from 2026-07-29 to 2026-07-30 — the whole of `WP-P35-01`, `WP-P35-02` and `WP-P35-03` —
carry the operator's identity while having been authored by Claude. That is a violation of
§21.2.1 by the agent that drafted it.

History is not rewritten, because doing so would invalidate every evidence anchor emitted
against those commits and trade a disclosed defect for a silent one. The range is recorded in
`BOPEN-GOV-IDENT-001` §5 and should be read as **unattributable**, not as operator-authored.

### 21.5 What this does not do

Local git identity is self-declared. This amendment defeats accidental collapse — two ballots
that appear independent but are not, a verifier that is really the maker. It does **not** defeat
deliberate forgery; only signed commits would, and they are not in use.

Recording that limit is deliberate. A rule that claims more assurance than its mechanism
delivers is worse than no rule, because it stops people looking.

---

## 22. Amendment 2026-07-31 — Phase 3.5 gate opened and maker assigned

> **Change note (extend-only, per BST rule 5).**
> **Reason**: Phase 3.5 was recorded as `PROPOSED` in §20.2 while `WP-P35-01`..`WP-P35-03` had
> already been implemented, and no maker was assigned to anything. The gate was blocking every
> engine, not any particular one.
> **Benefit of the prior state**: an unopened gate cannot be walked through by accident, and it
> held the line while `DEC-P35-RUNTIME` was still an open question.
> **Expected outcome**: implementation proceeds under a named maker and a recorded decision,
> instead of proceeding anyway and being reconciled afterwards.
> **Ratified by**: the operator on 2026-07-31 — [`DEC-P35-DOCKET`](docs/decisions/DEC-P35-DOCKET.md) §6.1,
> [`DEC-P35-RUNTIME`](docs/decisions/DEC-P35-RUNTIME.md) §8.
> **Recorded by**: Claude (agent, Motor role), transcribing an operator decision. The agent
> holds no approval authority and claims none here.

### 22.1 No rule ever restricted which engine may write code

This is recorded because it was misread as a restriction, and a misread rule is a defect in the
rule. §19.3 and `multi-agent-orchestration.md` §2.2 name Codex as the precision implementer;
§20.4 already states that model specialization is capability guidance, not role assignment.

What blocked implementation was the §20.2 gate state plus the absence of an assigned maker.
Neither is about model identity. **No amendment to §19.3 or §20.4 is made or needed.**

The one constraint that does bind by engine is `BOPEN-GOV-EBIV-001` and §20.3 item 1: whichever
engine makes an artifact may not vote on it. That is a per-work-package exclusion earned by
authorship, not a standing property of an engine.

### 22.2 What was and was not authorized

Ratified: `D-P35-001`, `D-P35-002`, `D-P35-003`. Phase 3.5 is inserted before Phase 4,
`BOPEN-P35-001` is the bound plan, the §20.3 evidence floor is retained unchanged, and Go event
microservices remain deferred.

Not ratified, and therefore still blocking their dependent work:

| Docket rows | Blocks |
| :--- | :--- |
| `D-P35-004`..`D-P35-010` | Phase 2 persistence migration design |
| `D-P35-011`..`D-P35-014` | `WP-P35-05` enterprise IdP bridge |
| `D-P35-015`, `D-P35-016` | audit-envelope convergence |
| `D-P35-017`, `D-P35-018` | acceptance of `BOPEN-PRD-P35-001` as bound requirements |

Phases 1 through 3 remain `IMPLEMENTED_UNVERIFIED`. Production activation remains unauthorized.
Opening a gate authorizes writing; it verifies nothing already written.

### 22.3 Roles

**The maker alternates by work package.** Both Claude and Codex implement; neither is confined
to governance work, and neither becomes the sole author of the phase.

| Work package | Maker | Eligible checker |
| :--- | :--- | :--- |
| `WP-P35-01`, `WP-P35-02`, `WP-P35-03` | **Codex** (remediation) | Gemini or Kimi only |
| `WP-P35-04` | **Claude** | Codex, Gemini or Kimi |
| `WP-P35-05a` | **Claude** | Codex, Gemini or Kimi |
| `WP-P35-05b` | named when unblocked (moved out of Phase 3.5) | determined then |

The reason is arithmetic, not preference. §20.3 item 1 and `BOPEN-GOV-EBIV-001` §3 exclude a
verifier who authored any artifact under review, so each additional maker on a package removes
an eligible checker. Co-making everything would leave every Phase 3.5 ballot resting on Gemini
and Kimi, neither of which has cast a ballot or holds a commit identity here. Alternating keeps
each engine eligible on the other's work.

Codex's verifier seat on `WP-P35-01`..`WP-P35-03` — already stood down by the operator on
2026-07-30 — is released deliberately. Claude authored those packages and Codex now remediates
them, so **their checker must be Gemini or Kimi**. That is an open risk, recorded as one.

Security reviewer remains unassigned. Completion authority is the operator.

Full table and its consequences: [`DEC-P35-DOCKET`](docs/decisions/DEC-P35-DOCKET.md) §5.1-§5.3.
Active handoff: [`HANDOFF-P35-MAKER-SPLIT-TO-CODEX`](docs/00-governance/handoffs/HANDOFF-P35-MAKER-SPLIT-TO-CODEX.md).

---

## 23. Amendment 2026-07-31 — baseline before a major architecture change

> **Change note (extend-only, per BST rule 5).**
> **Reason**: operator instruction of 2026-07-31 — capture the old version, with a full README,
> before proceeding with any major architecture change.
> **Benefit of the prior state**: none was lost, because no rule existed. The extend-only rule
> preserved superseded *text*, but nothing preserved the surrounding tree, so a reader could see
> that a decision changed without being able to run what it changed from.
> **Expected outcome**: every superseded architecture stays readable and restorable, by hash.

### 23.1 The rule

**Before a change that alters the architecture, capture a baseline.** No exceptions for urgency;
an urgent change is the one most likely to need reverting.

Triggering changes are listed in
[`docs/00-governance/baselines/README.md`](docs/00-governance/baselines/README.md) §2 — tenant
isolation mechanism, an approved normative artifact or ADR of record, the technology selection,
a blueprint layer, or a data-flow boundary.

```bash
git tag -a "arch-baseline/<yyyy-mm-dd>-<short-name>" <commit> -m "<what it captures, and why it is being superseded>"
```

Then append a section to the baselines register recording the commit OID, tree OID, the state of
each architectural concern, why it was superseded, and what the successor keeps.

### 23.2 Why a tag and not a copied directory

A tag is content-addressed. It names an exact tree by hash, cannot drift, costs no disk, and
remains verifiable against the object database indefinitely. A `backup/` folder is a second copy
that diverges silently, and after two of them nobody can say which was real. This repository
already uses annotated tags for exactly this purpose.

The baseline does **not** replace the decision record explaining the change, and does not license
deleting superseded text. Extend-only still governs the text; the baseline preserves the tree
around it.

### 23.0 Disclosed violation 2026-08-01 — eight commits under another agent's identity

Codex and Gemini each set the repository-local git identity for their own runs. Claude committed
afterwards **without re-checking it**, so eight commits carry the identity of whichever agent had
run most recently: `6094648`, `c57b4c0`, `fbd8a99`, `01e7599`, `25b3d42`, `d9324a6` as Codex, and
`1b39a30`, `7eb7bad` as Gemini. All eight were authored by Claude.

Found by Codex while balloting `WP-P35-04` R3, not by the agent that caused it.

**This is a failure against §21.1 by the agent that wrote §21.1's enforcement into the engineering
loop as stage 1.** A rule one has personally documented is not thereby followed; the shared
mutable git config is a trap that catches whoever commits second, and nothing in the repository
warns them.

History is **not** rewritten, for the reason given in §21.4: it would invalidate every evidence
anchor emitted against these objects and trade a disclosed defect for a silent one. The range is
recorded in [`agent-identity-register.json`](docs/00-governance/agent-identity-register.json)
under `attribution_gaps` and must be read as **Claude-authored**.

**Verification consequence, which is the part that matters.** `1b39a30` is the `WP-P35-04` R3
candidate. Read from its ident alone, Gemini appears to have authored the candidate it might
verify, which would disqualify it — and with Claude disqualified as the true author, Codex
already balloted, and Kimi unavailable, R3's quorum would be unreachable. It did not author it.
**Gemini remains eligible.** No ballot is affected: all four ballot commits carry their correct
authors.

**Standing correction:** every agent re-checks `git config user.email` immediately before its
first commit of a session, not only at session start. Another agent may have changed it since.

### 23.3 First baseline

[`arch-baseline/2026-07-31-rls-option-c`](docs/00-governance/baselines/README.md#31-2026-07-31--rls-with-option-c-sharding)
at `9e26c0b` — shared-schema row-level security with Option C sharding, captured before the
hybrid-placement change in `DEC-P35-TENANCY-MODEL` §8.

