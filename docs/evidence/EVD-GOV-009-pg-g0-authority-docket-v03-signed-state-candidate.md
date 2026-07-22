# EVD-GOV-009 — PG-G0 Authority Docket v0.3 Signed-State Candidate

**Evidence ID:** EVD-GOV-009
**Timestamp:** 2026-07-23T01:00:00+07:00
**Agent ID:** BST-Codex-Motor
**Source:** Operator-signed Batch 2 record at `60c4831f4fcdfabb876d62f4eb98949b4a1a5a66`
**Work package:** GOV-P0-04 (accepted)
**Branch:** `codex/GOV-P0-04-docket-v03`
**Substrate commit:** `60c4831f4fcdfabb876d62f4eb98949b4a1a5a66`
**Substrate tree:** `75775a659f1c36c1cc5b489be572a347e1ea496b`
**Evidence status:** `SIGNED_STATE_CANDIDATE`; independent exact-SHA review pending

## Scope and atomic result

This candidate mechanically encodes, without changing, all thirteen outcomes in the append-only Signing Pass 2 record. BOPEN-GOV-001, authority matrix v0.2 and DEC-0013 are effective; the six remaining program registers carry attributable approval provenance; GOV-P0-01 and GOV-P0-04 are accepted; DEC-0007/BOOT-B7 is approved; and GOV-P0-03 is active through the same signed B6 event appended to all five root ledgers.

Every prepared disposition contains a final `HUMAN-OPERATOR-001` `DIRECT` authority actor and the role-specific concurrence actor blocks required by its v0.2 preparation. The subjects remain bound to the exact commits and hashes signed in v0.2. The v0.3 repository binding and 41-record inventory instead bind the complete Signing Pass 2 substrate, avoiding self-reference.

## Fail-closed controls

- The validator reconstructs the inventory from Git objects at `60c4831`, then compares every record, path, digest and byte count.
- The seven signed JSON register transformations are exact: only the authorized version/status/provenance and matrix entry status changes are permitted.
- Each signed Markdown surface must preserve its substrate bytes as an exact prefix and contain the one authorized append marker.
- All thirteen final actors and concurrences resolve through the approved identity register at the signed substrate, with exact action, subject, role and `DIRECT` authority bindings.
- The five `PG-G0-DEC-001..005` B8 requests must remain byte-semantically identical to docket v0.2 and `PENDING`/ineffective.
- Root activation requires all five ledgers, one signed timestamp and the exact B6 references; zero, partial, malformed or divergent events fail.
- Schema and semantic checks reject unknown fields, altered outcomes, stale inventory, fabricated actors, missing provenance and any production-authority claim.

## Validation record

Required final checks are the focused docket/root/bootstrap/program-control suites, full unittest discovery, `pnpm validate`, deterministic report checks and `git diff --check`. The versioned manifests and reports are regenerated after all append-only documentation updates. The exact candidate SHA is intentionally not self-asserted inside its own commit; the independent reviewer must bind EVD-GOV-010 or its successor receipt to the actual commit and tree.

Observed before candidate commit:

- `python -m unittest tests.governance.test_pg_g0_authority_docket`: 49/49 passed; the subsequently added signed-register-provenance negative case also passed individually and in full discovery.
- Root-control, program-control and bootstrap focused suites: 28/28 passed.
- `python -m unittest discover -s tests -p "test_*.py"`: 182/182 passed.
- `pnpm validate`: exit 0; repository, 20 contracts, seven governed registers, authority identity, both readiness reports, 276-record document manifest, clean-room, secret and supply-chain checks passed.
- `python tools/validate_pg_g0_authority_docket.py --check`: readiness `NOT_READY`, zero validation errors.
- `python tools/validate_root_control_surfaces.py --check`: five activated root controls and the 11-file package manifest passed.
- `git diff --check`: exit 0.

The versioned manifests and reports are regenerated again after this validation append. The exact candidate SHA is intentionally not self-asserted inside its own commit; the independent reviewer must bind EVD-GOV-010 or its successor receipt to the actual commit and tree.

## Decision boundary and residual risk

The candidate state is `TECHNICAL_REVIEW`, and its deterministic authority-readiness result is `NOT_READY` with zero validation errors. The five B8 decisions, B9/PASS_PG_G0, merge, release, deployment, runtime and production implementation remain unauthorized. The signed Batch 2 outcomes may not be revised by technical review; any correction requires a new candidate SHA while preserving the operator record. Solo-operator role concentration remains disclosed and supplies attribution, not inter-human independence.

## Rollback and handoff

Before merge, rollback is deletion of this isolated branch/worktree; the signed substrate remains immutable. Claude must independently review the final exact commit SHA and tree, verify the parent is `60c4831f4fcdfabb876d62f4eb98949b4a1a5a66`, rerun the validation chain and issue a new exact-SHA receipt. The earlier EVD-GOV-008 receipt applies only to `b929821af83ff774be2bfb10dcb5588d862dcaf2` and cannot be upgraded in place.
