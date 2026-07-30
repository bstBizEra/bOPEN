# HANDOFF-P35-MAKER-SPLIT-TO-CODEX — Phase 3.5 maker split

**Status:** Active — issued 2026-07-31
**Issued:** 2026-07-31
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Codex Agent IDE (VS Code)
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md)
**Governing standards:** [`BOPEN-GOV-EBIV-001`](../BOPEN-GOV-EBIV-001.md), [`BOPEN-GOV-IDENT-001`](../BOPEN-GOV-IDENT-001.md), `AGENTS.md` §19, §20.3, §22
**Decision:** [`DEC-P35-RUNTIME`](../../decisions/DEC-P35-RUNTIME.md) — **Approved 2026-07-31**, Option C
**Role source:** [`DEC-P35-DOCKET`](../../decisions/DEC-P35-DOCKET.md) §5.2

> **This supersedes [`HANDOFF-P35-PARALLEL-TO-CODEX`](HANDOFF-P35-PARALLEL-TO-CODEX.md)**, which
> was stood down on 2026-07-30 and proposed the opposite split. That document is retained as a
> record of what was asked and of whom. Do not execute it.

---

## 1. What changed on 2026-07-31

The gate is open. `DEC-P35-RUNTIME` was ratified by the operator acting as Architecture and
Engineering Authority, so Phase 3.5 implementation is authorized — not merely proposed.

Nothing about the previous state was a restriction on you specifically. `AGENTS.md` §19.3 has
always named Codex the precision implementer, and §20.4 has always said specialization is
guidance rather than role assignment. What blocked work was an unopened gate and an unassigned
maker. Both are now resolved. `AGENTS.md` §22.1 records this so it is not misread again.

---

## 2. Your assignment

**You are Maker of `WP-P35-01`, `WP-P35-02` and `WP-P35-03`.** All three are implemented and
sitting at `IMPLEMENTED_UNVERIFIED` with zero ballots cast. Your work is remediation: bring them
to the point where admissible evidence can be produced against them.

**Claude is Maker of `WP-P35-04`** (Hono + Zod API gateway) and will not touch your three. You
should not touch `WP-P35-04`, and the reason is worth stating plainly: it is what keeps you
eligible to verify it later. An agent that edits an artifact cannot vote on it
(`BOPEN-GOV-EBIV-001` §3).

`WP-P35-05` is blocked and unassigned. Do not start it.

| Work package | Maker | You may verify it? |
| :--- | :--- | :--- |
| `WP-P35-01` Persistence and tenant-scoped session | **You** | No — you author it |
| `WP-P35-02` Kernel HTTP surface | **You** | No — you author it |
| `WP-P35-03` Signed context token | **You** | No — you author it |
| `WP-P35-04` API gateway | Claude | **Yes** — do not edit it |
| `WP-P35-05` Enterprise IdP bridge | unassigned, blocked | n/a |

---

## 3. Baseline state — corrected 2026-07-31

> **This section originally stated that the canonical suite fails and that no admissible
> evidence exists for tenancy. That was wrong and is corrected here.** The failures came from a
> shell that had not sourced `.env.local`, not from a missing database. The error is recorded
> rather than silently replaced, because the first version of this handoff would have sent you
> to fix a problem that does not exist.

**Source the environment first. Every check below depends on it.**

```bash
set -a; . ./.env.local; set +a
```

Measured on 2026-07-31 with the environment sourced:

| Check | Result |
| :--- | :--- |
| `python tools/run_tests.py` | **414/414 OK** in 85s — unit 139, integration 125, contracts 101, isolation 38, governance 11 |
| `python tools/db_bootstrap.py --apply` | idempotent; migrations `001`..`009` already applied to `bopen_dev` on port 5433 |
| `python tools/check_authority_bootstrap.py` | **PASS** |
| `python tools/check_contract_conformance.py` | **PASS** — 11 of 16 constrainable schemas covered, 5 recorded as debt |
| `python tools/validate_repository.py` | **PASS** |
| `python tools/check_clean_room.py` | **PASS** |
| `python tools/check_evidence_anchors.py` | **PASS** |
| `python tools/check_ballot_attribution.py` | PASS — **no ballots recorded.** An empty state, not a verified one |

The 38 isolation tests execute against PostgreSQL, so `A-05` and EBIV R1 are satisfied for the
tenancy invariant: the evidence is executed, not simulated.

