# Risk Register

| Risk | Likelihood | Impact | Control |
|---|---:|---:|---|
| Accidental source copying | Medium | High | Clean-room zones, PR provenance review |
| License obligations overlooked | Low-medium | High | License register and legal gate |
| Upstream changes after acquisition | Medium | Medium | Commit pin and quarterly provenance watch |
| Starter-kit assumptions mistaken for platform architecture | High | High | Gap analysis and independent bOPEN requirements |
| Implicit tenant context allows IDOR | Medium | Critical | G4 negative testing |
| Invitation replay/role escalation | Medium | High | Token, concurrency and payload tests |
| External audit/webhook outage changes transaction behavior | Medium | High | Failure-mode tests and outbox requirements |
| Billing state conflated with entitlement | High | High | Separate commercial/entitlement model |
| API key lacks accountable actor | High | High | Service-principal requirement |
| Dependency drift breaks reproduction | Medium | Medium | Lockfile checksum and environment manifest |
| Test environment leaks external data | Low-medium | High | Sandbox policy and synthetic data |
| Research findings lack traceability | Medium | High | Evidence IDs and gate reviews |
