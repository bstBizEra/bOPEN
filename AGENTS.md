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
| Phase 3.5 — Runtime realization | **AUTHORIZED 2026-07-31** — `DEC-P35-RUNTIME` (Option C); `BOPEN-P35-001` bound | **Closing under the two-agent profile (`BOPEN-GOV-EBIV-001` §6.5, ratified 2026-08-02).** `WP-P35-01`..`03` `CONFIRMED_UNDER_TWO_AGENT_PROFILE` (one verifier + operator disposition; rerun-evidence risk recorded). `WP-P35-04` **BLOCKED** — two standing refutations, accepted with known defects. `WP-P35-05a` R4 awaits one ballot. `WP-P35-05b` moved out by `DEC-P35-IDP-SPLIT` |
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


---

## 24. PROPOSED (not in force) — Analytical Reasoning, First-Principles Planning & Refusal Matrix Standards

> **STATUS: `PROPOSED` — NOT IN FORCE.** This section carries **no** normative authority. It is recorded
> as a proposal only and binds nothing until an explicit operator authorization with verifiable
> provenance is recorded in Git (per `BOPEN-GOV-EBIV-001` §2: an agent has no authority to make a
> normative specification binding by itself).
>
> **Provenance note.** This content was drafted as "§26" inside a 2026-08-05 amendment set whose
> authority-expanding parts — "§24 Delegated Human Governance Authority", "§25 Equal Governance
> Authority Parity", `DEC-GOV-AUTHORITY-PARITY`, `BOPEN-GOV-DELEGATION-001`, and the edit making
> Completion Authority an AI role — were **REJECTED by operator decision 2026-08-06** (fail-closed
> retained: an AI may not use its own authority to approve documents that expand AI authority). The
> reasoning/refusal-matrix standards below were separated out and are held as `PROPOSED` pending the
> operator's explicit, verifiable authorization.

### 24.1 First-principles & invariant-first analysis

For all non-trivial technical changes, architectural designs, or specification drafting, AI Agents
should begin with first-principles reasoning before writing code:

1. **Core Invariant Audit**: Identify all governing invariants (tenant isolation, PostgreSQL RLS, deny-by-default access, immutable identity, append-only audit history).
2. **Trade-off Analysis**: Explicitly evaluate design alternatives, documenting pros, cons, and residual risks.

### 24.2 Refusal Matrix & negative test design

AI Agents should explicitly formulate a **Refusal Matrix** defining inputs, boundary violations, invalid
state transitions, and cross-tenant leaks that the system **MUST reject loudly**. Negative test cases
derived from the Refusal Matrix should be implemented tests-first before code realization.

### 24.3 Structured 4-stage execution loop

1. **Stage 1 — Problem & Trade-off Analysis**: Establish invariants, trade-offs, and boundary scope.
2. **Stage 2 — Refusal Matrix & Plan**: Define explicit rejection criteria and test plan.
3. **Stage 3 — Tests-First Build**: Implement negative and positive tests before realization.
4. **Stage 4 — Empirical Verification**: Validate against automated suites (`validate_repository.py`, `check_clean_room.py`, canonical tests).

---

## 25. PROPOSED (not in force) — Governed Engineering Loop (the maker cycle)

> **STATUS: `PROPOSED` — NOT IN FORCE.** This section carries **no** normative authority and does not
> replace the in-force §5 workflow. It is recorded as a proposal only and binds nothing until an
> explicit operator authorization with verifiable Git provenance is recorded (per
> `BOPEN-GOV-EBIV-001` §2: an agent has no authority to make a normative specification binding by
> itself). It **describes** the governed maker cycle already practised across the disposed MILE-4.2
> foundations (Party, Money, Workflow, UOM, Party ContactPoint, Location); promoting it to a normative
> §5 revision is the operator's decision.

### 25.1 The loop

0. **Authorize-before-build.** A phase / foundation / work-package entry MUST be recorded in a `DEC`
   (e.g. `DEC-P4-ENTRY`) as an explicit operator decision **before** any build. A maker may not infer
   authorization from a verbal "start X"; an independent verifier fail-closes if the entry is unrecorded.
1. **Scope & invariants.** Identify the accepted work-package ID, the governing artifacts/ADRs, and the
   keystone invariant(s) the slice defends; define the **Refusal Matrix** — the inputs, boundary
   violations, invalid transitions, and cross-tenant leaks the system MUST reject loudly.
2. **Tests-first.** Write the negative (refusal) tests and the positive tests **before** the
   implementation.
3. **Migration + forced RLS.** New tenant-scoped tables get `ENABLE`+`FORCE ROW LEVEL SECURITY`,
   composite `(tenant_id, parent_id)` foreign keys, and append-only history with `ON DELETE RESTRICT`.
   **Register every new tenant-scoped table in BOTH `TENANT_SCOPED_TABLES` and the trial→paid
   `COPY_ORDER`** (parents before children) — the `INV-MIGRATE-COVERAGE-01` control fails the suite
   otherwise.
4. **Repository + bearer-gated endpoints.** All data access runs through `db.tenant_session`; there is
   no unscoped read of a tenant-owned table.
5. **Trace invariants (EBIV R2).** Every balloted proposition gets a row in
   `invariant-traceability.csv` mapping it to a named executed test.
6. **Maker submission.** Anchored to an exact candidate commit + blob SHAs. A passing suite carries no
   verdict weight (`EBIV` §8).
7. **Independent verification.** An eligible verifier that authored **no** artifact under review (not
   the maker) independently probes the claims and records a ballot in `ballots.jsonl` (admissibility
   R1–R5). Verdicts are read from the ballot **object**, never from prose.
8. **Operator disposition.** The **Completion Authority** — Human or named authority, **not** an agent
   role — accepts or rejects the assembled verdict and acknowledges the disclosed-risk record.
   Disposition is reserved to the operator; the maker never self-disposes.

### 25.2 Identity hygiene

Reset `git config user.email` to the acting agent's registered identity (`<agent>@bst.local`, §21.1)
**before every commit** — a shared workspace lets another agent's identity persist in the config.

---

## 26. PROPOSED (not in force) — URE-Loop adaptation: review lenses, feedback tiers, cost controls, ADR drafting, drift detection

