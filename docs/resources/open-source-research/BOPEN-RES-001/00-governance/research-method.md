# Research Method

## Method sequence

1. Verify source provenance and commit pin.
2. Reproduce the clone and environment.
3. Create a repository/path inventory.
4. Trace one lifecycle at a time from UI to API to model to database to event/audit.
5. Record direct observations before making interpretations.
6. Execute tests and negative cases where practical.
7. Map findings to bOPEN concepts.
8. Record gaps and architecture options.
9. Review security and license implications.
10. Approve requirements and ADR candidates.
11. Release a clean-room handoff.

## Trace standard

Each lifecycle trace should include:

```text
Entry surface
  -> route/API handler
  -> validation
  -> authentication/session
  -> context resolution
  -> authorization decision
  -> domain/model operation
  -> database change
  -> event/audit emission
  -> response
```

## Classification

Use `ADOPT`, `ADAPT`, `REJECT`, `DEFER` only after evidence review.

- **ADOPT:** the pattern is suitable conceptually, not necessarily source-compatible.
- **ADAPT:** the pattern is useful but requires stronger bOPEN contracts.
- **REJECT:** the pattern conflicts with bOPEN requirements.
- **DEFER:** evidence or architecture is insufficient.
