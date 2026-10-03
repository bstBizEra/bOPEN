# Risk Model

The final verdict is the most severe applicable category:

1. `SAFE`
2. `CONDITIONAL`
3. `REVIEW_REQUIRED`
4. `BREAKING`
5. `DESTRUCTIVE`
6. `SECURITY_CRITICAL`
7. `BLOCKED`
8. `UNKNOWN` when evidence is insufficient and no stricter category is known

`UNKNOWN` does not mean low risk. Operational status must be `REVIEW` or `ERROR`.

Security boundary removals are blocked. Possible data loss is destructive. Client compatibility breaks are breaking. Lock or backfill concerns are conditional or review-required depending on evidence.
