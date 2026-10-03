# Threat Model

Protected assets include tenant data boundaries, schema integrity, migration history, database credentials, audit evidence, and production availability.

Primary threats:

- malicious SQL or poisoned schema input;
- prompt injection embedded in comments or migration files;
- adapter command injection;
- credential disclosure;
- false-negative destructive change detection;
- RLS or privilege weakening;
- dependency-order failures;
- tool supply-chain compromise;
- unauthorized production mutation;
- evidence alteration.

Controls include deny-by-default tools, argument separation, redaction, read-only access, immutable input hashes, conservative verdicts, second opinions, independent review, sandboxing, version pinning, checksums, provenance, and revocation.
