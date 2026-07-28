# Documentation Changelog

## Append-only entry - 2026-07-29 - cycle 8 self-audit remediation (EVD-CLOSURE-030 amendment)

- Maker adversarial self-audit of `fdf0434` found four defects in the maker's own work; three are
  fixed here. `--execution-root ""` / `--repository ""` silently meant the process CWD and are now
  refused. The exemption-removal test was vacuous - it asserted against the test helper's signature,
  not production - and is replaced by a signature assertion plus a sweep proving no optional
  parameter of `verify_transition` can tolerate an absent binding. The CLI refusal added in cycle 8
  had no tests at all; five subprocess tests now exercise the real entrypoint on rc and stdout.
- Recorded, not fixed: EVD-CLOSURE-029's C7 invocation still names the deleted flag and is superseded;
  a corrected runbook is a separate work item. The `verdict` field still does not encode verification
  depth, which is latent because no library importer exists; raised for the checker rather than
  changed unilaterally.
- 111 tests in the verifier module; full suite green.

## Append-only entry - 2026-07-29 - PG-P0 closure repair, remediation cycle 8 (EVD-CLOSURE-030)

- Removed the cycle-7 unbound-legacy exemption outright: `closure_binding_required`, the
  `allow_unbound_legacy_decision` parameter, the `--allow-unbound-legacy-mandate` flag and the
  `legacy_unbound_exemption` receipt field are all deleted. No input can now produce exit 0 with a
  VERIFIED_EXACT verdict for a mandate carrying no closure binding.
- Root cause: the removed `required` flag conflated "must a binding exist" with "how deeply is
  execution verified". A binding is now unconditionally mandatory; depth follows from whether an
  execution root or repository is supplied, and the CLI refuses a structural-only result.
- Consequence: `PG-P0-CLOSURE-001` is unverifiable by this tool by design. The closure requires a
  newly issued and operator-signed mandate carrying a binding.
- Test fixtures are bound by default; an unbound mandate must be requested explicitly with
  `bound=False`. Full suite 267 tests OK.
- Ledgers gain the omitted cycle-7 `-0006` triple (recorded retrospectively) and the cycle-8 `-0007`
  triple, so the series is unbroken 0001-0007.
- The cycle-7 verdict was relayed by the operator and is NOT persisted in this repository; the maker
  did not read it and does not certify it. Persisting it verbatim remains an open control.

## Append-only entry - 2026-07-28 - PG-P0 closure repair, remediation cycle 7 (EVD-CLOSURE-028/029)

- Additive commit on `claude/PG-P0-closure-binding-default-cycle7` from cycle-6 tip
  `2a18ed5352930f7603543cdab00fe397e6b11dc4`. Advisory; independent review required.
- **Closure binding is now required by DEFAULT.** Cycle 2 built a sound fail-closed control but
  defaulted `require_closure_binding=False`, so it engaged only when a caller opted in. Against the
  real signed mandate at the cycle-6 tip, the bare invocation returned `VERIFIED_EXACT` rc=0 while
  the control sat inert. No validator, docket check or test enforced the flag, and the operative C7
  apply runbook (`EVD-CLOSURE-012`, inherited unchanged) never passed it - so an operator following
  the procedure of record would have gotten a clean verdict on an unbound mandate. Same lesson as
  `EVD-CLOSURE-016` H2: a control that must be switched on will eventually be left off.
- **Escape hatch is scoped to a decision id, not a boolean.** `--allow-unbound-legacy-mandate
  <DECISION_ID>` tolerates an absent binding only for a mandate carrying exactly that
  id, so it cannot wave through an attacker-substituted unbound mandate. `PG-P0-CLOSURE-001` needs
  it (signed before `closure_binding` existed); nothing else does. A present-but-malformed binding
  is still rejected under an exemption - absence only is tolerated.
- **The weaker mode is never invisible.** Receipt carries `legacy_unbound_exemption` and
  `closure_execution_verification: false`; stdout appends `(UNBOUND_LEGACY_EXEMPTION: <id>)` so the
  rc-and-stdout apply gate sees it too. `--require-closure-binding` retained as an accepted no-op.
