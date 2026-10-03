# Evidence Contracts

Evidence must include:

- request and authority references;
- source and target identifiers plus SHA-256 hashes;
- explicit comparison direction;
- source revision and migration history digest;
- PostgreSQL and tool versions;
- redacted commands and exit codes;
- raw output hashes;
- normalized changes;
- policy findings and rule IDs;
- verdict, status, required actions, residual risk, and limitations;
- package version and digest;
- reviewer and approval references when applicable.

Evidence must be append-only after closure. Corrections create a superseding envelope rather than modifying historical evidence.
