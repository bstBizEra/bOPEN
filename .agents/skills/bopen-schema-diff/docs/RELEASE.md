# Release Procedure

1. Update version and changelog.
2. Run package validation.
3. Run unit tests.
4. Run static evaluations.
5. Review adapter versions and vulnerability status.
6. Generate SBOM and provenance.
7. Generate `SHA256SUMS` and deterministic ZIP.
8. Independently verify ZIP contents and checksum.
9. Obtain architecture, security, and license approvals.
10. Sign the artifact and provenance through an approved build identity.
11. Publish only to an authorized registry.
