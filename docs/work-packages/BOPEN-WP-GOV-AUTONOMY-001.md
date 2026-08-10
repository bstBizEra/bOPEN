# BOPEN-WP-GOV-AUTONOMY-001 — Governed-Autonomy Bootstrap (SecB L0 port)

**Work Package:** `BOPEN-WP-GOV-AUTONOMY-001`
**Authorized by:** Operator (vily), session directive 2026-08-10 — *"tune the
bOPEN Engineer Loop so it can operate autonomously per the SecB Project
Framework plan; adjust locally and push to GitHub."*
**Decision record:** [`DEC-GOV-AUTONOMY-001`](../decisions/DEC-GOV-AUTONOMY-001.md)
**Status:** Delivered on branch `claude/BOPEN-WP-GOV-AUTONOMY-001`; awaiting operator ratification merge

## Scope

Port the SecB Project Framework governance machinery into bOPEN per SecB's
`NEW_PROJECT_BOOTSTRAP.md` runbook and bOPEN's own `AGENTS.md` §30.8
promotion conditions (item 1, the bootstrap/payload split):

1. GL root constitution (`docs/00-governance/GL_ROOT_CONSTITUTION.md`)
2. Delegation envelope at tier `AT1` (`config/delegation_envelope.json`)
3. Four enforcement scripts (`scripts/check_work_package_ref.py`,
   `check_budget.py`, `classify_authority_delta.py`, `check_dual_policy.py`)
4. Their subprocess tests, unittest-style (`tests/governance/`)
5. The `governance-gates` CI workflow
6. `AGENTS.md` §31 — the operative autonomous-merge rule
7. Gate-failure proofs (SecB runbook step 3: "prove the gates fail")

Out of scope: skill-router implementation (§28), ballot-layer activation,
external trust anchor, any release/production authority, ladder advance
beyond `AT1`.

## Acceptance criteria

- [x] All identifier collisions ruled in `AGENTS.md` §30.4 are honoured
      (`AD0`–`AD5`, `GL-0`–`GL-3`, `AT0`–`AT4`, `BOPEN-WP-*`)
- [x] Governance test suite green via `unittest discover` (stdlib only,
      matching the Bootstrap Governance workflow)
- [x] Each enforcement gate demonstrated **failing** on a crafted input, and
      the outputs recorded in
      `docs/evidence/governance-genesis/GATE-FAILURE-PROOFS.md`
- [x] Nothing binds before the operator's merge (`DEC-GOV-AUTONOMY-001` §1)

## Budget

`BUDGET: max_files=20 max_lines=2600` — declared on the pull request.
Over the 2000-line absolute ceiling by construction: a genesis package
installs the ceiling it will thereafter be measured by, and is
`CONSTITUTIONAL_REQUIRED` (operator-merged) regardless.
