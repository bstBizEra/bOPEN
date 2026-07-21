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

## Append-only second hardened-maker verification note — 2026-07-21

Reason: fresh non-maker review rejected the first successor because identity and delegation records were forgeable, technical review still targeted the governed-input base, terminal draft receipts were contradictory, and terminal state transitions were mutable. Benefit of the prior phase: it established commit-bound governed artifacts, exact subject maps, expanded negative coverage and honest `NOT_READY` reporting. Expected outcome: the next successor requires an approved hash-and-commit-bound identity registry, correlates delegation records, separates exact candidate review from governed inputs, permits complete but ineffective draft dispositions, and makes terminal states immutable.

Second successor maker checks:

- dedicated authority-docket suite: 37/37 passed;
- full suite: 140/140 passed;
- repository validator: PASS, 27 mandatory paths/invariants;
- contract validator: PASS, 18 machine-readable contracts;
- program-control validator: PASS, seven draft registers;
- deterministic reports and the 257-record versioned manifest: current;
- clean-room, secret and supply-chain checks: PASS;
- `git diff --check`: PASS.

The absent approved authority identity registry is an explicit blocker. These maker checks have no authority effect and require a fresh non-maker exact-SHA review.

## Append-only trust-root verification note — 2026-07-21

Reason: the second successor still trusted a repository-authored registry that merely declared itself approved and did not authenticate a delegation grantor. Benefit of the prior phase: identity and delegation records were already hash-, commit-, scope- and time-bound, making the remaining root-of-trust defect narrow and reproducible. Expected outcome: human authority receipts now fail unless the authority source is approved and effective, the identity registry is an approved governed artifact bound to the exact repository input, and any delegation grantor is an approved active registry identity with explicit delegation authority and scope.

The focused suite remains 37/37 and the full suite remains 140/140 after replacing the former self-authored-registry positive expectation with a fail-closed trust-root expectation. Matrix action class, status, expiry policy and concurrence semantics are now matched to the expected action contract. All baseline decisions remain pending and all authority flags remain false.

This is maker evidence only and requires another fresh non-maker exact-SHA review.

## Independent exact-SHA technical receipts — 2026-07-21

Candidate commit: `99192c9532f04052cd81c51b1f4f925b18a53fb5`

Candidate tree: `7e2ecc3dac9ca20ab9249dd057945888de4f9c5f`

- `/root/fresh_schema_acceptance`: `ACCEPT_EXACT_SHA` after independently reproducing the fabricated-registry and invented-delegation-grantor rejection probes, matrix semantic mutations, exact candidate binding, terminal disposition, state immutability, subject, concurrence, chronology and nested-field checks. Focused suite 37/37 and repository validation passed.
- `/root/second_fresh_traceability`: `ACCEPT_EXACT_SHA` after independently verifying clean exact ancestry, bounded scope, append-only evidence, 37/37 focused tests, 140/140 full tests, all repository validators, both deterministic reports and the 257-record manifest.

Both receipts are technical evidence only. They do not authenticate a human authority, accept GOV-P0-02, approve any artifact or decision, pass PG-G0, authorize merge, release, runtime, deployment or production implementation.

## Append-only CI portability repair note — 2026-07-21

Reason: Gitea Actions run 57/job 86 reproduced a stale authority-readiness report because the default one-commit checkout could not resolve the docket's historical governed-input binding. A local depth-one clone reproduced the same failure. Benefit of the prior phase: the validator failed closed instead of silently skipping commit ancestry and bound-content checks. Expected outcome: both mirrored governance workflows fetch complete history (`fetch-depth: 0`) so exact commit/tree and ancestor validation runs consistently on Windows and Linux.

No check is removed, skipped or weakened. This workflow-only portability correction requires a new CI run and exact-SHA receipt review and has no approval, gate, merge, release, runtime or production effect.

## Append-only manifest portability repair note — 2026-07-21

Reason: after historical commit resolution passed in Gitea Actions run 58/job 87, the versioned manifest still differed because Windows working-tree CRLF bytes and Linux LF bytes produced different text-document digests. Benefit of the prior phase: CI progressed to the next deterministic boundary and exposed the platform-specific hash input without bypassing it. Expected outcome: governed UTF-8 Markdown, JSON and YAML are hashed and sized after canonical LF normalization, while binary and invalid UTF-8 content remains byte-exact.

A regression test proves CRLF and LF forms of the same governed text document produce identical manifest records. No validation, permission or security control is weakened, and no authority state changes.

Post-repair maker checks: focused suite 38/38, full suite 141/141, repository validation PASS, and the normalized 257-record manifest is current. These results remain maker evidence pending exact-SHA review and protected CI confirmation.
