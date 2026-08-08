# EVD-P35-01-MAKER — WP-P35-01 Maker Submission

**Document ID:** `EVD-P35-01-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — this is not a completion decision
**Issued:** 2026-07-30
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-01`
**Commit:** `6ce069e3c3e09b4d33323d4d8d185b6c796213c0`
**Tree:** `434bc7302711efd5ed01b4a133a35a48cb994986`
**Maker:** Claude (agent, Motor role)
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> This document deliberately does **not** claim completion. Under EBIV §3 the Maker does not
> vote on its own work, and under §6.1 two independent verifiers are required to realize a
> confirmation. Zero ballots have been cast. The correct current status is
> `IMPLEMENTED_UNVERIFIED`, and it stays that way until verifiers say otherwise.

---

## 1. What changed materially

Before this work package the repository contained no database driver, no connection, and no
migration runner. Row-Level Security had never been executed by any automated check across
three phases recorded as complete. Tenant isolation — the property the entire product exists to
provide — was asserted in SQL files that had never been run.

It is now executed. The specific difference:

| | Before | After |
| :--- | :--- | :--- |
| PostgreSQL policies executed by CI | 0 | 12 invariants, executed |
| Isolation test fixture | a Python list | PostgreSQL 17.10 with migrations 001–003 |
| Behaviour with no database configured | suite green | suite **fails** |
| Quota ceiling enforcement | application `if` statement | `CHECK (used_quantity <= quota_limit)` |
| Audit immutability | convention | absence of UPDATE/DELETE policy, probed |
| Evidence anchors | agent-transcribed | tool-emitted, machine-validated |

## 2. Why the pass count is not the claim

`python tools/run_tests.py` reports 182/182. That number is not the evidence, and the Phase 3
record is the reason to say so plainly: it reported 169/169 while `RateLimitDecision` violated
its own frozen schema, because the suite loaded the schema and never applied it to an instance.
A pass count measures what a suite asserted, not what it declined to assert.

What makes these assertions evidence is that they can fail. Three schema mutations
([`mutation-probes.json`](mutation-probes.json)) removed one mechanism each and turned the suite
red every time; restoring each mechanism turned it green again.

Two supplementary probes license reading the green suite at all:

- **`bopen_app` cannot bypass RLS.** `rolsuper=false`, `rolbypassrls=false`, owns none of the 11
  tables. Had any of those been otherwise, every passing result would be worthless — a
  superuser sees all rows regardless of policy.
- **Tenant context does not leak across transactions on a reused connection.** The claim in
  `platform_kernel/db.py` that `set_config(..., is_local => true)` confines the tenant to one
  transaction was a code comment until it was executed against a shared connection. It holds.

## 3. What is not met, stated as such

**A-06 (migration reversibility) is unmet.** Migration `003` was applied forward against a
database already carrying `001` and `002`. The rollback script was authored but never executed,
so I cannot claim it works. Running `python tools/db_bootstrap.py --rollback 003` with
`BOPEN_DB_NON_PRODUCTION=1` and re-applying would close it.

**Mutation A is detected but not legible.** Dropping `tenant_isolation_resources` turns the
suite red, but as 13 `setUp` errors rather than one assertion naming the breach, because with
RLS enabled and no policy present the seed INSERT is itself refused. I judged this acceptable.
A verifier may reasonably judge it insufficient under R5, and the handoff invites exactly that
disagreement rather than presenting the result as clean.

**Findings F-4 through F-7 remain open.** The frozen-schema divergence, the unwired
transactional outbox, the tenant-blind feature toggles, and the never-resetting rate-limit
counters are entitlement-module defects. They are outside this work package and are not fixed
here. Migration `003` closed the *database-enforceable* half of F-2 (quota ceiling, positive
quantity, expiry ordering); the application code that ignores those rules still needs the
repository layer of `D-06`.

