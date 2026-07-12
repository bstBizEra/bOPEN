# Contract Governance

Contracts have owner, status, semantic version, compatibility rule and deprecation policy. Draft contracts are not stable dependencies. Breaking changes require major version or approved migration. Errors are explicit and machine-readable.

Machine-readable draft contracts must include `status: draft` metadata. Run `python tools/validate_contracts.py` before treating a schema or manifest example as an implementation input.
