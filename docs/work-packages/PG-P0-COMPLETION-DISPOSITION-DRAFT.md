# PG-P0 Completion and Integration Decision — Draft

**Artifact ID:** PG-P0-COMPLETION-001-DRAFT
**Version:** 0.1-draft
**Status:** DRAFT; NOT SIGNED; NOT EFFECTIVE
**Prepared by:** BST-Codex-Motor
**Prepared at:** 2026-07-25 (Asia/Vientiane)
**Accountable authority:** Architecture Authority
**Governed substrate:** `29949f460345a55b8f8079cad802d6ca85cbe46e`

## Purpose

Prepare, without exercising, the signed decision required to transition `PG-P0` from
`ACTIVE` to `COMPLETE` after its sole bound work item has been accepted. This draft
also surfaces the separate integration decision for the accepted skeleton; it does not
merge or promote that candidate.

## Current governed state

- Schedule register: `PG-REG-SCHEDULE-001`, encoded at substrate `29949f46`.
- `PG-P0`: `ACTIVE`; owner authority `Architecture Authority`.
- Bound work item: `SKEL-P0-01`.
- Human acceptance: `HUMAN-OPERATOR-001` accepted exact SHA
  `f1eea272442a0587ab5843ba28c6ce47b91e1615`; acceptance encoding successor
  `73912e483cc9f4b5bc107f84564b955c9a335ca4`.
- `PG-P1`: `NOT_READY`; no production implementation work items are accepted.

## Required human decisions

### Decision A — integration disposition

Choose one and record it before or alongside phase completion:

- **INTEGRATE:** authorize a separately reviewed merge/integration of the accepted
  `SKEL-P0-01` candidate into the governed lineage, subject to its own exact target,
  review, and merge controls; or
- **DEFER:** complete the phase disposition while explicitly keeping the accepted
  candidate branch-only and scheduling a later integration decision; or
- **REJECT/REMEDIATE:** reject the integration path and return the work item for a
  new bounded disposition.

This draft does not select an option.

### Decision B — phase completion

The Architecture Authority may sign a new Signing Pass transitioning:

`PG-P0: ACTIVE → COMPLETE`

The signature MUST reference the exact accepted work item, the independent technical
receipt, this integration disposition, and the final schedule-register successor.

## Preconditions to verify before signature

- `SKEL-P0-01` acceptance is attributable to `HUMAN-OPERATOR-001` and bound to exact
  SHA `f1eea272442a0587ab5843ba28c6ce47b91e1615`.
- Independent technical receipt is `ACCEPT_EXACT_SHA` for that exact SHA.
- The `pnpm-lock.yaml` scope amendment is limited to the two authorized workspace
  importer entries.
- No signed PG-G0 bytes or `docs/00-governance/**` bytes are changed.
- The proposed schedule successor changes only the intended `PG-P0` status and
  references; `PG-P1` remains `NOT_READY`.
- Integration, merge, release, deployment, runtime activation, and production
  implementation remain separately gated unless explicitly authorized by their own
  attributable decisions.

## Proposed signing record (blank)

**Decision ID:** `PG-P0-COMPLETE-001`
**Decision:** `PENDING HUMAN AUTHORITY`
**Authority actor:** `____________________________`
**Authority role:** `Architecture Authority`
**Signed at:** `____________________________`
**Integration disposition:** `INTEGRATE / DEFER / REJECT-REMEDIATE` (circle one)
**Exact accepted work-item SHA:** `f1eea272442a0587ab5843ba28c6ce47b91e1615`
**Schedule successor SHA:** `____________________________`
**Signature/attestation:** `____________________________________________________________`

## Explicit exclusions

This draft does not complete PG-P0, alter the schedule register, authorize PG-P1,
approve normative artifacts, pass BOPEN-RES-001 G3–G7, accept production kernel work
packages, merge to `main`, release, deploy, or activate runtime behavior.

## Disposition

**RETURN FOR HUMAN DECISION.** The worker preparation is complete; no authority effect
is asserted by this draft.

## Revision 0.2 — two-stage commitment and state separation (2026-07-25)

### Circularity correction

The authority mandate MUST NOT sign or require the hash of a schedule successor that
will contain the mandate or its encoding receipt. That would create a circular
commitment. The signed mandate instead binds:

