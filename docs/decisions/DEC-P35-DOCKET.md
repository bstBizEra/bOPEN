# DEC-P35-DOCKET - Phase 3.5 entry decision docket

**Document ID:** `DEC-P35-DOCKET-001`  
**Version:** `0.1.0`  
**Status:** Partially ratified 2026-07-31 - `D-P35-001`..`D-P35-003` accepted (§6.1); `D-P35-004`..`D-P35-018` awaiting designated authority decisions  
**Issued:** 2026-07-31  
**Owner:** Engineering Authority  
**Required concurrence:** Architecture Authority, Security Authority, Product Authority  
**Governing artifacts:** `AGENTS.md` sections 4, 16, 20; `BOPEN-GOV-EBIV-001`;
`BOPEN-ARCH-001`; `BOPEN-TENANT-001`; `BOPEN-AUTHZ-001`; `BOPEN-IDP-001`  
**Assisted plan:** [`BOPEN-P35-001`](../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md)  
**Requirements candidate:** [`BOPEN-PRD-P35-001`](../02-requirements/BOPEN-PRD-P35-001.md)

---

## 1. Purpose

`BOPEN-PRD-P35-001` sequence 0 requires four decisions before Phase 3.5 implementation.
The four source records contain the findings, options, and detailed rationale. This docket
does not replace them. It presents one bounded review surface so the designated authorities
can accept, reject, or return each recommendation without an agent choosing architecture by
implementation default.

Nothing in this docket is approved. Preparing it does not:

- accept `BOPEN-PRD-P35-001`;
- accept `BOPEN-P35-001`;
- authorize a migration or production-source mutation;
- assign an independent verifier;
- open Phase 4 or authorize production activation.

## 2. Live baseline

| Item | Live state on 2026-07-31 | Consequence |
|---|---|---|
| `DEC-P35-RUNTIME` | **Approved 2026-07-31** (was Proposed on preparation) | Phase 3.5 implementation authorized; see §6.1 |
| `DEC-P35-AUDIT-ENVELOPE` | Proposed | Two audit vocabularies remain an explicit interim |
| `DEC-P35-PHASE2-STORAGE` | Proposed | Phase 2 persistence shape cannot be selected in code |
| `DEC-P35-AUTH-BOUNDARY` | Proposed/advisory | Identity fixes cannot establish an IdP boundary by default |
| `BOPEN-PRD-P35-001` | Proposed | Review findings are requirements candidates, not implementation authority |
| Phase 1 through Phase 3 | `IMPLEMENTED_UNVERIFIED` under `AGENTS.md` section 20.2 | Green tests do not establish a completion verdict |
| Verifier ballots | None recorded | No EBIV quorum or exact-commit verdict exists |

The canonical PostgreSQL-backed suite passed 414 of 414 tests during preparation of the PRD.
That result is useful execution evidence, but it does not answer the decisions below and does
not count as an independent ballot.

## 3. Recommended decision order

The authority review SHOULD use this order because later choices depend on earlier ones:

1. Decide the Phase 3.5 runtime gate.
2. Decide Phase 2 storage items 2.1 through 2.6.
3. Decide the authentication and external IdP boundary using the accepted storage shape.
4. Decide the target audit envelope and its transition sequencing.
5. Decide whether to accept the PRD as planning input.
6. Assign exclusive maker, independent checker, security reviewer, and completion-authority
   roles before implementation begins.

The decisions MAY be recorded in one meeting or approval action, but each row remains
separately rejectable and must name its approving authority.

## 4. Decision docket

### 4.1 Runtime and plan entry

| Docket ID | Source | Proposed disposition | Required authority |
|---|---|---|---|
| `D-P35-001` | `DEC-P35-RUNTIME` | Adopt Option C: insert Phase 3.5 before Phase 4 and bind `BOPEN-P35-001` as the implementation plan. Retain the `IMPLEMENTED_UNVERIFIED` state until admissible verification exists. | Architecture and Engineering |
| `D-P35-002` | `DEC-P35-RUNTIME` section 5.1 / `BOPEN-GOV-EBIV-001` | Retain the executed, traced, machine-anchored, adversarial evidence floor and independent-verifier requirement already reflected in `AGENTS.md` section 20.3. | Architecture, Engineering, and Security |
| `D-P35-003` | `BOPEN-P35-001` | Keep Go event microservices deferred pending observed load. Deferral is not cancellation and does not authorize Phase 4. | Architecture and Engineering |

