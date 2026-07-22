---
workflow: conformance-review
requires:
  skills:
    - bopen-governance-check
    - bopen-sec-qa-lead
    - bopen-release-readiness
eligibility: registry-resolved
---

# /conformance-review

1. When the user explicitly requests this review, run `python tools/validate_skill_registry.py --resolve-workflow conformance-review --explicit-skill bopen-release-readiness`; candidate/inactive gate skills must stop.
2. Load requirement and verification matrices.
3. Confirm evidence source integrity.
4. Re-run mandatory high-risk checks where authorized.
5. Classify each gate PASS, FAIL, BLOCKED or NOT APPLICABLE.
6. List residual risks and expired exceptions.
7. Produce a recommendation for human Conformance Authority.
