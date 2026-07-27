---
name: bopen-windows-toolchain
description: Avoid the Windows and tooling failure modes that silently corrupt bOPEN governed artifacts or produce false validation verdicts. Use before writing, generating or validating any governed artifact on Windows, and whenever a check fails on one machine but passes on another, fails locally but passes in CI, or a manifest, document manifest or readiness report reports unexplained staleness.
---

# bOPEN Windows Toolchain

Every item below caused a real rejected artifact or a false verdict. Apply before writing or
validating any governed file.

## Paths: MAX_PATH produces FALSE failures

`tools/generate_document_manifest.py` walks `docs/` with `rglob` and no long-path guard. Files whose
absolute path exceeds 260 characters are silently skipped, so the manifest `--check` FAILS on a deep
checkout and PASSES on a short one. The same trap hits any post-execution verification harness.

- Run validators from a SHORT worktree path (for example `C:/b-<slug>`), not from a deep
  `.claude/worktrees/...` path.
- If a manifest or readiness report reports "stale" and nothing else is wrong, check the path
  length before concluding anything about the commit.
- Remediation when hardening a walker: apply the `\\?\` extended-length prefix to the ROOT before
  walking. That alone is sufficient and is a pure path-handling change with no semantic effect.
  Enumerating with `git ls-files` does NOT fix it on its own (`is_file()` and `read_bytes()` still
  fail on long paths) and, if added, changes the manifest's meaning to tracked-files-only and adds a
  subprocess dependency. Prefer the prefix; reach for `git ls-files` only if you actually want
  tracked-only semantics.

## Encoding: write explicit UTF-8, prefer ASCII

- Use `open(path, "w", encoding="utf-8", newline="\n")` and `json.dumps(..., ensure_ascii=True)`.
- NEVER build a governed file with `python - > file` on Windows: stdout uses cp1252, so an em dash
  becomes byte `0x97`, which fails a strict `read_text(encoding="utf-8")` and rejects the artifact.
- Assert before committing: zero `0x97` bytes, zero `\r\n`, and for signed or verified artifacts
  zero non-ASCII characters.
- Pin `core.autocrlf=false`, `core.eol=lf`, `core.safecrlf=false` when comparing applied patches;
  autocrlf translation misattributes diffs.

## Interpreters and commands

- Use the pinned full-path interpreter for validation. A bare `python` or a package-manager wrapper
  can fail to resolve in sandboxed reviewer environments.
- Pass commit messages with `git commit -F <file>`. Nested heredocs and apostrophes break the shell.
- `npm run validate` maps to the Python validator chain; `npm run test:governance` is a
  governance-only subset - run full discovery when a closure claim depends on it.

## Validators

- The authority docket `--check` can return a non-zero exit with no printed reason. Import the
  module and call the validation function directly to surface `validation_errors`.
- NEVER run `--write` to "fix" a failing `--check`. `--write` regenerates the report to match the
  CURRENT state, converting a genuine integrity failure into a pass. Investigate instead.
- There are TWO document manifests and the default one indexes the other. Regenerate in order:
  the explicit `--output` manifest FIRST, the default manifest LAST, in every commit.
- History-dependent validators cannot run from `git archive` output; materialise a commit with
  `git clone --shared --no-checkout` plus a detached checkout.

## Git hygiene

- Commits made in a detached worktree are orphaned unless a ref points at them. Keep a lightweight
  non-authoritative tracking branch and repoint it after each commit.
- Prune stale worktrees. Registered worktrees whose directories are gone can make `worktree add`
  and `prune` misbehave, and they keep old commits reachable.
- Use a literal expected-old SHA for compare-and-swap. The all-zero object id means "must not
  exist" and yields a misleading error.
