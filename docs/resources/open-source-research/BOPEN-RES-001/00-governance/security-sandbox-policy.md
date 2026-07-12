# Security Sandbox Policy

The study clone must run in a non-production environment with synthetic identities and test data.

## Controls

- no production credentials or customer data;
- no live payment keys;
- no production SSO/SCIM tenant;
- no externally reachable default deployment;
- secrets loaded from local non-committed environment files;
- dependency and container scanning;
- restricted outbound access where practical;
- separate database and object storage;
- terminal logs redacted before evidence publication;
- destroyable environment.

## External services

Prefer local mocks or test tenants for email, webhooks, audit, SSO, directory sync and payments. Document any external data transfer.
