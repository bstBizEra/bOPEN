# .agents Changelog

## 2026-07-28 - Tooling, and defects found by that tooling

Added working package tooling: `schemas/skill-manifest.schema.json`, `tools/validate_skill_package.py`
(stdlib-only; multi-skill discovery, maturity tiering, cross-skill and repo-path resolution, encoding
hygiene, trigger quality, `--strict-triggers`, `--json`) and `tools/test_validate_skill_package.py`
(32 tests, all fail-closed cases pinned). Estate: 15 skills at tier L0, 1 at L3 - bimodal, no gradient.

### Fixed - a routing fail-open

"the manifest check fails on my machine but not in CI" shares no content word with
`bopen-windows-toolchain` and three with `bopen-ci-repair`, so it mis-routed. `bopen-ci-repair` then
said "make the smallest authorized fix", and the repository ships that fix as one word
(`report:program-g0-authority` runs the docket validator with `--write`), which regenerates the report
to match the current state and converts an integrity failure into a pass. The prohibition existed only
in the skill that would not fire. `bopen-ci-repair` now carries a fifth cause class
(environment-dependent verdict), an explicit never-regenerate-an-attested-artifact rule, and a route to
`bopen-windows-toolchain`, whose description now matches how the failure is actually described.

### Fixed - a self-contradiction introduced by the 2026-07-27 upgrade

`bopen-worktree-management` gave three different answers for a failure inside an apply worktree,
because the apply rule was appended without scoping the pre-existing general rule. The file now
distinguishes a **work worktree** (retain until closure evidence exists) from an **apply worktree**
(disposable; destruction on failure is required, not premature), and the stop condition is scoped to
the former.

### Fixed - duplication and a missing preflight

`bopen-phase-closure` restated authority-scope rules owned by `bopen-governance-check` and was the only
governance-critical skill that never invoked it. It now has a Preconditions section pointing at the
preflight and keeps only the phase-transition-specific delta. `bopen-git-governance` keeps a pointer
instead of a restatement.

### Corrected - `bopen-evidence-envelope` destination

`docs/06-evidence/EVIDENCE-ENVELOPE.md` exists on disk in one working tree but is tracked in no git
lineage, so it is absent from any fresh clone and from CI. The skill now says so and adds the general
rule: resolve a destination by git tracking, not disk presence.

### Corrected - MAX_PATH remediation advice

The 2026-07-27 entry recommended a `git ls-files` + `\\?\` hybrid. Independent reproduction showed the
`\\?\` prefix applied to the walk ROOT is sufficient on its own (332 records on a deep root, versus 326
for `git ls-files` alone), so the git half is unnecessary and would have added a subprocess dependency
plus a real semantic change to tracked-files-only. `bopen-windows-toolchain` now says so.

### Known defects found, not yet fixed (owned by the bopen-architecture package)

- `ci/validate-skill.yml` filters on `bopen-architecture/**` with `working-directory: bopen-architecture`,
  but the package lives under `.agents/skills/`. The filter never matches: no skill has working CI.
- `scripts/validate_package.py` prints a U+2014 em dash, which becomes byte `0x97` under a cp1252
  stdout - redirecting its output to build an evidence receipt produces a corrupt receipt.
- The manifest schema's `version` pattern has an unbracketed leading alternation, so `"0abcXYZ"`
  validates; this defeats `immutableVersionRequired`.
- Twelve package files carry typographic dashes, including all five `assets/*-template.md`, so the
  corruption propagates into every generated ADR and conformance review.
- `bopen-portal-verification` cites routes that exist nowhere; `apps/` holds only AGENTS.md and README.md.
- The validator resolves repo paths against disk rather than git tracking.

## 2026-07-27 - Upgrade from the PG-P0 closure track

Source of change: lessons implemented and independently verified during the PG-P0 phase-closure
track (signed Stage-1 mandate, fail-closed apply pipeline, adversarial fail-proof rounds). Every
item below traces to a real rejected artifact, a false verdict, or an independent review finding.

`.agents` is untracked local operating guidance, not a governed register artifact. It informs
practice; it carries no governance authority.

### Added

- `skills/bopen-phase-closure` - the governed phase-transition playbook: authority model, the
  authority-basis rule, the coordinated-change requirement, three evidence layers, the C0-C11
  sequence, the six-condition acceptance rule, human-only acts, and stop conditions.
- `skills/bopen-windows-toolchain` - the environment failure modes that silently corrupt governed
  artifacts or produce false verdicts: MAX_PATH false staleness, cp1252 `0x97` corruption from
  stdout redirection, CRLF, dual-manifest regeneration order, `commit -F`, silent validator exit
  codes, `--write` as a dangerous "fix", history-dependent validators, orphaned detached commits.

### Corrected

- `skills/bopen-evidence-envelope` - previously pointed only at `docs/06-evidence/EVIDENCE-ENVELOPE.md`,
  which is absent from the governance lineage. Now names both destinations, requires verifying which
  exists, and adds exact-subject binding, honest independent-vs-advisory classing, layering (a
  post-execution receipt must not be referenced from the commit it attests), and recording failures.

### Upgraded

- `skills/bopen-git-governance` - added the authorized-apply section: expected-old compare-and-swap,
  patch-digest pre-check, gating signature verification on exit code AND stdout, one-commit
  coordinated change, and short-path/encoding pointers.
- `skills/bopen-worktree-management` - retention and removal are now asymmetric (retain on success
  until recognition is recorded; remove on every failure path so a refused compare-and-swap leaves
  no reachable orphan), never retry in place after an abort, plus path-length and stale-worktree
  hygiene.
- `skills/bopen-governance-check` - added per-component authority scope, expiry as a live control
  with days remaining, explicit maker/checker separation, and escalation for governance-narrative
  gaps that byte checks cannot detect.

### Known gaps not yet addressed

- `tools/generate_document_manifest.py` long-path hardening (`git ls-files` enumeration plus the
  `\\?\` prefix) remains a proposed post-closure change.
- Trust-root ingest hardening (reject duplicate key ids and small-order public keys) and absolute
  timestamp comparison instead of lexical ISO-8601 ordering remain proposed.
- `tools/validate_program_controls.py` has no fail-closed rule for a phase in
  `READY_FOR_AUTHORITY_REVIEW`.
