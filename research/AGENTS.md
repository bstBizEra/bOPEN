# AGENTS.md — Clean-room research

This file supplements the root [`AGENTS.md`](../AGENTS.md). Root rules remain mandatory.

## Directory purpose

Upstream clones live only under `research/upstream/` and are excluded from commits. Findings must separate observation, inference and decision. Every material observation needs repository, commit, path and locator. Research output cannot become production code directly.

### Physical workspace clarification

Under `DEC-0009`, `research/upstream/` is the logical governance boundary and repository marker, not a physical clone destination. Windows clones and raw logs must live under `C:\laragon\www\bopen-research\<operator-run>`. Non-Windows execution requires an explicitly approved absolute root supplied as `BOPEN_RESEARCH_APPROVED_ROOT`; absence disables the shell workflow. The bOPEN worktree must keep `research/upstream/` source-free so `tools/check_clean_room.py` can fail closed. Only sanitized findings, checksums, decisions and evidence receipts may be committed.

## Required completion evidence

- applicable artifact, requirement, ADR and work-package IDs;
- tests or validation appropriate to the directory;
- documentation/contract updates;
- security and clean-room declaration;
- residual risks and blocked decisions.
