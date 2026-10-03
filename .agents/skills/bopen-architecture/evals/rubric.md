# bOPEN Architecture Skill Evaluation Rubric

Score each dimension 0–4.

## 1. Activation

- 4: triggers on all in-scope prompts and avoids unrelated prompts;
- 3: one minor false positive/negative;
- 2: inconsistent boundary;
- 1: broad or vague activation;
- 0: unusable routing.

## 2. Architectural correctness

- 4: preserves all applicable baseline separations and ownership boundaries;
- 3: correct with one minor omission;
- 2: material ambiguity;
- 1: conflates a core concept;
- 0: recommends a prohibited pattern.

## 3. Tenancy and security

- 4: context, RLS, authorization, entitlement, cross-tenant tests, and evidence are explicit;
- 3: one control needs more precision;
- 2: incomplete threat/control analysis;
- 1: weak default-deny posture;
- 0: cross-tenant or privilege-escalation risk.

## 4. Evidence and research

- 4: sources are authoritative/current, facts are cited, and uncertainty is explicit;
- 3: evidence is sufficient with minor gaps;
- 2: mixed source quality or missing dates;
- 1: unsupported material claims;
- 0: fabricated evidence or approval.

## 5. Implementability

- 4: owned contracts, work packages, tests, recovery, evidence, and exit gates are actionable;
- 3: mostly actionable;
- 2: high-level only;
- 1: aspirational;
- 0: contradictory or unsafe.

## 6. Efficiency and focus

- 4: bounded to the task with progressive use of references;
- 3: minor excess;
- 2: substantial unrelated material;
- 1: unfocused;
- 0: fails to address the task.

### Passing rule

- total at least 21/24;
- tenancy/security at least 3;
- no fabricated evidence;
- no cross-tenant failure;
- no recommendation that a skill, entitlement, role, or client-supplied tenant value grants authority by itself.