**Entry effect if accepted:** `WP-P35-01` through `WP-P35-03` become eligible for assignment
and implementation in the accepted sequence. `WP-P35-04` and `WP-P35-05` remain subject to
their dependencies. Production activation remains unauthorized.

### 4.2 Phase 2 storage

| Docket ID | Source item | Proposed disposition | Required authority |
|---|---|---|---|
| `D-P35-004` | `DEC-P35-PHASE2-STORAGE` 2.1 | Store bOPEN identifiers as bare UUIDs. Prefixes, if retained, exist only at an API presentation boundary. | Architecture, Engineering, and Data |
| `D-P35-005` | 2.2 and Addendum A.3 | Protect `authentication_sessions` with a principal-scoped policy and a `principal_session` helper that refuses an empty principal. | Architecture, Engineering, and Security |
| `D-P35-006` | 2.3 and Addendum A.2 | Resolve a delegated grant with one parameterized lookup inside `tenant_session(target_tenant_id)`. Do not introduce `SECURITY DEFINER`. | Architecture, Engineering, and Security |
| `D-P35-007` | 2.4 | Extend `active_contexts` rather than create a second context table; reconcile the per-session supersession invariant explicitly. | Architecture, Engineering, Data, and Security |
| `D-P35-008` | 2.5 and [`DEC-P35-PHASE2-STORAGE-ADD-001`](DEC-P35-PHASE2-STORAGE-ADDENDUM.md) section 3 | Permit one effective mapping per `(directory_id, group_external_id)`. Treat `mapping_policy_version` as the required revision and audit stamp, preserve prior revisions as history, and fail closed if more than one effective row exists. | Architecture, Engineering, and Security |
| `D-P35-009` | 2.6 and [`DEC-P35-PHASE2-STORAGE-ADD-001`](DEC-P35-PHASE2-STORAGE-ADDENDUM.md) section 4 | Permit multiple records but prohibit overlapping usable intervals for one `(source_principal_id, target_tenant_id)`. Enforce at activation and in PostgreSQL; ambiguous legacy data denies context issuance rather than merging or selecting. | Product, Architecture, Engineering, and Security |
| `D-P35-010` | section 3 | Bind the storage-independent security constraints: never persist bearer access tokens; store SSO state and nonce as digests; do not add a redundant PKCE challenge column; do not serialize idempotency results; do not index normalized invitation email as an identity key. | Engineering and Security |

**Entry effect if accepted:** migration design for Phase 2 persistence may begin only after
the authorities accept or replace the proposed outcomes in `D-P35-008` and `D-P35-009`. Any
migration remains subject to append-only, rollback, RLS, contract-first, and
independent-review controls.

### 4.3 Authentication and external IdP boundary

| Docket ID | Source | Proposed disposition | Required authority |
|---|---|---|---|
| `D-P35-011` | `DEC-P35-AUTH-BOUNDARY` section 2 | Keep the identity provider outside the kernel process behind a network boundary. The kernel owns principals, sessions, tenant connection configuration, and normalized protocol results; it does not become an IdP. | Architecture, Engineering, and Security |
| `D-P35-012` | sections 3 and 4 | Bind external identities by connection, issuer, and subject. Never link or route trust by email equality. Replace asserted booleans with verifiable, purpose-bound artifacts before exposing a link operation. | Architecture, Engineering, Security, and Privacy |
| `D-P35-013` | sections 4.3 and 4.4 | Require adapters to verify issuer-bound authorization responses and, for SAML, consume only the signed reference subtree from one parse and one DOM. | Engineering and Security |
| `D-P35-014` | section 5 | Re-verify the license and supported release of the selected broker against an exact pinned commit or image digest before `WP-P35-05` dependency lock. Do not infer current suitability from the aged `DEC-0003` evidence. | Architecture, Engineering, Security, and Legal/Product as applicable |

**Entry effect if accepted:** authentication-boundary contract work may proceed after the
Phase 2 storage decisions are accepted. `WP-P35-05` implementation remains blocked until
`D-P35-014` has a recorded result and pinned dependency.

### 4.4 Audit envelope

