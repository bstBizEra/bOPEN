# Documentation Changelog

## 2026-08-01 - The last verifier seat is a role conflict, not a dispatch

- Kimi is unavailable, so the second seat on `WP-P35-01`..`03` was re-scoped. **Gemini cannot fill
  it** — it is already the sole verifier there, and EBIV §3.1 counts sequential verifiers who can
  read prior verdicts as one. A second Gemini pass adds ballots, not a verifier.
- **Codex is the only remaining eligible agent, and this was verified rather than assumed.**
  `git log --format='%an'` over `db.py`, `tokens.py`, `db_bootstrap.py` and their tests returns
  only `BizEra` and `Claude Opus 5`. Codex appears nowhere, so §3's exclusion — which is on having
  *authored* an artifact — does not bite. Its maker assignment there is prospective.
- Raised `DEC-P35-VERIFIER-REASSIGN`: Codex cannot hold maker and verifier on the same package, so
  one has to give. Recommends Codex verify now and the remediation maker seat return to Claude,
  who already authored those packages and so creates no new exclusion.
- The argument is ordering, not preference. **Verification precedes remediation** — you remediate
  what verification finds. Codex's maker assignment was made on 2026-07-31 when nobody had
  verified anything, so its remediation scope is currently guesswork; two verifier passes would
  give it an actual defect list.
- Recorded why this matters most for `WP-P35-01`: its single existing verifier used the maker's
  own `test_rls_database_behavior.py` as the `probe_command` for **13 separate ballots**. That
  establishes the named test passes. It does not establish that anyone tried to break tenant
  isolation and failed — and disposing that package on §6.3 would leave the platform's primary
  security property on the thinnest evidence in the repository.
- Corrected the phase manifest, which still read `ballots_cast: 0` and `quorum_status:
  UNREACHABLE`. Quorum is now recorded per candidate; Kimi's seat reads stood down rather than
  pending.


## 2026-08-01 - F-6 reconciled after enumeration, and the Kimi seat re-scoped

- **F-6 updated.** `D-CP-003` enumerated the live catalogue: `pg_policies` reports **27 active
  policies across 16 tables**, every `qual` and `with_check` inspected, and **exactly one** carries
  a cross-plane dependency — `principals_read` on `principals`, whose `USING` clause is
  `EXISTS (SELECT 1 FROM memberships …)`.
- That is materially better than F-6 first assumed. The exposure is one policy, not an uncounted
  class. It does not dissolve the finding: `principals` is control-plane by F-2 and `memberships`
  is tenant-scoped, so the policy still cannot be evaluated across a split and the 6,657-row
  disclosure still reopens unless `memberships` is co-located, projected, or the policy replaced.
- **`PRD-P35B-PLANE-001` is no longer blocked on counting** — it is blocked on deciding
  `memberships`' plane. A single decision instead of an open survey.
- The PRD and the docket had been contradicting each other since the enumeration landed: one said
  ENUMERATED, the other said never counted. Reconciled.
- **Handoff re-scoped after Gemini ruled.** `WP-P35-04` now holds quorum and no longer needs a
  seat, except for `P35-04R-15`/`16` which postdate Gemini's run and remain unballoted.
  `WP-P35-01`..`03` have one verifier each, so **Kimi is the second seat** and the only remaining
  route to quorum on those three.
