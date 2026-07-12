# AGENTS.md — Tooling

This file supplements the root [`AGENTS.md`](../AGENTS.md). Root rules remain mandatory.

## Directory purpose

Tools may validate, generate or inspect but shall not silently mutate normative documents. Generated files must be deterministic. Validation failures must be actionable and non-destructive. Tools must use only standard libraries unless dependencies are approved.

## Required completion evidence

- applicable artifact, requirement, ADR and work-package IDs;
- tests or validation appropriate to the directory;
- documentation/contract updates;
- security and clean-room declaration;
- residual risks and blocked decisions.
