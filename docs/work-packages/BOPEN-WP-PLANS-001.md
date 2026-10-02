# BOPEN-WP-PLANS-001 — A governed home and format for plan documents

**Work Package:** `BOPEN-WP-PLANS-001`
**Status:** Proposed — awaiting operator acceptance; merging this file is the acceptance
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role), 2026-10-02 — advisory until accepted
**Dependencies:** none
**Governing artifacts:** [`AGENTS.md`](../../AGENTS.md) §3, §5, §6, §11, §12, §16, §31.2–31.3; [`config/delegation_envelope.json`](../../config/delegation_envelope.json)

## Objective

Give bOPEN plan documents one inventory rule, one location rule, one ID scheme, one metadata block
and one template, and have `tools/validate_repository.py` enforce the header for new and draft
plans.

Plans are already an established document type here, but inconsistent (state of `main` at
`a467711`):

- about 17 plan documents across `docs/01-product/`, `docs/03-architecture/`, `docs/`,
  `docs/work-packages/` and `docs/resources/`;
- seven ID styles (`PLAN-MILE-4.1`, `PLAN-NOTIFY-MIGRATE`, `PLAN-P35-06-*`, `BOPEN-PROD-PLAN-001`,
  `BOPEN-ARCH-PLAN-001`, `BOPEN-GOV-ACTION-001`, work-package IDs), and one plan with none;
- two header layouts (bold-label lines; a metadata table the validator cannot read);
- free-text status wording;
- no plan template in `docs/templates/`.

## In scope

| Step | Deliverable | Paths | Expected class | Merged by | Budget (lines) |
|---|---|---|---|---|---|
| 0 | This work package and its register row | `docs/work-packages/` | AD0 | Operator (acceptance) | ≤ 150 |
| 1 | Decision request `DEC-DOC-PLANS-001` | `docs/decisions/` | AD1 | Operator | ≤ 250 |
| 2 | `docs/templates/plan-template.md` | `docs/templates/` | AD0 | §31.2 if `AUTO_APPROVED`, else operator | ≤ 150 |
| 3 | Plan-header check in the validator, warn-only, with tests | `tools/`, `tests/governance/` | AD1 | Operator | ≤ 350 |
| 4a | Headers normalised: plans outside `docs/work-packages/` | `docs/` | AD0 | §31.2 if `AUTO_APPROVED`, else operator | ≤ 300 |
| 4b | Headers normalised: work-package execution plans | `docs/work-packages/` | AD0 | as 4a | ≤ 200 |
| 5 | Validator check switched to enforcing | `tools/` | AD1 | Operator | ≤ 40 |
| 6 | One pointer line under `AGENTS.md` §12 | `AGENTS.md` | AD4 | Operator | ≤ 10 |

Expected classes are predictions; the classifier's `VERDICT:` line on each PR decides.

Order: 0 → 1 → (2 ∥ 3) → 4a → 4b → 5 → 6. Steps 2, 4a and 4b are serial because each regenerates
`docs/DOCUMENT-MANIFEST.json`. Step 3 touches no `docs/` file, so it runs beside Step 2.

**Step 1 asks the operator to rule on:** what counts as a plan (including `docs/resources/` plans
and `BOPEN-P35-006-SHARD-ROUTING`); location (recommended: no moves — execution plans stay in
`docs/work-packages/`, other plans stay in the area they serve; the alternative, one `docs/plans/`
folder, means moving `BOPEN-P35-001-EXECUTION-PLAN.md`, which 17 documents link to); ID scheme
(recommended: `PLAN-<AREA>-<NNN>` for new plans, existing IDs kept as aliases); a closed status
set for new and draft plans (`Draft`, `Proposed`, `Approved`, `Live`, `Superseded`, `Withdrawn`)
with authority wording in a separate **Authority** field; and whether unregistered plan IDs get
`ARTIFACT-REGISTER.md` rows. It first checks whether the "governance ID-registry" that the MILE-4.2
plan cites already exists.

## Out of scope

- A top-level `plans/` folder. `AGENTS.md` §12 says to use `docs/templates/` rather than invent
  new formats.
- Editing any plan's body text.
- Rewriting the Status line or register row of any Approved, Accepted or Live document. Those
  record operator dispositions; such documents get **appended** lines only (extend-only).
- Changing the ID registry, the manifest generator or the governance gate scripts.

## Deliverables

The eight items in the In-scope table, each as its own pull request on a
`claude/BOPEN-WP-PLANS-001-*` branch citing this work-package ID and one `BUDGET:` line.

## Acceptance criteria

1. `DEC-DOC-PLANS-001` carries an operator ruling on every question listed under Step 1.
2. `docs/templates/plan-template.md` carries every field `AGENTS.md` §12 requires.
3. `python tools/validate_repository.py` reports no plan-header failure, in enforcing mode.
4. For every Approved, Accepted or Live plan touched, `git diff` shows added lines only.
5. Every renamed ID or path still resolves from every document that referenced it.
6. `AGENTS.md` §12 names the template and the decision.

## Required checks/evidence

On every PR: `python tools/validate_repository.py` exits 0;
`python -m unittest discover -s tests/governance -p 'test_*.py'` passes; the manifest is
regenerated with `python tools/generate_document_manifest.py`, never hand-edited; the four
`governance-gates` jobs and `Bootstrap Governance / validate` are green **and** the verdict job's
`VERDICT:` line matches the expected class (that job always exits 0). Step 3's tests are
`unittest`-style under `tests/governance/`, following `test_governance_validators.py`, with
negative cases. Each merge is confirmed on GitHub (`gh pr view <n> --json state,mergeCommit`),
not on report.

## Risks and rollback

| Risk | Mitigation |
|---|---|
| Header work overwrites an operator disposition | Extend-only rule; a Step 3 test asserts an approved free-text status is not flagged |
| Old IDs break references | Aliases kept; `git grep` every old ID before merge |
| Validator blocks before plans conform | Warn-only until Step 5, after Step 4b empties the warning list |
| Documentation PRs become operator-merge PRs | `tools/` changes isolated in Steps 3 and 5 |
| Concurrent PRs conflict on the manifest | Steps 2 → 4a → 4b serial; rebase and regenerate before each merge |

Every step reverts cleanly on its own; until Step 5 nothing gates anything.

## Completion record

_Not started. Filled in at closure._