- **C7 runbook corrected** (`EVD-CLOSURE-029`, superseding only `EVD-CLOSURE-012`'s C7 line): states
  the two legitimate invocations, requires recording the exemption suffix when present, and names
  the prohibited "make the rejection go away" resolutions.
- Tests 96 -> 103. New `ClosureBindingRequiredByDefaultTests` pins the inverted default, the public
  signature's own default, exemption scoping, receipt disclosure, and predicate semantics.

## Append-only entry - 2026-07-28 - PG-P0 closure repair, remediation cycle 6 (EVD-CLOSURE-027)

- Additive commit on `claude/PG-P0-closure-repair-c8-v2` after Codex's cycle-5 fail-closed result
  named one blocker against `d4cd5d594d9b9e25fed8634ef0def5dea18c354a`. Reproduced before fixing.
- **`expected_old` was never compared to `predecessor_commit`.** They mean different things -
  `predecessor_commit` is the baseline the whole verification diffs from, `expected_old` is the
  value the C9 compare-and-swap publishes on top of - and both are only 40-hex-validated. So
  `expected_old = "f" * 40` passed while both other fields stayed genuine. The transition proven
  would not have been the transition applied, and every cycle-3-to-5 control inherits that
  divergence silently because all are anchored to `predecessor_commit`.
- **Fixed** with new stable reason code `EXPECTED_OLD_MISMATCH`, enforced inside the *structural*
  validator so it runs in both modes, before any repository or tree work, and cannot be skipped by
  omitting `--repository`. Needs no I/O: both fields are inside the signed payload.
- Five tests: positive equality; the all-f attack; `expected_old` naming a **different real commit**;
  a swapped pair (`predecessor_commit` moved forward, `expected_old` keeping the true baseline); and
  a structural case with no repository supplied at all. DSSE suite 96/96.
- Disclosed: three fixtures binding placeholder `expected_old` values now bind the fixture's real
  base commit, and two cycle-5 tests that override `predecessor_commit` now also override
  `expected_old` so they still reach their intended reason codes. No control was weakened.
- Preserved: all cycle-3-to-5 controls; frozen signed artifacts byte-identical to base; unsigned
  proposal still `DRAFT_NOT_SIGNABLE` / `BLOCKED_PENDING_EXECUTION_BYTES` (its `expected_old` and
  `predecessor_commit` are both `042dda53...` and already satisfy the new check);
  `PG-P0-CLOSURE-002` revocation scoping; withdrawn backdated verification guidance; no Graphify
  artifacts.

## Append-only entry - 2026-07-28 - PG-P0 closure repair, remediation cycle 5 (EVD-CLOSURE-026)

- Additive commit on `claude/PG-P0-closure-repair-c8-v2` after Codex returned `REJECT_EXACT_SHA` on
  `fc4960fcc99df3cf35aa3140e9a01bf215abfa91`. Two exact defects, both reproduced before fixing.
- **Rename detection was never actually disabled.** `tree_diff_paths` passed `--no-renames` then
  `-M0`; git applies last-option-wins, so `-M0` re-enabled it. A rename record carries three
  NUL-separated fields, not two, so the parser recorded the source and skipped the destination:
  renaming a **permitted** path to an **undeclared** one enumerated only the permitted source and
  passed. `--no-renames` is now the final rename-related flag, and the parser handles `R`/`C`
  records explicitly, recording **both** paths. Regression: `docs/CHANGELOG.md` renamed to
  `evil.txt` now enumerates the destination and rejects `TREE_SCOPE_VIOLATION`.
- **`predecessor_commit` was never resolved.** It and `predecessor_tree` floated free, so the signed
  base commit could be paired with a substituted real tree and every downstream check would run
  against that baseline. `assert_predecessor_commit_binds_tree()` now runs before any diff: the
  commit must be a real commit object (`PREDECESSOR_COMMIT_INVALID`) whose `^{tree}` equals the
  signed `predecessor_tree` (`PREDECESSOR_TREE_MISMATCH`). The negative test substitutes a genuine
  existing tree object, not a nonexistent id.
- Two new reason codes; 7 new regression tests. DSSE suite 91/91.
- Disclosed: adding the predecessor anchor invalidated three fixtures that bound placeholder
  commits. The helper now creates a real empty base commit whose tree is the empty tree, so fixtures
  bind a genuinely consistent pair; the check was not weakened.
- Preserved: all cycle-4 controls, frozen signed artifacts byte-identical to base,
  `DRAFT_NOT_SIGNABLE` / `BLOCKED_PENDING_EXECUTION_BYTES`, `PG-P0-CLOSURE-002` revocation scoping,
  withdrawn backdated verification guidance, no Graphify artifacts.

## Append-only entry - 2026-07-28 - PG-P0 closure repair, remediation cycle 4 (EVD-CLOSURE-025)

- Additive commit on `claude/PG-P0-closure-repair-c8-v2` after Codex's cycle-3 assurance conflict
  resolved fail-closed to HOLD: an independent attack added an **undeclared file** under the
  execution root and verification still accepted. Cycle 3 verified the seven declared paths
  thoroughly but never enumerated anything else, so per-path checks could not establish scope.
- **Scope now comes from the complete change.** `closure_binding` gains a required `successor_tree`
  (40-hex git tree id; the proposal carries `UNRESOLVED` and therefore rejects). Closure mode
  requires a bounded `--repository`, requires both trees to be real git tree objects
  (`TREE_OBJECT_INVALID`), enumerates the full `predecessor_tree -> successor_tree` diff with
  `--no-renames` so renames decompose into delete+add, and rejects any added, modified, deleted,
  renamed, mode-changed or type-changed path outside the seven permitted effects
  (`TREE_SCOPE_VIOLATION`).
- **Execution root must BE the successor tree** - no extra file, no missing file, no differing byte
  (`EXECUTION_ROOT_MISMATCH`). Untracked bytes are invisible to a tree diff, so the root is compared
  to the tree in full; this is the control that actually catches the reported attack.
- **A symlink is also a blob in git**, so permitted-effect entries are additionally mode-allow-listed
  to regular files (`100644`/`100755`); `SUCCESSOR_TREE_ENTRY_INVALID` otherwise.
- Eight new reason codes; 18 tree-scope attack tests. DSSE suite 84/84.
- Disclosed dependency change: tree-scope helpers shell out to the `git` binary via `subprocess`
  (read-only: `cat-file`, `ls-tree`, `diff`, `rev-parse`), mirroring
  `tools/validate_pg_g0_authority_docket.py`. Tests skip cleanly when git is absent.
- Preserved: frozen signed artifacts byte-identical to base, `DRAFT_NOT_SIGNABLE` /
  `BLOCKED_PENDING_EXECUTION_BYTES` status, revocation scaffold scoped to `PG-P0-CLOSURE-002`,
  withdrawn backdated verification guidance, no Graphify artifacts.

## Append-only entry - 2026-07-28 - PG-P0 closure repair, remediation cycle 3 (EVD-CLOSURE-024)

- Additive follow-up commit on `claude/PG-P0-closure-repair-c8-v2` after the independent Codex
  checker returned `REJECT_EXACT_SHA` on `17b9075d97c9022c698097e4d88ca628fc9e9c31`. That commit is
  preserved in history; nothing was amended or rebased.
- **successor_blobs strictly bound.** Closure mode now requires the map's keys to equal the seven
  manifest permitted-effect paths exactly (missing, extra or renamed paths reject
  `SUCCESSOR_BLOBS_INCOMPLETE`), every value to be a 40-character lowercase git object id
  (`UNRESOLVED`, non-hex, uppercase and truncated reject `SUCCESSOR_BLOBS_UNRESOLVED`), an
  `--execution-root` to be supplied (`EXECUTION_ROOT_REQUIRED`), and every bound id to equal the git
  blob id recomputed from the real file bytes (`SUCCESSOR_BLOB_MISMATCH`). Path resolution is bounded
  inside the root; traversal and absolute paths reject `EXECUTION_PATH_UNSAFE`. 18 new negative tests;
  67/67 DSSE tests pass.
- **Status corrected to blocked.** `READY_FOR_HUMAN_SIGNATURE` is withdrawn. The V2 manifest carries
  `_signing_status: DRAFT_NOT_SIGNABLE` and `_blocking_state: BLOCKED_PENDING_EXECUTION_BYTES`; the
  binding carries `successor_blobs_status: BLOCKED_PENDING_EXECUTION_BYTES`. Regression tests assert
  the shipped proposal stays rejected `SUCCESSOR_BLOBS_UNRESOLVED` in closure mode - the correct
  current state, not a defect.
- **Revocation scaffold retargeted** to the proposed decision `PG-P0-CLOSURE-002` (not the signed
  `PG-P0-CLOSURE-001`), marked `PENDING_HUMAN_ATTESTATION` and still non-authoritative.
- **Backdated verification guidance withdrawn.** The `2026-07-27T00:00:00+07:00` example is removed
  and replaced by a policy requiring the actual verification-event instant, a justification of why it
  is the true event time, and a receipt bound to the exact commit and tree. Additionally disclosed:
  the payload's inherited `authority.effective_at` must be replaced at re-issuance, which also
  changes the authorized successor digest.
- Frozen signed artifacts unchanged: `PG-P0-CLOSURE-MANIFEST.json` (`7417cc6a...fb33a`),
  `PG-P0-CLOSURE-MANDATE.md`, `.dsse.json`, `SCHEDULE-REGISTER.json`, `EVD-CLOSURE-014`.

## Append-only entry - 2026-07-28 - PG-P0 closure repair, remediation cycle 2 (EVD-CLOSURE-022/023)

- Rebuilt from exact base `042dda535be70927b73cd1a131b2545349729643` on branch
  `claude/PG-P0-closure-repair-c8-v2` after the independent Codex checker returned
  `REJECT_EXACT_SHA` on candidate `2134ea2d53f78b79522b476e78f4b33022595615`. Not built atop the
  rejected candidate; evidence ids EVD-CLOSURE-017..021 stay consumed by it and are not carried over.
- **Fail-closed closure verification.** `tools/verify_phase_transition.py` gains a `closure_binding`
  mandate object with a closed required-key set and a `--require-closure-binding` mode: absent,
  malformed or mismatched bindings are hard rejections, enforced before authority resolution. Six new
  reason codes. The cycle-1 test asserting an unbound mandate is "not contradicted" is deleted, not
  replaced. Two semantic attacker negative tests prove that widening `permitted_effects` (e.g. adding
  a write to `AUTHORITY-MATRIX.json`) is rejected while the transform and signature stay valid.
  49/49 tests pass.
- **Frozen artifacts preserved.** `PG-P0-CLOSURE-MANIFEST.json` is byte-identical to base
  (`7417cc6a...fb33a`, 6613 bytes); cycle 1 had mutated it and wrongly claimed the existing C4
  signature still bound it. Corrections now live in a new unsigned
  `PG-P0-CLOSURE-MANIFEST-V2-PROPOSAL.json` under a new decision id, generated programmatically from
  the frozen file so its seven permitted effects cannot drift.
- **C9 target corrected.** `refs/heads/main` is withdrawn as factually impossible: `git merge-base`
  exits 1, `main` is a single-commit orphan history disjoint from the closure lineage. Corrected to
  `refs/heads/pg-p0-closure-lineage` @ `042dda535be70927b73cd1a131b2545349729643`.
- **External state corrected.** Consumed registry emptied - the C5 check was advisory verification,
  not consumption. Revocations relabelled a non-authoritative maker scaffold requiring operator
  attestation.
- **Unsigned signing packet** `PG-P0-CLOSURE-MANDATE-V2-PROPOSAL` marked `READY_FOR_HUMAN_SIGNATURE`.
  Nothing is signed or authorized. Six of seven successor blob bindings remain `UNRESOLVED` because
  constructing the C6-C8 execution bytes is classifier-blocked for any agent (EVD-CLOSURE-023); the
  packet must not be signed until they resolve.

## 2026-07-27 - EVD-CLOSURE-015/016: pre-apply fail-proof evidence

- EVD-CLOSURE-015 (INDEPENDENT BST-Codex-Motor): adversarial fail-proof of the C6-C9 apply pipeline = PIPELINE_FAILS_CLOSED. 9/9 negative cases rejected (forged sig, swapped payload, wrong key, missing mandate, tampered patch, wrong-parent CAS, validator-only apply, schedule-only apply, reversed manifest order) + happy-path control accepted. Binds PATCH_SHA256 1A9FF63B...499D88BE, maker-verified to match the on-disk apply patch. No commit or ref movement on any failing case; source repo untouched.
- EVD-CLOSURE-016 (advisory maker-side, 4 nodes): EXECUTION_CANDIDATE_VALID + GUARD_FAILS_CLOSED + SIGNATURE_GATE_FAILS_CLOSED (60 probes, 0 critical) + ABORT_SAFE_AND_CAS_PROTECTED. Records 7 hardening findings; H1-H3 were adopted into the apply runbook (never use --write to fix a stale --check; gate VERIFY-P0-01 on rc AND stdout; destroy the worktree on the CAS-failure path). H4/H5 (trust-root ingest, ISO-8601 offset) queued post-closure.
- Additive evidence only; SCHEDULE-REGISTER untouched (PG-P0 still ACTIVE, closure subject and mandate binding unaffected). PG-P1 NOT_READY; main a908bbe.

## 2026-07-27 - EVD-CLOSURE-014: C5 independent verification of the operator-signed mandate (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent BST-Codex-Motor C5 receipt for the signed mandate at d38ab2d: verify_ed25519 True, verify_transition VERIFIED_EXACT, signer HUMAN-OPERATOR-001, authority/scope/manifest-binding/signed-decision-anchor PASS, non-execution confirmed (PG-P0 still ACTIVE). Proof of possession independently confirmed -> trust root ACTIVE. Next: C6-C8 apply, bounded by DEC-0014 (verifier + human apply). PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - C5: record the operator-signed Stage-1 closure mandate (pre-execution)

- Added docs/00-governance/signing/PG-P0-CLOSURE-MANDATE.md (decision record) + PG-P0-CLOSURE-MANDATE.dsse.json (DSSE envelope carrying HUMAN-OPERATOR-001 Ed25519 signature, keyid operator-pgp0-completion-1). Maker verified on receipt: verify_ed25519 True, verify_transition VERIFIED_EXACT (proof of possession; trust root APPROVED_PENDING_PROOF_OF_POSSESSION -> ACTIVE). The record names both authorizing actions + the bound closure-manifest content sha256 7417cc6a + the #signed-decision anchor per INTERP-002 v0.4 SS5. This commit RECORDS the signed mandate only; it does NOT mutate SCHEDULE-REGISTER (PG-P0 stays ACTIVE) or the docket - that is the C6-C8 execution commit. Independent C5 verification pending. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - EVD-CLOSURE-013: durable receipt for the C3 re-freeze (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent BST-Codex-Motor receipt for the C3 closure-manifest re-freeze at 27e70fa8: verdict ACCEPT_EXACT_SHA. The four signing digests are UNCHANGED (mandate 0f34a306, predecessor e80f7b93, successor 1f8d183e, PAE bd5113a6) so the operator C4 signature subject + command are unaffected; only the manifest sha256 changed 9e67cd0b -> 7417cc6a (the real C6 mandate record must name 7417cc6a). Round-trip VERIFIED_EXACT; both manifest checks + 189 tests PASS; no finding. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - C3 manifest re-freeze (permitted_effects +test delta) + EVD-CLOSURE-012 dry-run

- EVD-CLOSURE-012: persisted the advisory C6-C8 execution dry-run (throwaway key, scratch, destroyed) = EXECUTION_PROVEN (successor 1f8d183e, docket + both manifests + VERIFY-P0-01 VERIFIED_EXACT + 189 tests; PG-P1 drift fails). It found the C3 permitted_effects omitted tests/governance/test_program_control_validation.py (two tests hardcode PG-P0==ACTIVE).
- Corrected PG-P0-CLOSURE-MANIFEST.json permitted_effects_at_execution_C8 to include that test-delta file. Mandate/predecessor/successor/PAE digests UNCHANGED (0f34a306/e80f7b93/1f8d183e/bd5113a6) -> operator C4 signature subject unaffected. New manifest sha256 7417cc6a (was 9e67cd0b); the real C6 mandate record must name the new sha256 per INTERP-002 v0.4 SS5. Re-verified round-trip VERIFIED_EXACT. Both manifests regenerated. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - EVD-CLOSURE-009/010/011: advisory maker-side closure audits (3 parallel nodes)

- Persisted the three parallel advisory audits of the PG-P0 closure (Claude worker sub-agents; maker-side, NOT independent BST-Codex-Motor verification; they authorize nothing): EVD-CLOSURE-009 chain-integrity = CHAIN_SOUND (+ confirmed the MAX_PATH manifest reproducibility risk); EVD-CLOSURE-010 C7 negative-control battery = MECHANISM_ROBUST (13/13 fail-closed + docket J1/J2/J3, throwaway key); EVD-CLOSURE-011 authority-boundary = DISCIPLINE_HELD. Advisory evidence only; C0-C3 de-risked; only the human C4 signature remains. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - EVD-CLOSURE-008: durable receipt for the C3 closure manifest (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for the re-issued C3 manifest at b0e56564 (bc4ysdfum): round-trip VERIFIED_EXACT, strict UTF-8 PASS, all four digests exact (predecessor e80f7b93, successor 1f8d183e, mandate 0f34a306, PAE bd5113a6), authority + trust-root key confirmed, 189 tests + both manifest checks PASS, no finding. Green light for operator C4 signature. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - C3 (reissue): freeze PG-P0 closure manifest, clean UTF-8 (supersedes 7d13898b)

- Re-froze docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST.json as pure ASCII / valid UTF-8 / LF. The prior C3 draft 7d13898b carried a single cp1252 em-dash byte (0x97) from a Windows stdout redirect and failed the verifier strict read_text(encoding=utf-8) round-trip (independent review REJECT). Digests unchanged (predecessor e80f7b93, successor 1f8d183e, mandate 0f34a306, PAE bd5113a6); the embedded mandate_payload_b64 and thus the operator C4 signing subject are identical. Re-verified end-to-end through VERIFY-P0-01 (throwaway key) = VERIFIED_EXACT. Carries no signature; mutates no register/validator. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - EVD-CLOSURE-007: durable receipt for SIGNING-PASS-12 issuance + manifest housekeeping

- Persisted verbatim the independent checker receipt (bsad7ar0b): signing_pass_12_issuance ACCEPT_EXACT_SHA + manifest_housekeeping ACCEPT. Pre-existing default-manifest staleness independently confirmed at 73912e4 and 52bd96ec; canonical pnpm validate + 189 tests PASS; SP-12 binds v0.4 blob f4948f90; C2 blob 0641b01a unchanged; no new finding. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - chore: regenerate legacy docs/DOCUMENT-MANIFEST.json (pre-existing staleness)

- Regenerated the tool-default document manifest docs/DOCUMENT-MANIFEST.json, STALE since the accepted head 73912e4 and base 52bd96ec (pre-existing legacy condition, not introduced by closure work). Canonical pnpm validate gates on docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json (always current here); the default-path manifest is tracked but not in pnpm validate, so an independent reviewer running generate_document_manifest.py --check (default) correctly flagged it. Regen order matters: the default manifest indexes the GOV-P0-02 manifest, so GOV-P0-02 is regenerated first and the default last; both --check paths now pass. Touches only the two manifests + CHANGELOG; zero register/authority/decision/validator change. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - SIGNING-PASS-12: re-issue PG-P0-INTERP-002 against v0.4 exact text (C1 current)

- Encoded HUMAN-OPERATOR-001 re-issuance attestation: PG-P0-INTERP-002 v0.4 EFFECTIVE against exact text at e55012c3 (v0.4 blob sha256 f4948f90...), narrowly superseding the v0.3 issuance (SIGNING-PASS-10; SS4-only change) with review receipt EVD-CLOSURE-006 (ACCEPT_EXACT_SHA) on file. The C2 approval (SIGNING-PASS-11) and trust-root candidate remain valid. Appended issuance record to the v0.4 doc extend-only.
- Closure C1 complete on the current lineage; C2 trust root remains APPROVED_PENDING_PROOF_OF_POSSESSION; C3-C11 remain. Additive; full validate incl docket --check PASSES. PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe.

## 2026-07-27 - EVD-CLOSURE-006: durable receipt for INTERP-002 v0.4 (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for v0.4 at e55012c3: scope confirmed SS4-only, de-circularization sound (no layer-3/mechanism break), prior artifacts unchanged, validators + 189 tests PASS, v0.4 blob digest exact, no finding. Ready for human re-issuance against the v0.4 exact text. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - INTERP-002 v0.4: de-circularize successor evidence_refs (supersedes v0.3 at SS4 only)

- Added PG-P0-INTERP-002-CLOSURE-AUTHORIZATION-V0.4.md correcting SS4: the sanctioned successor evidence_refs now reference only execution-time-available evidence sorted({SIGNING-PASS-8, SIGNING-PASS-10, <closure mandate signing record>}); the C10 post-execution receipt is REMOVED from the set and attests the result externally (layer 3, per SS3). Root cause: v0.3 SS4 embedded the post-execution receipt, which cannot exist inside the C8 commit it attests -> docket evidence-ref check would fail at execution. Found during C3 prep from the exact VERIFY-P0-01/docket contract.
- Scope: SS4 ONLY. SS1-2 authority-scope finding + dual-action basis, SS3 layers, SS5 validator extension, SS6 C0-C11, SS7 receipts, SS8 acceptance rule unchanged. The trust-root candidate (8346f33e) and operator C2 approval (SIGNING-PASS-11, 5b19fd13) remain valid; v0.4 re-issuance re-affirms the same authority basis. C1 re-executes on re-issuance against the v0.4 exact text.
- Draft only; no live register/schema/docket/validator mutation; nothing issued/signed. PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe.

## 2026-07-27 - EVD-CLOSURE-005: durable receipt for the C2 approval encoding (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for SIGNING-PASS-11 (C2 trust-root approval) at 5b19fd13: bound candidate digests exact, candidate_unmutated true, non_activation_boundary_verified true, no finding. Trust root APPROVED_PENDING_PROOF_OF_POSSESSION (not active until C4). PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - SIGNING-PASS-11: C2 trust-root approval (APPROVED_PENDING_PROOF_OF_POSSESSION)

- Encoded HUMAN-OPERATOR-001 C2 approval of the trust-root candidate at 8346f33e (separate receipt per the no-circularity rule; binds candidate commit 8346f33e, tree 42ab3439, trust-root blob 0641b01a, raw sha256 a6806c16, public key + fingerprint, authority basis PG-P0-INTERP-002 v0.3). Lifecycle CANDIDATE_PENDING_C2_APPROVAL -> APPROVED_PENDING_PROOF_OF_POSSESSION. The candidate JSON is NOT mutated (bound digests stay valid).
- Boundary: approval binds the key to authority but does NOT activate the trust root; it becomes ACTIVE only on the first valid C4 mandate signature verified by VERIFY-P0-01 (proof of possession). No mandate accepted; no register/validator mutation; PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe. Next: C3 manifest + mandate-bytes freeze.

## 2026-07-27 - K4: trust-root CANDIDATE with operator public key (CANDIDATE_PENDING_C2_APPROVAL)

- Added docs/00-governance/signing/PG-P0-COMPLETION-TRUST-ROOT-CANDIDATE.json: the operator-generated Ed25519 PUBLIC key (raw-32 hex) + SHA-256 fingerprint, intake-validated per the corrected K3 logic (strict lowercase-hex, constant-time fingerprint match, canonical decompress/recompress roundtrip = structural validity only). Profile named sha256:rfc8032-ed25519-raw-32. Private key generated and held solely by the operator (encrypted PKCS8, offline); no agent generated, received, or handles it.
- Lifecycle: CANDIDATE_PENDING_C2_APPROVAL -> APPROVED_PENDING_PROOF_OF_POSSESSION (operator signed C2 receipt) -> ACTIVE (valid C4 mandate signature = proof of possession). No circularity: the separate C2 receipt binds the resulting commit/tree/blob digests. V2 placeholder draft preserved as history. Additive; no live surface changed. PG-P0 ACTIVE; PG-P1 NOT_READY.

## 2026-07-27 - EVD-CLOSURE-004: durable receipt for the SIGNING-PASS-10 encoding (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for the v0.3 re-issuance encoding at 266ca800: binding digests recomputed exact; supersession of the v0.2 issuance correct with history byte-preserved; strictly additive; validators 11/11; full tests 189/189; no finding. C1 final; C2 (operator keygen) next.

## 2026-07-27 - SIGNING-PASS-10: re-issue PG-P0-INTERP-002 against v0.3 exact text (C1 final)

- Encoded HUMAN-OPERATOR-001 re-issuance attestation: PG-P0-INTERP-002 v0.3 EFFECTIVE against exact text at a210e8a4 (v0.3 blob sha256 15c01709...), superseding the v0.2 issuance (SIGNING-PASS-9, preserved as history), with independent review receipt EVD-CLOSURE-003 (ACCEPT_EXACT_SHA, no finding) on file. Appended the issuance record to the v0.3 doc (extend-only; immutable Draft header preserved).
- Closure C1 COMPLETE on the consolidated execution lineage. C2-C11 remain separately gated (trust root placeholder/NOT EFFECTIVE; no mandate; no register/validator mutation). PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe.

## 2026-07-27 - EVD-CLOSURE-003: durable receipt for INTERP-002 v0.3 (ACCEPT_EXACT_SHA)

- Persisted verbatim the independent checker receipt for v0.3 at a210e8a4: hard check PASS (verifier in-lineage, 27/27), byte-faithful carries PASS, sorted-refs rule + preserved controls confirmed, validators 11/11, full suite 189/189, v0.3 blob digest exact match, no finding. Advisory only; human re-issuance remains authoritative.

## 2026-07-27 - INTERP-002 v0.3 + consolidated execution lineage on accepted base'

- Consolidated the PG-P0 closure records into the accepted integrated base' `52bd96ec` — the lineage that contains VERIFY-P0-01 in-tree (operator hard check: the verifier must exist in the exact execution lineage). Carried byte-faithfully: SIGNING-PASS-8 + issued PG-P0-INTERP-001 (from `d6252de1`); SIGNING-PASS-9 + INTERP-002 v0.2 text + trust-root v2 draft (from `32271aa2`); EVD-CLOSURE-001/002 (from `52359dc4`).
- Added `PG-P0-INTERP-002-CLOSURE-AUTHORIZATION-V0.3.md`: supersedes v0.2 per operator direction (a signed exact-text blob must not carry a known ordering ambiguity). The correction is normative: the executed successor's `evidence_refs` MUST be the canonical `sorted(...)` of the sanctioned set (EVD-CLOSURE-002 finding); examples are non-normative. All other content (authority-scope finding, corrections 2–4, C0–C11, negative tests, six-condition rule) preserved; C1 re-executes on human re-issuance against the v0.3 exact text.
- Drafts only; no live register/schema/docket/validator mutation; nothing issued or signed by this commit. PG-P0 ACTIVE; PG-P1 NOT_READY; main a908bbe.

## 2026-07-25 - PG-P0 preparation base' — integrate the SIGNING-PASS-6 accepted batch

- Integrated, at their exact accepted bytes, the four work items accepted by HUMAN-OPERATOR-001 in SIGNING-PASS-6 into a single governed preparation successor (base') off the accepted head `73912e4`:
  - VERIFY-P0-01 (`3946e946`): `tools/verify_phase_transition.py`, `tests/governance/test_phase_transition_verify.py`, `docs/work-packages/VERIFY-P0-01.md`, `docs/evidence/EVD-VERIFY-001-executable-verifier.md`.
  - GATE-P0-01 (`f552da30`): `docs/00-governance/PG-P0-GATE-CONTRACT-DRAFT.md` (v0.1 draft), `docs/00-governance/AUTHORITY-MATRIX-COMPLETE-PHASE-PROPOSAL.md`, `docs/work-packages/GATE-P0-01.md`.
  - DEC-0014 (`8b8b79ed`): `docs/decisions/DEC-0014.md` + its `DECISION-REGISTER.md` row.
  - SKEL-P0-01 reconciliation (`11329bba`): the appended "Current status (derived)" section.
- Carried the acceptance record `docs/00-governance/signing/SIGNING-PASS-6.md` (`98ec002f`).
- Regenerated the document manifest; reconciled this changelog. Additive only: no live register mutated (AUTHORITY-MATRIX.json / AUTHORITY-IDENTITY-REGISTER.json byte-unchanged); no merge to `main`; PG-P0 remains ACTIVE; PG-P1 NOT_READY. This base' is the ground on which the effective-successor gate contract and the completion-enablement drafts are rebuilt so their references resolve in-tree.

## 2026-07-21 - GOV-P0-01 Program Goal v0.2 controlled draft

- Converted the supplied Program Goal v0.2 into BOPEN-GOAL-001 with a source hash and explicit non-authorizing status.
- Added BOPEN-GOV-001, DEC-0010 and namespaced program/roadmap/bootstrap/research lifecycle aliases to prevent gate-status leakage.
- Established draft program registers, a source-complete requirement catalog and fail-closed program-control validation.
- Extended work-item, evidence and handoff templates with maker/checker, session, worktree, SHA, scope and authority separation fields.
- Kept PG-G0 NOT_READY, B7/DEC-0007 pending, RES-G3-G7 open and production implementation unauthorized.

## 2026-07-21 - BOOT-P0-12 external-control reconciliation

- Reconciled BOOT-P0-01 and BOOT-P0-08 with the protected Gitea PR #1 merge and current `main` protection observation.
- Updated EVD-BOOT-011 without changing the historical activation record.
- Moved deterministic bootstrap readiness to `ready_for_authority_review` while preserving B7 as pending and production implementation authority as false.
- Kept DEC-0007 proposed for the bOPEN Architecture Authority.

## 2026-07-13 - research R0 control establishment

- Approved DEC-0009 to keep physical upstream clones and raw evidence outside the bOPEN worktree.
- Assigned the R0 SARCHI/ARCHI/ENGIN/REV responsibilities and SecB license/compliance ownership.
- Consolidated the BoxyHQ source ID and expected pin, license and lock checksums.
- Hardened the Windows clone and verification scripts against ambient credential prompting, wrong origins, attached branches, missing locks and checksum drift.
- Added a recorded baseline runner and reproduced the exact result in separate ENGIN and REV workspaces.
- Recorded npm 10.9.2 as the R0 compatibility requirement, npm 11 lock rejection, the pinned upstream format failure, and passing lint/types/unit/build outcomes.
- Added EVD-RES-002 and marked G0-G2 `PASS WITH CONDITIONS`; G3-G7 and production implementation remain closed.

## 2026-07-13 - multi-tenant DEV readiness

- Accepted DEV-P0-01 for contract, fixture, validator, and test execution only.
- Added draft membership, active-context, and tenant-ownership schemas.
- Added seven synthetic multi-tenant readiness scenarios with API and database cross-tenant denial.
- Extended contract validation and focused tests for membership separation, trusted context, tenant ownership, deny-by-default behavior, and audit correlation.
- Added EVD-DEV-001 while keeping G7, normative approval, and production implementation gates closed.

## 2026-07-13 - bGitea protected review activation

- Created and verified the private `bst-sa/bopen` local source-of-truth repository and configured credential-free `origin`.
- Added separated Gitea Architect, Engineer, and Reviewer teams with repository-only membership.
- Installed the checksum-verified repository-scoped Gitea Runner 2.0.1 over rootless Podman.
- Protected `main` against direct/force pushes and administrator bypass, with Reviewer-only approval and merge authority.
- Added Gitea CODEOWNERS and governance workflow controls plus EVD-BOOT-011.
- Observed successful Actions run 17/job 33 and required the exact `Bootstrap Governance / validate (pull_request)` context.
- Recorded RSK-012 for rootless WSL host job networking required by the unavailable `/dev/net/tun` device.
- Applied independent review findings by making the Gitea workflow token read-only, pinning external actions to full commits, and validating both GitHub and Gitea workflows.
- Reported the Gitea hardening incident and residual host decisions to SecB and bstSA SARCHI without credential values.

## 2026-07-13 - GitHub draft review activation

- Published the reconciliation branch and opened draft GitHub PR #1.
- Recorded the passing Bootstrap Governance workflow result.
- Replaced placeholder CODEOWNERS teams with verified repository administrator `@bstBizEra`.
- Recorded DEC-0008 and RSK-011 after GitHub rejected private-repository branch protection under the current account plan.
- Approved DEC-0008 option 2, preserving private bGitea as the protected working source and GitHub as the stable review/publication surface.

## 2026-07-13 - approved GitHub reconciliation

- Recorded sponsor approval of DEC-0006 option 1.
- Rebuilt the BOOT-P0 history on a reconciliation branch from existing GitHub `main`.
- Preserved the GitHub root commit and resolved the one-line README conflict with the governed bootstrap README.
- Added EVD-BOOT-010 and kept direct or force publication to `main` prohibited.

## 2026-07-13 - BOOT-P0 completion self-review

- Audited all BOOT-P0-01 through BOOT-P0-12 outcomes against current evidence.
- Added executable secret and supply-chain checks with tests and full CI/pre-commit coverage.
- Added the missing exception register and formal DEC-0006/DEC-0007 decision requests.
- Classified ten packages as execution-complete, two as external-activation-pending, and BOOT-P0-12 as authority-review-pending.
- Recorded EVD-BOOT-009 without retaining local bGitea credentials.

## 2026-07-13 - missing bootstrap evidence

- Generated EVD-BOOT-001 AGENTS hierarchy validation evidence.
- Generated EVD-BOOT-002 document manifest validation evidence.
- Updated BOOTSTRAP-GATES B2/B3 status to evidence generated.
- Refreshed the bootstrap gate readiness report so pending evidence is no longer listed.

## 2026-07-13 - bootstrap gate readiness

- Added a deterministic bootstrap gate readiness report tool for BOOT-P0-12.
- Generated `artifacts/validation/bootstrap-gate-readiness.md`.
- Added governance tests for the report and EVD-BOOT-007 evidence.
- Confirmed B7 remains review-required and production implementation remains unauthorized.

## 2026-07-13 - vertical-slice fixtures

- Added the first vertical-slice acceptance fixture for BOOT-P0-11.
- Added a draft authorization audit-event schema.
- Extended contract validation to check `.acceptance.json` fixtures and correlation consistency.
- Added contract tests covering the seven first-slice acceptance scenarios.
- Added EVD-BOOT-006 evidence.

## 2026-07-13 - first coding move

- Added a standard-library contract validation harness for Phase 0 machine-readable contracts.
- Added contract validator tests and package scripts.
- Marked existing draft JSON schemas with top-level draft status metadata.
- Added EVD-BOOT-005 evidence for BOOT-P0-10.

## 2026-07-13 - roadmap build start

- Started the roadmap-safe Phase 0 build lane through BOOT-P0-09/BOOT-P0-01.
- Documented the local bGitea working remote and GitHub stable publication model.
- Added EVD-BOOT-004 source-control baseline evidence and traceability.
- Recorded DEC-0006/RSK-009 for the unrelated local bootstrap and GitHub `main` histories.
- Verified local bGitea service at `http://localhost:3030/` and recorded RSK-010 for the unverified local `origin` repository path.

## 2026-07-13 - local preparation

- Prepared downloaded BOPEN-BOOT-001 full pack for local version control.
- Fixed `pnpm test:governance` quoting so unittest discovery works in Windows PowerShell.
- Added local bootstrap validation evidence for BOOT-P0-05.

## 2026-07-12 — v1.0

- Created BOPEN-BOOT-001 full AGENTS.md and documentation bootstrap pack.

## Append-only entry — 2026-07-21 — GOV-P0-02 authority-docket proposal

- Added a draft exact-bound PG-G0 authority docket using only actions present in the live draft authority matrix.
- Added fail-closed human-identity, concurrence, Git/tree, artifact-hash, expiry and non-authority validation.
- Proposed DEC-0012 for five missing root instruction paths and generated-manifest handling.
- Preserved missing governance/register/gate actions, technology checker dates and every human disposition as blockers.
- Kept PG-G0 NOT_READY and production implementation unauthorized.

## Append-only entry — 2026-07-21 — GOV-P0-02 authority-record hardening

- Required explicit action, subject, validity, revocation and evidence controls for bound authority identity records.
- Required grantors to carry explicit delegation-specific action and subject scopes.
- Bound identity and delegation evidence existence to the referenced commit.
- Added negative tests for omitted scopes, malformed scope types, revoked identities, malformed validity and missing historical evidence.
- Preserved all authority and implementation outcomes as false pending external human authority.

## Append-only entry — 2026-07-22 — GOV-P0-04 exact-SHA review

- Recorded EVD-GOV-005 with a technical `REJECT` verdict for exact candidate `203ed05`.
- Preserved the passing 44-test focused and 160-test full-suite results while disclosing the failing required manifest check.
- Identified identity-provider/subject, approval-provenance, evidence and delegation incompatibilities between the proposal and docket validator.
- Repaired the docket test helper to prefer temporary fixtures and added a conflicting-repository-file regression case.
- Drafted a non-effective PG-G0 authority-docket v0.2 rebinding plan.

## Append-only entry — 2026-07-22 — GOV-P0-04 corrective-candidate review

- Issued EVD-GOV-006 as independent `ACCEPT_EXACT_SHA` evidence for candidate `d7d8699326345bb1a2f027e4027fb90d18649022` after all focused, full and repository checks passed.
- Preserved EVD-GOV-005 as an immutable `REJECT` for predecessor `203ed05162dccb2729d4c39e25050817384c3b4b`.
- Kept GOV-P0-04 proposed, PG-G0 not ready and every activation, merge, release, deployment and production outcome false pending human authority.

## Append-only entry — 2026-07-23 — PG-G0 authority docket v0.2 preparation

- Bound the successor docket to Operator Batch 1 commit `26bea090c0aca14f1337c4be1a146fd48bb1f626` and its exact 34-record substrate inventory.
- Adopted the ten-entry authority-matrix proposal as a draft bound matrix with approval provenance still null.
- Prepared 13 unsigned and ineffective Batch 2 disposition surfaces while preserving the original five pending docket decisions.
- Revised root-control validation so activation can occur only as one complete five-ledger Signing Pass 2 event; no activation event was added.
- Kept independent review pending and PG-G0, merge, release, deployment and production implementation false.

## Append-only entry — 2026-07-23 — PG-G0 authority docket v0.3 signed state

- Encoded all thirteen operator-signed Batch 2 dispositions with exact role-bound human actors and required concurrence blocks.
- Approved the authority matrix and six program registers with attributable provenance; made BOPEN-GOV-001 and DEC-0013 effective; accepted GOV-P0-01/GOV-P0-04; approved DEC-0007/BOOT-B7.
- Activated the five root ledgers through one identical append-only B6 event and retained their immutable Draft/Inactive genesis prefixes.
- Rebound the v0.3 inventory to Signing Pass 2 commit `60c4831f4fcdfabb876d62f4eb98949b4a1a5a66` and enforced exact signed transformations in schema, validator and negative tests.
- Preserved all five B8 requests as `PENDING` and PG-G0, merge, release, deployment, runtime and production implementation as unauthorized pending a new independent exact-SHA review and later decisions.

## Append-only entry - 2026-07-24 - PG-G0 terminal gate passage

- Encoded the operator's Signing Pass 4 `PG-G0-DEC-006` `PASS_PG_G0` approval without altering the signed subject or outcome.
- Transitioned the docket to terminal `DISPOSED`, regenerated readiness as `PG_G0_PASSED`, appended the passage event to all five root ledgers, and opened PG-P0 for authority review.
- Kept production implementation, merge, release, deployment and runtime flags false; final independent exact-SHA review remains required.

## Append-only entry - 2026-07-24 - PG-P0 preparation opening

- Encoded the operator's Signing Pass 5 transition of PG-P0 from `READY_FOR_AUTHORITY_REVIEW` to `ACTIVE` preparation.
- Bound the schedule entry to SKEL-P0-01, SIGNING-PASS-5 and EVD-GOV-017; the work package remains proposed and unaccepted.
- Preserved preparation/review-only scope and kept production implementation, migrations, merge, release, deployment and runtime unauthorized.

## Append-only entry - 2026-07-24 - SKEL-P0-01 checker review

- Recorded Codex concurrence with bounded findings on scope, allowed paths, acceptance reproducibility and the fail-closed skeleton-validator requirement.
- Kept SKEL-P0-01 proposed and unaccepted pending Human Engineering Authority disposition; no skeleton implementation was performed.

## Append-only entry - 2026-07-23 - v0.4 remediation rebuild

- Rebuilt from `8a0987070efa4108e7f9ada716a8fb533fa47e42`, preserving the signed docket and all B8 outcomes.
- Appended the remediation ledger event after the existing final entry and regenerated the GOV-P0-03 package manifest in the same commit.
- Removed the live DELEGATED validator path, added temporary-fixture manifest ordering and DIRECT-only negative coverage, and retained the 33-item disposition table.

## Append-only entry - 2026-07-23 - PG-G0 authority docket v0.4 B8 signed successor

- Encoded exactly the five Signing Pass 3 B8 approvals with final-authority identity-register provenance, signing timestamp and decision references.
- Rebound the v0.4 inventory and repository binding to the post-signing substrate; readiness now reports `ready_for_pg_g0_gate_decision: true` with zero validation errors.
- Surfaced B9/PASS_PG_G0 as pending with an independent-conformance prerequisite; no B9, merge, release, deployment, runtime or production authority was signed.

## Append-only entry - 2026-07-23 - v0.4 review-finding remediation

- Preserved the v0.4 docket, inventory, B8 approvals, B9 staging and readiness bytes unchanged.
- Itemized all 33 removed predecessor docket tests with v0.4 obsolescence/supersession decisions and added a repeatable root-manifest regression test.
- Clean-checkout discovery passes 144/144; `pnpm validate` passes. EVD-GOV-012 remains an immutable reject and a new exact-SHA review is required.

## Append-only entry - 2026-07-24 - MANIFEST-P0-01 deterministic manifest check

- Fixed `tools/generate_document_manifest.py`: `--check` now adopts the committed `generated` date so a byte-frozen candidate no longer goes stale at UTC-midnight rollover, restoring exact-SHA reproducibility; content drift (paths/sha256/bytes/count) still fails. Write mode uses `newline="\n"` (LF) to fix silent CRLF emission on Windows.
- Added regression test `tests/governance/test_document_manifest_reproducibility.py` proving date-invariance and content-sensitivity.
- Demonstrated on an isolated branch for operator disposition; the tool is outside SKEL-P0-01 allowed paths, so acceptance/merge requires a separate operator decision. No manifest content changed; no signed byte changed. Status: Proposed; not accepted.

## Append-only entry - 2026-07-24 - MANIFEST-P0-01 acceptance-criteria correction

- Corrected a self-contradicting acceptance criterion in `docs/work-packages/MANIFEST-P0-01.md`: it read "no manifest content changes", but the commit legitimately adds its own work-package record and changes the CHANGELOG record in GOV-P0-02. The criterion now states the ONLY manifest record changes are the documents this commit adds/changes (its work package + changelog), with no other record change and no signed byte change. Independent-review finding (WSL BST-Codex-Motor); wording-only fix, no behavior change.

## 2026-07-24 — MANIFEST-P0-01 acceptance

- HUMAN-OPERATOR-001 accepted `MANIFEST-P0-01` at exact SHA `78e985b41ed8354f6525154d5cdfbe4b1052a2d5` after dual independent `ACCEPT_EXACT_SHA` receipts and canonical reproducibility verification.
- This acceptance advances only the governed preparation lineage; merge, release, deployment, runtime activation, production implementation, PG-P0 completion and PG-P1 transition remain unauthorized.

## Append-only entry - 2026-07-24 - SKEL-P0-01 sole-maker candidate on accepted base'

- Rebuilt SKEL-P0-01 as a fresh sole-Claude-maker candidate on governed base' `aab8bd9` (Option B): the human-accepted MANIFEST-P0-01 reproducibility fix is inherited from the accepted base, so SKEL owns only the reconciled `pnpm-lock.yaml` (workspace importers), not the manifest tool.
- Every SKEL byte is authored solely by Claude (`claude-opus-4-8`); the earlier operator replay `700cf1e` carried Codex-authored bytes from conflict resolution and is superseded. Re-authored skeleton validator (fail-closed non-.d.ts rule); references the MANIFEST-P0-01 acceptance record.
- Canonical `pnpm validate` clean under `--frozen-lockfile`; signed surfaces byte-unchanged. Status: Proposed; not accepted; fresh independent Codex review required.

## 2026-07-25 — SKEL-P0-01 acceptance

- HUMAN-OPERATOR-001 authorized the `pnpm-lock.yaml` scope amendment and accepted SKEL-P0-01 at exact SHA `f1eea272442a0587ab5843ba28c6ce47b91e1615`.
- Acceptance is bounded to the governed preparation lineage; merge, release, deployment, runtime activation, PG-P0 completion and PG-P1 transition remain separately gated.
