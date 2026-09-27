# MODULES.md — bOPEN Module Portfolio and Harness Allocation v0.1

## Layers

```text
Platform Kernel
→ Common Business Foundation
→ Shared Capability Packages
→ Industry Packs
→ Product Composition
→ Tenant Extensions
```

## P0 work packages and default allocation

| Work package | Scope | Maker lead | Checker lead | Specialist verifier |
|---|---|---|---|---|
| WP-01 | Repository and governance | Codex | Claude | Human governance owner |
| WP-02 | Principal and authentication adapter | Codex | Claude | Security reviewer |
| WP-03 | Tenant, membership and active context | Codex | Claude | Tenant-isolation verifier |
| WP-04 | Authorization and PostgreSQL RLS | Codex | Claude | Independent security/human verifier |
| WP-05 | Product, module, capability and entitlement | Codex | Claude | Contract-test verifier |
| WP-06 | Portal foundations | Antigravity + Codex | Claude | Browser/E2E verifier |
| WP-07 | Events, audit and transactional outbox | Codex | Claude | Recovery/replay verifier |
| WP-08 | bPro reference integration | Codex + Antigravity | Claude | Independent conformance reviewer |

## Parallelization rule

Parallelize modules only when their contracts and shared schemas are frozen. Shared
contract changes are completed first by the contract owner, then consumed by separate
worktrees.

## Human-only decisions

- architecture and technology freeze;
- acceptance of security risk or policy exception;
- production secret access;
- destructive production migration;
- release and rollback authority;
- tenant-isolation conformance verdict;
- activation of regulated or sensitive workloads.
