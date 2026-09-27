# Verification Matrix

| Control | Static | Unit | Contract | Integration | Negative | Independent |
|---|---:|---:|---:|---:|---:|---:|
| Global principal model | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| Active tenant context | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PostgreSQL RLS | ✓ | ✓ |  | ✓ | ✓ | ✓ |
| Authorization | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Entitlement | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Module boundaries | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| Audit/outbox atomicity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Cache/file/search isolation |  | ✓ | ✓ | ✓ | ✓ | ✓ |
| Backup/restore |  |  |  | ✓ | ✓ | ✓ |
| Release evidence | ✓ |  | ✓ | ✓ |  | ✓ |
