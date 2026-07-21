# bOPEN — Open Business Platform Kernel

This repository bootstrap pack establishes the governed foundation for bOPEN: a multi-tenant, multi-industry platform kernel that will support products such as bPro, bFleet, PropTech, bERP, LDM and future industry solutions.

## Current authorization boundary

Program Goal v0.2 is controlled as [`BOPEN-GOAL-001`](docs/01-product/BOPEN-GOAL-001-DRAFT.md) under proposed work package [`GOV-P0-01`](docs/work-packages/GOV-P0-01.md). The goal, program authority baseline, lifecycle crosswalk and registers are drafts; `PG-G0` is `NOT_READY` and they provide no implementation or release authority.

This pack is approved for:

- repository and documentation bootstrap;
- root and scoped `AGENTS.md` installation;
- research workspace creation;
- CI, security and evidence controls;
- requirements, architecture and contract drafting;
- clean-room research execution.

It is **not** approval to implement the production platform kernel. Production implementation requires the BOPEN-RES-001 `G7` clean-room release and approval of the applicable normative artifacts.

## Current development-readiness lane

`DEV-P0-01` makes the multi-tenant boundary executable as draft contracts and negative tests: principal-to-tenant membership, server-validated active context, tenant-owned resources, deny-by-default authorization, API isolation, database isolation, and correlated audit evidence. This is contract readiness only; it does not open the production implementation gate.

`BOPEN-RES-001` Research Sprint R0 has executed RES-P0-01 through RES-P0-03 with two isolated operators. G0-G2 pass with recorded conditions; R1 lifecycle research is next, while G3-G7 and production implementation remain closed.

Research Sprint R1 has now executed the static RES-P0-04 through RES-P0-07 trace. Repository orientation is complete at E2; identity, membership and invitation runtime acceptance remains incomplete. G3-G7 and production implementation remain closed pending the isolated synthetic G3 runtime pack documented in EVD-RES-003.

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
