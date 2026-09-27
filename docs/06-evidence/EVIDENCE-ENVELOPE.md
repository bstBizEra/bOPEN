# Evidence Envelope

```yaml
evidence_id:
work_item_id:
artifact_version:
created_at:
producer:
checker:
repository:
branch:
worktree:
base_commit:
head_commit:

authority:
  authorization_id:
  effective_at:
  expires_at:

traceability:
  goals: []
  requirements: []
  decisions: []
  risks: []

change:
  summary:
  files: []
  migrations: []
  dependencies: []

verification:
  commands: []
  static_checks: []
  unit_tests: []
  contract_tests: []
  integration_tests: []
  tenant_isolation_tests: []
  security_tests: []
  recovery_tests: []

results:
  passed:
  failed:
  skipped:
  unresolved_findings: []

artifacts:
  logs: []
  reports: []
  screenshots: []
  hashes: []

rollback:
  method:
  verified:

decision:
  maker_disposition:
  checker_disposition:
  conformance_disposition:
  release_authorized: false
```
