# DEC-GOV-AUTONOMY-001 — Genesis Ratification of the Governed-Autonomy Bootstrap (Engineer Loop autonomous merge)

**Decision ID:** `DEC-GOV-AUTONOMY-001`
**Version:** `1.0.0`
**Status:** **PROPOSED — RATIFIED UPON THE OPERATOR'S MERGE OF THE `BOPEN-WP-GOV-AUTONOMY-001` PULL REQUEST**
**Issued:** 2026-08-10
**Governing Standard:** `AGENTS.md` §30.8 item 1 (bootstrap/payload split), §30.7 (Genesis Ratification constraint), `BOPEN-GOV-EBIV-001` §2
**Work Package:** `BOPEN-WP-GOV-AUTONOMY-001`
**Source Framework:** SecB Project Framework (`bstBizEra/secb_pf`) — L0 governance ratified there at `SECB-WP-FWK-012`, ported per its runbook `docs/15-runbooks/NEW_PROJECT_BOOTSTRAP.md` (`SECB-WP-FWK-017`)

---

## 1. The decision

The operator directed on 2026-08-10, in session: *tune the bOPEN Engineer Loop
so it can operate autonomously under the SecB Project Framework plan.*

This decision record installs the **bootstrap**: the GL root constitution, the
delegation envelope at tier `AT1`, the four enforcement scripts, their tests,
and the `governance-gates` CI workflow. On the operator's merge of the pull
request that carries this record, `AGENTS.md` §31 comes into force and an
agent may merge its own pull request **only** when every §31.2 condition
holds. Until that merge, nothing in this package binds anything.

The merge itself is the "explicit operator authorization with verifiable Git
provenance" that `BOPEN-GOV-EBIV-001` §2 requires. Consistent with §30.7, the
agent that drafted this package cannot bring it into force, and does not:
**ratification is the operator's merge, not this document.**

## 2. What comes into force at ratification

| Artifact | Role |
| :--- | :--- |
| `docs/00-governance/GL_ROOT_CONSTITUTION.md` | GL-0: layers, ceilings, prohibited actions, change classes `AD0`–`AD5`, authority verdicts |
| `config/delegation_envelope.json` | GL-1: `ENV-BOPEN-2026-001`, tier `AT1`, scope, caps, ladder, expiry 2026-11-08 |
| `scripts/check_work_package_ref.py` | Authority gate: No Ticket, No Work |
| `scripts/check_budget.py` | Budget circuit breaker: declared diff budget honoured |
| `scripts/classify_authority_delta.py` | Authority-delta classifier: `AD0`–`AD5` → authority verdict |
| `scripts/check_dual_policy.py` | Anti-self-approval: base and head policy must agree |
| `.github/workflows/governance-gates.yml` | The four executable gates |
| `tests/governance/test_check_*.py`, `test_classify_*.py` | Proof the gates work — an uncopied test is an unproven gate |
| `AGENTS.md` §31 | The operative autonomous-merge rule |

## 3. Identifier rulings honoured (`AGENTS.md` §30.4)

| SecB token | bOPEN token | Reason |
| :--- | :--- | :--- |
| `G0`–`G5` change classes | `AD0`–`AD5` | `G`-prefix collides with in-force "GATE G7 CLEARED" |
| `L0`–`L3` layers | `GL-0`–`GL-3` | `L3` already means assurance Level 3 in `EVD-SEC-001` |
| `A0`–`A4` tiers | `AT0`–`AT4` | `A0`–`A4` already carries URE-Loop v1.5 meanings in §28.2 |
| `SECB-WP-*` | `BOPEN-WP-*` (legacy `BOPEN-P*`, `WP-P*`, `BOOT-P*` accepted) | Project prefix |
| Verdict tokens | Unchanged, always set-qualified as *authority verdicts* | Distinct from EBIV ballot verdicts and operator dispositions |

## 4. What stays excluded

- **No agent merge of governance classes.** `AD1`/`AD2` escalate to the
  operator while `ballot_layer.state` is `NOT_ACTIVE` (§30.6: two verifying
  agents cannot form a quorum). `AD4` is always the operator's.
- **No self-advance up the ladder by assertion.** `AD3` exists only for the
  conditions the envelope records in advance, objectively met — and tiers
  `AT3`/`AT4` stay unreachable until the ballot layer is active.
- **No release, deployment, or production authority.** §31 covers **merge**
  of `AD0` changes only. `LC` stages 9–11 (§29), `BUILD_COMPLETE` semantics,
  and operator dispositions (§25.1 step 8) are untouched.
- **No external trust anchor yet.** The verifier runs inside the repository
  it judges; every change under `.github/` is therefore `AD4`
  (`CONSTITUTIONAL_REQUIRED`) as the compensating control (§30.8 item 2).

## 5. Duties attached to every autonomous merge

1. Classifier authority verdict `AUTO_APPROVED`, dual-policy `PASS`, all
   `governance-gates` jobs green, envelope unexpired and unrevoked.
2. The PR body carries exactly one `BUDGET: max_files=<n> max_lines=<n>` line
   and cites its work-package ID.
3. **Every autonomous merge is announced** (verdict + gate results + merge
   SHA + work-package ID) on the ticket. Silence is a policy violation.
4. The commit is authored under the acting agent's registered identity
   (`AGENTS.md` §21.1).

## 6. Revocation and expiry

The operator may revoke or narrow this delegation at any time by statement in
session or a comment on the ratification PR, effective immediately, without a
pull request. The envelope expires 2026-11-08; expiry lapses all delegation.
**Never extend that date to unblock a specific PR** (a prohibited-action
signature).

## 7. Candidate binding

| Field | Bound value |
| :--- | :--- |
| Branch | `claude/BOPEN-WP-GOV-AUTONOMY-001` |
| Base | `561333a` (`claude/BOPEN-P35-001-runtime-realization`) |
| Ratification SHA | *the operator's merge commit — recorded on the PR at merge* |

---

*Drafted by Claude (BST-SA Motor) under the operator's 2026-08-10 session
directive. This document confers no authority by itself (§30.7).*