- Added §3.1 to the handoff: an explicit probe bar. Independent probes (Codex's 90 hostile
  combinations, Gemini's 14 hand-written gateway probes) establish that an agent constructed an
  attack and it failed. Named-test reruns establish that the maker's test passes. Both are
  legitimate; **only the first is refutation**, and 32 of 63 ballots so far sit in the second
  tier. For `WP-P35-01`'s isolation invariants the handoff now asks for hand-written SQL rather
  than a rerun of `test_rls_database_behavior.py`.


## 2026-08-01 - The quorum check was counting the wrong thing

- Gemini cast 49 ballots (`adc97fc`, author `gemini@bst.local`): 14 on `WP-P35-04` and the first
  ever on `WP-P35-01`, `02` and `03`. Verified from repository objects — anchors match the
  submissions, the proposition IDs resolve to `invariant-traceability.csv`, and the 14 gateway
  probes are independently written rather than reruns of the maker's suite.
- **`check_ballot_attribution.py` counted verifiers per phase, not per work package.** It
  reported *"2 attributable verifier(s) toward a quorum of 2 — PASS"* while three of four
  candidates had a single verifier each. EBIV §3 assigns roles per work package and §6.1 requires
  two verifiers to confirm a proposition, so quorum is a per-candidate property.
- The false reading propagated into **two** agent reports before anyone checked by hand, both
  claiming "2-of-2 quorum MET" across all four packages. Neither agent was wrong to say it — the
  tool told them. **A check that reports a weaker property than the rule it enforces is worse
  than no check, because its PASS gets quoted as if it were the rule.**
- Fixed: quorum is now counted and reported per candidate commit. Corrected output —
  `88e6ed2` (`WP-P35-04`) has two verifiers and holds quorum; `6ce069e`, `a969bb5` and `767cb81`
  have one each and are recorded `quorum NOT MET`.
- The exit code deliberately stays `0` on a shortfall. Attribution is what this tool attests, and
  EBIV §6.3 makes a shortfall an escalation to the Completion Authority rather than an error. But
  the summary now names every short candidate and states that the PASS attests attribution only.
- This is the same defect class as `check_evidence_anchors.py` verifying that an OID *resolves*
  rather than that it names the work it claims. Both are the enforcement mechanisms the whole
  governance model rests on, and both check something weaker than the rule.
- Quality note recorded rather than smoothed: 32 of Gemini's 49 ballots use the maker's own test
  files as `probe_command`. Following the traceability CSV's named test is legitimate and
  establishes that the test passes at that commit. It does not establish that an independent
  agent tried to break the invariant and failed, which is what EBIV §8 means when it says a
  maker's passing suite carries no verdict weight.
- 63 ballots, zero refutations, zero abstentions. `P35-04R-15` and `16` — offered by the maker
  *expecting* refutation — remain unballoted.


## 2026-08-01 - AUTH-D1 disposed and cross-plane RLS dependencies enumerated

- Recorded the operator's acceptance of `AUTH-D1` option 3: every protected endpoint derives
  authority from a verified signed bearer token, with no fallback to `X-Context-ID`. The research
  annex supplies the normative basis independently of `AUTH-D3`.
- Kept `AUTH-D3` open. A self-naming enrollment credential is recommended only as a separate,
  single-use, 10-minute, local out-of-band enrollment trust domain; the authorities must decide
  whether reintroducing bearer-by-identifier authority under those bounds is acceptable.
- Executed the `D-CP-003` inventory against live PostgreSQL: 27 active policies on 16 tables,
  exactly one cross-table dependency - `principals_read` queries `memberships`.
- The enumeration is complete but plane assignment remains blocked. Since `principals` is
  control-plane, membership visibility must be co-located, projected with enforced consistency,
  or replaced by another database-enforced boundary. The unscoped system-role aperture also
  remains explicit.
- No implementation, migration, RLS policy, ballot, or production activation changed.

## 2026-08-01 - A third proposition found to overclaim, and a verifier seat reopened

- Amended `EVD-P35-04-MAKER-R2` with section 6A. The candidate commit is unchanged at `88e6ed2`,
  so Codex's 14 ballots remain valid and are not reopened; only the proposition set grows.
- Added `P35-04R-15` (path fidelity) and `P35-04R-16` (base-path containment), both offered by the
  maker **expecting `REFUTED`**. A defect recorded only in a prose limitations section cannot be
  balloted and therefore cannot block, and EBIV §6.1 gives a single refutation with a reproducible
  probe the power to block. These move two known defects from prose into the ballot record.
- **Found while writing them: `P35-04R-02` overclaims.** It asserts a base path prefix survives;
  its test exercises only a path with no dot segments. Measured: base `/api` with `/../../admin`
  yields `/admin` — **the prefix is escapable**. Codex's `CONFIRMED` on it is not an error, it
  ruled on what the proposition asserts, but the proposition asserts more than its test checks.
- That is the **third** instance in two days of the same defect shape: revision 1's path test
  (fixture had no `.` or `%`, hid a critical SSRF behind 31 green tests), section 6.1's path
  normalisation (no proposition claimed it at all), and now this. The recurring fault is in how
  propositions are written, not in any one mechanism, and the new Gemini/Kimi handoff names it as
  the fastest route to a real defect.
- `P35-04R-16` is latent rather than live: with no base path configured — the documented
  deployment — there is nothing to escape. No code change accompanies the amendment, because
  fixing now would move the candidate and invalidate the only independent verification this
  repository has for a second time. The fix is recorded as owed and must land before `WP-P35-04`
  reaches a Completion Authority.
- Issued `HANDOFF-P35-VERIFY-R2-TO-GEMINI-KIMI` and superseded the 2026-07-30 handoff, which
  predated the SSRF, the R2 reissue, `WP-P35-05a` and Codex's ballots entirely. Dispatching it
  would have repeated the stale-anchor mistake Codex caught.
- The new handoff asks for two things: the **second verifier seat** on `WP-P35-04`, where quorum
  stands at 1 of 2, and the **first ever look** at `WP-P35-01`..`03` — which only Gemini or Kimi
  can give, since Claude authored them and Codex remediates them. `WP-P35-01` carries the tenant
  isolation claim, the most consequential unverified assertion in the repository.
- No contract, migration, specification or production source changed.


## 2026-08-01 - The first ballots in this repository's history, and what they do not establish

- Codex cast **14 admissible `CONFIRMED` ballots** on `WP-P35-04` R2 at `88e6ed2`, committed as
  `0d12332` under its own identity. Independently verified from repository objects: author *and*
  committer are `codex@bst.local`, the commit touches only `ballots.jsonl`, every ballot anchors
  the exact commit and tree that were issued, and none is missing a mandatory probe field.
- **Quorum is not met and no confirmation is realized.** `BOPEN-GOV-EBIV-001` §6.1 requires two
  independent verifiers; there is one. `check_ballot_attribution.py` states the shortfall on its
  own face — *"quorum NOT MET — a confirmation cannot be realized"* — which is the tool refusing
  to let a partial result read as a pass.
- Codex's adversarial probes: 90 hostile path and search combinations against the SSRF fix, no
  origin escape found. Canonical suite 433/433, gateway suite 43/43, attribution, anchors,
  repository validation and clean-room all PASS.
- **The maker's proposition set had a hole, and Codex's precision exposed it.** Path
  normalisation remains reproducible — `/v1/../admin` still reaches the kernel as `/admin` — but
  Codex correctly declined to refute any of `P35-04R-01`..`14` on it, because **none of the
  fourteen propositions claims path fidelity**. So a real, reproduced defect passed through the
  ballot untouched, not because the verifier missed it but because the maker never offered a
  claim it could contradict.
- That is the same failure shape as revision 1: propositions that were true, and did not cover
  the line that mattered. Revision 1's gap was a critical SSRF; this one is a known MEDIUM defect,
  recorded in `EVD-P35-04-MAKER-R2` §6.1 as open rather than accepted. **A ballot can only rule on
  what it was offered.**
- `WP-P35-05a` untouched, per Codex's standing `HOLD_FOR_DECISION`.
- Registers updated: `AGENTS.md` §20.2, work-package register, document status, action plan. The
  2026-07-31 status-correction note in the work-package register said *"no ballot has been cast"*
  and is now itself corrected — one day old and already drift.

## 2026-08-01 - Codex preflight stops stale WP-P35-04 and 05a ballots

- Bound the live branch to commit `88e6ed2b4f2ab80a6b8ef0e8d570f761d8725b4b`
  and tree `39da471ae01ade3e3ee619f788d99fabbe1fde3d` before verification.
- Marked the Codex ballot handoff `HOLD`: WP-P35-04 still names the pre-SSRF-fix candidate
  `c03cd4f...`; current gateway subtree is `485f6b3...` and passes 43/43 tests.
- Did not rewrite Claude's maker submission, preserving Codex verifier independence. Claude must
  reissue the proposition set against the corrected exact commit.
- Established that WP-P35-05a has no later implementation blob to anchor. Repointing it to HEAD
  would falsely imply repair.
- Executed live PostgreSQL-backed probes showing a configured authenticator still permits
  `200 ALLOW` through the unsigned legacy context path, and unauthenticated principal and tenant
  creation still return `201`.
- Raised `DEC-P35-AUTH-CLOSURE` with explicit advisory recommendations for `AUTH-D1` and
  `AUTH-D3`. No decision, implementation authority, ballot, or completion is claimed.

## 2026-07-31 - Phase 3.6 opened: roadmap, implementation plan, action plan, engineering loop

- **Roadmap extended.** Phase 3.6 — Tenant Privacy and Platform Observability — inserted between
  3.5 and 4 in `roadmap.md` and `PHASE-OUTLINE-SPEC.md`. The phase count is now **seven**; the
  overview previously said five, then six, having twice not been updated when a phase was
  inserted. It now carries the date it was last checked, because a count is a fact that drifts
  silently.
- **Implementation plan** `BOPEN-P36-001`: 10 deliverables (D-16..D-25), 10 acceptance criteria
  (A-17..A-26) each inheriting a removal probe from `BOPEN-PRD-P35-002`, a dependency-ordered
  sequence, risks and rollback. Entry is **blocked** pending Security and Privacy review.
- Sequencing states its own reasoning: cross-plane integrity is placed *before* placement routing,
  because building routing first would let tenants be placed into a topology whose integrity story
  is unwritten, creating the orphans before the mechanism that refuses them exists.
- `A-21` is named as the criterion carrying the guarantee — control-plane credentials refused by
  PostgreSQL, not by application code declining to issue a query.
- **Action plan** `BOPEN-GOV-ACTION-001`: twelve sequenced actions with owners and gates, plus a
  register of what is deliberately *not* being done so absence reads as decision rather than
  oversight. Its critical path is not on any execution plan — **seat a verifier**. Three actions
  are available today with nothing blocking them; the rest are gated.
- **Engineering loop** `BOPEN-ENG-LOOP-001`: the nine-stage cycle from bind to record, with stage
  8 (verify) marked as where the loop stops if nobody is seated. Includes the mutation-probe
  discipline, the anchor rules, the required-check list, and eight anti-patterns — every one of
  them observed in this repository rather than imagined.
- **Status correction in `WORK-PACKAGE-REGISTER`.** `BOPEN-P1-001` and `BOPEN-P2-001` were
  recorded as *Completed & Verified*, and `BOPEN-P3-001` as *GO ON EVIDENCE*. All three conflict
  with `AGENTS.md` §20.2, the operative gate register, which records them `IMPLEMENTED_UNVERIFIED`.
  No ballot has ever been cast here. The authorizations were real; the verification was not.
  "Verified" had meant a passing suite, which EBIV §8 holds to be maker self-assessment carrying
  no verdict weight.
- Document status register extended with the PRD, both new decisions, the P36 plan, the action
  plan, the engineering loop and the baseline register.
- No contract, migration, specification or production source changed.

## 2026-07-31 - PRD research for the hybrid-placement plan

- Added `BOPEN-PRD-P35-002`, requirements for tenant privacy and platform observability under
  the hybrid-placement architecture. Additive to `BOPEN-PRD-P35-001`, which addressed runtime
  assurance of the single-database kernel and remains valid.
- Five findings established by inspection at `arch-baseline/2026-07-31-rls-option-c`, then
  **queried against the live PostgreSQL instance** rather than left as readings of the SQL:
  - **F-1**: **12** foreign keys reference `tenants`, `principals`, `memberships` or
    `active_contexts` and cannot survive a plane split, because PostgreSQL cannot enforce a
    foreign key across databases. Reading the migrations had given five; the database reported
    twelve. The reproduction query is included in the PRD.
  - **F-2**: `principals_email_key` makes email globally unique, forcing `principals` into the
    control plane — which means the control plane necessarily holds personal data. As drafted,
    `DEC-P35-CONTROL-PLANE` §4 forbids exactly that. The prohibition needs refining before
    ratification, not after.
  - **F-3**: `audit_events` carries `action`, `resource_type` and `resource_id` — business
    identifiers. Platform security monitoring wants them central; tenant privacy wants them
    tenant-side. Both defensible, incompatible, undecided.
  - **F-4**: `usage_meter_balances.tenant_id` is `character varying` against `tenants.id` `uuid`,
    with 0 foreign keys. Metering is already plane-portable by accident.
  - **F-5**: nothing in the schema records placement. The new load-bearing concept does not exist
    in the model.
- Ten requirements with removal probes, and an acceptance matrix where each proposition names the
  mutation that must break it. `PRD-P35B-CRED-001` is the one that makes privacy structural: the
  control plane holds no credential for any tenant database, so it cannot read business rows even
  if asked.
- **Recorded a false negative rather than hiding it.** The first verification query returned zero
  foreign keys and looked like a refutation of F-1. The cause was
  `information_schema.constraint_column_usage` filtering by table ownership under the
  unprivileged application role. Re-run against `pg_catalog` it returned twelve. A PRD whose
  findings were never executed is what EBIV R1 exists to refuse, so both the undercount and the
  false negative are in the provenance section.
- Delivery sequence puts Security and Privacy review of `DEC-P35-CONTROL-PLANE` first and
  blocking, because F-2 and F-3 must be resolved there rather than in code.
- No contract, migration, specification or production source changed. The PRD carries no
  implementation authority.

## 2026-07-31 - Tenant privacy: hybrid placement, and a boundary for what the platform may see

- Captured `arch-baseline/2026-07-31-rls-option-c` at `9e26c0b` **before** changing the
  architecture, per the new `AGENTS.md` §23 rule. An annotated tag rather than a copied folder:
  content-addressed, cannot drift, costs no disk, verifiable indefinitely.
- **`DEC-P35-TENANCY-MODEL` §8 supersedes §7.** Option D — hybrid placement — replaces Option C:
  a dedicated database per tenant by default, with a shared RLS pool for trial and free-tier
  tenants who must be told they are sharing.
- The reversal is legitimate rather than a contradiction, and the record predicted it. §7 recorded
  its driver as *load, not isolation*, and stated that an isolation driver would make
  database-per-tenant stronger and require Security concurrence. The operator then stated a
  tenant-privacy requirement. The analysis did not change; the question did.
- **`ADR-0005` and `BOPEN-ARCH-001` stand.** RLS remains the live mechanism for the shared pool,
  so the 16 policy-bearing tables and the 38 executed isolation tests keep their meaning. That is
  the principal reason Option D was preferred to Option B: no evidence is discarded to gain the
  isolation.
- `WP-P35-06` is **generalized, not withdrawn** — shard routing becomes placement routing, and the
  resolver returns a connection target that may be a dedicated database or a shared pool. Two
  criteria added: `A-15` requires that a tenant placed as `dedicated` be unroutable to the shared
  pool *by construction*, with a negative probe showing the attempt fail; `A-16` requires the
  shared pool to remain covered by the existing isolation suite.
- Raised `DEC-P35-CONTROL-PLANE` to answer the operator's second requirement — that private
  tenants must not blind the platform. Control plane holds usage aggregates, operational
  telemetry, authorization outcomes, lifecycle events and entitlement state; tenant business rows,
  field values, free text and literal-bearing query logs never cross. The platform can know a
  tenant's call count, storage, latency and quota without reading one invoice.
- Recommended that the boundary be **structural, not procedural**: the control plane holds no
  credential for any tenant database and aggregates are pushed outward, never pulled. A boundary
  that depends on the platform choosing not to look is not a boundary.
- Flagged the one that needs care: row counts are metadata, but row-count *patterns* tracked
  across an industry are market intelligence nobody granted permission to derive.
- **`DEC-P35-CONTROL-PLANE` is NOT ratified.** It creates a data flow out of tenant boundaries and
  requires Security and Privacy Authority review before implementation. The tenancy change was
  ratified because it tightens isolation; this one is not a tightening and is recorded as
  unreviewed rather than assumed.
- No contract, migration, specification or production source changed.
- **Authority:** operator decision transcribed by Claude (agent, Motor role).
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Tenancy model decided: shard for load, keep RLS for isolation

- Raised and ratified `DEC-P35-TENANCY-MODEL` in response to a request to adopt an
  ERPNext/Frappe-style database-per-tenant model to avoid overloading one database.
- **Option C adopted:** tenants shard across PostgreSQL instances; row-level security is retained
  within each shard. `ADR-0005` and `BOPEN-ARCH-001`'s isolation clause stand unchanged. No RLS
  policy or isolation test is removed.
- The driver was recorded explicitly as **load, not isolation**, because it changes the answer.
  Had it been regulatory or blast-radius isolation, database-per-tenant would have been stronger
  and Security Authority concurrence would have been required.
- The premise was examined rather than accepted: separate databases do not distribute load —
  separate *instances* do. Fifty databases on one server share a buffer pool, a WAL writer and a
  connection limit while adding fifty catalogs, autovacuum targets and migration runs. Load
  distribution and the isolation mechanism are independent axes, and only the first is about
  load.
- Also recorded: Frappe needs a database per site because sites carry structurally different
  schemas, a constraint bOPEN designed out via versioned capability contracts; and Frappe runs on
  MariaDB, which the technology matrix rejected for this platform on the ground of weak native
  RLS.
- **Clean-room boundary stated:** cloning Frappe source is prohibited by `AGENTS.md` §6 and
  enforced by `check_clean_room.py`. Independent implementation of the pattern is permitted, and
  every option assumed it.
- Option D (RLS by default, dedicated database for named tenants) remains available per case
  without a further architecture decision, since §8 already permits approved physical isolation.
- Added `WP-P35-06` specifying shard routing, with the risk stated before any code exists:
  sharding moves failure from "policy is wrong" to "routing is wrong", and RLS cannot catch a
  mis-routed tenant because the session is correctly scoped to a tenant with no rows on that
  shard — a silent wrong answer rather than a refusal. `A-09` and `A-11` therefore require
  refusal, never an empty result, and `A-14` requires single-shard behaviour to be identical so
  the change is additive.
- **Rebalancing is explicitly deferred and named**, so that placement being effectively permanent
  is a known constraint rather than a later discovery.
- No contract, migration, specification or production source changed.
- **Authority:** operator decision transcribed by Claude (agent, Motor role).
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - WP-P35-05 split, and the kernel gains an authentication boundary

- `DEC-P35-IDP-SPLIT` ratified: `WP-P35-05` becomes `05a` (kernel authentication boundary,
  stays in Phase 3.5) and `05b` (BoxyHQ federation, moved out and still blocked). The trigger
  was that `D-P35-014` is a *licensing* re-verification, so a runtime security hole was waiting
  on a legal question about a third party.
- **Correction recorded in the decision itself.** The advice that prompted the split said it
  would leave `05a` needing only the design decisions. That understated the position: no
  migration defines `sso_connections`, `external_identities` or `authentication_sessions`, so a
  per-tenant connection model needs new tables and lands back on the unratified
  `D-P35-004`..`D-P35-010`. Splitting removes the vendor from the critical path, not the storage
  decisions.
- Implemented `WP-P35-05a`. The kernel now verifies a signed, audience-bound assertion from an
  external authenticator before issuing a context, instead of taking the caller's word. Three
  properties are the point, and each has a negative probe: a partial configuration refuses
  rather than opening the unauthenticated path; a configured authenticator **cannot** be
  disabled by `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`; and an assertion vouching for
  one principal cannot mint a context for another.
- Two mutation probes: letting the development flag win broke 5 tests including the central one;
  removing the principal comparison broke the impersonation test.
- Binding is by issuer and subject only — no email claim is read, per `D-P35-012`. The assertion
  is never persisted, per `D-P35-010`.
- **Limits recorded rather than left to be discovered:** one authenticator for the whole kernel,
  no per-tenant connections, **no replay protection** (`jti` is checked but not stored, because
  storing it is the persistence that is blocked), no key rotation, and no other endpoint
  authenticated yet. Listed in `EVD-P35-05A-MAKER` §5.
- Also recorded: the module's own claim type-check is currently unreachable because PyJWT
  rejects non-string `sub`/`iss`/`jti` first. Kept as defence in depth but marked redundant, and
  the tests assert refusal rather than which layer refused.
- Canonical suite 433/433 against PostgreSQL. `WP-P35-05a` is `IMPLEMENTED_UNVERIFIED` with zero
  ballots; a maker reporting a green suite carries no verdict weight (EBIV §8).
- Committed separately: Addendum C of `EVD-SEC-001` and its `api.py` correction, authored in an
  earlier session and found uncommitted. They are one unit and landed together rather than being
  bundled into unrelated commits.
- **Authority:** operator decision transcribed, implementation by Claude (agent, Motor role).
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - WP-P35-04 API gateway implemented

- Built `apps/gateway` — a Hono reverse proxy validating the `HTTP_HEADER_SPEC.md` contract at
  the platform edge. This closes blueprint layer 1, which `DEC-P35-RUNTIME` §3.1 recorded as
  having no implementation at all.
- 31 tests pass with no kernel process required. Written to EBIV R4: every rule carries a
  negative probe, because a happy-path test passes just as well once the mechanism is deleted.
- Executed three mutation probes to establish the suite can fail — relaxing the correlation-ID
  limit, stripping identifier prefixes on forward, and dropping `.strict()` from the contract
  binding each broke exactly one test. Tree restored and re-verified at 31/31 after each.
- **Defect found and recorded:** the identifiers documented in `HTTP_HEADER_SPEC.md` are not
  RFC 9562 conformant — `tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c` carries variant nibble `5`.
  Zod 4's `z.uuid()` enforces the RFC and made the gateway stricter than the kernel it fronts,
  rejecting requests the kernel would have served, including the repository's own examples. The
  gateway validates UUID shape only and a test locks that in. Whether bOPEN identifiers should
  be RFC-conformant is left with `D-P35-004` rather than answered in a regex.
- Recorded what the gateway declines to do and why: it never rewrites or injects `X-Tenant-ID`,
  never strips prefixes, never truncates `X-Correlation-ID`, never reports kernel health from
  its own endpoint, never echoes an offending value in a 400, and never reinterprets an upstream
  status. Each would break something specific; the reasons are in `apps/gateway/README.md` §3.
- Added `EVD-P35-04-MAKER` with 12 falsifiable propositions, each naming a test and the
  mechanism whose removal makes it fail. Anchors read from git with `git rev-parse`, not
  transcribed, per EBIV R3 and `A-07`.
- Three runtime dependencies pinned exactly (`hono`, `@hono/node-server`, `zod`); Node 24 native
  type stripping means no build step and no transpiler in the tree.
- **Not established:** any end-to-end path. The suite injects the upstream, so no request has
  been executed through the live kernel to PostgreSQL and back. Also unaddressed: upstream
  timeouts, retries, rate limiting and TLS. Recorded in the submission §6.
- `WP-P35-04` is `IMPLEMENTED_UNVERIFIED` with zero ballots. Eligible verifier: Codex, Gemini or
  Kimi. A maker reporting a green suite carries no verdict weight (EBIV §8).
- **Authority:** implementation by Claude (agent, Motor role) as assigned maker.
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Executed baseline measured, and a correction

- Executed the canonical suite against the real PostgreSQL verification instance with
  `.env.local` sourced: **414 of 414 pass** in 85s — unit 139, integration 125, contracts 101,
  isolation 38, governance 11. Migrations `001`..`009` are applied to `bopen_dev` on port 5433.
- All governance checks pass with the environment sourced: repository validation, clean-room,
  authority bootstrap, evidence anchors, ballot attribution, and contract conformance
  (11 of 16 constrainable schemas covered, 5 recorded as debt).
- **Correction.** Two earlier reports in this session — the handoff §3 and the maker-split
  changelog entry — stated that the suite fails on an unset `BOPEN_DATABASE_URL` and that no
  admissible evidence existed for the tenancy invariant. Both were wrong. The cause was a shell
  that had not sourced `.env.local`, not a missing database. The 38 isolation tests do execute
  against PostgreSQL, so EBIV R1 and acceptance criterion `A-05` are satisfied for tenancy. The
  wrong text is corrected in place with the error left visible rather than removed.
- **No phase status changes.** `WP-P35-01`..`WP-P35-03` stay `IMPLEMENTED_UNVERIFIED`, but the
  reason is now different and should be read differently: it was *evidence cannot be produced*;
  it is now *evidence exists and no independent verifier has ruled on it*. Zero ballots are
  recorded. `BOPEN-GOV-EBIV-001` §8 holds that a maker reporting a green suite carries no
  verdict weight, and this entry is a maker report.
- Redirected Codex's remediation scope accordingly: the work is not to make the tests pass, but
  to establish what a green suite is not covering — the 5 uncovered schemas, the unclassified
  `membership-transition-matrix.json`, invariant traceability, and whether `003`'s rollback has
  been executed rather than merely written.
- **Authority:** measurement and reporting by Claude (agent, Motor role).
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Phase 3.5 maker split and Codex handoff

- Replaced the sole-maker assignment with an alternating split, so Claude and Codex both
  implement: Codex makes `WP-P35-01`..`WP-P35-03` (remediation), Claude makes `WP-P35-04`.
  `WP-P35-05` stays unassigned because it is blocked.
- Rationale recorded rather than assumed: `BOPEN-GOV-EBIV-001` §3 excludes a verifier who
  authored any artifact under review, so each additional maker on a package removes an eligible
  checker. Co-making everything would have left every Phase 3.5 ballot resting on Gemini and
  Kimi, neither of which has cast a ballot or holds a commit identity here. Alternating keeps
  each engine eligible on the other's work.
- Confirmed against the standard before assigning: roles are per work package and mutually
  exclusive within it (`BOPEN-GOV-EBIV-001` §3), so co-makers are permitted; the constraint is
  on verifier eligibility, not on the number of makers.
- Added `HANDOFF-P35-MAKER-SPLIT-TO-CODEX` in `docs/00-governance/handoffs/` — tracked
  governed documentation, not an untracked root file per `AGENTS.md` §19.2. It names the
  assignment, the unratified decisions that remain off-limits, and the commit-identity
  requirement.
- **Corrected same day:** this entry and handoff §3 originally reported that the canonical
  suite fails on an unset `BOPEN_DATABASE_URL` and that no admissible evidence existed for
  tenancy. Both were wrong — the failures came from a shell that had not sourced `.env.local`.
  See the 2026-07-31 executed-baseline entry below for the measured state.
- Marked `HANDOFF-P35-PARALLEL-TO-CODEX` superseded. It proposed the opposite split (Codex on
  `WP-P35-04`) and is retained as a record only.
- Updated `AGENTS.md` §22.3, `DEC-P35-DOCKET` §5.1-§5.3, `BOPEN-P35-001` completion record and
  the agent alignment register to carry the same table.
- No decision status changed. No contract, migration, or production source changed. All five
  packages' verification state is unaffected; assigning a maker verifies nothing.
- **Authority:** operator decision transcribed by Claude (agent, Motor role).
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Phase 3.5 gate ratified and maker assigned

- Operator ratified `D-P35-001`..`D-P35-003` as Architecture and Engineering Authority.
  `DEC-P35-RUNTIME` moves Proposed to Approved (Option C); `BOPEN-P35-001` becomes the accepted
  Phase 3.5 work package. Recorded in `DEC-P35-DOCKET` §6.1 and `DEC-P35-RUNTIME` §8.
- Assigned **Codex** as maker for all Phase 3.5 work packages, including remediation of
  `WP-P35-01`..`WP-P35-03`. Codex's verifier seat on that evidence record — stood down by the
  operator on 2026-07-30 — is released deliberately rather than left recorded as unreached.
- Recorded the consequence rather than smoothing it: under `AGENTS.md` §20.3 item 1 Codex may
  now cast no Phase 3.5 verdict, and Claude is disqualified on `WP-P35-01`..`WP-P35-03` by
  authorship, so the independent checker there must be Gemini or Kimi. Neither has cast a
  ballot or holds a commit identity in this repository. Logged as an open risk.
- Added `AGENTS.md` §22 (extend-only) and updated the §20.2 gate table. §22.1 records that no
  rule ever restricted which engine may write code — §19.3 already names Codex as the
  implementer and §20.4 already makes specialization guidance rather than assignment. No
  amendment to either was made.
- Left `D-P35-004`..`D-P35-018` undecided. Phase 2 persistence migration design, `WP-P35-05`,
  audit-envelope convergence, and acceptance of `BOPEN-PRD-P35-001` all remain blocked.
  Security Authority and Product Authority concurrence is absent and is recorded as absent.
- Phases 1-3 and `WP-P35-01`..`WP-P35-03` remain `IMPLEMENTED_UNVERIFIED`. No evidence artifact
  was edited; opening a gate verifies nothing already written.
- No contract, migration, or production source changed in this entry.
- **Authority:** operator decision transcribed by Claude (agent, Motor role).
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Phase 3.5 storage ambiguity recommendations

- Added `DEC-P35-PHASE2-STORAGE-ADD-001` with advisory closure recommendations for the two
  unresolved Phase 2 storage semantics.
- Recommended one effective group-role mapping per directory/group, with
  `mapping_policy_version` retained as an auditable revision stamp and prior revisions kept
  as history.
- Recommended prohibiting overlapping usable delegated-grant intervals for one
  principal/tenant because the approved delegated-context contract carries one `dgr`.
- Executed an order-reversal probe that reproduced first-row selection for both mappings and
  grants; no repository or database state was changed by the probe.
- Updated the docket and document controls without accepting either recommendation,
  authorizing a migration, or changing production code.
- **Authority:** Advisory design preparation only.
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Phase 3.5 entry decision docket

- Added `DEC-P35-DOCKET-001` as the bounded next step in `BOPEN-PRD-P35-001`
  sequence 0.
- Consolidated the four proposed Phase 3.5 decision records into one review surface with
  dependency order, proposed dispositions, required authority concurrence, entry effects,
  role assignments, and explicit ratification fields.
- Preserved unresolved choices for group-role mapping version semantics and overlapping
  delegated grants rather than selecting them by implementation default. Advisory
  recommendations were added subsequently and remain pending authority disposition.
- Registered and traced the docket without changing any source decision, contract, migration,
  production source, phase status, or authority field.
- **Authority:** Advisory decision preparation only.
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-31 - Review-driven Phase 3.5 product requirements candidate

- Added `BOPEN-PRD-P35-001`, a proposed and non-authorizing PRD that converts the
  independently reproduced authorization, identity-binding, metering provenance, module
  lifecycle, transactionality, contract, dependency, and status-control gaps into falsifiable
  requirements and acceptance tests.
- Mapped the requirements to the existing `BOPEN-P35-001` sequence without opening Phase 4,
  approving `DEC-P35-RUNTIME`, amending approved specifications, or granting production authority.
- Registered the candidate in the artifact, coverage, status, and traceability controls.
- **Source:** Live working-tree review at commit
  `4e1bcedeb62e5b0c3a6e14915ac44083d251f017`, with the two pre-existing modified paths
  disclosed in the PRD provenance.
- **Authority:** Advisory document preparation only.
  `execution_authority: false`; `approval_authority: false`.

## 2026-07-29 — Evidence and Phase 3 contract-control repair

- Corrected `EVD-P2-DECISION-001` from an unsupported conditional-acceptance claim to
  maker-side technical evidence with independent, security, and completion authority pending.
- Corrected `D-P2-015`: migration `001_tenant_isolation_baseline.sql` contains no durable
  transactional outbox.
- Repaired `tools/run_tests.py` so contracts are mandatory and category totals are reported.
- Added six Phase 3 schema-control tests and tightened the seven Phase 3 schemas for lifecycle,
  context, idempotency, quota, reason-code, and rate-limit consistency.
- Aligned artifact, coverage, status, traceability, and work-package registers with the
  Phase 3 implementation hold. No Phase 3 production source or migration was created.
- **Source:** Direct repository inspection and deterministic local verification.
  **Timestamp:** `2026-07-29T06:57:43Z`. **Agent ID:** `Codex`.
- **Reason:** Repair evidence-integrity and contract-test gaps before any Phase 3 entry gate.
  **Benefit of old phase:** Earlier artifacts collected the intended milestones, roles, and
  risks. **Expected outcome:** Verifiable contract-freeze evidence that cannot be mistaken for
  approval, production authority, or Phase 3 implementation authority.

## 2026-07-29 — Phase 2 entry and implementation

- Bound `BOPEN-IDP-001` (Approved for Phase 2) into `docs/04-platform/`; marked
  `BOPEN-IDP-001-DRAFT.md` **Superseded** with a pointer to the replacement (WP-P2-01).
- Bound `BOPEN-P2-001` execution plan into `docs/work-packages/`; registered
  `BOPEN-P1-001` and `BOPEN-P2-001` in the work-package register.
- Recorded `DEC-0007` (adopt IDP-001), `DEC-0008` (bind P2-001) and `DEC-0009`
  (ADR/decision resolution — **Open, blocking**).
- Added `AGENTS.md` §3.1 recording the Phase 2 implementation hold.
- Implemented `MILE-2.1`..`MILE-2.5` (invitation engine, membership state machine,
  tenant context switching, enterprise IdP/SCIM bridge, delegated cross-tenant access)
  with 145 passing tests.
- **Implementation proceeded ahead of the `BOPEN-P2-001` §23 entry gate on explicit
  operator direction.** The deviation, the thirteen decisions taken by implementation
  default, and the known gaps are recorded in
  [`docs/evidence/phase-2/provisional-decisions.md`](evidence/phase-2/provisional-decisions.md).

## 2026-07-13 - local preparation

- Prepared downloaded BOPEN-BOOT-001 full pack for local version control.
- Fixed `pnpm test:governance` quoting so unittest discovery works in Windows PowerShell.
- Added local bootstrap validation evidence for BOOT-P0-05.

## 2026-07-12 — v1.0

- Created BOPEN-BOOT-001 full AGENTS.md and documentation bootstrap pack.