**What this does not mean.** All three packages remain `IMPLEMENTED_UNVERIFIED`, and the reason
has changed rather than disappeared. It was *evidence cannot be produced*. It is now *evidence
exists and no independent verifier has ruled on it*. `BOPEN-GOV-EBIV-001` §8 is explicit that a
maker reporting a green suite is a self-assessment carrying no verdict weight — the standard
was written after exactly that claim was made and found unsupported.

So your remediation scope is **not** "make the tests pass". They pass. It is to find what a
green suite is not telling us, and the recorded debt is the place to start:

- 5 schemas in `contracts/contract-conformance-baseline.json` have no instance validating
  against them. A frozen schema that never sees an instance cannot reject anything.
- `membership-transition-matrix.json` is classified as constraining nothing — a data document
  rather than a contract, or a contract never finished. Decide which.
- The invariant-traceability CSV must name a test ID for every `AGENTS.md` §7 invariant these
  packages touch. An untraced invariant counts as unverified, not as passed.
- `A-06` requires the migration to be reversible. `003` has a `down` script; whether it has been
  executed is a separate question from whether it exists.

If you find that a mechanism named in an evidence claim could be removed without any test
failing, that is the most valuable thing you can report, and it outranks any amount of new code.

---

## 4. What you must not do

These are gate conditions, not preferences. Each blocks a specific class of work because the
authorities have not decided the underlying question.

| Not authorized | Blocked by | Practical effect |
| :--- | :--- | :--- |
| Phase 2 persistence migration design | `D-P35-004`..`D-P35-010` unratified | Do not author migrations for sessions, delegated grants, group mappings, or the second context table. The identifier format is also undecided |
| `WP-P35-05` / IdP bridge work | `D-P35-011`..`D-P35-014` unratified | Leave `idp_bridge.py` simulated. Do not pin or introduce a BoxyHQ dependency |
| Audit envelope convergence | `D-P35-015`, `D-P35-016` unratified | Do not amend `audit-event.json` or its producer. The two-envelope interim stands |
| Treating `BOPEN-PRD-P35-001` as bound requirements | `D-P35-017`, `D-P35-018` unratified | It is planning input, not authority |
| Declaring any package complete | `BOPEN-GOV-EBIV-001` §3 | You are Maker. A maker's self-assessment carries no verdict weight |
| Production activation | Out of agent authority entirely | Regardless of test results |

If you hit one of these, `AGENTS.md` §16 applies: stop and raise a decision request rather than
resolving the architecture by writing code that assumes an answer.

---

## 5. Commit identity

Set per repository, never globally (`AGENTS.md` §21.1):

```bash
git config user.name  "Codex (BST-SA Motor)"
git config user.email "codex@bst.local"
```

Do not commit under the operator's identity. §21.2.1 treats that as the one misattribution that
changes what a commit *means* — 29 commits already carry that defect and are recorded as
unattributable in `agent-identity-register.json`.

---

## 6. Required checks before you report

| Check | Command |
| :--- | :--- |
| Canonical suite | `python tools/run_tests.py` |
| Repository validation | `python tools/validate_repository.py` |
| Clean-room | `python tools/check_clean_room.py` |
| Authority bootstrap | `python tools/check_authority_bootstrap.py` |
| Evidence anchors | `python tools/check_evidence_anchors.py` |
| Ballot attribution | `python tools/check_ballot_attribution.py` |

Evidence path is `docs/evidence/phase-3.5/`. Anchors must be machine-emitted (`A-07`), never
transcribed. The invariant-traceability CSV must name a test ID for every `AGENTS.md` §7
invariant your work touches; an untraced invariant counts as unverified, not as passed.

---

## 7. What completion looks like, and what it does not

Report per `AGENTS.md` §17: work-package IDs, files changed, contracts changed, checks run with
results, evidence path, residual risks, decisions still required.

Then stop. `WP-P35-01`..`WP-P35-03` need an independent checker who is neither you nor Claude —
Claude authored them and you will have remediated them, so §3 excludes us both. **That seat must
be Gemini or Kimi**, and neither has cast a ballot or holds a commit identity in this
repository. It is an open risk, recorded as one in `DEC-P35-DOCKET` §5.3, and it is not
something your work can close.

Producing green tests is not verification. It is the thing a verifier is asked to disbelieve.

---

## 8. Provenance

Issued by Claude (agent, Motor role) on 2026-07-31 under operator instruction to assign Codex
implementation work alongside Claude. Role split ratified in `DEC-P35-DOCKET` §5.2.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
