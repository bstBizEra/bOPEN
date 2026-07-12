# Clone Provenance Policy

## Required clone metadata

- canonical repository;
- upstream owner;
- clone date;
- default branch;
- pinned commit SHA;
- tag, if used;
- repository archived status;
- license checksum;
- local patch list;
- dependency lock checksum;
- researcher identity;
- workstation/toolchain record.

## Branch policy

Research may use a local branch, but every evidence record must cite `abc9b686823cbfb4973c79bc36fea37a3244be6c` or another explicitly approved commit. `main`, `latest` and floating tags are not acceptable evidence pins.

## Upstream refresh

A refresh requires a new baseline record and comparison. Existing evidence remains bound to its original commit.

## Acquisition/transfer watch

Because BoxyHQ has been acquired by Ory, the custodian shall check quarterly for repository transfer, archival, license change, dependency rename and documentation relocation.
