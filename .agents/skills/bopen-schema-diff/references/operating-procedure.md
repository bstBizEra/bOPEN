# Operating Procedure

## 1. Intake

Record request ID, source, target, direction, PostgreSQL version, repository revision, migration directory digest, environment classification, and authority reference. Reject ambiguous direction.

## 2. Source acquisition

Accept SQL files, Atlas HCL, migration directories, Prisma schema files, Git revisions, sanitized database snapshots, or runtime references to read-only database URLs. Never persist database passwords.

## 3. Deterministic planning

Run at least one deterministic engine. For security-sensitive or destructive changes, require a second opinion. Save tool version, command with secrets redacted, stdout/stderr digests, and exit code.

## 4. Normalization

Translate raw outputs to canonical changes. Preserve ambiguity. Do not silently map drop/create to rename.

## 5. Semantic checks

Apply migration safety, tenant isolation, RLS, privilege, evidence-table, outbox, audit, and module-boundary rules.

## 6. Risk scoring

Use the highest-severity applicable verdict. Missing information never lowers risk. Engine disagreement produces `REVIEW_REQUIRED` unless a stricter verdict applies.

## 7. Evidence

Generate JSON and Markdown. Hash inputs, outputs, normalized change sets, and final report. Redact credentials and personal data.

## 8. Disposition

- PASS: safe or explicitly conditioned, no unresolved mandatory action.
- REVIEW: human judgment, coordination, incomplete evidence, or engine disagreement.
- BLOCK: security boundary violation, destructive unapproved change, unauthorized mutation, or evidence integrity failure.
