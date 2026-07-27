# BOPEN-TECH-001 — P0 Technology Baseline and Freeze Decision Record v0.1

**Status:** PROPOSED — NOT YET FROZEN

## Candidate baseline

- Architecture: modular monolith
- Primary language: TypeScript
- Web: React-based server-rendered portal framework
- Backend: structured TypeScript framework
- Database: PostgreSQL
- Isolation: `tenant_id` plus PostgreSQL RLS
- Cache: Redis-compatible adapter
- Files: S3-compatible adapter
- Identity: OIDC/OAuth provider adapter
- Contracts: OpenAPI plus versioned event schemas
- Events: transactional outbox
- Telemetry: OpenTelemetry/OTLP
- Packaging: OCI containers
- Supply chain: dependency lock, SBOM, provenance and signing

## Freeze gates

1. Decision owner and alternatives documented.
2. Compatibility matrix completed.
3. Security, licensing and operational review completed.
4. Local Windows/WSL development path verified.
5. CI and deployment proof completed.
6. Rollback and upgrade policy documented.
7. Architecture Authority approves a dated freeze.

Until then, implementation may conduct bounded proofs but shall not claim stack freeze.
