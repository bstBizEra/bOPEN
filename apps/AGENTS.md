# AGENTS.md — Application surfaces

This file supplements the root [`AGENTS.md`](../AGENTS.md). Root rules remain mandatory.

## Directory purpose

Applications compose approved services and packages into user experiences. They do not own platform domain truth. Do not implement authorization solely in UI. Route handling must resolve and validate context server-side. UI prototypes must not create implicit domain models.

## Required completion evidence

- applicable artifact, requirement, ADR and work-package IDs;
- tests or validation appropriate to the directory;
- documentation/contract updates;
- security and clean-room declaration;
- residual risks and blocked decisions.