| Docket ID | Source | Proposed disposition | Required authority |
|---|---|---|---|
| `D-P35-015` | `DEC-P35-AUDIT-ENVELOPE` | Adopt Option A as the target: amend `audit-event.json` and its producer to converge on the approved `BOPEN-P1-001` section 10.2 vocabulary. | Architecture and Engineering |
| `D-P35-016` | `DEC-P35-AUDIT-ENVELOPE` section 5 | Retain Option B only as a named interim until Phase 2 persistence exists. Keep executable tests for both envelopes so a third vocabulary cannot appear. | Architecture, Engineering, and Security |

**Entry effect if accepted:** the target contract is decided, but producer and schema changes
remain sequenced after Phase 2 persistence and require the contract-first workflow.

### 4.5 Product requirements

| Docket ID | Source | Proposed disposition | Required authority |
|---|---|---|---|
| `D-P35-017` | `BOPEN-PRD-P35-001` | Accept as the product-requirements input assisting `BOPEN-P35-001`, subject to Architecture, Engineering, and Security concurrence. Acceptance does not itself activate a work package. | Product, Architecture, Engineering, and Security |
| `D-P35-018` | PRD section 10 | Bind `P35-PRD-T001` through `P35-PRD-T010` as required falsifiable acceptance propositions. A test is inadmissible if removal of its named mechanism does not make it fail. | Product, Engineering, and Security |

## 5. Required role assignments

Before any accepted Phase 3.5 implementation begins, record:

| Role | Required property | Assignee |
|---|---|---|
| Maker | May implement and author tests; does not vote on its own work | **Alternates by work package** — see §5.2 |
| Independent checker | Did not author implementation or its tests; ballot is blind to other verdicts | **Determined by the maker of that package** — see §5.2 |
| Security reviewer | Required for identity, authorization, tenancy, RLS, dependency, and audit decisions | *Pending* — not decided by the 2026-07-31 ratification |
| Completion authority | Records completion only after admissibility and unresolved-refutation checks | **Operator** (`BizEra <ounkhamvilay@gmail.com>`), consistent with `docs/evidence/phase-3.5/manifest.json` |

Model identity is capability guidance, not a standing role assignment. Git author identity and
ballot attribution must comply with `BOPEN-GOV-IDENT-001`.

### 5.1 Why the maker alternates

`BOPEN-GOV-EBIV-001` §3 excludes a verifier who authored *any* artifact under review. Every
additional maker on a package is therefore one fewer engine able to verify it. Four engines
participate, and two of them — Gemini and Kimi — have never cast a ballot here and hold no
commit identity in `agent-identity-register.json`.

Making both Claude and Codex co-makers everywhere would be the fastest way to write code and
the fastest way to lose the ability to check it: every Phase 3.5 ballot would then depend on
the two engines with no demonstrated participation. Alternating instead keeps each engine
eligible on the other's work, which is the only cross-check currently backed by an agent that
has actually shown up.

Codex held verifier seat `V1_Codex` on the `WP-P35-01`..`WP-P35-03` evidence record. That seat
was already stood down by the operator on 2026-07-30 (`manifest.json`, `quorum_status`), so no
cast ballot is discarded. The operator released it deliberately on 2026-07-31 rather than
leaving it recorded as unreached.

### 5.2 Maker and eligible-checker table

| Work package | Maker | Eligible independent checker | Why |
|---|---|---|---|
| `WP-P35-01` Persistence and tenant session | **Codex** (remediation) | **Gemini or Kimi only** | Claude authored the original; Codex now co-authors by remediating. Both are excluded by §3 |
| `WP-P35-02` Kernel HTTP surface | **Codex** (remediation) | **Gemini or Kimi only** | As above |
| `WP-P35-03` Signed context token | **Codex** (remediation) | **Gemini or Kimi only** | As above |
| `WP-P35-04` API gateway (Hono + Zod) | **Claude** | **Codex, Gemini or Kimi** | Codex does not touch it, so Codex stays eligible to verify it |
| `WP-P35-05` Enterprise IdP bridge | *Named when unblocked* | *Determined then* | Blocked by `D-P35-011`..`D-P35-014`; assigning a maker to a blocked package would imply an authority that does not exist |

The rule, stated once: **an engine that edits a package cannot vote on it.** An agent picking up
work not listed here shall record its own row before writing, not after.

This inverts the split in
[`HANDOFF-P35-PARALLEL-TO-CODEX`](../00-governance/handoffs/HANDOFF-P35-PARALLEL-TO-CODEX.md),
which was stood down on 2026-07-30 and proposed Codex as maker of `WP-P35-04`. That document is
a record, not a current instruction.