> **STATUS: `PROPOSED` — NOT IN FORCE, EXCEPT §26.2.** This section carries **no** normative
> authority, does not replace the in-force §5 workflow, and does not amend §25. It is recorded as a
> proposal only and binds nothing until an explicit operator authorization with verifiable Git
> provenance is recorded (per `BOPEN-GOV-EBIV-001` §2: an agent has no authority to make a normative
> specification binding by itself).
>
> **QUALIFIED 2026-08-07 — §26.2 is in force.** The operator authorized the architecture & boundary
> lens as a working review role under
> [`DEC-URE-ARCHITECT-LENS`](docs/decisions/DEC-URE-ARCHITECT-LENS.md). §26.2 alone is promoted.
> §26.3, §26.4, §26.5, §26.8 and §26.9 remain `PROPOSED`; the ten §26.6 exclusions remain excluded;
> no identity was registered and no authority was conferred.
>
> **Provenance note.** Adapted from an external design document, *Unified Review Engineer Loop
> (URE-Loop)*, supplied by the operator on 2026-08-07 — first at **v0.4**, then superseded the same
> day by **v0.6**, which adds the Agentic ADR Engine (§26.8) and the Continuous State & Telemetry
> Reconciliation Engine (§26.9). Both intakes are recorded; this section reflects v0.6. An external
> design document is **not** a bOPEN source of truth (§4): it may not substitute for an approved
> artifact, ADR or contract. It is recorded here in adapted form. Ten of its mechanisms conflict with
> in-force rules and are recorded as **excluded** in §26.6 rather than silently dropped or silently
> adopted, per §1.
>
> **v0.9 supersedes v0.6 — see §27.** This section continues to govern the v0.4/v0.6 mechanisms
> unchanged. §27 covers only what v0.9 adds, and its §27.1 records that v0.9 restates this
> repository's own governance **inaccurately**: where an external document mirrors a `DEC` back at
> us, the `DEC` governs and the mirror is not evidence of anything.

### 26.1 What this adds, and what it does not touch

§25 already describes the governed maker cycle end to end (authorize → scope → tests-first →
migration → build → trace → submit → verify → dispose). URE-Loop contributes five layers that
§25 and [`BOPEN-ENG-LOOP-001`](docs/08-engineering/ENGINEERING-LOOP.md) do not describe:

| Layer | §26 | Sits inside |
| :--- | :--- | :--- |
| Multi-lens review panel | §26.2 | §25.1 step 7 — independent verification |
| Feedback-latency tiers | §26.3 | §25.1 steps 2–4 — the build inner loop |
| Token-cost controls | §26.4 | Any stage; constrained by §4 and §5.1 |
| ADR auto-detection & drafting | §26.8 | §25.1 step 1 and §16 — before the build |
| Desired-vs-actual drift detection | §26.9 | Outside the loop; feeds §16 decision requests |

It changes **no** gate, quorum rule, admissibility rule, or disposition authority. Where this
section and any in-force section disagree, the in-force section governs and this section is the
defect.

### 26.2 Review panel — lenses, not authority

> **IN FORCE 2026-08-07** under [`DEC-URE-ARCHITECT-LENS`](docs/decisions/DEC-URE-ARCHITECT-LENS.md).
> The operator seated the architecture & boundary lens as a working review role: findings only, no
> ballot, no registered identity, no authority. The operator's directive named **that lens only**;
> the security and performance lenses stay described-but-unseated until separately named, so this
> note is not read as seating all three. A persona was deliberately **not** added to
> `agent-identity-register.json` — see `DEC-URE-ARCHITECT-LENS` §3 for why, which binds future
> requests of the same shape.

The panel is a **set of probing lenses**, not a decision body. It supplies findings; `ballots.jsonl`
supplies verdicts.

| Lens | Probes | Services |
| :--- | :--- | :--- |
| Security & refusal | boundary violations, cross-tenant leaks, invalid transitions, deny-by-default gaps | §9, §25.1 step 1 Refusal Matrix, EBIV R4 |
| Architecture & boundary | kernel/industry separation, clean-room zones, contract compatibility, `tenant_session` discipline | §6, §7, §10, §25.1 step 4 |
| Performance & test quality | negative-test mutation survival, coverage of the traced invariants, migration/rollback cost | §11, EBIV R2 |

Binding constraints if this section is ever promoted:

1. A lens is **not** a verifier seat. Who may ballot is governed solely by EBIV admissibility
   R1–R5; a maker running all three lenses has produced findings and no verdict (EBIV §8).
2. Lenses run by the same agent, or by agents able to read each other's output, count as **one**
   verifier — the same collapse rule as sequential verifiers in `BOPEN-ENG-LOOP-001` §2.8.
3. Verdicts are read from the ballot **object**, never from panel prose, and never from a score.
4. One `REFUTED` ballot carrying a reproducible probe blocks regardless of what the other lenses
   report. There is no aggregation that discharges it; only a failed reproduction does.

### 26.3 Feedback tiers — convenience above, evidence below

| Tier | What runs | Admissible as evidence |
| :--- | :--- | :--- |
| 1 — editor | LSP diagnostics, type check, lint | **No** |
| 2 — inner loop | tests for the impacted module only | **No** |
| 3 — canonical | the §19.4 / `BOPEN-ENG-LOOP-001` §3 required check set | **Yes** |

The tiering is a latency convenience for the maker and nothing else. **No completion claim,
submission or ballot may cite a tier-1 or tier-2 result.** A selective run proves the selection was
correct and nothing about what it skipped, and the failure mode this repository has already seen —
a check that exits quietly being read as a pass — is exactly what a partial run reproduces at
scale. `CANNOT RUN` remains not a pass at every tier.

### 26.4 Token-cost controls, and the floor beneath them

Adopted as engineering practice: ordering prompts static→dynamic for prefix cache reuse; supplying
signature-level repository maps instead of raw source dumps; running broad searches in isolated
subagent contexts that return distilled summaries; emitting targeted search/replace diffs instead of
full-file rewrites; and cascading cheaper models onto mechanical stages.

Three floors that cost optimization may not cross:

1. **The §5.1 read is not prunable.** Root and all scoped `AGENTS.md` files plus
   `docs/00-governance/AGENT-ALIGNMENT.md` are read in full before a change. Likewise the §4
   hierarchy: an approved artifact is read, not summarized by a subagent.
2. **A distilled summary is not evidence.** Evidence anchors are read from git objects
   (`BOPEN-ENG-LOOP-001` §2.6); a subagent's condensed report of what a file contained is an informal
   note under §4 and outranks nothing.
3. **Model cascading is guidance, not role assignment** (§20.4). Routing a stage to a cheaper engine
   confers no authority on that engine and removes none from the stage's requirements.

### 26.5 Git lifecycle — the adopted part

Branch naming per work package, atomic conventional commits at each passing iteration, and a PR body
carrying the changed-file table, the check results and the panel findings, are consistent with §15
and §17 and are adopted as practice.

The URE-Loop co-authorship trailer `Co-authored-by: URE-Loop Agent <agent@antigravity.local>` is
**not usable here**. §21.1 requires the acting agent's registered per-agent address
(`<agent>@bst.local`); a shared generic local-part is the precise defect §21.1 was written to
remove, and `check_ballot_attribution.py` cannot bind a ballot to it.

### 26.6 Excluded — mechanisms that conflict with in-force rules

Recorded under §1 (conflicts are recorded, not silently resolved). These are **not** adopted, not
in force as proposals, and would each require a separate operator decision.

