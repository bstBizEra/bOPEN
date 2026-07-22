# bOPEN — Open Business Platform Kernel

This repository bootstrap pack establishes the governed foundation for bOPEN: a multi-tenant, multi-industry platform kernel that will support products such as bPro, bFleet, PropTech, bERP, LDM and future industry solutions.

## Current authorization boundary

This pack is approved for:

- repository and documentation bootstrap;
- root and scoped `AGENTS.md` installation;
- research workspace creation;
- CI, security and evidence controls;
- requirements, architecture and contract drafting;
- clean-room research execution.

It is **not** approval to implement the production platform kernel. Production implementation requires the BOPEN-RES-001 `G7` clean-room release and approval of the applicable normative artifacts.

## Governing lifecycle

```text
PLATFORM
  -> PRINCIPAL
  -> TENANT
  -> MEMBERSHIP
  -> CONTEXT
  -> AUTHORIZATION
  -> ENTITLEMENT
  -> CAPABILITY
  -> RESOURCE / ACTION
  -> EVENT / AUDIT / USAGE
```

## Start here

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`BOPEN-BOOT-001.md`](BOPEN-BOOT-001.md).
3. Read [`docs/README.md`](docs/README.md).
4. Review [`docs/DOCUMENT-STATUS.md`](docs/DOCUMENT-STATUS.md).
5. Select an accepted work package from [`docs/work-packages/WORK-PACKAGE-REGISTER.md`](docs/work-packages/WORK-PACKAGE-REGISTER.md).
6. Run `python tools/validate_repository.py` before and after changes.
7. Resolve shared skills through [`docs/registers/skill-registry.json`](docs/registers/skill-registry.json) and [`.agents/SKILL-ROUTING.md`](.agents/SKILL-ROUTING.md); run `python tools/validate_skill_registry.py` for integrity and `--resolve-workflow <name>` before execution.

## Repository zones

| Zone | Purpose | Production code permitted? |
|---|---|---:|
| `research/upstream/` | Pinned external research clones | No |
| `research/findings/` | Evidence, observations and synthesis | No |
| `docs/` | Normative and supporting documentation | Documentation only |
| `contracts/` | Approved machine-readable contracts | Only after approval |
| `services/`, `packages/`, `apps/` | Clean implementation | Only after implementation gate |

## License status

No open-source license is granted by this bootstrap pack. See [`LICENSE`](LICENSE) and [`docs/00-governance/license-strategy.md`](docs/00-governance/license-strategy.md).
