# BOPEN-RES-001 Artifact Set

This directory is the execution package for **BOPEN-RES-001 — bOPEN Open-Source Platform Kernel Research, Clone Governance & Clean-Room Study Plan v1.0**.

## Package objective

Study BoxyHQ SaaS Starter Kit as the first bOPEN research clone while preserving source provenance, license controls, evidence traceability and clean-room implementation boundaries.

## First target

- Repository: `boxyhq/saas-starter-kit`
- Pin: `abc9b686823cbfb4973c79bc36fea37a3244be6c`
- Reference release: `v1.6.0`
- License observed at pin: Apache-2.0
- Baseline date: 2026-07-12

## Start here

1. Read `BOPEN-RES-001.md`.
2. Review `00-governance/clean-room-boundary.md` and `00-governance/license-compliance-plan.md`.
3. Run the appropriate script under `scripts/` to create the isolated study clone.
4. Execute work packages in `02-execution/work-package-register.md`.
5. Record source evidence using `03-templates/source-observation-template.md`.
6. Do not transfer upstream code into a bOPEN implementation repository.

## Package structure

```text
BOPEN-RES-001/
├── BOPEN-RES-001.md
├── RESEARCH-MANIFEST.json
├── RESEARCH-STATUS.md
├── RESEARCH-COVERAGE.md
├── CHANGELOG.md
├── 00-governance/
├── 01-boxyhq/
├── 02-execution/
├── 03-templates/
└── scripts/
```

## Research chain

```text
PLATFORM -> PRINCIPAL -> TENANT -> MEMBERSHIP
-> CONTEXT -> AUTHORIZATION -> ENTITLEMENT -> CAPABILITY
```

## Control principle

The upstream clone is a research instrument. Approved bOPEN requirements, contracts and ADRs are the only inputs permitted into clean implementation.
