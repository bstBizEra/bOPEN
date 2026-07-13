# Contributing to bOPEN

## Entry requirements

Contributions must be associated with an accepted work package and comply with all applicable `AGENTS.md` files.

## Branch convention

```text
feat/<work-package>-<summary>
fix/<work-package>-<summary>
docs/<work-package>-<summary>
research/<work-package>-<summary>
chore/<work-package>-<summary>
```

## Commit convention

```text
<type>(<scope>): <summary> [<work-package>]
```

Examples:

```text
docs(governance): add decision escalation process [BOOT-P0-03]
research(boxyhq): record invitation evidence [RES-P0-07]
```

## Pull request requirements

- work-package ID and acceptance criteria;
- governing artifacts/requirements/ADRs;
- risk and security impact;
- tests and validation results;
- evidence path;
- migration/rollback details where applicable;
- documentation updates;
- clean-room declaration.

## Review requirements

Two approvals are recommended for tenancy, authorization, security, entitlement, contracts and migrations. At least one reviewer must be a designated owner in `.github/CODEOWNERS`.
