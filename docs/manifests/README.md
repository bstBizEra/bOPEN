# Versioned Document Manifest Snapshots

**Version:** 0.1
**Status:** Draft operational convention pending DEC-0012
**Owner:** Engineering Authority
**Issued:** 2026-07-21
**Work package:** GOV-P0-02 (Proposed; not accepted)

This directory preserves candidate document manifests without replacing the canonical generated `docs/DOCUMENT-MANIFEST.json`. A snapshot excludes the canonical manifest and its own output path. It is technical evidence only and does not approve documents or resolve DEC-0012.

Reason: literal append-only instructions conflict with deterministic replacement of the canonical generated manifest. Benefit of the old phase: the canonical manifest remains unchanged and its Git history is preserved. Expected outcome: DEC-0012 selects an approved long-term convention.

## QUAL-INTEG-001 append-only extension

`MANIFEST-INDEX.jsonl` appends ordered, prefix-chained records. Immutable records bind raw working-tree bytes to an exact source commit, tree, path and blob. Current records bind separately named integration and aggregate manifests. The aggregate excludes itself and the index, preventing circular digests. Package validators continue to verify the underlying package contracts; the index is an additional integrity control, not a substitute for them.

## Append-only hardening â€” QUAL-INTEG-001 rework 001

Manifest generation is create-once. Write mode requires explicit `--aggregate`, a normalized versioned `*-MANIFEST.json` name directly under `docs/manifests/`, and a target that has never existed or appeared in the index. The canonical manifest, every existing snapshot and every indexed path are write-protected. Check modes are read-only.

The index validator reads each Git blob as binary from the genesis commit forward. Every successor, including a pending worktree append, must preserve the complete prior blob as an exact prefix and append one or more valid LF-only JSONL objects. Truncation, mutation, reordering, CRLF conversion and malformed appended records fail closed. The legacy `current_aggregate` mode name is retained for schema compatibility, but an indexed aggregate is an immutable raw-byte snapshot rather than a mutable view of the latest tree.