| URE-Loop mechanism | Conflicts with | Why it cannot stand here |
| :--- | :--- | :--- |
| Rubric score ≥ 85 → auto-approve for merge | §25.1 step 8; EBIV §8 | A self-computed score is maker self-assessment, which carries no verdict weight. Disposition is reserved to the Completion Authority — a Human or named authority, never an agent role. |
| Agent triggers `gh pr merge --squash --delete-branch` | §18; §20.3 | Merge, release, deployment and production activation are outside agent authority regardless of vote. No skill, score or green suite creates it. |
| 100-point weighted score as the merge gate | §4; §9; §11 | A score is an informal note and cannot outrank a contract or a failing negative test. Weighted aggregation also lets a 0.20-weighted security failure be outvoted by speed and cleanliness; bOPEN fail-closes on a single refused isolation or authorization test. |
| Score 60–84 → agent self-correction loop, no escalation | `BOPEN-ENG-LOOP-001` §2.8 | A `REFUTED` ballot is discharged only by a failed reproduction of its probe. A score rising after a patch is not a failed reproduction. |
| CI-failure self-healing auto-push | §15; §21 | An unattended patch loop bundles unrelated hunks into one commit and misattributes them, and pushes changes no seated verifier has seen. |
| Automatic skill / memory synthesis from a fixed bug | §18 | Repository-local skills are registered only as validated `SKILL.md` packages, and registration grants no authority. Automatic promotion of a distilled lesson into the registry is not authorized. Recording the lesson in `docs/CHANGELOG.md` or the work-package log is. |
| **v0.6** — panel review moves an ADR `Proposed → Accepted` and commits it | §4; §24 provenance note; EBIV §2 | An Accepted ADR sits second in the source-of-truth hierarchy and constrains every later change. An agent panel accepting one is an agent making a normative artifact binding by itself — the exact authority expansion the operator **rejected** on 2026-08-06. Drafting is adopted (§26.8); acceptance is not. |
| **v0.6** — ADRs indexed into agent long-term memory as the enforcement mechanism | §4; §26.4 floor 1 | An index is an informal note. A future run must read `docs/adr/` and `docs/decisions/`, not a cached summary of them, or a stale index silently overrides an ADR that was superseded. |
| **v0.6** — reconciliation triggers `terraform apply` / corrective environment routines | §14; §20.3 | Applying to a live environment is deployment. Outside agent authority regardless of drift severity, and a destructive change still requires the §14 staged-rollout and recovery strategy. |
| **v0.6** — production alert → agent patch → auto-merge at score ≥ 85 | §25.1 step 8; §8; §13 | Unattended production self-healing is the merge-gate exclusion above, applied to the highest-blast-radius surface, with no seated verifier. Separately, feeding APM stack traces and error payloads into an agent context is an **untested tenant-data egress path**: §8 requires cross-tenant negative tests for tenant-owned data, and no such control exists for telemetry ingestion. |

### 26.7 What promotion would require

Promotion of §26.2–§26.5, §26.8 or §26.9 to normative status requires an operator decision recorded
in a `DEC` with verifiable Git provenance, naming which subsections bind. The §26.6 exclusions remain
excluded unless each is separately decided; a decision promoting this section does not reach them.

**Promoted so far:** §26.2 only, by [`DEC-URE-ARCHITECT-LENS`](docs/decisions/DEC-URE-ARCHITECT-LENS.md)
(2026-08-07). That decision states in its own §4 that it reaches nothing else — a promotion is read
from the `DEC`, not inferred from the section next to it.

### 26.8 ADR engine — drafting is adopted, acceptance is not

The v0.6 auto-detection trigger is sound and aligns with §10 and §16: a change that touches a
database schema, introduces an external dependency, alters the auth model, or breaks an API contract
is exactly a change that must not resolve an architectural question by implementation default. Where
§16 says *stop and raise a decision request*, URE-Loop supplies the artifact shape for doing so.

Adopted: on any of those four triggers, the maker drafts an ADR **before** building, using the
existing bOPEN form — `docs/adr/ADR-NNNN.md`, with `**Status:** Proposed`, `**Date:**`, and
`**Owner:**` naming the responsible **Authority** (Architecture, Security, Engineering), per
`docs/adr/ADR-0001.md`..`ADR-0019.md`. The v0.6 template's *Context & Problem Statement / Decision
Drivers / Considered Options / Decision Outcome & Rationale / Consequences & Trade-offs* headings map
cleanly onto that form and onto §24.1's trade-off analysis, and are adopted as drafting structure.

Four corrections to the v0.6 schema:

1. **`Status` stays `Proposed`.** Only an authority moves it to `Accepted` (§26.6). A maker that
   drafts an ADR and then builds against it as though Accepted has resolved the decision by default.
2. **`Owner` is an Authority, not an agent.** v0.6 puts *"Author / Agent: URE-Loop Staff Architect
   Agent"* in the owner slot. Record the drafting agent as author if useful, but the owner field
   carries accountability an agent does not hold.
3. **Numbers are not auto-assigned.** v0.6's `docs/adr/000X-{slug}.md` with an agent picking the next
   number collides with an occupied register — its own worked example, "ADR-0004: Introduce
   Distributed Caching Layer via Redis", is already taken here by **ADR-0004 — Contract-first
   implementation (Accepted)**. Read the directory and take the next free number; never mint one.
4. **Reversal is by supersession, not by index.** ADR-0001 already states changes require a
   superseding ADR. That is the enforcement mechanism, and it lives in git, not in agent memory.

### 26.9 Reconciliation — observation is adopted, actuation is not

The v0.6 reconciliation loop is split cleanly by bOPEN's rules: **observing** a divergence between
desired and actual state is valuable and permitted; **closing** it automatically is not.

Observation is in fact a lesson this repository already paid for. `BOPEN-ENG-LOOP-001` §5 records
*"Reading a spec instead of querying the database — reading migrations gave 5 foreign keys; the
database had 12."* Reconciliation is that anti-pattern's remedy generalized: query the live object,
diff it against the declared one, and treat the difference as a finding.

| Pillar | Adopted | Excluded |
| :--- | :--- | :--- |
| Spec ↔ code drift | Scanning implementation against contracts and active ADRs; reporting the diff | Auto-opened `refactor/reconcile-spec-drift` PRs that merge without a seated verifier |
| Infrastructure / schema drift | Comparing live schema and environment metadata against the declared state | `terraform apply` or any corrective routine executed against an environment (§26.6) |
| Production telemetry | — | The whole pillar (§26.6): both the auto-heal merge and the untested telemetry ingestion path |

Binding constraints if promoted:

1. A drift finding is a **§16 decision request**, not a work item a maker may self-assign. Drift
   often means the declared state was wrong, and patching the code to match production would ratify
   an undecided architecture by observation instead of by ADR.
2. Reconciliation reads **live objects**, never a cached index, and records what it queried — a
   single query's empty result is not evidence (`BOPEN-ENG-LOOP-001` §5, `information_schema` vs
   `pg_catalog`).
3. Any reconciliation surface that ingests tenant-bearing data — telemetry, error payloads, live row
   samples — is tenant-owned data movement and requires the §8 controls, including cross-tenant
   negative tests, before it is built. None exist today.

---

