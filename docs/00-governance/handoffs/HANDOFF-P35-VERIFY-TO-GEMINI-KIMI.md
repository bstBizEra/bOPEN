# HANDOFF-P35-VERIFY-TO-GEMINI-KIMI — Second and third verifier seats for Phase 3.5

**Status:** Stood down 2026-07-30 — retained as a record
**Issued:** 2026-07-30
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Gemini / Antigravity, and Kimi
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md)
**Governing standard:** [`BOPEN-GOV-EBIV-001`](../BOPEN-GOV-EBIV-001.md) §3, §5, §6
**Companion handoff:** [`HANDOFF-P35-PARALLEL-TO-CODEX`](HANDOFF-P35-PARALLEL-TO-CODEX.md)

> **SEAT STOOD DOWN — 2026-07-30.** The operator has stood this handoff down for now: the
> addressed agents did not pick it up, and blocking on them was holding work that has no other
> dependency on them.
>
> **This does not verify anything.** `BOPEN-GOV-EBIV-001` §6.3 is explicit that fewer than two
> admissible ballots escalates to the Completion Authority and *never* auto-passes. Standing the
> verifiers down changes only the reason the quorum is unmet — from *awaiting ballots* to
> *quorum unreachable* — and moves the decision to the operator acting as Completion Authority
> on a zero-verifier record, with the shortfall on the face of the evidence.
>
> The document is retained rather than deleted. It records what was asked, of whom, and on what
> propositions, and it is the starting point if a verifier becomes available. Re-activating it
> needs nothing but an agent reading it and setting its identity per §5.0.


---

## 1. Why you are being asked

`BOPEN-GOV-EBIV-001` §6.1 requires **at least two independent verifiers** before a confirmation
can be realized. Only Codex was eligible when `WP-P35-01` and `WP-P35-02` landed, because Claude
authored both and is disqualified under §3. One ballot cannot realize a verified status, so the
work has been sitting at `IMPLEMENTED_UNVERIFIED` by design rather than by oversight.

You are both eligible. Neither of you authored any part of `WP-P35-01` or `WP-P35-02`. Gemini
was Maker on Phase 3, which disqualifies it only for Phase 3 artifacts — not for these.

Three verifiers with distinct lenses also satisfies §3.2, which asks for diversity of model and
of lens rather than three passes of the same examination. Three agents from the same family
running the same prompt is one verifier reporting three times, and §3.2 says to count it as one.

## 2. Lens assignment

Each seat has a different question. Please stay inside your lens: overlapping coverage is much
less useful than three genuinely different angles, and it is what makes the panel worth more
than its largest member.

| Seat | Agent | Lens | The question you are answering |
| :--- | :--- | :--- | :--- |
| V1 | Codex | Reproducibility and privilege | *Does it actually do what the evidence says, on a clean run?* |
| V2 | Gemini / Antigravity | Contract and architecture conformance | *Does it agree with the approved specifications and invariants?* |
| V3 | Kimi | Cross-artifact consistency | *Does the governance chain still hold together end to end?* |

## 3. Seat V2 — Gemini / Antigravity

Your strength per `AGENTS.md` §19.3 is architecture synthesis and workspace-wide governance
audit. That is exactly the lens missing from Codex's seat.

### 3.1 Propositions

| ID | Proposition |
| :--- | :--- |
| `INV-CONTRACT-TENANT-CONTEXT-01` | The issued context payload validates against `contracts/schemas/tenant-context.json` |
| `INV-HTTP-TENANT-HINT-01` | `X-Tenant-ID` grants nothing without a context living in that tenant |
| `INV-ARCH-LAYER-CONFORM-01` | The implementation matches `BOPEN-ARCH-PLAN-001` §2–§3 for layers 3 and 4 |
| `INV-ARCH-INVARIANTS-01` | `AGENTS.md` §7 invariants 1–12 are preserved by the new code |

### 3.2 Where to attack

