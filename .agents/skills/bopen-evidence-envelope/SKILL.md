---
name: bopen-evidence-envelope
description: Create a reproducible bOPEN evidence envelope or durable independent-review receipt for an authorized work item after tests and review artifacts exist.
---

# Evidence Envelope

Record authority, traceability, commits, files, commands, tests, findings, artifacts, hashes,
rollback and maker/checker dispositions. Do not mark unexecuted tests as passed.

## Destination

Use the destination that exists in the lineage you are working in - verify before writing:

- `docs/evidence/EVD-<TRACK>-NNN-<slug>.md` is the established convention in the governance
  lineage (closure receipts, review receipts, reproduction records). It is git-tracked.
- `docs/06-evidence/EVIDENCE-ENVELOPE.md` is the work-item envelope template. As of this writing it
  exists ONLY as an untracked file in one working tree - it is in no git lineage, so it is absent
  from a fresh clone and from CI. Treat it as a local convenience, not a governed template, until
  it is committed.

Resolve a destination by git tracking, not by disk presence. An untracked template is unversioned,
unreviewable, and invisible to any other checkout.

## Bind exact subjects

Every receipt binds full 40-character commit and tree SHAs, content digests of the artifacts it
attests, the checker identity and independence basis, the exact commands and tool versions, the
test result, the verdict, and a timestamp. Bind SHAs, never branch names. A runtime task id is a
pointer, never a trust anchor.

## Class the receipt honestly

State plainly whether the receipt is an INDEPENDENT checker verdict or an ADVISORY maker-side
result, and say what it does not certify. Persist an independent checker's content verbatim; do
not paraphrase a verdict you did not produce, and do not certify a verdict you did not read
yourself from its own output.

## Layering

A post-execution receipt attests a commit and therefore must not be referenced from inside that
commit. Keep pre-execution manifests, the execution commit and post-execution receipts in separate
artifacts (see `bopen-phase-closure`).

## Record failures too

A rejected candidate, a reproduction that refuted a claim, and a superseded artifact are evidence.
Persist them with the correction, not only the eventual pass.
