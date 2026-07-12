# AGENTS.md — Platform services

This file supplements the root [`AGENTS.md`](../AGENTS.md). Root rules remain mandatory.

## Directory purpose

Services implement approved bounded contexts and contracts. Cross-service data access requires an approved integration contract. Avoid shared-database shortcuts between bounded contexts. Every externally observable behavior requires contract and failure semantics.

## Required completion evidence

- applicable artifact, requirement, ADR and work-package IDs;
- tests or validation appropriate to the directory;
- documentation/contract updates;
- security and clean-room declaration;
- residual risks and blocked decisions.
