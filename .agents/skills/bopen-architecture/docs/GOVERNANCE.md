# Governance

## Lifecycle

```text
OBSERVED
  -> CANDIDATE
  -> NORMALIZED
  -> VALIDATED
  -> EVALUATED
  -> APPROVED
  -> SIGNED
  -> PUBLISHED
  -> MONITORED
  -> DEPRECATED | SUSPENDED | REVOKED
```

This package is a `CANDIDATE`: deterministic checks may pass, but that does not promote
its lifecycle. It is inactive and has not been independently evaluated, approved,
signed, or published.

## Promotion requirements

Before `APPROVED`:

- activation and non-activation prompts are evaluated across supported models/runtimes;
- outcome, process, style, efficiency, security, tenancy, and recovery cases pass;
- architecture and security authorities review the package;
- source, privacy, and license review is complete;
- ownership, support, deprecation, and incident handling are assigned.

Before `PUBLISHED`:

- version is immutable and digest-bound;
- SBOM and provenance are complete;
- artifact and attestations are signed;
- registry metadata and revocation channel exist;
- tenant entitlement/enablement/binding controls are verified where applicable.

## Separation of duties

The author may prepare evidence. Independent reviewers approve architecture, security, and publication. A skill cannot approve its own promotion or exceptions.
