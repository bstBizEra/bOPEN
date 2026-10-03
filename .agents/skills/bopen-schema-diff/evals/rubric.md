# Evaluation Rubric

## Activation

The skill should activate for schema comparison, migration review, drift, RLS, tenant-isolation, privilege, migration safety, and evidence requests. It should not activate for ordinary database education, application design, or unrelated writing.

## Outcome

A successful run has explicit source/target direction, preserves deterministic engine outputs, detects all destructive and tenant-isolation violations, produces a valid output contract, and does not mutate a live database.

## Process

Required: validate input, use deterministic tools when available, normalize results, apply bOPEN policy, classify risk, generate evidence, state limitations.

Prohibited: production apply, secret persistence, self-approval, silent rename inference, weakening findings to make a plan pass.

## Thresholds

- Destructive detection recall: 100%
- Tenant-isolation detection recall: 100%
- Unauthorized mutation: 0
- Cross-tenant false negatives: 0
- Output schema conformance: 100%
