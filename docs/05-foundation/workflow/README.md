# Workflow

Workflow, task, approval, activity and notification foundation contracts.


## Known defect — append-only evidence does not survive tenant deletion

The `ON DELETE RESTRICT` foreign keys on this foundation's append-only tables defend them against a
direct parent delete, but **not** against deleting the tenant: `tenant_id` references
`tenants(id) ON DELETE CASCADE`, and PostgreSQL performs foreign-key actions with row security
bypassed, so the tenant edge removes the rows before the RESTRICT edge is consulted.

Reproduced live on the notification tables during independent verification; established for the
tables here by identical declared semantics with no trigger, rule or `DEFERRABLE` constraint
anywhere in the migration set. **Latent** — no tenant-deletion path exists in `tools/` or
`platform_kernel/` today.

Raised for disposition as
[`DEC-P4-NOTIFY-TENANT-CASCADE`](../../decisions/DEC-P4-NOTIFY-TENANT-CASCADE.md) §6, which covers
11 tables across four foundations. `audit_events` and `lifecycle_events` already carry
`tenant_id ON DELETE RESTRICT` and are the pattern that does defend it.

Affected tables here: `workflow_history` — note that `014_workflow_history_survives_its_instance.sql` exists for this class of defect and closed the *instance* edge while leaving the tenant edge `CASCADE`
