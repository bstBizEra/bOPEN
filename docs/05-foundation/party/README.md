# Party

Party, person, organization and contextual party roles.

Research for the proposed Party-owned ContactPoint extension is recorded in
[`RESEARCH-MILE-4.2-PARTY-CONTACTPOINT`](../../01-product/MILE-4.2-party-contactpoint-extension-research.md).
Its independent advisory review is
[`REVIEW-MILE-4.2-PARTY-CONTACTPOINT`](../../01-product/MILE-4.2-party-contactpoint-extension-review.md):
`RETURN FOR REVISION`. The operator's separate implementation authorization is recorded at
`DEC-P4-ENTRY` §10; it does not close the review findings or constitute an EBIV verdict.


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

Affected tables here: `party_contact_points`, `party_contact_point_verification_events`
