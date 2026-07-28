# BOPEN-EVIDENCE-TO-SKILL-001 - Evidence-to-Skill Improvement Loop

**Version:** 0.1
**Status:** PROPOSED_NON_EFFECTIVE
**Owner:** Skill Governance
**Updated:** 2026-07-28

## Objective

Convert verified delivery evidence into reusable agent behavior without letting
agents promote unverified conclusions or activate controls through consensus.

## Eligible sources

- accepted independent-review findings;
- reproducible failures and negative tests;
- authorized incident or post-phase records;
- recurring remediation patterns supported by multiple receipts;
- measured delivery friction with a control-safe improvement;
- successful practices independently reproduced on more than one task.

Chat summaries, model confidence, majority opinion and undocumented experience
are investigation inputs, not promotion evidence.

## Proposed lifecycle

```text
OBSERVED
-> VERIFIED
-> PROPOSED
-> FORWARD_TESTED
-> TECHNICALLY_ACCEPTED
-> PILOT_AUTHORIZED
-> ACTIVE
-> MEASURE
-> RETAIN_OR_ROLL_BACK
```

Exceptional states are `REJECTED`, `HOLD_INSUFFICIENT_EVIDENCE`,
`HOLD_CONFLICT`, `SUPERSEDED`, `ROLLED_BACK` and `RETIRED`.

## Procedure

1. **Observe:** link a learning record to exact evidence and separate symptom,
   cause, contributing factors and impact.
2. **Verify:** obtain independent reproduction. Otherwise retain `HYPOTHESIS`.
3. **Generalize:** extract the smallest reusable rule; exclude temporary hashes,
   secrets, personal identities and one-reviewer wording.
4. **Propose:** identify target skill/version, triggers, evidence, instruction
   delta, benefit, risk, tests, rollback and review date.
5. **Review:** keep maker and decisive checker separate. Security or authority
   changes require control review.
6. **Forward test:** use fresh agents and a frozen corpus covering positive,
   negative, boundary, regression and conflict cases.
7. **Approve:** distinguish technical acceptance from activation.
8. **Measure:** compare acceptance, false findings, rework, execution time,
   control violations and context cost.
9. **Retain or roll back:** preserve candidate, evidence, decision and rollback
   record.

Codex and Claude evaluators should submit independently and must not see each
other's disposition before submission.

## Initial candidate lessons

| Lesson | Proposed behavior |
| --- | --- |
| Governed-base integration | Do not leave mutually dependent artifacts on disconnected branches |
| In-tree references | Fail closed when a governing artifact is absent from the candidate tree |
| Exact-byte integration | Compare imported blobs or patches with accepted digests |
| Technical-review discipline | Separate maker result, checker disposition and human authority |
| Evidence normalization | Require exact SHAs, commands, exits, provenance and dissent |
| Phase-state guard | Never report completion before the effective gate decision |
| Skill-promotion gate | Require verified sources, forward tests, activation and rollback |

## Activation

No skill changes under this proposal become active until the repository's
effective skill lifecycle, registry and human activation controls accept the
exact candidate.
