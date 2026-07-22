---
workflow: start-governed-work
requires:
  skills:
    - bopen-governance-check
    - bopen-git-governance
    - bopen-worktree-management
    - bopen-evidence-envelope
eligibility: registry-resolved
---

# /start-governed-work

1. Run `python tools/validate_skill_registry.py --resolve-workflow start-governed-work`; stop on unknown, inactive, explicit-only or digest-drifted entries.
2. Run `bopen-governance-check`.
3. Read the work item and linked artifacts.
4. Produce a plan with files, risks, tests and stop conditions.
5. Wait for or confirm existing authorization.
6. Create/use the assigned isolated worktree.
7. Invoke the narrowest applicable implementation skill using `.agents/SKILL-ROUTING.md`.
8. Run verification and `bopen-evidence-envelope`.
9. Send the structured handoff to the assigned checker.