## 27. PROPOSED (not in force) — URE-Loop v0.9: capability baseline, stage gates, ballot governance

> **STATUS: `PROPOSED` — NOT IN FORCE.** No normative authority. Does not replace §5, amend §25, or
> extend the one promotion recorded in §26 (`DEC-URE-ARCHITECT-LENS`, §26.2). Binds nothing until an
> explicit operator authorization with verifiable Git provenance is recorded (`BOPEN-GOV-EBIV-001`
> §2).
>
> **Provenance note.** *URE-Loop v0.9* was supplied by the operator on 2026-08-07, superseding v0.6
> (§26). It adds four mechanisms: §9 governance lens binding, §10 stage-gate and documentation
> standard, §11 capability matrix, §12 ballot governance. §26 continues to govern the v0.4/v0.6
> mechanisms; this section covers only what v0.9 adds. **Read §27.1 before anything else in this
> section.**

### 27.1 A provenance warning that is specific to v0.9

v0.9 §9 restates **bOPEN's own governance** — it quotes `DEC-URE-ARCHITECT-LENS`, `AGENTS.md` §26.2,
`agent-identity-register.json`, EBIV R1–R5 and `approver: BizEra` back at this repository.

**An external document that mirrors our governance is not a source of truth about it** (§4). It is a
lossy copy, and it is the most hazardous kind of source precisely because it reads as authoritative.
The mirror in v0.9 §9 already contains two misstatements of rules that are in force here:

| v0.9 §9 says | What is actually in force |
| :--- | :--- |
| *"NOT a Verifier Seat: EBIV R1-R5 governs **human** ballot voting"* | R1–R5 is the admissibility floor for **agent-cast** verification ballots. Agents are the verifiers here. On 2026-08-07 Codex cast 31 admissible Location ballots at commit `64a2bfa`. The lens is not a verifier seat because it is a lens, **not** because ballots are human-only |
| *"NOT a Quorum Contribution: Cannot count toward formal **release** quorum"* | Quorum is a **verification** quorum. It never authorizes release — §20.3 and EBIV keep release, deployment and production activation outside agent authority entirely, quorum or no quorum. Conflating the two invents an authority path that does not exist |

**Rule: read the `DEC`, never the mirror.** Where v0.9 §9 and `DEC-URE-ARCHITECT-LENS` disagree, the
`DEC` governs and v0.9 is simply wrong about this repository.

### 27.2 Adopted as vocabulary — the capability baseline (v0.9 §11)

v0.9 §11's eight skills and nine layers largely restate obligations this repository already carries.
Adopting them costs nothing and gives shared naming:

