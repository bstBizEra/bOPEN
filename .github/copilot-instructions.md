# GitHub Copilot Instructions for bOPEN

Read root `AGENTS.md` before proposing or changing code.

Discover shared procedures from `.agents/skills/` and verify lifecycle state in
`docs/registers/skill-registry.json`; do not treat skill availability as authority.

- Work only within an authorized issue/work item.
- Preserve tenant context, RLS, authorization and module boundaries.
- Do not weaken tests or security scans.
- Do not add dependencies without approval.
- Update contracts and documentation with behavior.
- Produce evidence and request independent review.
- Never treat PR mergeability as release authorization.
