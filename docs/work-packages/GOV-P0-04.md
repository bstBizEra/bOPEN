# GOV-P0-04 — Authority Identity Surfaces, Matrix v0.2 Proposal and Operator Decision Packet

**Version:** 0.1
**Status:** Proposed; not accepted
**Owner:** Engineering Authority
**Authorization source:** User direction ("help finish the G0 phase; assist Codex"); BOPEN-BOOT-001 documentation and contract drafting authority only
**Accepted by/at:** Pending attributable Human Engineering Authority disposition
**Lifecycle:** PG-G0 proposal; no gate passage
**Dependencies:** GOV-P0-01 at `c893062`; GOV-P0-02 at `82ed6b3`; GOV-P0-03 at `a29ec1d`; DEC-0012; DEC-0013 (this package)
**Governing artifacts:** BOPEN-BOOT-001; BOPEN-GOV-001 Draft; PG-G0-AUTH-001
**Maker:** Claude (BST-SA Motor worker agent; claude-sonnet-5)
**Independent checker:** Pending (must not be the maker; Codex checker eligible)
**Branch/worktree:** `claude/GOV-P0-04-authority-identity-surfaces` / `C:\laragon\www\bopen\.claude\worktrees\elegant-jackson-05259b`
**Base SHA:** `a29ec1d8ab28d38621dc4db176b7b2abf2ea44cb`
**Base tree:** `ff3cb910385f04ccc3b0e077cf4329b79f7fe3f6`
**Expiry:** 2026-08-21T00:00:00+07:00

## Objective

Prepare the draft surfaces that the PG-G0 authority docket records as absent — a hash-bindable human authority identity register, an authority matrix v0.2 proposal covering the three missing actions and the ACCEPT_WORK_ITEM reconciliation — plus an independent verification receipt for the GOV-P0-03 candidate and a single consolidated operator decision packet.

## In scope

- `contracts/governance/authority-identity-register.schema.json` (draft);
- `docs/00-governance/AUTHORITY-IDENTITY-REGISTER-DRAFT.json` (draft; one pending solo-operator record with independence disclosure; moved to the validator-bound registers path only at approval);
- `docs/00-governance/AUTHORITY-MATRIX-0.2.0-PROPOSAL.json` (proposal file; bound v0.1 register untouched);
- `docs/decisions/DEC-0013.md` (proposed);
- `docs/evidence/EVD-GOV-004-gov-p0-03-independent-verification.md` (independent exact-SHA receipt for `a29ec1d`);
- `docs/00-governance/PG-G0-OPERATOR-DECISION-PACKET.md` (advisory).

## Out of scope

Approving any register, matrix, identity, decision, work package or gate; modifying the bound AUTHORITY-MATRIX.json or the PG-G0 docket; docket v0.2 rebinding (Codex follow-up); production code, migrations, runtime or infrastructure; research gate changes.

## Allowed paths

`docs/00-governance/`, `docs/decisions/DEC-0013.md`, `docs/evidence/EVD-GOV-004*`, `docs/work-packages/GOV-P0-04.md`, `contracts/governance/authority-identity-register.schema.json`.

## Prohibited paths

`apps/`, `services/`, `packages/`, `infrastructure/`, `research/upstream/`, migrations, runtime configuration, secrets, existing bound registers and dockets.

## Acceptance criteria

- All new artifacts are additive; no bound artifact SHA changes;
- register and schema are structurally valid and fail closed (draft status, pending record, null approvals);
- matrix proposal preserves all seven v0.1 entries and only adds the three missing actions plus the prose-aligned ACCEPT_WORK_ITEM concurrence;
- existing repository, contract, program-control, docket, clean-room, secret and supply-chain checks remain green at the candidate SHA;
- an independent checker (not Claude) accepts the exact final SHA.

## Risks and rollback

Risk: the pending identity record or matrix proposal is mistaken for an effective approval. Control: draft/pending statuses, null approval fields and fail-closed validators; the docket continues to report `NOT_READY`. Rollback: delete the isolated branch; no bound state is touched.

## Completion record

Maker drafting complete. Independent checker verdict and Human Engineering Authority acceptance pending. This proposed record does not accept itself.

## Append-only correction record — 2026-07-22

The independent checker (BST-Codex-Motor) reviewed candidate `203ed05162dccb2729d4c39e25050817384c3b4b` and returned `REJECT` with findings RF-001..004 (EVD-GOV-005, checker review branch `codex/GOV-P0-04-review-203ed05`). The maker accepts all four findings. Scope extension for the corrective candidate (reason: RF-003 requires semantic negative tests and a dedicated validator; benefit of the old phase: it kept the first candidate documentation-only; expected outcome: fail-closed register semantics proven by tests):

- **Allowed paths extended:** `tools/validate_authority_identity_register.py`, `tests/governance/test_authority_identity_register.py`, `package.json` (validate chain only), `docs/manifests/GOV-P0-02-DOCUMENT-MANIFEST.json` (deterministic regeneration only).
- Corrections per DEC-0013 append-only correction note: docket-compatible identity semantics, status-coupled approval provenance, DIRECT-only authority mode, refreshed manifest, `pnpm validate` green.
- The `REJECT` receipt for `203ed05` stands; this corrective candidate carries a new SHA and requires a new independent exact-SHA review.