| v0.9 §11 skill | Already required by |
| :--- | :--- |
| Verification Before Completion (its #1 control) | `BOPEN-ENG-LOOP-001` §3; §19.4; EBIV §8 — a `CANNOT RUN` or an unread summary line is not a pass |
| TDD contract `RED → GREEN → REFACTOR → VERIFY` | §25.1 step 2 tests-first; §24.3 stage 3; the §5 probe-then-mutate discipline |
| Requirements traceability | §5.7; EBIV R2; `invariant-traceability.csv` |
| Systematic debugging, smallest sufficient fix | §5.5 smallest coherent change; `BOPEN-ENG-LOOP-001` §2.4 |
| Security & authorization review | §9, §11, §13 |
| Subagent isolation with structured statuses | §26.4, bounded by its three floors |
| Safe integration / expand-migrate-contract | §14 |

The one genuine addition is the **structured status vocabulary** — `DONE`, `DONE_WITH_CONCERNS`,
`BLOCKED`, `NEEDS_CONTEXT`. A maker report that must choose one of these cannot quietly land in the
gap between "finished" and "finished with a disclosed limitation", which §17 currently leaves to
prose.

### 27.3 Excluded — identifier collisions that would corrupt in-force records

These are not stylistic objections. Each reuses a token that already means something else here, and
adopting it would make existing records ambiguous or false.

| v0.9 mechanism | Collides with | Consequence |
| :--- | :--- | :--- |
| **§10 stage gates `G0`–`G7`** | §3: **"GATE G7 CLEARED (EVD-RES-001-G7)"** | bOPEN's `G7` means the normative specifications are Approved and Phase 1 kernel implementation is authorized. v0.9's `G7` means *"Stabilization Exit — Transfer to Operations"*, i.e. post-production. bOPEN's G7 is **already cleared**, so importing the ladder would make an in-force line read as though production stabilization were complete. This is the most damaging item in v0.9 |
| **§12 "ballot" / `BAL-GOV-001`** | `docs/evidence/phase-3.5/ballots.jsonl`, §21.3, EBIV | "Ballot" is already bound to EBIV verification ballots. v0.9 §12 uses it for project-governance voting and states *"AI Agents do not vote on ballots... or count toward human quorums"* — see §27.4 |
| **§10 `docs/pack/` 13-folder topology** | `docs/00-governance` … `docs/10-products`, `docs/adr/`, `docs/decisions/` | The numbers collide with different meanings: here `02` is requirements and `07` is security; in v0.9 `02` is ux-service-design and `07` is engineering-devsecops. Adopting it forks the documentation tree and makes every numeric reference ambiguous |
| **§10 ADR path `docs/pack/03-architecture/adr/`** | `docs/adr/ADR-NNNN.md` (19 records) | Compounds the §26.8 numbering defect: a second ADR root guarantees duplicate IDs |

### 27.4 The §12 contradiction, stated plainly

v0.9 §12 asserts: *"AI Agents **do not vote** on ballots as human voters or count toward human
quorums."*

In force here, the opposite is true and the entire evidence base depends on it. Agent verifiers cast
the ballots. `ballots.jsonl` holds 397 of them — 346 `codex`, 51 `gemini` — and EBIV quorum is
counted from exactly those. Adopting v0.9 §12's rule unqualified would retroactively invalidate every
verification this repository has performed.

One principle inside §12 is worth keeping under a different name. **`BAL-INV-020`** — *a ballot
cannot override non-waivable security, legal or safety controls; no vote bypasses a failing test or
a hard invariant* — is the same fail-closed rule bOPEN already applies, and states it more crisply
than §26.6 does. It is compatible; only the surrounding vocabulary is not.

### 27.5 What adoption would require

Nothing in §27.3 can be adopted under its current names. If the operator wants the stage-gate ladder
or project-decision ballots, they need distinct identifiers chosen so that no existing record changes
meaning — for example a `PG-` prefix for project gates, and a term other than "ballot" for
governance voting. §27.2 could be promoted on its own; it introduces no new identifier.

Promotion of any part requires an operator decision recorded in a `DEC` with verifiable Git
provenance, naming which subsections bind. §26.6's ten exclusions are untouched by this section.

---

## 28. PROPOSED (not in force) — URE-Loop v1.5: Autonomous Authority Plane, Runtime Trust Fabric & Skill Router

> **STATUS: `PROPOSED` — NOT IN FORCE.** No normative authority. Does not replace §5, amend §25, or
> extend the promotion recorded in §26 (`DEC-URE-ARCHITECT-LENS`, §26.2). Binds nothing until an
> explicit operator authorization with verifiable Git provenance is recorded (`BOPEN-GOV-EBIV-001`
> §2).
>
> **Provenance note.** *URE-Loop v1.5 (Autonomous Skill Routing and Orchestration)* was supplied by
> the operator on 2026-08-09 (via Google Drive `1meTS5PZBF8HlIvEkqG2XYOZbUn3vbMZr`), superseding
> v0.9 (§27), v0.6 (§26), and integrating v1.0–v1.4 upgrade specifications (`AUTH-URE-ENGLOOP-20260808-001`,
> `AUTH-URE-BALLOT-UPGRADE-20260808-001`, `AUTH-URE-RUNTIME-ASSURANCE-20260809-001`, and
> `AUTH-URE-SKILL-ROUTER-20260809-001`). It adds five primary pillars: Autonomous Authority Plane
> (§13–§14), Autonomous Specification Factory & Git Controller (§16–§17), Autonomous Ballot Governance
> & Single-Use Transition Warrants (§19–§20), Deterministic Runtime Assurance & Agent Trust Fabric
> (§21–§29, FIT-061–100), and Autonomous Skill Routing & Orchestration Controller (§30–§31, FIT-101–120).
> **Read §28.1 before anything else in this section.**

### 28.1 Provenance & source-of-truth hierarchy

An external design document — even at v1.5 — remains an external specification and **not** a bOPEN
source of truth (§4). It cannot substitute for an approved bOPEN artifact, ADR, or contract. Where
an external mirror restates bOPEN governance or in-force rules, the in-force `DEC` or `AGENTS.md` section
governs and the external mirror is not evidence of anything.

### 28.2 Adopted mechanisms and vocabulary

The following v1.5 architectural mechanisms enrich bOPEN's engineering loop vocabulary and design:

| Pillar | v1.5 Section | Adopted concept & vocabulary | Alignment with bOPEN |
| :--- | :--- | :--- | :--- |
| **Autonomous Skill Router** | §30–§31 | Intent classification, registry capability discovery, minimum-sufficient skill selection, prerequisite DAG resolution, typed multi-skill orchestration, output validation, fallback, routing evidence, outcome-calibrated learning (FIT-101–120) | Expands `.agents/skills/` routing discipline; routing cannot create authority, bypass confirmation/warrants, or mutate system state outside the Task Authority Envelope |
| **Autonomous Authority Plane** | §13–§14 | Risk Tier (R0–R4) × Authority Level (A0–A4) matrix, Task Authority Envelope contract, circuit breakers, budget engines, ephemeral sandbox isolation, HITL escalation, durable checkpoint recovery, idempotency ledger | Reinforces §7, §9, §13, §25 authority boundaries and deny-by-default controls |
| **Autonomous Ballot & Warrants** | §19–§20 | Immutable evidence snapshot, registered independent machine voters, deterministic ballot calculation, single-use Transition Warrants issued prior to state mutation | Maps to `BOPEN-GOV-EBIV-001` verification ballots; Transition Warrants enforce explicit authorization before state transitions |
| **Deterministic Runtime Trust Fabric** | §21–§29 | Event-history replay, attested workload identity, context & tool trust boundaries, formal verification lab, attested artifact admission, progressive delivery, interop gateway (FIT-061–100) | Extends §11, §14, §19 testing, isolation, and evidence assurance |

### 28.3 Exclusions and binding constraints

To preserve repository invariants (§1, §4, §7, §20.3):

1. **Skill Routing does not create authority.** The Autonomous Skill Router selects and sequences registry-qualified skills; it cannot grant permissions, bypass warrants, or self-authorize outputs.
2. **Transition Warrants require EBIV verification.** A single-use Transition Warrant issued by the Authority Engine requires 100% passing tests and admissible EBIV ballots.
3. **No self-assessed merge or release.** Rubric scores (even $\ge 85$) and autonomous ballots do not authorize production deployment or merge without explicit authority and operator decision.
4. **Identifier collisions remain excluded.** The v0.9 stage-gate naming collisions (`G0`–`G7` vs bOPEN's cleared `G7`) and documentation tree topology overrides remain excluded (§27.3).

### 28.4 Implementation Readiness & Readiness Status

With URE-Loop v1.5 specification integration complete in `AGENTS.md` §28:
- Specification integration: **`READY_TO_IMPLEMENT`**
- Verification requirement: Implementation of Skill Router, Authority Control Plane, or Warrant controllers must satisfy test suites (`tools/run_tests.py`), clean-room verification (`tools/check_clean_room.py`), authority bootstrap (`tools/check_authority_bootstrap.py`), and contract conformance (`tools/check_contract_conformance.py`).


---

## 29. PROPOSED (not in force) — Enterprise delivery lifecycle: PRD → Production (`LC-1`…`LC-14`)

> **STATUS: `PROPOSED` — NOT IN FORCE.** Recorded as the operator's directive of 2026-08-10, transcribed
> by Claude (Motor). It binds nothing until promoted by an explicit operator decision with Git
> provenance (`BOPEN-GOV-EBIV-001` §2 — an agent has no authority to make a normative specification
> binding by itself).
>
> **This section differs from §26–§28 in one respect:** it relaxes no control, widens no permission
> and creates no authority. It only adds gates between "built" and "in production". Whether that makes
> promotion cheaper to accept is the operator's judgement, not a property an agent may assert on its
> behalf.

### 29.1 Why the identifiers are `LC-n`

`Step` is already the vocabulary of §25.1's maker cycle (steps 0–8), and `Stage 1` appears in six
documents for the Notification build — five governance records and one draft disposition. Reusing
either word would create the same identifier ambiguity v0.9's `G0`–`G7` would have (§27.3). The
lifecycle steps are therefore written `LC-1` … `LC-14`, and `step` continues to mean §25.1 only.

### 29.2 The delivery lifecycle — `LC-1` … `LC-12`

| | Step | Primary output / gate |
| ---: | :--- | :--- |
| `LC-1` | PRD Review and Baseline | Approved PRD and acceptance criteria |
| `LC-2` | Requirement Decomposition | Epics, user stories, NFRs and RTM |
| `LC-3` | Architecture Design | System architecture, data model and ADRs |
| `LC-4` | Detailed Solution Design | API contracts, workflows, UX, RBAC and audit design |
| `LC-5` | Security and Compliance Design | Threat model, privacy controls and security requirements |
| `LC-6` | Implementation Planning | Work packages, estimates, environments and release plan |
| `LC-7` | Development | Working code, migrations, configurations and documentation |
| `LC-8` | Engineering Verification | Code review, unit, integration and end-to-end tests |
| `LC-9` | Quality and Security Validation | Performance, resilience, vulnerability and penetration testing |
| `LC-10` | UAT and Pilot | Business acceptance, defect closure and pilot evidence |
| `LC-11` | Production Readiness Review | Runbooks, monitoring, backup, rollback and operational approval |
| `LC-12` | Production Deployment | Controlled release, smoke testing and deployment evidence |

### 29.3 The production lifecycle — `LC-13`, `LC-14`

| | Step | Purpose |
| ---: | :--- | :--- |
| `LC-13` | Hypercare and Stabilization | Closely monitor incidents, performance and user adoption |
| `LC-14` | Post-Implementation Review | Measure KPIs, document lessons and authorize normal operations |

**`LC-1`–`LC-12` is the delivery lifecycle. `LC-1`–`LC-14` is the complete production lifecycle.**

### 29.4 Governance flow

```
PRD_APPROVED → DESIGN_READY → IMPLEMENTATION_READY → BUILT → TESTED
  → SECURITY_VALIDATED → UAT_ACCEPTED → PRODUCTION_READY → DEPLOYED → STABILIZED
```

**The load-bearing rule, stated by the operator and adopted verbatim:**

> *"Built" or "sandbox tested" does not mean production-ready; `LC-9`–`LC-11` must still be passed
> before production authorization.*

`BUILT` is the one state name in this flow that already appears in the repository, in two forms — as
`BUILT AND UNVERIFIED` in `WP-P35-07` and `DOCUMENT-MANIFEST.json`, and as a quoted phase label
`COMPLETED & BUILT` in `BOPEN-P1-001-EXECUTION-PLAN.md` §25, where the surrounding text says that
status *"must be treated as an assertion until implementation evidence is inspected."* Both readings
agree with each other and with this flow, and the longer form is the safer one:
**`BUILT` asserts that code exists, never that it was verified.** The remaining nine state names were
checked against the tree and collide with nothing.

### 29.5 Reconciliation with §25.1 — different axes, not competing loops

§25.1 governs **one work package**. `LC-1`–`LC-14` governs **one release of the product**. A single
`LC-7`/`LC-8` contains many complete §25.1 cycles.

| Lifecycle | Existing bOPEN mechanism |
| :--- | :--- |
| `LC-1`–`LC-4` | `docs/01-product`, `docs/02-requirements`, `docs/03-architecture`, `docs/adr`, `TRACEABILITY-MATRIX.md` |
| `LC-5` | `docs/07-security` — **shells only**, see §29.6 |
| `LC-6` | `DEC-*` entry gates (§25.1 step 0), `docs/work-packages` |
| `LC-7` | §25.1 steps 1–6 |
| `LC-8` | §25.1 step 7 — `BOPEN-GOV-EBIV-001` ballots, `tools/run_tests.py` |
| `LC-9`–`LC-11` | **No release-wide gate exists.** Component-level evidence does exist in places — see the correction below |
| `LC-12` | §20.3 places release and production outside agent authority; no pipeline exists |
| `LC-13`–`LC-14` | **none exists** |

**A §25.1 step-8 disposition is an `LC-8` verdict, never an `LC-12` authorization.** All 33
`production_activation_authority` fields across `docs/evidence/` read `false`; no disposition claims
otherwise.

**What that does *not* mean — a correction found by independent re-derivation on 2026-08-10.** This
subsection first read *"none of them says anything about performance, resilience, ... or rollback —
because no bOPEN mechanism has ever examined those."* **That was false, and the counter-example is
one of the twelve disposed records.** `trial-to-paid-disposition.md` names
`INV-MIGRATE-ROLLBACK-SAFE-01` as a balloted invariant, records that a failure before cutover leaves
the tenant safely on the shared pool, discloses that a failure at or after the cutover UPDATE is not
auto-repaired, and reports a measured latency regression (~365→417s). It examines rollback,
failure-resilience and performance directly.

The true statement is narrower and still sufficient:

> No disposition establishes **release-wide** `LC-9`–`LC-11` readiness, and none confers `LC-12`
> authority. Some contain component-level rollback, resilience and performance evidence, scoped to
> the work package they accept.

Reading any disposition as production readiness remains the error this section exists to prevent —
but the reason is scope, not absence.

**Scope of "every disposition".** The claims above are derived from the **12 non-draft dispositions in
`docs/evidence/phase-3.5/`**. They do not extend to earlier phase records: `phase-3/completion-decision.md`
is `IMPLEMENTED_UNVERIFIED` with its prior *GO ON EVIDENCE* withdrawn on 2026-07-30, and is not a
disposition of verified work at all.

### 29.6 Where bOPEN actually stands, derived from the tree on 2026-08-10

The **evidence column** is file existence and line counts, reproducible by `find` and `wc -l`. The
**one-word labels** — "substantive", "shell", "absent" — are a reading of that evidence, and an
earlier draft of this line claimed the whole table was "not an assessment", which was itself an
overclaim. Read the counts; the labels are a convenience.

| | Evidence in the repository |
| :--- | :--- |
| `LC-1`–`LC-4` | Substantive. Populated product, requirements, architecture and ADR trees. |
| `LC-5` | **Shell.** `docs/07-security/threat-model/README.md` is **3 lines** and states what a threat model *shall* contain; it is not one. `07-security/privacy/privacy-baseline.md` and `07-security/supply-chain/dependency-policy.md` are **3 lines each**. `BOPEN-SEC-001-DRAFT.md` is 26 lines and `DOCUMENT-STATUS.md` classifies it "Draft shell". **No SBOM of any format exists.** |
| `LC-6`–`LC-8` | Substantive, and the most developed part of the repository. |
| `LC-9` | **No general package.** Searches for performance, load, benchmark, penetration and vulnerability artifacts returned nothing outside `node_modules`. **Narrow evidence does exist:** `tools/probes/probe_trial_to_paid_codex.py` exercises failure-before-cutover behaviour, and `trial-to-paid-disposition.md` records a latency measurement. Whether that clears an `LC-9` gate is **unanswerable** — this section defines no coverage threshold. |
| `LC-10` | **Absent.** No UAT or pilot record exists. |
| `LC-11` | **Shell.** `09-operations/backup-recovery.md`, `deployment.md`, `observability.md` and `service-level-objectives.md` are **3 lines each**; two runbooks (`migration-rollback.md`, 8 lines; `bootstrap-validation.md`) carry content. |
| `LC-12` | `.github/workflows/` holds one governance workflow. **No deployment pipeline exists.** |

**No position statement is made here, and an earlier draft was wrong to make one.** It read
*"Position: `BUILT`, entering `TESTED` — four states short of `PRODUCTION_READY`."* That arithmetic is
correct against §29.4's sequence, but a state is a property of **an identified release**, and this
section binds none: no release or candidate is named, no state-entry criterion is defined, and nothing
here establishes that all `LC-8` work is complete. Counting transitions on a sequence is not the same
as locating the product on it.

What the table does support is narrower and enough to act on:

> `LC-5`, `LC-9`, `LC-10` and `LC-11` have **no artifact that could be presented at a gate review**,
> whatever the entry criteria eventually say.

**Two corrections to earlier statements are recorded here rather than elsewhere,** because a
correction filed away from the claim it fixes is not a correction:

1. A statement made in session on 2026-08-09 that *"no threat-model file exists"*. The file exists; it
   is a three-line statement of what a threat model must contain. The substance was right, the wording
   was not.
2. The `LC-9` row and the §29.5 absence claim, both overstated in the version committed at `909e4f5`
   and both found by independent re-derivation the same day — not by re-reading the text.

### 29.7 What promotion would require

1. An operator decision recording `LC-1`–`LC-14` as normative, and whether it revises §5 or sits beside it.
2. A named gate owner for `LC-9`, `LC-10` and `LC-11` — each is currently unowned, and `LC-11` ends in
   an *operational* approval that §20.3 already places outside agent authority.
3. A ruling on whether `LC-9`–`LC-11` evidence is admissible under `BOPEN-GOV-EBIV-001` or governed
   separately. EBIV was built for propositions about code behaviour; a pilot acceptance and an SLO are
   not that shape.
4. **State-entry criteria, and a bound release.** §29.4 names ten states but defines entry to none of
   them, and §29.6 shows why that is not cosmetic: without criteria and an identified release, the
   flow can order work but cannot say where the product currently is. Until both exist, no agent and
   no document should assert a current state.

Recorded advisory-only. Confers no implementation, approval, merge, release or production authority.

---

## 30. PROPOSED (not in force) — Evidence-Backed Agent Governance: authority-delta classification, delegation envelopes, dual-policy evaluation

> **STATUS: `PROPOSED` — NOT IN FORCE.** Recorded as the operator's directive of 2026-08-10,
> transcribed by Claude (Motor). Binds nothing until promoted by an explicit operator decision with
> Git provenance (`BOPEN-GOV-EBIV-001` §2). Unlike §29, **this one would move authority if adopted
> whole.** §30.5 names every part that would; those parts are excluded, not adopted.

### 30.1 What it was written for, and why that matters here

The source analysis concerns a pull request that modifies `ci.yml`, an OPA policy bundle, an ADR and a
risk classifier — the machinery that decides its own permissions. **bOPEN has none of that
machinery.** Verified against the tree on 2026-08-10: `.github/workflows/` contains one file
(`bootstrap-governance.yml`), there is no `.rego` policy of any kind, no classifier, no merge queue,
no GitHub App and no organization ruleset.

The proposal therefore cannot be applied here; it can be adopted as design vocabulary, and its central
idea is worth adopting on its own merits.

### 30.2 Adopted as vocabulary — authority-delta over file-path

> Replace *"touched a protected file ⇒ human required"* with *"increased authority beyond the
> delegated envelope ⇒ constitutional review required."*

This is the strongest idea in the source, and it is **the distinction bOPEN had already reached from
the other end**. `DEC-STANDING-ENTRY-AUTHORIZATION` §2 — raised 2026-08-10, still `Proposed` —
separates an **entry gate** (authorizes *starting* work whose scope a disposed decision already fixed;
can be standing) from a **disposition** (the verdict itself; cannot be). Both say: **classify by what a
change does to authority, not by which path it touches.**

Also adopted as vocabulary, without the machinery: signed policy bundles, evidence digests bound to a
commit SHA, transparency logging, dual-policy evaluation (a change to policy judged by *both* the
current and the proposed rule), shadow-mode comparison before activation, and two-epoch activation for
any gate script.

### 30.3 Already in force — do not import these twice

Three of the source's proposals are existing bOPEN rules. Re-adopting them under new names would
create two vocabularies for one control:

| Source proposal | Already in force as |
| :--- | :--- |
| §6 "proposer may not cast a ballot" | `BOPEN-GOV-EBIV-001` §3 maker exclusion — *any line of the artifact under review* |
| §6 "evidence builder may not certify its own evidence" | EBIV §8 — a maker's own passing suite carries no verdict weight |
| §5 "a new push invalidates all ballots" | EBIV candidate binding — a ballot names `commit_oid` and `tree_oid` and is void anywhere else |

### 30.4 Excluded — identifier collisions, two of them repeats

| Source token | Collides with | Ruling |
| :--- | :--- | :--- |
| `G0`–`G5` change classes | §3's in-force **"GATE G7 CLEARED (EVD-RES-001-G7)"** | **Excluded.** §27.3 already excluded v0.9's `G0`–`G7` for this exact reason and called it *"the most damaging item in v0.9"*. This is the second proposal in a row to reuse `G`-prefixed stage identifiers; a different prefix is required before the change classes can be considered. |
| `A0`–`A4` authority ladder | §28.2 already records **Authority Level `A0`–`A4`** from URE-Loop v1.5, with different meanings | **Excluded as written.** Two `PROPOSED` sections would define `A2` as both "medium-risk changes" and a v1.5 authority level. One meaning per token, or neither. |
| `L0`–`L3` governance layers | `EVD-SEC-001` line 561 uses `L3` to mean **assurance Level 3** | **Rename before use.** `GL-0`…`GL-3` is unused. Milder than the above, but an evidence document already reads `L3` as a maturity claim. |
| `BAL-GOV-2026-001` ballot | EBIV ballots in `ballots.jsonl` (433 records) | **Excluded.** §27.3 already ruled on `BAL-GOV-001`: a second artifact called a "ballot", with a different admissibility model, makes "the ballot confirmed it" ambiguous. |
| `REJECTED` verdict | EBIV verdicts are `CONFIRMED` / `REFUTED` / `INADMISSIBLE` | **Usable, but keep it distinct.** `REJECTED` appears zero times in `ballots.jsonl`, so there is no live conflict — but operator dispositions already use ACCEPT/REJECT, and a ballot verdict and a disposition outcome must not merge into one word. |

### 30.5 Excluded — the parts that would move authority

These are why this section carries a stronger banner than §29:

1. **Retiring `HUMAN_REQUIRED` as a generic outcome (source §11).** bOPEN does not use that token, but
   it uses the thing: §20.3 places merge, release and production outside agent authority, and §25.1
   step 8 reserves disposition to the Completion Authority, *"which is not an agent role"*. Neither is
   a placeholder awaiting a better council.
2. **`AGENT_BALLOT_ELIGIBLE` for governance implementation (`G1`/`G2`).** Under it, agents would merge
   changes to the gate and the classifier that judge them. EBIV §2 — *"agents may certify; agents may
   not self-authorize"* — forbids exactly this.
3. **`CONDITIONAL_AGENT_ELIGIBLE` ladder advance (`G3`).** An agent promoting its own authority tier on
   KPI attainment is self-authorization with a counter attached.
4. **Agent-executed auto-merge of any class.** §20.3, unconditional.
5. **Optimistic auto-merge with rollback.** Excluded on a different ground — absent prerequisite, not
   authority. It presumes a rollback capability; §29.6 records `09-operations/backup-recovery.md` as a
   three-line shell.

### 30.6 Not satisfiable here — the five-agent council

The source requires five role-separated voters with distinct service identities, 4-of-5 approval,
5-of-5 for gate changes, and Governance/Security veto.

**bOPEN has two available verifying agents** — Claude and Codex — with gemini appearing in the
historical record. `EBIV` §6.5's `CONFIRMED_UNDER_TWO_AGENT_PROFILE` exists precisely because the
population is too small for a quorum of that shape, and §6.5.4 sets the profile to expire rather than
pretend otherwise. Every one of the six candidates currently awaiting disposition carries **one**
independent verifier.

A 4-of-5 rule adopted today would not raise assurance. It would make every governance change
permanently unmergeable while presenting itself as a stronger control. Recorded as **blocked on
population, not on principle.**

### 30.7 Adopted in full — the Genesis Ratification constraint

The source's own closing safeguard is adopted verbatim as the condition on everything above:

> Without an existing authority signing the Genesis Ratification, making the change agent-approved
> would be a retroactive self-grant of authority, and cannot count as credible governance evidence.

This restates `BOPEN-GOV-EBIV-001` §2. It is also why §30 is recorded as `PROPOSED` by the agent that
transcribed it rather than adopted by it: **a section that would widen agent authority cannot be
brought into force by an agent, and least of all by citing itself.**

### 30.8 What promotion would require

1. A **bootstrap/payload split**, as the source itself recommends — one operator ratification
   installing the envelope, ballot schema and verifier, with the policy payload following under it.
2. A **verifier outside the tree it judges.** bOPEN's only workflow lives in the repository it
   validates, so a pull request can edit it. Closing that is a prerequisite to every
   `AGENT_BALLOT_ELIGIBLE` class — and is worth doing on its own merits even if nothing else here is
   adopted.
3. A ruling on whether that verifier's output is admissible under `BOPEN-GOV-EBIV-001` or governed
   separately — the same open question §29.7 item 3 raises for `LC-9`–`LC-11`.
4. Enough independent verifying agents to make a quorum meaningful (§30.6), or an explicit decision to
   keep operating under the two-agent profile with its expiry intact.

Recorded advisory-only. Confers no implementation, approval, merge, release or production authority.

---

## 31. CONDITIONAL — Governed Autonomy: evidence-backed autonomous merge for the Engineer Loop

> **STATUS: `PROPOSED` UNTIL THE GENESIS RATIFICATION; IN FORCE FROM THE OPERATOR'S MERGE OF THE
> `BOPEN-WP-GOV-AUTONOMY-001` PULL REQUEST.** That merge is the "explicit operator authorization
> with verifiable Git provenance" required by `BOPEN-GOV-EBIV-001` §2 and recorded in
> [`DEC-GOV-AUTONOMY-001`](docs/decisions/DEC-GOV-AUTONOMY-001.md). Consistent with §30.7, the agent
> that drafted this section cannot bring it into force and has not: **before that merge this section
> binds nothing; after it, this section binds exactly what it says and no more.**
>
> **Provenance.** This is the §30.8 item-1 bootstrap/payload split, executed. The machinery is
> ported from the SecB Project Framework (`bstBizEra/secb_pf`, L0 governance ratified at
> `SECB-WP-FWK-012`, port procedure `SECB-WP-FWK-017`) under the operator's session directive of
> 2026-08-10. §26.6's exclusions and §30.5's authority exclusions are amended **only** where §31.2
> explicitly says so.

### 31.1 What binds, and the identifier map

The GL root constitution ([`docs/00-governance/GL_ROOT_CONSTITUTION.md`](docs/00-governance/GL_ROOT_CONSTITUTION.md)),
the delegation envelope (`config/delegation_envelope.json`, `ENV-BOPEN-2026-001`, tier `AT1`,
expires **2026-11-08**), the four enforcement scripts (`scripts/check_work_package_ref.py`,
`check_budget.py`, `classify_authority_delta.py`, `check_dual_policy.py`), their tests under
`tests/governance/`, and the `governance-gates` workflow.

Honouring the §30.4 collision rulings: change classes are **`AD0`–`AD5`** (not `G0`–`G5`),
governance layers are **`GL-0`–`GL-3`** (not `L0`–`L3`), authority tiers are **`AT0`–`AT4`** (not
`A0`–`A4`; §28.2's `A0`–`A4` keep their URE-Loop v1.5 meanings). The classifier's outputs form the
**authority verdict** vocabulary (`AUTO_APPROVED`, `AUTO_APPROVED_WITH_CONDITIONS`,
`AGENT_BALLOT_REQUIRED`, `CONSTITUTIONAL_REQUIRED`, `REJECTED`) — a separate set from EBIV ballot
verdicts and from operator dispositions; always name the set.

### 31.2 The autonomous merge rule — the one thing this section changes

An agent MAY merge its own pull request **when and only when ALL of the following hold**:

1. The authority-delta classifier returns authority verdict `AUTO_APPROVED` (`AD0`) for the PR's
   full diff against its base.
2. Dual-policy evaluation returns `PASS` — base and head logic agree the envelope covers it.
3. Every `governance-gates` job is green, including the Authority gate (a work-package ID cited)
   and the Budget gate (exactly one `BUDGET: max_files=<n> max_lines=<n>` line, honoured).
4. The envelope is unexpired, unrevoked, and `current_tier` is `AT1` or higher.
5. The merge is **announced** on the work-package ticket — authority verdict, gate results, merge
   SHA, work-package ID. **Silence is a policy violation.**
6. The commits are authored under the acting agent's registered identity (§21.1), and §25.2
   identity hygiene was applied.

To this extent — and to this extent only — §20.3's placement of *merge* outside agent authority and
§26.6/§30.5's exclusion of agent-executed auto-merge are amended for `AD0` changes. Everything else
those sections place outside agent authority (release, deployment, production, dispositions,
verdict authority) is unchanged.

### 31.3 Escalation, unchanged

- `AGENT_BALLOT_REQUIRED` (`AD1`/`AD2`) escalates to the operator while `ballot_layer.state` is
  `NOT_ACTIVE` (§30.6: two verifying agents cannot form a quorum; EBIV §6.5 two-agent profile).
- `CONSTITUTIONAL_REQUIRED` (`AD4`) is decided and merged by the operator, always — including every
  change to this section, the constitution, the envelope, the gate scripts, `.github/`, `AGENTS.md`
  itself, `GOVERNANCE.md` and `CODEOWNERS`.
- `REJECTED` (`AD5`) is withdrawn, not argued. Prohibited-action signatures are listed in the
  constitution and are never weighed against benefit.
- Escalations are raised as decision requests (§16), not as merged facts.

### 31.4 What this section does not grant

No release, deployment, or production authority (§29's `LC-9`–`LC-14` remain untouched and stages
9–11 unbegun). No ballot-layer activation. No ladder advance: `AT2` requires the envelope's
recorded conditions objectively met and remains `AD3`; `AT3`/`AT4` are unreachable while the ballot
layer is inert. No external trust anchor: the verifier still runs inside the repository it judges,
which is exactly why `.github/` sits on the constitutional surface (§30.8 item 2 stays open and
worth closing independently).