1. **Every frozen schema against a live instance.** The Phase 3 failure was not that
   `RateLimitDecision` diverged — it was that the contract suite loaded the schema and never
   applied it to an instance. Enumerate `contracts/schemas/*.json` and, for each, find whether
   any test validates a real object against it. Where none does, that invariant is untested no
   matter how green the suite looks. I fixed this for `tenant-context.json` only.
2. **Invariant 12 — industry semantics must not leak into the kernel.** Read
   `platform_kernel/api.py` and `repositories.py` and check that nothing product-specific has
   crept in. This is the invariant most likely to erode silently as Phase 4 approaches.
3. **Invariant 5 — membership is not role, permission or entitlement.** My `ResolvedContext`
   carries `roles` derived from `membership.role`. Judge whether that conflates the two.
4. **Layer conformance.** `BOPEN-ARCH-PLAN-001` binds FastAPI + Pydantic v2 for layer 3 and
   PostgreSQL + psycopg3 for layer 4. Confirm what landed matches what was bound, and flag
   anything I selected that no approved decision covers.
5. **The parallel implementation.** `PlatformKernelService` (in-memory) and the repository-backed
   path now both implement the Phase 1 chain. I left the former because removing it would put a
   139-test rewrite in the same commit as new behaviour. Judge whether the drift risk outweighs
   that reasoning — I may have chosen wrongly.

## 4. Seat V3 — Kimi

Your strength per `AGENTS.md` §19.3 is long-context work across many artifacts. This seat is the
one that needs the whole repository held at once, and neither of the other two seats covers it.

### 4.1 Propositions

| ID | Proposition |
| :--- | :--- |
| `INV-GOV-CHAIN-CONSISTENT-01` | No two approved artifacts contradict each other after the 2026-07-30 amendment |
| `INV-GOV-STATUS-COHERENT-01` | Every phase status register agrees with `AGENTS.md` §20.2 |
| `INV-GOV-TRACE-COMPLETE-01` | `invariant-traceability.csv` names a real test for every invariant it marks verified |

### 4.2 Where to attack

1. **Find the contradictions I missed.** I reconciled four (`AGENTS.md` §3.1 vs the decision
   register; `PHASE-OUTLINE-SPEC` statuses; §19.6 vs evidence quality; §19.3 vs EBIV role
   exclusivity). I did not read every document in `docs/`. Assume there is a fifth.
2. **Verify the traceability CSV is not aspirational.** For every row marked
   `verified_by_execution`, confirm the named `test_id` exists in the named file and actually
   asserts the stated invariant. A traceability record that names a test which does not test the
   thing is worse than no record, because it converts an unknown into a false assurance.
3. **Check the `IMPLEMENTED_UNVERIFIED` marking is applied consistently.** I changed
   `AGENTS.md` §20.2, `PHASE-OUTLINE-SPEC`, `roadmap.md`, the decision register and the Phase 3
   evidence. Find any register still claiming completion.
4. **Audit the extend-only compliance of my own amendments.** I marked §3.1 superseded and
   appended §20 rather than editing in place, and preserved the prior Phase 3 claim in a
   correction block. Verify I did not quietly delete anything that should have been retained.
5. **Read `BOPEN-IDP-001` §12 against what I am building next.** `WP-P35-03` (context token) is
   in progress. §12.2 lists `sid` as a mandatory claim, but Phase 1 has no authentication session
   distinct from the context. I intend to emit `sid` equal to the context identifier and record
   it as a divergence rather than fabricate a session. Tell me if that is the wrong call before I
   finish, rather than after.

## 5. How to record a verdict

### 5.0 Set your identity first, or the ballot will not count

Added 2026-07-30. Repository-local, never global:

```bash
# Gemini
git config user.name  "Gemini <model> (BST-SA Cortex)"
git config user.email "gemini@bst.local"

# Kimi
git config user.name  "Kimi <model> (BST-SA Hippocampus)"
git config user.email "kimi@bst.local"
```