**Migrations `001` and `002` have no rollback scripts**, contrary to `AGENTS.md` §14.
Pre-existing, not introduced here, not corrected here.

## 4. Two defects I introduced and found by executing my own work

Both were invisible on reading and appeared within minutes of running the tool:

1. `forward_migrations()` classified `003_phase1_context_audit.down.sql` as a **forward**
   migration. The negative lookahead tested whether the remainder ended in `.down`, but it ends
   in `.sql`. Every rollback script would have been applied as a migration.
2. `app_url()` hardcoded port 5432 while the verification instance runs on 5433, so the tool
   printed a URL that could not connect.

Both existed because I wrote the tool and the test for it — which is the precise failure mode
EBIV §3 exists to interrupt. A verifier should assume there is a third.

## 5. Verification status

| Field | Value |
| :--- | :--- |
| Ballots cast | 0 |
| Quorum required | 2 (EBIV §6.1) |
| Eligible verifiers | Codex Agent IDE; Gemini / Antigravity |
| Disqualified | Claude — authored the implementation and its tests (§3) |
| Handoff | [`HANDOFF-P35-PARALLEL-TO-CODEX`](../../00-governance/handoffs/HANDOFF-P35-PARALLEL-TO-CODEX.md) |

Ballots belong in [`ballots.jsonl`](ballots.jsonl), one JSON line per proposition, schema at
EBIV §7. A single `REFUTED` ballot carrying a reproducible probe blocks, and I cannot discharge
it by re-asserting that the work is correct — only a failed reproduction discharges it.

## 6. Reproduction

```bash
python -m pip install -r requirements.txt
set -a; . ./.env.local; set +a
python tools/db_bootstrap.py --apply     # idempotent
python tools/run_tests.py                # 182/182
python tools/check_evidence_anchors.py   # PASS
```

Credentials are registered in
[`BOPEN-SEC-VAULT-001`](../../07-security/secrets/BOPEN-SEC-VAULT-001.md). The verification
cluster is at `C:\laragon\data\bopen-verify`, loopback only, port 5433.

## 7. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

Anchors in §front-matter and in [`manifest.json`](manifest.json) were emitted by
`python tools/check_evidence_anchors.py --emit`. No OID in this package was transcribed by an
agent, which is the specific defect that made the Phase 3 manifest unverifiable.

---

# WP-P35-07 — machine-readable disposition record and §6.5 quorum reporting

**Submitted:** 2026-08-08
**Maker:** Claude (agent, Motor role) — disqualified from voting on this package (EBIV §3)
**Candidate commit:** `bdc07e5e3fa651b96b1128ee94fbf09d51e85139`
**Candidate tree:** `e0121de88dd6def62fa3948d19e5951bb70216e6`
**Governing:** [`WP-P35-07`](../../work-packages/WP-P35-07-QUORUM-DISPOSITION-RECORD.md); [`DEC-P35-QUORUM-TOOL-GAP`](../../decisions/DEC-P35-QUORUM-TOOL-GAP.md) §7, §8
**Baseline:** `arch-baseline/2026-08-08-pre-quorum-disposition` (taken before the change, §23)

**This submission carries no verdict weight (EBIV §8).** A passing suite is not a confirmation.

## Falsifiable propositions

Eleven, registered as `WP07-INV-*` in `invariant-traceability.csv`. Each names one invariant, one
executed test, and the mechanism whose removal makes that test fail. All eleven were mutated and
observed red; the two that matter most to attack:

| Proposition | Claim | Mechanism |
| :--- | :--- | :--- |
| `WP07-INV-OPERATOR-ONLY-01` | A disposition not committed under the operator identity is refused and reported | the `D3` guard in `load_dispositions` |
| `WP07-INV-REFUTE-BLOCK-02` | A refutation blocks even alongside a genuine confirmation | the `if refuted:` branch in `main` |

## What changed

