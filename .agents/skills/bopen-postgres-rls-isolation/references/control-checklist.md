# Control Checklist

- [ ] Every tenant-owned table is registered and covered.
- [ ] Policies never rely only on caller-provided Tenant IDs.
- [ ] INSERT and UPDATE use WITH CHECK.
- [ ] Runtime roles cannot bypass RLS.
- [ ] Tests prove default deny and cross-Tenant denial.