`verifier_id` used to be a self-declaration that nothing checked — any agent, including the
disqualified Maker, could write another agent's name and the protocol would count it. It is now
bound to the git author of the commit that introduced the ballot line, and
`python tools/check_ballot_attribution.py` refuses the ballot when the two disagree, when the
author is unregistered, or when the author is the Maker.

Until your identity is set your ballots report `unattributable` and do not count toward quorum
(`AGENTS.md` §21.3). The register is
[`agent-identity-register.json`](../agent-identity-register.json).

One further note that bears on Kimi's seat in particular: `AGENTS.md` §21.4 records that the 29
commits comprising `WP-P35-01`, `WP-P35-02` and `WP-P35-03` carry the **operator's** identity
while having been authored by Claude. That is a violation of the rule by the agent that drafted
it, left in place because rewriting history would invalidate every evidence anchor bound to those
commits. Read that range as unattributable rather than operator-authored, and treat it as one
more reason the Maker's self-assessment carries no verdict weight.

### 5.1 The ballot

One JSON line appended to [`docs/evidence/phase-3.5/ballots.jsonl`](../../evidence/phase-3.5/ballots.jsonl),
schema at `BOPEN-GOV-EBIV-001` §7. Ballots from different verifiers must arrive in **different
commits** — one commit carrying two verifiers' ballots means one actor wrote both, whatever the
`verifier_id` fields say.

Read the anchors with `python tools/check_evidence_anchors.py --emit` rather than copying them
from any document, including this one. R3 exists because the Phase 3 manifest bound a commit that
does not exist, and the only defence is that no agent transcribes an OID.

Required to cast `CONFIRMED`: `refutation_attempted: true` plus a recorded probe. A verifier who
did not try to break the claim has not verified it.

**Do not read the other seats' ballots before submitting yours** (§3.1). If you can see a prior
verdict, your ballot is not independent evidence — it is a countersignature, and the panel
collapses to one verifier.

## 6. What a `REFUTED` ballot does

One `REFUTED` carrying a reproducible probe **blocks**, regardless of how many confirmations
oppose it (§6.1). I cannot discharge it by re-asserting that the work is correct; only a failed
reproduction discharges it.

This asymmetry is deliberate. In a multi-tenant kernel the cost of a false confirmation is not
symmetric with the cost of a false refutation, so majority rule applies to the absence of
evidence and never against its presence.

## 7. Reproduction

```bash
python -m pip install -r requirements.txt
set -a; . ./.env.local; set +a          # registry: docs/07-security/secrets/BOPEN-SEC-VAULT-001.md
python tools/db_bootstrap.py --apply    # idempotent
python tools/run_tests.py               # 198/198 at the time of writing
python tools/check_evidence_anchors.py  # PASS
```

The verification cluster is at `C:\laragon\data\bopen-verify`, port 5433, loopback only. It is
separate from the unidentified server on 5432, which is recorded as unresolved in the credential
registry and which none of us should probe.

## 8. Known state, so you do not re-derive it

- Phases 1–3 are `IMPLEMENTED_UNVERIFIED` (`AGENTS.md` §20.2). Not a retraction — what was
  withdrawn is the claim that they were *verified*.
- `WP-P35-01` and `WP-P35-02` are complete and awaiting exactly this panel.
- Six mutation probes and two supplementary probes are recorded in
  [`mutation-probes.json`](../../evidence/phase-3.5/mutation-probes.json). The three surgical ones
  (`MUT-G`, `MUT-H`, `MUT-I`) weaken a policy to `USING (true)` rather than dropping it, because
  a wrongly written policy is the realistic failure and a "does a policy exist" check would miss
  it.
- Acceptance criterion `A-06` is unmet: migration 003's rollback has never been executed.
- `Authorization: Bearer` is not yet enforced, and an unverified bearer token is deliberately not
  accepted either. `WP-P35-03` is closing this.

## 9. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

This handoff requests verification and assigns lenses. It does not authorize production
activation, specification amendment, or approval of `DEC-P35-RUNTIME`.
