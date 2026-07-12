# Security Policy

## Reporting

Report suspected vulnerabilities privately to the designated bOPEN Security Authority. Do not publish exploit details in public issues.

## Scope

Security review includes source, dependencies, CI/CD, infrastructure, identity, tenant isolation, authorization, entitlements, data handling, integrations, agents and operational procedures.

## Mandatory controls

- deny-by-default access;
- least privilege;
- explicit tenant context;
- database-enforced isolation;
- auditable privileged access;
- secret scanning;
- dependency and license review;
- signed or attestable build/release evidence when introduced;
- incident and recovery runbooks.

## Supported status

This repository is in bootstrap and architecture phase. No production-security assurance is claimed until BOPEN-SEC-001 and deployment-specific security gates are approved.