`tools/check_ballot_attribution.py` learns three things it did not do before, each required by
§6.5's wording *"one admissible CONFIRMED ballot"*: it reads `verdict`, it reads `admissibility`,
and it accepts `--root` so negative cases can be staged in a fixture rather than as false evidence
in the real record. `dispositions.jsonl` is read if present; **none is written by this package.**

## Checks

- Canonical suite, serialized: `Ran 680 tests in 642.998s` / `OK` / exit 0 / 0 FAIL-ERROR.
- `validate_repository.py`, `check_clean_room.py`, `check_evidence_anchors.py` — pass.
- Traceability verified both ways: no row names a missing test; no test lacks a row.

## Limitations and disclosed risks

1. **A judgment, not a quotation.** A refutation is cast against a *proposition*, but this blocks
   the whole *candidate*. That is the fail-closed reading of §6.2 and the reviewer should test it
   rather than inherit it. If the intended semantics are per-proposition, this is wrong and the
   test `test_R4b` encodes the wrong contract.
2. **The shortfall moved 26 → 27** (`WP-P35-07` §10). `88e6ed2` was the only candidate the old
   count treated as quorum-met and it holds two `REFUTED` ballots from `gemini`; it has been
   blocked under §6.2 since 2026-07-31 unseen. **Zero of 27 candidates are currently confirmable
   under §6.1.** True before this change; only now visible.
3. **`--root` is a new surface.** It cannot forge a verdict about the real repository — a fixture
   root yields a verdict about the fixture — but it is a way to run the checker against something
   that is not this repository, and the reviewer should confirm the canonical invocation is
   unaffected.
4. **The recursion.** This package must be disposed under the *existing* rules. Using
   `dispositions.jsonl` to confirm the change that created it would be circular (`WP-P35-07` §5).
5. **Untested composition.** No candidate in the real repository has a disposition, so the §6.5
   path has been exercised only in fixtures, never against live evidence.

### Correction 2026-08-08 — the recorded suite result is NOT a candidate-bound result

The "Checks" section above reports `Ran 680 tests in 642.998s / OK` beneath a submission anchored to
`bdc07e5` / `e0121de`. **That figure was not measured on that tree and must not be read as though it
were.**

`tools/run_tests.py` discovers tests by walking the working tree (`loader.discover`). The run was
executed in the primary workspace while it carried 21 uncommitted items belonging to an unrelated
in-flight change-set, and the log shows it collected them:

- `tests/isolation/test_notification_isolation.py` — **untracked, and absent from the candidate tree
  entirely** (20 occurrences in the run log)
- `tests/isolation/test_rls_database_behavior.py` — modified relative to the candidate's blob
  (35 occurrences)

A candidate-bound run would therefore have a different test count. The recorded `OK` says the dirty
workspace was green; it does not establish that `e0121de` is green.

**Consequences, recorded rather than repaired, because repairing requires a clean checkout that is
not currently available:**

1. The `Checks` bullet for the canonical suite is **withdrawn** as candidate evidence. The three
   static checks (`validate_repository`, `check_clean_room`, `check_evidence_anchors`) and the
   traceability verification are unaffected — none of them depends on test discovery.
2. `WP-P35-07` §8 requires a green canonical suite *for the candidate*. That criterion is
   **not yet met**, and this submission should not be balloted on the suite result until a run is
   performed with the working tree at exactly `e0121de`.
3. The `WP07-INV-*` propositions themselves are unaffected in substance — `test_quorum_disposition`
   builds its own disposable repositories and touches neither the shared database nor the dirty
   files — but the *evidence for them* must still come from a run at the candidate.

This was found by the maker after the operator questioned the workspace/candidate mismatch, not by
the verifier. It is recorded here so that a verifier reads it as a disclosed limitation rather than
discovering an unsound claim in the report.

### Candidate-bound suite result 2026-08-08 — `FAILED (failures=1)`, and §8 is still unmet

