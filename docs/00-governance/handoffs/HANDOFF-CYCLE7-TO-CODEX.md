# Handoff — PG-P0 closure repair cycle 7 → Codex independent review

> Placed in the repository working tree (UNTRACKED, deliberately not committed) so Codex Agent IDE
> can read it directly, per the BST-SA contract's "coordinate through shared files". It is a
> coordination artifact, not part of the reviewed candidate. Do not `git add` it.
> Format per `docs/02-agents/HANDOFF-CONTRACT.md`.

```yaml
handoff_id: HANDOFF-PG-P0-CLOSURE-CYCLE7-001
work_item_id: PG-P0 closure repair, remediation cycle 7
from_actor: Claude Opus 5 (BST-SA Motor worker agent), sole maker
to_actor: BST-Codex-Motor (independent checker)
role_completed: maker
repository: C:/laragon/www/bopen
branch: claude/PG-P0-closure-binding-default-cycle7
worktree: C:/laragon/www/bopen-worktrees/pg-p0-binding-default-c7
base_commit: 2a18ed5352930f7603543cdab00fe397e6b11dc4   # cycle 6, reported accepted
head_commit: 1756bad2cea88298a094bcfe20e01d7efd9c8473
head_tree:   ccd0d12953cbf028165e2ec2d8cfb1d27f88e573

requirements:
  - Close ONE root cause: the cycle-2 fail-closed closure-binding control defaulted OFF, so it
    engaged only when a caller passed --require-closure-binding, and the operative C7 apply runbook
    (EVD-CLOSURE-012) never passed it.
  - Do not modify or weaken any cycle-2..6 control.
  - Do not expand scope beyond that root cause.

decisions:
  - Inverted the default rather than documenting the flag: a control that must be switched on will
    eventually be left off (this lineage already learned that in EVD-CLOSURE-016 H2).
  - Escape hatch is scoped to a single decision id, NOT a boolean off-switch, so it cannot wave
    through an attacker-substituted unbound mandate. Exists solely for PG-P0-CLOSURE-001, signed
    before closure_binding existed.
  - --require-closure-binding retained as an accepted no-op so the invocation already written into
    PG-P0-CLOSURE-MANDATE-V2-PROPOSAL.md keeps working.
  - Corrected EVD-CLOSURE-012's C7 line (extend-only, via EVD-CLOSURE-029) because inverting the
    default breaks the documented invocation; shipping without it would strand an operator at a
    rejection, which is when people reach for whatever flag makes it pass.

changed_files:
  - tools/verify_phase_transition.py
  - tests/governance/test_phase_transition_verify.py
  - docs/evidence/EVD-CLOSURE-028-cycle7-closure-binding-required-by-default.md
  - docs/evidence/EVD-CLOSURE-029-c7-runbook-verifier-invocation.md
  - docs/CHANGELOG.md
  - docs/DOCUMENT-MANIFEST.json
  - docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json

commands_run:
  - python -m unittest tests.governance.test_phase_transition_verify
  - python -m unittest discover -s tests -p "test_*.py"
  - python tools/validate_repository.py | validate_contracts | validate_program_controls
  - python tools/validate_authority_identity_register.py | validate_root_control_surfaces
  - python tools/validate_pg_g0_authority_docket.py --check
  - python tools/generate_document_manifest.py --output <each manifest> --check
  - python tools/check_clean_room.py | check_secrets.py | check_supply_chain.py
  - python tools/verify_phase_transition.py <real inputs> [with/without the hatch]

tests:
  dsse_suite: 103/103 OK   # was 96; 7 added
  full_suite: 265/265 OK
  validators: 11/11 PASS
  manifests: both --check clean

evidence_paths:
  - docs/evidence/EVD-CLOSURE-028-cycle7-closure-binding-required-by-default.md
  - docs/evidence/EVD-CLOSURE-029-c7-runbook-verifier-invocation.md

findings:
  - Reproducible on cycle 6 (2a18ed5), the whole claim; refute it if you can:
      bare invocation                    -> VERIFIED: VERIFIED_EXACT              rc=0  (inert)
      with --require-closure-binding     -> REJECTED: CLOSURE_BINDING_REQUIRED    rc=1
    On 1756bad the bare invocation rejects.
  - No validator, docket check or test enforced the flag; only the verifier CLI accepted it.

residual_risks:
  - MAKER NOT DISINTERESTED. Cycles 2-6 exist because MY OWN cycle-1 candidate (2134ea2) was
    rejected; cycle 7 is me grading my successor's work. Treat my reasoning as a lead, not a result.
  - Highest-risk change is the test-helper default: _verify now defaults to exempting this file's
    own fixture decision id (PG-P0-COMPLETE-001) so pre-cycle-7 tests keep their intent. This is the
    most likely place a test quietly stopped testing what it claims, and I am the wrong party to
    judge it. Please check it directly.
  - Disclosed: after first committing cycle 7 I trimmed my own overengineering (speculative
    multi-id exemption support and its test) and AMENDED the unpushed commit rather than adding a
    correction commit, so cited test counts stay coherent. Pre-trim SHA 92cd7e0 was never shared.

blocked_items:
  - Cycle 7 has NO root-control ledger events. Progress_Log.md / Backlog.md / Recap_Today.md carry
    matched triples for cycles 2-6 (...-0001..0005) but zero references to cycle 7,
    EVD-CLOSURE-028 or EVD-CLOSURE-029. Maker omission, not a verifier defect. I did NOT amend
    1756bad to fix it because that SHA is the subject under review, and changing it mid-review is
    the exact coordination failure I made on cycle 6. Closure: fold the ...-0006 triple into the
    cycle-7 remediation commit if this review returns findings, or a follow-up commit if 1756bad is
    accepted as-is. Reviewer's call.
  - TWO UNPERSISTED VERDICTS, neither of which I can close. PG-P0-INTERP-002 section 7 and
    bopen-phase-closure require independent verdicts persisted verbatim as durable receipts:
      (a) cycle-1 REJECT_EXACT_SHA on 2134ea2 - asserted in EVD-CLOSURE-022 and docs/CHANGELOG.md,
          no EVD-* artifact holds the text;
      (b) cycle-6 acceptance on 2a18ed5 - reached me only as an operator relay; no receipt exists in
          the tree (git grep 2a18ed5 -- docs/evidence returns nothing at that commit).
    I authored neither. I have read neither verdict, and writing a receipt for a verdict I did not
    read is the "never certify a relayed verdict you did not read yourself" stop condition. If Codex
    holds either text, please persist it.
  - C6-C8 execution bytes remain the human-only blocker of EVD-CLOSURE-023. Unchanged by cycle 7.

recommended_next_action: >
  Independent exact-SHA review of 1756bad. Attack order: (1) the test-helper default; (2) whether
  the hatch is genuinely scoped - --allow-unbound-legacy-mandate PG-P0-CLOSURE-001 must verify while
  the same flag against any other decision_id must still reject; (3) whether an exempted run can
  pass as a bound one at an rc-and-stdout gate, given the receipt sets legacy_unbound_exemption and
  closure_execution_verification=false and stdout appends (UNBOUND_LEGACY_EXEMPTION: <id>);
  (4) whether the hatch weakens a PRESENT binding - it must tolerate absence only.

authorization_required: >
  None granted or requested by this handoff. It authorizes nothing, signs nothing, moves no ref,
  consumes no decision. C8 execution, the C9 ref move, merge, PG-P1 and production remain human-only
  and separately gated. main unmoved at a908bbea1975ffc52a636765cd9f823dfeb978eb;
  PG-P0 ACTIVE; PG-P1 NOT_READY.

timestamp: 2026-07-28T09:00:00+07:00
```

## Verified-clean at this SHA (so a reviewer does not re-derive it)

Cross-link monitoring pass over `1756bad`: root-control surface validator PASS; all three ledgers in
sync at event 0005; every `EVD-CLOSURE-*` cited in `docs/CHANGELOG.md` resolves to a file; all 15
existing cycle events (5 per ledger) carry every required cross-link field.

The `EVD-CLOSURE-017..021` citations in `Backlog.md` and `docs/CHANGELOG.md` are **supersession
notes explaining those ids' absence**, not dangling links — a naive link check flags them as broken
and wastes effort, as my own first pass did.

## Signed-artifact non-interference

`PG-P0-CLOSURE-MANDATE.dsse.json`, `PG-P0-CLOSURE-MANDATE.md` and
`docs/00-governance/registers/SCHEDULE-REGISTER.json` are byte-identical to cycle 6 — verify with:

```
git diff 2a18ed5 1756bad -- docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.dsse.json \
  docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md \
  docs/00-governance/registers/SCHEDULE-REGISTER.json    # expect empty
```
