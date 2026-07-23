# EVD-GOV-010 — Independent Exact-SHA Review of the PG-G0 Authority Docket v0.3 Signed-State Candidate

**Version:** 0.1
**Status:** Draft technical evidence
**Work package:** GOV-P0-04 (accepted via PG-G0-PREP-011 as encoded in this candidate)
**Generated:** 2026-07-23
**Maker under review:** BST-Codex-Motor (v0.3 signed-state encoder; EVD-GOV-009)
**Independent checker:** Claude (BST-SA Motor worker agent; claude-fable-5 session)
**Checker independence:** Different agent vendor, runtime and session; the checker authored none of the reviewed commit. The checker recorded the operator's signing record in the parent commit, which is disclosed; the reviewed delta `60c4831..65da2fb` is entirely Codex-authored.
**Candidate commit SHA:** `65da2fb3deec1684d07f184f8c06a773ac36b504`
**Candidate tree SHA:** `d69b44d0b988c2817e703be4ac9eba35b9194d1e`
**Parent (operator signing record):** `60c4831f4fcdfabb876d62f4eb98949b4a1a5a66`
**Branch:** `codex/GOV-P0-04-docket-v03`
**Worktree state:** clean at the exact candidate SHA throughout the review
**Verdict:** `ACCEPT_EXACT_SHA` (technical evidence only)

## Commands and results (at the exact candidate SHA)

- `npm run validate` — exit 0: all validator, report, manifest (276 records), clean-room, secret and supply-chain checks PASS.
- `python -m unittest discover -s tests -p 'test_*.py'` — 182/182 passed.
- Docket validator — zero validation errors; readiness `NOT_READY` with only B8/B9, this pending review, and standing authorization/disclosure blockers.
- `git diff --check` — clean.

## Signature-fidelity verification (core review question)

Every one of the thirteen prepared dispositions was compared against the operator's Batch 2 signing record (`SIGNING-PASS-2.md#append-only-batch-2-signing-record--2026-07-23`, commit `60c4831`):

1. **Outcomes faithful:** each surface carries decision verb `APPROVE` against its unchanged v0.2 `requested_state` (`APPROVED`/`ACCEPTED`/`ACTIVE`), so the encoded outcome equals the signed outcome for all thirteen; no requested state was altered.
2. **Actor blocks:** all thirteen bind `HUMAN-OPERATOR-001` through the approved identity register with `decided_at: 2026-07-23T00:45:00+07:00` — the exact signed timestamp — and the signing-record `decision_ref`.
3. **Artifact effects consistent:** authority matrix `0.2.0 approved`; six registers `0.1.0 approved` (empty AGENT/MODULE/SKILL entry sets preserved; schedule entries remain `NOT_READY`); BOPEN-GOV-001 and DEC-0013 carry append-only approval/acceptance records citing the signing ref; GOV-P0-01/04 acceptance and DEC-0007/BOOT-B7 records present; all five root ledgers carry exactly one atomic activation event with identical signed fields and untouched genesis prefixes.
4. **Boundaries preserved:** the five `PG-G0-DEC-001..005` B8 decisions remain `PENDING`; `program_goal_approved` and `evidence_accepted` remain false; `ready_for_pg_g0_gate_decision` false; every `non_authority_flags` entry false; merge/release/runtime/production unauthorized.
5. **Binding inventory:** all 41 records byte-exact against the parent commit `60c4831` — zero SHA-256 mismatches.

## Decision boundary

This receipt verifies the mechanical encoding of an already-given human signature and the technical health of the exact candidate SHA. It does not dispose any B8 decision, pass PG-G0, or authorize merge, release, runtime or production implementation. B8 and B9 remain exclusively with the operator.

## Self-certification

```yaml
self_certification:
  agent_id: Claude BST-SA Motor (claude-fable-5)
  peer_agent_id: BST-Codex-Motor
  certification_scope: advisory_only
  execution_authority: false
  approval_authority: false
  candidate_verdict: ACCEPT_EXACT_SHA
  ready_for_operator_review: true
```
