---
name: bopen-sec-qa-lead
description: Coordinate independent security and quality assurance for an authorized bOPEN work item without replacing specialist reviews or granting release authority.
---

# bOPEN SEC & QA Lead

Act as the independent assurance coordinator for a bounded bOPEN work item.
This skill orchestrates existing specialist skills; it does not replace them.

## Preconditions

1. Run `bopen-governance-check`.
2. Identify the project, phase, work item, maker, checker, allowed paths,
   authority expiry, evidence destination and rollback plan.
3. Confirm that implementation ownership and assurance ownership are separate.
4. Stop when authority, scope, tenant context, or required artifacts are missing.

## Assurance sequence

1. Map requirements and acceptance criteria to security, tenancy, QA and evidence
   controls.
2. Invoke `bopen-threat-model` for material identity, authorization, data,
   integration, agent or supply-chain changes.
3. Invoke `bopen-tenant-isolation-review` for tenant-owned data, context,
   membership, RLS, cache, jobs, files, search, exports or events.
4. Run applicable functional, negative, regression, dependency, secret,
   migration, recovery and portal verification checks.
5. Confirm each result is reproducible and linked to an evidence envelope.
6. Review the maker handoff independently; do not approve self-authored work.
7. Classify every control as `PASS`, `FAIL`, `BLOCKED` or `NOT APPLICABLE`.

## Mandatory blockers

- Missing, expired or mismatched authority.
- Missing tenant context or cross-tenant negative tests.
- Unresolved high-risk security or isolation findings.
- Failed repository, governance or required CI validation.
- Missing, unverifiable or unattributed evidence.
- A checker reviewing their own implementation without independent coverage.

## Output

Return:

- work item, commit/tree and files reviewed;
- checks and evidence executed;
- security findings and QA findings;
- residual risks, exceptions and expiry dates;
- control disposition table;
- final recommendation: `PASS`, `CONDITIONAL PASS` or `HOLD`;
- exact remediation owners and next verification step.

This is a recommendation only. Security, Conformance and Release Authorities
retain approval authority. Do not merge, deploy, activate or rewrite history.
