# AGENTS.md — Tests and evidence

This file supplements the root [`AGENTS.md`](../AGENTS.md). Root rules remain mandatory.

## Directory purpose

Tests are evidence, not implementation decoration. Security-sensitive behavior needs negative tests. Cross-tenant access must be tested from the database and API boundary. Never reduce coverage or skip checks without an approved exception.

## Required completion evidence

- applicable artifact, requirement, ADR and work-package IDs;
- tests or validation appropriate to the directory;
- documentation/contract updates;
- security and clean-room declaration;
- residual risks and blocked decisions.
