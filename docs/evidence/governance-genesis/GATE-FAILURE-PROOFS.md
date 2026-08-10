# Gate-failure proofs — governed-autonomy bootstrap

**Work package:** `BOPEN-WP-GOV-AUTONOMY-001` · **Decision:** `DEC-GOV-AUTONOMY-001`
**Recorded:** 2026-08-10, on branch `claude/BOPEN-WP-GOV-AUTONOMY-001` (base `561333a`)
**Procedure:** SecB `NEW_PROJECT_BOOTSTRAP.md` step 3 — *"a copied gate is an
unproven gate; green CI proves nothing: a gate wired to nothing is also green."*

Each enforcement gate was driven to **failure** on a crafted input, then shown
recovering on a corrected input. Outputs below are verbatim from local
execution (Python 3, WSL2, worktree `bopen-worktrees/gov-autonomy-001`).
The unit suite (44 tests, `unittest discover -s tests/governance`) passed in
the same tree.

## 1. Authority gate — fails without a ticket, passes with one

```text
$ WP_TEXT="chore: tidy docs, no ticket" python3 scripts/check_work_package_ref.py
AUTHORITY GATE FAIL: no BOPEN-WP-* work-package reference found. AGENTS.md section 5: identify the accepted work-package ID. No Ticket, No Work.
exit=2

$ WP_TEXT="Closes BOPEN-WP-GOV-AUTONOMY-001" python3 scripts/check_work_package_ref.py
AUTHORITY GATE PASS: work-package reference BOPEN-WP-GOV-AUTONOMY-001
exit=0
```

The failure message carries the **bOPEN** prefix, proving the rename reached
the enforcement path and not only the documentation (SecB trial finding 1).

## 2. Budget gate — trips on `max_lines=1`, passes when honest

```text
$ printf '40\t20\tdocs/a.md\n' | BUDGET_TEXT="BUDGET: max_files=5 max_lines=1" python3 scripts/check_budget.py
BUDGET GATE FAIL: diff exceeds the declared budget -- 1/5 files, 60/1 changed lines. A reached cap is a stop condition; shrink the change or re-negotiate the budget on the work-package ticket.
exit=2

$ printf '40\t20\tdocs/a.md\n' | BUDGET_TEXT="BUDGET: max_files=5 max_lines=100" python3 scripts/check_budget.py
BUDGET GATE PASS: 1/5 files, 60/100 changed lines
exit=0
```

## 3. Classifier — constitutional surface escalates; prohibited signature rejects; AD0 passes

```text
$ printf '2\t1\tconfig/delegation_envelope.json\n' | python3 scripts/classify_authority_delta.py
VERDICT: CONSTITUTIONAL_REQUIRED — root authority surface touched: config/delegation_envelope.json
exit=2

$ printf '3\t4\tdocs/note.md\n' | DIFF_TEXT='-        run: python scripts/check_budget.py' python3 scripts/classify_authority_delta.py
VERDICT: REJECTED — prohibited: removes an enforcement step from CI — run: python scripts/check_budget.py
exit=3

$ printf '5\t2\tdocs/note.md\n' | python3 scripts/classify_authority_delta.py
VERDICT: AUTO_APPROVED — AD0, 1 path(s), 7/600 lines, tier AT1
exit=0
```

## 4. The genesis package judges itself as requiring the operator

The bootstrap diff itself, classified under the head policy, and evaluated
under dual policy against its base:

```text
$ git diff --numstat --cached 561333a | python3 scripts/classify_authority_delta.py
VERDICT: CONSTITUTIONAL_REQUIRED — root authority surface touched: .github/workflows/governance-gates.yml, AGENTS.md, config/delegation_envelope.json, docs/00-governance/GL_ROOT_CONSTITUTION.md
exit=2

$ git diff --numstat 561333a...HEAD | BASE_REF=561333a python3 scripts/check_dual_policy.py
DUAL POLICY: ESCALATE — base logic not recoverable at 561333a (first installation, or the base ref is unavailable). Genesis and bootstrap changes escalate by construction.
exit=2
```

This is the healthy output (SecB trial, 2026-08-10): the machinery's first act
is to rule that **it cannot approve its own installation**. Ratification is
the operator's merge (`DEC-GOV-AUTONOMY-001` §1), exactly as `AGENTS.md` §30.7
requires. Do not expect base-vs-head divergence on a real PR — the
anti-self-approval property holds earlier and harder than divergence-hunting
suggests; divergence is observable only in the unit test
`test_divergence_escalates_even_when_head_would_pass`, which passes.
