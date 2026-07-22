# Release Procedure

1. Update version in `SKILL.md`, `bopen.skill.yaml`, `pyproject.toml`, `CHANGELOG.md`, and release metadata.
2. Run package validation and unit tests.
3. Run static evals and supported model-level evals.
4. Complete architecture, security, source, privacy, and license reviews.
5. Record an attributable human approval bound to the immutable source revision and make approved lifecycle metadata effective through the controlled registry.
6. Run `scripts/package_release.py`; it must fail while the package is candidate, inactive, or source-unbound.
7. Verify the ZIP digest and inventory.
8. Produce an approved SBOM and SLSA/in-toto provenance statement.
9. Sign the immutable artifact and attestations using the approved signing service.
10. Publish to the controlled registry and record default/version pointers.
11. Monitor activation, success, policy denial, cost, latency, incidents, and model drift.

The bundled provenance is an unsigned build statement. It is not a cryptographic attestation until signed by an approved identity and verification chain.
