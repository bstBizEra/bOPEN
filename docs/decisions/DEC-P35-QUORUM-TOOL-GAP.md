# DEC-P35-QUORUM-TOOL-GAP — the ratified two-agent profile is not implemented, so 26 candidates report a quorum shortfall

**Decision ID:** `DEC-P35-QUORUM-TOOL-GAP`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16 (two approved artifacts conflict)**
**Issued:** 2026-08-07
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §6.1, §6.3, §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](DEC-P35-TWO-AGENT-QUORUM.md); `AGENTS.md` §20.3

---

## 1. The conflict

Two approved artifacts disagree about what quorum this repository requires.

- **`BOPEN-GOV-EBIV-001` §6.1** requires **two** independent verifiers to confirm.
- **`BOPEN-GOV-EBIV-001` §6.5**, added 2026-08-02 by `DEC-P35-TWO-AGENT-QUORUM` and **ratified**,
  provides that while a two-agent team is in effect, confirmation requires **one** admissible
  `CONFIRMED` ballot plus an explicit Completion Authority disposition, labelled
  `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.

`tools/check_ballot_attribution.py` implements **only §6.1**. Its sole quorum logic is a hardcoded
message — *"QUORUM SHORTFALL — N candidate(s) below two verifiers"* — with no §6.5 path. As of
2026-08-07 it reports **26 candidates** below two verifiers, including `1cde994` (Location), whose
31 ballots were freshly re-cast by Codex under `DEC-P4-LOCATION-BALLOT-ATTRIBUTION`.

This is not a defect introduced by that repair. It predates it and cannot be closed by re-casting.

## 2. Why it matters more than one candidate

Three distinct costs:

1. **The ratified accommodation is unreachable in practice.** §6.5 exists precisely because a
   two-agent team can never satisfy §6.1 — *"one is always the Maker"*. If the tool only ever
   reports §6.1, the accommodation the operator ratified has no expression in any automated check.
2. **Alarm fatigue on a live control.** A 26-line shortfall block printed on every run trains
   readers to scroll past it. A control that still fires but is no longer read is worse than one
   that was removed, because the repository retains the appearance of enforcement. This repository
   has already recorded the sibling failure mode — *"assuming a check passed because it exited
   quietly"* (`BOPEN-ENG-LOOP-001` §5).
3. **`CONFIRMED_UNDER_TWO_AGENT_PROFILE` is unverifiable.** §6.5.2 requires that label, and §6.5.1
   requires a recorded Completion Authority disposition. Neither is machine-checkable today, so the
   distinction §6.5.2 insists on — *"different verdicts and must not be conflated"* — rests entirely
   on prose discipline.

## 3. What §6.5 actually requires, and why it is not trivially automatable

§6.5 confirmation has three parts. Only the first is currently checkable:

| Requirement | Machine-checkable today |
| :--- | :--- |
| One admissible `CONFIRMED` ballot from an independent verifier | **Yes** — `ballots.jsonl` + admissibility R1–R5 |
| An explicit Completion Authority disposition on the disclosed-risk evidence | **No** — dispositions are recorded in prose across `DEC` files |
| The verdict labelled `CONFIRMED_UNDER_TWO_AGENT_PROFILE` | **No** — no field carries it |

The gap is therefore not merely "the tool is behind the spec". §6.5 depends on an operator act that
has no machine-readable home. That is the real missing piece.

## 4. Options

| # | Option | Assessment |
| :--- | :--- | :--- |
| 1 | **Add a machine-readable disposition record** (e.g. `dispositions.jsonl`: candidate, artifact, disposing authority, date, label) and teach the checker to report `CONFIRMED_UNDER_TWO_AGENT_PROFILE` where one ballot plus a disposition exist | **Recommended.** It closes the gap at its root — the operator act becomes evidence rather than prose — and makes §6.5.2's labelling enforceable instead of aspirational. It is additive and weakens nothing: a candidate with neither two verifiers nor a disposition still reports a shortfall |
| 2 | **Record dispositions for the 26 candidates in prose only**, and annotate the tool's output as expected | Cheaper, but leaves the label unverifiable and the 26-line block still printing. Alarm fatigue is unaddressed |
| 3 | **Teach the checker that one verifier is sufficient** whenever the two-agent profile is in effect | **Recommended against.** This drops the disposition requirement §6.5.1 makes load-bearing, converting an operator-gated accommodation into an automatic pass — a control-weakening change |
| 4 | **Leave as-is** and treat the shortfall as known noise | Not recommended, for the reason in §2.2 |

## 5. What this decision request does not do

It does not confirm any candidate, dispose any work package, alter any ballot or verdict, or modify
`check_ballot_attribution.py`. It records a conflict between two approved artifacts and asks for a
disposition, per §16.

Note that a decision here does **not** by itself confirm Location. Under §6.5 that still requires an
explicit Completion Authority disposition on `1cde994`, which is the operator's act and is not
implied by fixing the tooling.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.

## 6. Decision support — the concrete shape of Option 1, if it is chosen

Prepared so the decision is cheap to make. **This specifies nothing and authorizes nothing**; it
describes what Option 1 would look like if the operator selects it. Presenting it is not a claim
that it has been selected.

### 6.1 The record

`docs/evidence/phase-3.5/dispositions.jsonl` — one JSON object per line, append-only, alongside
`ballots.jsonl` and read the same way:

```json
{
  "disposition_id": "dsp_0001",
  "candidate_commit_oid": "1cde9942096b29795ddd937a2130e170c970b2e7",
  "artifact": "BOPEN-LOC-001",
  "profile": "two_agent",
  "verdict": "CONFIRMED_UNDER_TWO_AGENT_PROFILE",
  "disposing_authority": "BizEra <ounkhamvilay@gmail.com>",
  "authority_role": "Completion Authority",
  "disclosed_risk_ack": "docs/evidence/phase-3.5/...",
  "issued_at": "2026-08-08T00:00:00+07:00",
  "recorded_by": "claude"
}
```

### 6.2 What the checker would then do

For a candidate with **one** admissible `CONFIRMED` ballot:

- **with** a matching disposition → report `CONFIRMED_UNDER_TWO_AGENT_PROFILE`, satisfying §6.5;
- **without** one → continue reporting the shortfall exactly as today.

Nothing is relaxed. §3 maker exclusion, §6.2's refutation asymmetry and §6.3's escalation are
untouched, and a candidate with zero admissible ballots is unaffected.

### 6.3 The property that makes this worth doing

The disposition becomes **evidence rather than prose**, so §6.5.2's requirement that the two verdicts
"must not be conflated" becomes machine-enforced instead of a naming convention nobody can check.

### 6.4 The integrity condition

The disposition line must be introduced by a commit authored by the **operator's** identity, checked
the same way `check_ballot_attribution.py` binds a ballot to its author. Otherwise an agent could
write a disposition granting confirmation to its own work — reintroducing, on the authority side,
precisely the defect `DEC-P4-LOCATION-BALLOT-ATTRIBUTION` was raised to repair on the verifier side.

This is the one place where §21.2.1 — *no agent commits under the operator's identity* — becomes
load-bearing rather than hygienic. An agent may **draft** a disposition line; only the operator may
commit it.

## 7. Amendment 2026-08-08 — Option 1 selected; Location disposition deferred; build plan

> **Change note (extend-only).** Recorded **before** any build, per `AGENTS.md` §25.1 step 0.

### 7.1 What the shortfall actually covers

Measured 2026-08-07 across `docs/evidence/phase-3.5/ballots.jsonl`: **27 candidates in total, 26 of
them below two verifiers** (23 verified by `codex`, 3 by `gemini`). They are not duplicate or stale
commits. They are distinct work items spanning almost everything this repository has produced —
`AUTH-D1`, `AUTH-D3`, gateway decoding, the placement seam, trial→paid migration, Party, the Workflow
state engine, UOM, Party ContactPoint and Location.

This reframes the finding recorded in §2. §6.5 is not an accommodation for an edge case; it is **the
normal operating mode of this repository**, and no automated check has ever been able to express it.
A tool that can only speak §6.1 can never report that anything here is verified.

### 7.2 Decision

| Field | Value |
| :--- | :--- |
| **Decision** | **Option 1 selected** — add a machine-readable disposition record and teach the checker to report `CONFIRMED_UNDER_TWO_AGENT_PROFILE`, per the shape in §6 |
| **Rejected** | Option 3 (teach the checker one verifier suffices) — drops the disposition requirement §6.5.1 makes load-bearing and converts an operator-gated accommodation into an automatic pass |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture & Engineering Authority |
| **Decision timestamp** | 2026-08-08 |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision. `execution_authority: false`, `approval_authority: false` |

### 7.3 Location disposition is deferred, deliberately

The operator **has not** disposed `1cde994`, and that is the recommended sequence rather than an
omission. Disposing it in prose now would mean recording it twice once `dispositions.jsonl` exists,
and 26 candidates are waiting — a single pass in one consistent format is better than 26 one-off
prose entries. Nothing is blocked meanwhile: Location remains un-confirmed, and the in-flight
MILE-4.2 work does not depend on its confirmation.

### 7.4 This build is not a small change, and is not authorized to proceed by this amendment

`check_ballot_attribution.py` is the control that guards the entire evidence base. Changing it earns
the full governed cycle, not a patch:

1. **Baseline first** (§23) — tag before the change lands, never after.
2. **Refusal Matrix** — the change must be unable to confirm a candidate that has no disposition,
   no admissible ballot, a maker-cast ballot, a `REFUTED` ballot, or a disposition not committed
   under the operator's identity (§6.4).
3. **Tests-first**, negative tests before implementation, then mutate the mechanism and confirm the
   tests fail.
4. **Independent verification by Codex**, which authored none of it.
5. **Operator disposition** — and note the recursion: the first artifact this new mechanism would
   confirm is the mechanism itself, which must therefore be disposed under the *existing* rules.

A proposed work-package ID and the entry-gate record are still required before any code is written
(§5 step 2). **This amendment authorizes the direction, not the build.**
