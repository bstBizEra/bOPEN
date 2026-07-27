---
name: bopen-governance-check
description: Validate bOPEN authority, phase gates, scope, required artifacts, maker-checker separation and stop conditions before repository mutation.
---

# bOPEN Governance Check

1. Identify project, phase and work item.
2. Verify authorization, owner, expiry and allowed paths.
3. Read linked requirements, ADRs, security and tenancy controls.
4. Confirm worktree, maker, checker, tests, evidence destination and rollback.
5. Report missing controls as blockers.
6. Do not mutate files until all mandatory checks pass.

## Authority scope

Verify the authority actually covers every component you intend to change - register, tool or
validator source, signing record, derived artifacts, and any ref move. One action rarely covers
all of them. If a component is uncovered, stop: an interpretation cannot enlarge its own authority.

Prefer scoping an existing held action to proposing a new one. Adding an authority-matrix action
is normally blocked, because the terminal authority docket rebuilds the expected registers from a
signed substrate and byte-compares them.

## Expiry is a live control

Check `valid_from`, `expires_at` and `revoked_at` on every identity you rely on, and the validity
window of the docket and any trust root. Report the days remaining, not just a pass. An authority
that expires mid-track is a scheduling blocker, not a footnote.

## Separation

The maker never self-certifies. Confirm the checker authored none of the bytes under review, and
that the human - not an agent - authors every attributable decision. An agent may prepare, verify
and encode; it may not approve, sign, or move an authoritative ref.

## Narrative consistency

Byte checks do not detect a governance-narrative gap. If an earlier signed record states
prerequisites that the current path does not satisfy, and no signed record reconciles them,
escalate to the human before proceeding.
