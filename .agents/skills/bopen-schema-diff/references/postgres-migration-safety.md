# PostgreSQL Migration Safety

Review each statement for:

- data loss or truncation;
- table or index locking;
- table rewrites and full scans;
- long-running backfills;
- transaction duration;
- constraint validation strategy;
- index build strategy;
- application backward compatibility;
- replication and logical decoding impact;
- dependency order;
- rollback or forward-fix feasibility.

## Mandatory patterns

Prefer expand-and-contract for breaking application changes. Prefer `CREATE INDEX CONCURRENTLY` where operationally appropriate and supported. Add foreign keys or check constraints as `NOT VALID` before validation when reducing lock duration is required. Separate large data backfills from DDL. Verify existing data before `SET NOT NULL` or type conversion.

Never assume a generated plan is safe merely because it is syntactically valid.
