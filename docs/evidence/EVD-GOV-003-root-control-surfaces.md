# EVD-GOV-003 — Exact Root Control Surface Evidence

**Document ID:** EVD-GOV-003
**Version:** 0.1
**Status:** Draft maker evidence; independent review pending
**Owner:** Engineering Authority
**Issued:** 2026-07-21
**Evidence ID:** EVD-GOV-003
**Work package:** GOV-P0-03
**Decision reference:** DEC-0012 option 1
**Environment:** Windows / `C:\laragon\www\bopen-worktrees\gov-p0-03-root-controls`
**Source/base commit:** `82ed6b38b118aab14a9961c5d75a33e515cb136a`
**Source/base tree:** `cad6b595fb74a70cc706a78d45778e15524aebd9`
**Maker:** `/root/gov_p0_03_preflight`
**Checker:** Pending different-agent exact-SHA review
**Authority effect:** None

## Authority and traceability

The current user explicitly authorized DEC-0012 option 1 for drafting-only work through 2026-08-21. The authorization permits the exact package paths and does not accept GOV-P0-03, approve governance, resolve DEC-0012 manifest options, pass a gate, authorize merge, release, runtime or production implementation.

## Procedure

1. Bind work to the exact GOV-P0-02 base commit and tree.
2. Create all five exact root surfaces together with Draft, Inactive and false-authority metadata.
3. Validate exact paths, casing, file type, metadata, cross-links, unresolved config, ledger semantics, append-only history and the package manifest.
4. Run negative tests, the full repository validation chain and scope checks.
5. Commit only after maker checks pass, then require a different-agent exact-SHA review.

## Expected result

All authorized package checks pass while `PG-G0 passed`, `production implementation authorized`, `merge authorized` and `release authorized` remain false.

## Actual result

Pending maker execution. No unexecuted check is represented as passed.

## Artifacts and logs

- Root controls: `Roadmap.md`, `Master_Standards.md`, `Progress_Log.md`, `Backlog.md`, `Recap_Today.md`
- Draft schema: `contracts/governance/root-control-surface.schema.json`
- Validator: `tools/validate_root_control_surfaces.py`
- Tests: `tests/governance/test_root_control_surfaces.py`
- Package manifest: `docs/manifests/GOV-P0-03-PACKAGE-MANIFEST.json`

## Security and clean-room declaration

No secrets, personal identity values, production data, upstream source, application code, services, packages, infrastructure, migrations, runtime configuration, deployment or external activation are in scope.

## Rollback

Before merge, remove the isolated proposal branch/worktree. No protected branch, runtime or production state is changed.

## Independent verdict

Pending exact final commit and tree. A technical verdict cannot accept GOV-P0-03 or authorize any gate, merge, release, runtime or production action.

## Residual risks

- Shared document status, traceability, evidence and work-package indexes are outside the authorized path set and therefore remain unreconciled.
- The instruction-level `/opt/bizera-smartthink/config/` sources are unavailable and remain `UNRESOLVED_EXTERNAL_DEPENDENCY`.
- DEC-0012 manifest-option disposition remains pending; this package manifest is candidate evidence only.

## Append-only maker verification record — 2026-07-21

**Source:** Commands executed in the authorized GOV-P0-03 worktree
**Agent ID:** `/root/gov_p0_03_preflight`
**Candidate state:** Uncommitted maker candidate; exact commit and tree pending

Executed results:

- `python tools/validate_root_control_surfaces.py --check`: PASS; five root controls and eleven manifest-bound package files checked.
- `python -m unittest tests.governance.test_root_control_surfaces`: PASS; 11/11 tests.
- `python -m unittest discover -s tests -p "test_*.py"`: PASS; 158/158 tests.
- `python tools/validate_repository.py`: PASS; 27 mandatory paths/invariants.
- `python tools/validate_contracts.py`: PASS; 19 machine-readable contracts.
- `python tools/validate_program_controls.py`: PASS; seven draft registers; no PG-G0 assertion.
- `python tools/report_program_g0.py --check`: PASS; deterministic report current.
- `python tools/validate_pg_g0_authority_docket.py --check`: PASS; deterministic authority report current.
- `python tools/check_clean_room.py`: PASS.
- `python tools/check_secrets.py`: PASS.
- `python tools/check_supply_chain.py`: PASS.
- `git diff --check`: PASS.
- `python tools/generate_document_manifest.py --output docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json --check`: expected fail-closed result, because the historical GOV-P0-02 snapshot inventories `docs/` as a mutable current set and GOV-P0-03 is prohibited from replacing it.

Reason: execute every in-scope maker check and preserve the preflight manifest conflict rather than weakening or rewriting an earlier snapshot. Benefit of the old phase: the existing check detects documentation drift and fails closed. Expected outcome: independent review can distinguish a fully passing GOV-P0-03 package/test surface from the still-unresolved DEC-0012 manifest-option design.

The manifest failure is a residual repository-wide validation blocker, not a skipped or passing check. It does not alter the Draft, Inactive or non-effective status of this package.

## Append-only exact-byte rework record — 2026-07-22

**Source:** Independent checker `REQUEST_CHANGES` against commit `651951f229f6f72c4ebab35a2458ebd9a4216583`
**Agent ID:** `/root/gov_p0_03_preflight`
**Disposition:** Rework in progress; successor exact commit and tree pending

The checker demonstrated that the first validator normalized CRLF and CR bytes before package-manifest hashing and used Python text-mode subprocess decoding before append-only Git-blob comparison. Those transformations allowed a line-ending-only byte mutation to compare as equivalent even though the repository bytes changed.

The successor validator hashes `Path.read_bytes()` directly, reads historical blobs through binary `git cat-file blob`, and applies prefix validation to the unmodified byte sequences. New negative tests require a CRLF-only package mutation to stale the manifest and prove that rewriting a committed CRLF blob to LF fails byte-prefix validation.

Reason: exact-byte integrity is required for an append-only control and package evidence binding. Benefit of the prior phase: the first validator established exact paths, metadata, authority-state and atomic-genesis checks, allowing the remaining byte-normalization flaw to be isolated. Expected outcome: platform or checkout newline transformations cannot conceal a manifest change or historical rewrite.

This rework has no authority effect and does not accept GOV-P0-03, resolve DEC-0012 manifest options, pass a gate, authorize merge, release, runtime or production implementation.

## Append-only exact-byte maker verification — 2026-07-22

The successor maker candidate passed the exact-byte package validator, 13/13 focused GOV-P0-03 tests and 160/160 full repository tests. Repository validation passed 27 mandatory paths/invariants; contract validation passed 19 machine-readable contracts; program-control validation passed seven draft registers; both deterministic program reports were current; clean-room, secret, supply-chain and `git diff --check` checks passed.

The new negative tests reproduced both checker cases: converting a manifest-bound file from LF to CRLF makes the package manifest stale, and rewriting a committed CRLF blob to LF is observed byte-for-byte and rejected as truncation plus prefix rewriting. These are maker results only. A fresh different-agent review must bind the successor exact commit and tree.
