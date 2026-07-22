# Usage

## Explicit invocation

```text
Use $bopen-architecture to review this tenant-context design and issue a conformance verdict.
```

## Common requests

```text
Use $bopen-architecture to create an ADR deciding whether the Skills Registry belongs in the P0 modular monolith.
```

```text
Use $bopen-architecture to research the current Agent Skills format and map it to bOPEN governance.
```

```text
Use $bopen-architecture to turn BOPEN-SYS-001 into implementation work packages, evidence requirements, and exit gates.
```

## Input contract

Structured callers can use `schemas/input.schema.json`. The example is `evals/example-input.json`.

## Output contract

Structured callers can use `schemas/output.schema.json`. Narrative artifacts should follow the templates in `assets/` and preserve the same concepts: disposition, decisions, controls, risks, verification, evidence, and assumptions.

## Local utilities

- `new_artifact.py`: create a non-overwriting artifact skeleton beneath a separately authorized output directory;
- `check_architecture.py`: detect missing control groups and prohibited patterns;
- `validate_package.py`: validate the package, schemas, links, examples, evals, secrets, and checksums;
- `run_static_evals.py`: run deterministic utility checks and write a new report beneath a separately authorized output directory;
- `package_release.py`: fail closed for candidate or source-unbound packages and build only after separate release authorization is effective.

The candidate skill does not have shell or Python execution permission. A caller must
authorize each utility invocation independently; selecting this skill is insufficient.