The run withdrawn above was repeated in a scoped worktree placed at the exact candidate
(`WP-P35-07` §11). Worktree verified before the run: `HEAD` `bdc07e5…`, tree `e0121de…` matching
this submission's anchor, zero tracked modifications, and **zero foreign test files**.

```
Ran 660 tests in 613.505s
FAILED (failures=1)
run_tests_rc=1
```

**660, not 680.** The 20-test difference is exactly the foreign `test_notification_isolation.py`
that the dirty-workspace run had collected, which confirms and quantifies the withdrawal above.

**The suite is not green at the candidate. `WP-P35-07` §8 is NOT met, and this submission does not
claim otherwise.**

#### The single failure, attributed

`test_every_table_in_the_schema_is_classified_and_protected` — the live database holds 8 tables the
candidate's classification registry does not know:

`notifications`, `notification_attempt`, `notification_dispatch`, `notification_fairness`,
`notification_provider_health`, `notification_quota`, `notification_quota_suspend`,
`notification_receipt`

Established from repository objects rather than assumed:

| Question | Answer |
| :--- | :--- |
| Does the candidate define these tables? | **No.** Its migrations end at `020_location_foundation.sql`; there is no `021` in tree `e0121de` |
| What does the candidate contain about notification? | **Documentation only** — 11 `docs/01-product/MILE-4.2-notification-*.md` specs, ADR drafts and reviews. No migration, no code, no schema |
| Where do the live tables come from? | `infrastructure/database/021_notification_foundation.sql`, which is **untracked** in the working tree and has already been applied to the shared database |

The test reads the **live** schema and compares it against the candidate's registry. The live
database is ahead of the candidate because an unrelated change-set applied its migration before
committing it.

#### Why this is not fixable by re-running

A worktree isolates the file tree but not the database, and there is one shared PostgreSQL. So long
as those 8 tables exist in it, **this assertion cannot pass at any commit that predates the
notification change-set** — including every one of the 26 other candidates. The failure is a
property of the environment, not of `e0121de`.

That is an attribution, **not a discount**. The correct reading is that §8's criterion is currently
unsatisfiable for this candidate, not that it has been satisfied. Whether to ballot the eleven
`WP07-INV-*` propositions on their own evidence — `test_quorum_disposition` builds disposable
repositories and touches neither the shared database nor these tables — is a judgment for the
verifier and the Completion Authority, and this submission does not make it.

---

# Notification foundation Stage 1 — schema, forced RLS, tenant isolation

**Submitted:** 2026-08-08
**Maker:** Claude (agent, Motor role) — disqualified from voting on this package (EBIV §3)
**Candidate commit:** `d3a5be25ce6e37d26b740579e58c4c1c4c3fbf52`
**Candidate tree:** `ba2eb5d09cebba7a1ce9c2f4f0a6d9aeacfde239`
**Build commit:** `b0c15e8` (migration, tests, registrations) — this candidate adds its traceability
**Authorization:** `DEC-P4-ENTRY` §12, recorded **before** the build (`d4b40ef`)
**Governing:** `BOPEN-GOV-EBIV-001`; `AGENTS.md` §8, §14, §25.1; `RESEARCH-MILE-4.2-NOTIFICATION`

**This submission carries no verdict weight (EBIV §8).** A passing suite is not a confirmation.

## Scope — Stage 1 only

Schema, forced RLS and tenant isolation for 8 tables. **Not built, and explicitly deferred:** the
worker/claimer plane, the callback ingest plane, provider adapters, the elevated
`bopen_notify_claimer` / `bopen_notify_callback` roles and their grants, templates, recipient
resolution, retry/cancel, export and cache surfaces.

That scope boundary is the single most important thing for a verifier to hold, because the parent
invariants it cites are much broader than what is built.

## Falsifiable propositions