### 5.3 What the assignment does not establish

`WP-P35-01`..`WP-P35-03` remain `IMPLEMENTED_UNVERIFIED` with zero ballots. Assigning a maker
does not verify them; remediation by a new maker does not either. Their checker seat needs
Gemini or Kimi, and that seat is a real open risk rather than a formality.

## 6. Ratification record

Authorities should record one outcome per docket row:

```text
Outcome: ACCEPT | REJECT | RETURN_WITH_CONDITIONS
Conditions:
Approver role:
Approver identity:
Decision timestamp:
Evidence or rationale:
```

For `D-P35-008` and `D-P35-009`, `ACCEPT` adopts the explicit disposition recorded in section
4.2. An alternative outcome must state its contract-visible selection and composition
semantics. Silence is not a decision.

### 6.1 Recorded ratification — 2026-07-31

The operator, acting as Architecture Authority and Engineering Authority, ratified the runtime
and plan-entry rows. No other row was decided.

| Docket ID | Outcome | Conditions |
|---|---|---|
| `D-P35-001` | **ACCEPT** | None. Option C adopted; `BOPEN-P35-001` bound as the implementation plan. `IMPLEMENTED_UNVERIFIED` retained for Phases 1-3 |
| `D-P35-002` | **ACCEPT** | None. The evidence floor and independent-verifier requirement in `AGENTS.md` §20.3 are retained unchanged |
| `D-P35-003` | **ACCEPT** | None. Go event microservices remain deferred; deferral is not cancellation and does not open Phase 4 |
| `D-P35-004` .. `D-P35-018` | **Not decided** | Remain Proposed. Their dependent work stays blocked per §4.2, §4.3 and §4.4 |

```text
Outcome: ACCEPT (D-P35-001, D-P35-002, D-P35-003 only)
Conditions: none attached to the accepted rows
Approver role: Architecture Authority and Engineering Authority
Approver identity: BizEra <ounkhamvilay@gmail.com> (operator)
Decision timestamp: 2026-07-31T02:24:53+07:00
Evidence or rationale: DEC-P35-RUNTIME §3 findings of fact and §4 option analysis;
  operator instruction of 2026-07-31 to open the Phase 3.5 gate and assign Codex as maker
Recorded by: Claude (agent, Motor role) — transcription at operator direction;
  execution_authority: false, approval_authority: false
```

Security Authority and Product Authority concurrence is **not** recorded. `D-P35-002` names
Security among its required authorities. It is ratified here on the basis that it relaxes
nothing — it retains an existing constraint verbatim — and that reading should be checked
rather than assumed. Every row that would *change* a security-bearing position
(`D-P35-005`..`D-P35-016`) is left undecided precisely because that concurrence is absent.

**Entry effect now in force:** `WP-P35-01` through `WP-P35-03` are eligible for assignment and
implementation, with Codex assigned as maker per §5. `WP-P35-04` and `WP-P35-05` remain subject
to their dependencies. Production activation remains unauthorized.

After ratification:

1. update each source decision record with its decision and approver;
2. update `docs/decisions/DECISION-REGISTER.md`;
3. update `BOPEN-P35-001` status and role assignments only to the extent actually approved;
4. update controlled status, coverage, traceability, changelog, and manifest records;
5. run repository, clean-room, evidence-anchor, ballot-attribution, and authority checks;
6. begin only the first accepted and assigned work package.

## 7. Stop and rollback conditions

- A rejected runtime gate leaves all Phase 3.5 work proposed.
- A returned storage decision blocks its dependent migration work.
- A returned authentication-boundary decision blocks `WP-P35-05`.
- A returned audit decision preserves the two-envelope interim and blocks convergence work.
- A missing authority identity, timestamp, or required concurrence is not ratification.
- A failing mandatory validator or unresolved reproducible refutation returns the affected
  item to `HOLD`.

Because this docket changes no contract, migration, or production source, rollback is removal
of this proposed candidate and its control-register entries. Accepted decisions are not rolled
back by deleting this docket; they require a new governed decision.

## 8. Preparation provenance

Prepared by Codex as an advisory, reversible next step under the user instruction to proceed
according to `BOPEN-PRD-P35-001` and `BOPEN-P35-001`. The preparation used the live decision
records and did not alter their status or approval fields.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
