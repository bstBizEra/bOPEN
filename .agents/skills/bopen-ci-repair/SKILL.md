---
name: bopen-ci-repair
description: Diagnose and repair a failing bOPEN CI workflow within an authorized work item while preserving security and verification controls. Use when a build, test or validator step fails, including when it fails only on one machine or only in CI.
---

# CI Repair

Reproduce the failure.
Separate infrastructure, dependency, flaky-test, product-code and **environment-dependent-verdict** causes.
Make the smallest authorized fix.
Do not weaken tests or security scanning to obtain green status.
Capture before/after evidence.

## Before fixing: is the verdict real?

If the result differs between machines, between a deep and a short checkout path, or between a local
run and CI, suspect the verdict before the code. A validator can report a FALSE failure - for example
a document-manifest or readiness report that is "stale" only because long paths silently truncated the
file walk. Route to `bopen-windows-toolchain` and confirm the failure reproduces on a short path with
the pinned interpreter before changing anything.

## Never regenerate an attested artifact to obtain green

A failing `--check` on a signed, pinned or attested surface is an INTEGRITY signal, not a staleness
nuisance. The same tools expose a `--write` mode, and the repository ships one-word wrappers for it
(for example `report:program-g0-authority`). Running `--write` regenerates the report to match the
CURRENT state, converting a genuine integrity failure into a pass and destroying the evidence that
something diverged.

- NEVER run `--write`, `--fix`, `--update`, `--accept` or a regeneration wrapper as remediation for a
  failing `--check` on a governed artifact.
- Regeneration is legitimate ONLY as a declared, authorized step of a governed change, where the
  inputs changed for an approved reason - never as a repair for a check you did not expect to fail.
- If you cannot explain WHY the artifact diverged, you have not diagnosed the failure. Stop and
  escalate; see `bopen-governance-check`.

## Scope limits

Green is not authorization. A passing pipeline does not authorize merge, release or deployment, and
does not substitute for independent review. Do not touch governed registers, signed records, trust
roots or validator expected-state to make a pipeline pass - those are governed changes with their own
authority path (`bopen-phase-closure`, `bopen-governance-check`).
