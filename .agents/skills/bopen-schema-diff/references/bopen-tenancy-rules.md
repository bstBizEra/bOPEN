# bOPEN Tenancy Rules

A tenant-owned table must normally satisfy:

1. `tenant_id` exists.
2. `tenant_id` is `NOT NULL`.
3. Type is compatible with `tenants.id`.
4. A valid foreign key exists unless an approved exception is documented.
5. Tenant-local unique keys include `tenant_id` where uniqueness is tenant-scoped.
6. RLS is enabled.
7. `FORCE ROW LEVEL SECURITY` is enabled for tables whose owner could otherwise bypass policy.
8. Read policy has an explicit tenant predicate.
9. Insert/update policy has an explicit `WITH CHECK` tenant predicate.
10. Cross-tenant foreign keys are prohibited unless the relationship is explicitly modeled and independently approved.

Tables categorized as global reference data must be explicitly declared. Absence of `tenant_id` is not automatically safe merely because a table name appears global.
