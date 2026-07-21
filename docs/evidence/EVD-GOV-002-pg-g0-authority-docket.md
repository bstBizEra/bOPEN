# EVD-GOV-002 — PG-G0 Authority Docket Technical Evidence

**Version:** 0.1
**Status:** Draft maker evidence; exact-SHA review pending
**Evidence ID:** EVD-GOV-002
**Work package:** GOV-P0-02
**Generated:** 2026-07-21
**Environment:** Windows / `C:\laragon\www\bopen-worktrees\gov-p0-02-authority-docket`
**Source/base commit:** `c893062c197e74c15214e5ce1c425b9e9ed8002f`
**Maker:** Codex root proposal maker
**Checker:** Pending different-agent exact-SHA review

## Procedure

1. Bind the supplied Program Goal v0.2 and current draft authority artifacts to exact hashes.
2. Model only action IDs present in the live draft authority matrix.
3. Preserve missing action mappings and exact instruction paths as blockers.
4. Validate human-only authority, maker/checker separation, Git bindings, artifact hashes, time windows, concurrence and non-authority flags.
5. Run negative tests, full repository validation and a fresh-archive checker review.

## Expected result

The proposal is structurally valid and deterministically `NOT_READY`; every effective outcome and authority flag is false.

## Actual result

The draft docket validates structurally and returns `NOT_READY`, `ready_for_human_gate_decision: false`, `pg_g0_passed: false` and `production_implementation_authorized: false`. It contains five pending requests mapped to live action IDs and explicitly blocks the three absent governance/register/gate actions.

Maker checks:

- dedicated negative suite: 16/16 passed;
- full suite: 119/119 passed;
- repository validator: PASS, 27 mandatory paths/invariants;
- contract validator: PASS, 18 machine-readable contracts;
- program-control validator: PASS, seven draft registers;
- deterministic Program G0 and authority-docket reports: current;
- clean-room, secret and supply-chain checks: PASS;
- `git diff --check`: PASS.

The versioned candidate manifest is under `docs/manifests/`; the canonical generated manifest is intentionally not overwritten while DEC-0012 remains pending.

## Security and clean-room declaration

No credentials, personal identity values, production data, upstream source, runtime code, migrations, infrastructure activation or deployment are in scope. Human identity fields remain null rather than using invented or plaintext values.

## Independent verdict

Pending exact maker SHA. Technical acceptance cannot approve GOV-P0-02, any authority request, PG-G0, merge, release, runtime or production implementation.

## Append-only documentation-review rework note — 2026-07-21

Reason: exact-SHA documentation review requested explicit declaration of three changed support paths and an instruction-precedence constraint on DEC-0012 option 3. Benefit of the old phase: the first maker candidate already preserved missing paths, pending authorities and all non-authority flags fail closed. Expected outcome: the successor maker candidate states its exact documentation-support scope and confirms that only a new explicit user-level instruction can amend the replacement instructions.

This note records pending rework only. It does not change the maker check counts above, supply a checker verdict, accept GOV-P0-02, resolve DEC-0012 or change any gate or implementation authority.

## Append-only hardened-maker verification note — 2026-07-21

Reason: the three exact-SHA reviewers identified bypasses in nested-field enforcement, commit-bound artifact verification, actor separation, terminal dispositions, chronology, expiry, concurrence handling and state transitions. Benefit of the old phase: the initial 16-test baseline proved the draft docket remained structurally `NOT_READY` and exposed the precise adversarial gaps without granting authority. Expected outcome: the successor maker candidate rejects those probes while preserving every authority and production flag as false.

Successor maker checks:

- dedicated authority-docket suite: 26/26 passed;
- full suite: 129/129 passed;
- repository validator: PASS, 27 mandatory paths/invariants;
- contract validator: PASS, 18 machine-readable contracts;
- program-control validator: PASS, seven draft registers;
- deterministic Program G0 and authority-docket reports: current;
- versioned manifest: current, 257 records;
- clean-room, secret and supply-chain checks: PASS;
- `git diff --check`: PASS.

These are maker results only. Independent acceptance must bind a successor exact commit and tree; this note does not accept GOV-P0-02, approve any decision, pass PG-G0, authorize merge, or authorize runtime or production implementation.