**20 verified** (`NOTIFY-S1-*`, `verified_by_execution`) and **8 disclosed gaps** (`NOTIFY-S1-GAP-*`,
status `UNVERIFIED`), all in `docs/evidence/phase-3.5/invariant-traceability.csv`.

The rows are Stage-1 scoped rather than claiming the parent `NOTIFY-INV-01..16`. `NOTIFY-INV-01`
alone spans read, infer, request, retry, cancel, template, resolve, callback, export, cache and
observe; Stage 1 builds none of those surfaces. Every row that cites a parent carries an explicit
narrowing qualifier.

## Checks

- Canonical suite at this candidate, run serialized in a clean working tree:
  `Ran 680 tests in 623.203s` / `OK` / `run_tests.py` exit 0 / 0 FAIL-ERROR, with all 20
  notification tests collected. The tree was verified unmodified during the run.
- Registrations verified in both places `AGENTS.md` §25.1 step 3 requires — `TENANT_SCOPED_TABLES`
  (7 tenant-scoped) and the trial→paid `COPY_ORDER` (parents before children), with
  `notification_provider_health` deliberately excluded from `COPY_ORDER` as non-tenant.
- Traceability verified in both directions: no verified row names a missing test; no test lacks a
  verified row.

## Limitations and disclosed risks

1. **These rows were corrected after an adversarial audit, and the correction pattern matters.**
   Nine of twenty first-draft rows were wrong and — as the auditor put it — *every error ran in the
   direction that flattered the build*. Three were hard errors: an `executed_db` claim on a test
   that runs no SQL, a mechanism ("grants") that appears nowhere in the migration set, and an
   isolation claim for a table the test never opens. A verifier should treat the corrected rows as
   a maker's second attempt, not as a clean first one.

2. **`NOTIFY-S1-GAP-TENANT-CASCADE-01` is recorded as SUSPECTED WRONG, not merely untested.**
   `tenant_id` is `ON DELETE CASCADE` while `fk_attempt_dispatch` is `ON DELETE RESTRICT`, so
   deleting a tenant holding notification evidence likely **raises** rather than preserving it —
   the opposite of what the migration header claims. Latent only because no tenant-deletion path
   exists yet. This is the finding most worth reproducing.

3. **`unq_receipt_dedup` is a cross-tenant existence oracle.** Its scope is deliberate per the
   migration, but a tenant submitting a receipt whose `(provider_id, provider_message_id,
   dedup_key)` triple already exists under another tenant receives a distinguishable
   `UniqueViolation`. That is squarely within `NOTIFY-INV-04` anti-enumeration. Disclosed and
   unpinned by any test.

4. **`notification_provider_health` deny-by-default is asserted only structurally.** The design
   relies on `ENABLE + FORCE` with *no policy*. Only the flags are tested; nothing probes that a
   tenant-scoped session actually reads zero rows or cannot write circuit-breaker state. An
   over-broad policy added in the worker stage would break no test today.

5. **Four probes assert refusal generically.** `test_a_cross_tenant_notification_insert_is_refused`
   and the three composite-FK tests use `assertRaises(psycopg.errors.Error)`, the base class, so any
   database error passes. The mechanisms named are real and load-bearing, but the assertions do not
   bind the refusal to them the way the vocabulary tests (`CheckViolation`) and idempotency tests
   (`UniqueViolation`) do.

6. **Two isolation probes lack an owner-visibility control.** `test_a_dispatch_is_invisible_across_tenants`
   and `test_control_rows_are_isolated_across_tenants` assert only that tenant B sees zero. A policy
   mutated to `USING (false)` would break the owner and still pass — the dispatch case is saved only
   incidentally by a `RETURNING` clause in a helper.

7. **No work-package document exists for Notification.** This is consistent with every other
   MILE-4.2 foundation (Money, Workflow, UOM, ContactPoint, Location all lack one and were
   authorized through `DEC-P4-ENTRY` amendments), but it means the scope statement above lives in
   this submission rather than in an accepted work package.
