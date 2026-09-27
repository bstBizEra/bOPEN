# TECHNOLOGY.md

The P0 stack remains subject to formal BOPEN-TECH-001 approval.

Recommended baseline for decision:

- Modular monolith with explicit module boundaries
- TypeScript for primary application code
- React-based server-rendered web portals
- Structured TypeScript backend framework
- PostgreSQL with tenant-aware schema and RLS
- Redis-compatible cache only for derived/ephemeral state
- S3-compatible object storage behind an adapter
- OIDC/OAuth identity-provider adapter
- Transactional outbox and versioned event envelope
- OpenAPI and event schema contracts
- OpenTelemetry instrumentation
- OCI containers, SBOM, provenance and signed release artifacts

No listed technology is implementation-authorized solely by appearing in this file.
