---
workflow: module-cycle
requires:
  skills:
    - bopen-requirement-to-work-item
    - bopen-architecture
    - bopen-module-contract
    - bopen-tenant-isolation-review
    - bopen-sec-qa-lead
    - bopen-evidence-envelope
eligibility: registry-resolved
---

# /module-cycle

1. Run `python tools/validate_skill_registry.py --resolve-workflow module-cycle` and stop on an ineligible dependency.
2. Register and classify the module.
3. Run `bopen-requirement-to-work-item`.
4. Run `bopen-module-contract`.
5. Architecture/security review using the routing map.
6. Authorized implementation in isolated worktree.
7. Contract, integration and tenant-isolation verification.
8. Portal verification where applicable.
9. Evidence and independent review.
10. Pilot or remediation recommendation.