- the accepted candidate SHA `f1eea272442a0587ab5843ba28c6ce47b91e1615`;
- the independent receipt digest and checker disposition;
- the current schedule-register digest;
- a canonical, immutable successor-transform specification digest;
- the authorized field changes and invariants; and
- the separate integration disposition.

After signature, the maker deterministically applies the transform. A separate
append-only encoding receipt then records the actual predecessor and successor
schedule digests, the mandate digest, transform-spec digest, validator identity and
validation evidence. The receipt verifies that the produced successor matches the
signed mandate; it does not retroactively participate in the mandate signature.

### Stage 1 — signed completion mandate

```yaml
decision_id: PG-P0-COMPLETE-001
program: BOPEN
phase: PG-P0
accepted_candidate_sha: f1eea272442a0587ab5843ba28c6ce47b91e1615
independent_receipt_sha256: <receipt-digest>
current_schedule_sha256: <predecessor-digest>
successor_transform_spec_sha256: <transform-spec-digest>
authorized_changes:
  - PG-P0.status: ACTIVE -> COMPLETE
  - PG-P0.actual_end: <signed-or-rule-derived-time>
  - PG-P0.completion_decision_ref: PG-P0-COMPLETE-001
required_invariants:
  PG-P1.status: NOT_READY
governance_bytes_unchanged: true
separate_authorizations:
  merge: required
  release: required
  deployment: required
  runtime_activation: required
  production_use: required
integration_disposition: INTEGRATE
```

The Architecture Authority signs this canonical payload only after identity,
role, time-window, revocation, maker/checker separation and all pre-signing
controls pass.

### Stage 2 — deterministic encoding receipt

```yaml
record_id: SIGNING-PASS-6
decision_digest: <signed-decision-digest>
predecessor_schedule_sha256: <old-digest>
successor_schedule_sha256: <new-digest>
transform_spec_sha256: <transform-digest>
validation_result: PASS
validator_version_or_digest: <immutable-validator-binding>
validator_evidence_sha256: <evidence-digest>
encoded_by: <maker-identity>
encoded_at: <trusted-timestamp>
```

The receipt MUST confirm exact predecessor ancestry, authorized field-only change,
`PG-P1: NOT_READY`, protected-governance invariants, canonicalization, and clean
validation. It MUST be appended only after the successor exists.

### Separate state machines

Completion and integration are distinct:

```text
PG-P0 completion: DRAFT -> SIGNED -> ENCODED -> VALIDATED -> EFFECTIVE
candidate integration: ACCEPTED -> INTEGRATION_AUTHORIZED -> MERGE_REVIEWED -> MERGED
```

`INTEGRATE` in the completion mandate authorizes entry into the separate integration
workflow; it does not execute or approve a merge. `DEFER` may still permit PG-P0
completion if the signed definition of done does not require merge. If merge is a
completion precondition, that requirement MUST be stated explicitly in the mandate.

### Required pre-signing controls

The machine-generated report MUST verify candidate identity and ancestry, valid
independent receipt, lockfile scope, protected governance bytes, transform boundary,
P1 invariant, unknown-field/duplicate-key rejection, UTF-8/LF/no-BOM canonicalization,
validator binding, cryptographic signature validity, authority role at signing time,
trusted time, revocation status, segregation of duties, and downstream exclusions.

### Corrected controlling wording

> Closing PG-P0 requires an attributable authority decision, deterministic encoding
> into the signing record and schedule successor, cryptographic and semantic
> validation, and governed incorporation. The completion decision may authorize
> integration, but it does not itself execute or approve merge, release, deployment,
> runtime activation, or production use.

Until both stages are complete and incorporated, the effective state remains:

```text
PG-P0: ACTIVE
Completion package: DRAFT or SIGNED_PENDING_ENCODING
PG-P1: NOT_READY
Production implementation: NOT_AUTHORIZED
```

### Segregation-of-duties policy fields

```yaml
segregation_of_duties:
  maker_must_differ_from_approver: true
  checker_must_differ_from_maker: true
  checker_must_differ_from_approver: <governing-policy-value>
  signer_may_not_verify_own_authority: true
```

This revision supersedes the circular successor-hash wording in the original draft;
it does not itself sign, encode, complete PG-P0, authorize integration, or open PG-P1.
