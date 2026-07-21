# EVD-RES-004 - G3 Synthetic Runtime Pack Design

**Document ID:** EVD-RES-004

**Version:** 0.1

**Status:** Design evidence; authority review required; G3 open

**Owner:** bCodex (Senior Architect)

**Issue/update date:** 2026-07-21

**Governing artifacts:** BOPEN-RES-001, DEC-0009, DEC-0011 (proposed)

**Work packages:** RES-P0-05, RES-P0-06, RES-P0-07

**Source:** EVD-RES-003 and the repository-controlled G3 design contract

**Timestamp:** 2026-07-21T19:15:00+07:00

**Agent ID:** `/root` (bCodex/Senior Architect)

## Evidence scope

This evidence records only the creation and deterministic validation of a non-executing G3 runtime-pack design. The package defines mandatory lifecycle cases, isolation requirements, secure-oracle separation, evidence levels, authority prerequisites, and fail-closed report semantics.

## Controlled artifacts

- `docs/resources/open-source-research/BOPEN-RES-001/02-execution/g3-runtime-pack-design.md`
- `research/sources/boxyhq-g3-runtime-design.schema.json`
- `research/sources/boxyhq-g3-runtime-design.json`
- `tools/validate_research_g3_design.py`
- `tools/report_research_g3_design.py`
- `tests/governance/test_research_g3_design_controls.py`
- `artifacts/validation/research-g3-design-readiness.md`

## Validation outcome

Maker validation on 2026-07-21 produced:

| Check | Result |
|---|---|
| `python tools/validate_repository.py` | PASS; 35 mandatory paths and governance invariants |
| `python tools/validate_contracts.py` | PASS; 9 machine-readable contract files |
| `python tools/validate_research_g3_design.py` | PASS; 19 mandatory families and 126 stable cases |
| Focused G3 negative tests | PASS; 17 tests |
| `python tools/check_clean_room.py` | PASS |
| `python tools/check_secrets.py` | PASS |
| `python tools/check_supply_chain.py` | PASS |
| Full `tests/test_*.py` discovery | PASS; 96 tests |
| Readiness report | `DESIGN_READY_FOR_AUTHORITY_REVIEW`; runtime/G3/production false |

The generated readiness report binds contract SHA-256 `489003f4ae0c6400fc3d8a98625ded20b00ff53b63b02871cf75d915139bca32`, schema SHA-256 `a73e256ca407503b06d4a657d2b938ba905818eca031ecb0d283820a7d100130`, and validator SHA-256 `e55fd524ee7a00419e49c5e6a1ff8bba8778315d4070b23e419cd003b8f866d4`. Exact-commit independent checker disposition remains required before publication or acceptance.

## Gate decision

**G3 remains OPEN.** The strongest allowed report state is `DESIGN_READY_FOR_AUTHORITY_REVIEW`. Required machine-readable flags are `runtime_executed=false`, `g3_pass=false`, and `production_implementation_authorized=false`.

No container, database, upstream process, external service, runtime probe, or raw runtime evidence was started or collected for this design evidence.

## Independent checker receipt - 2026-07-21

Independent checker `/root/kernel_readiness_audit` reviewed exact maker SHA `e323ef9b6241cd6166389cfd12a593bc88d143bc` and returned `ACCEPT_EXACT_SHA` for the non-executing G3 design package. The checker independently reproduced 16/16 focused controls, 95/95 full tests, repository/contracts/clean-room/secrets/supply-chain checks, the 55-record research inventory, exact report hashes, and rejection of all nine previously reproduced fail-open mutations.

The acceptance is design-only. DEC-0011 remains proposed and ineffective; E3/E4 runtime evidence is absent; G3, RES-P0-08, clean-room handoff, and production implementation remain unauthorized.

## CI portability repair - 2026-07-21

Gitea Actions run 50/job 79 reproduced a stale-inventory failure on Linux because the original inventory hashed Windows working-tree line endings. The bounded repair normalizes controlled text files to LF before hashing, adds a cross-platform stability test, and retains exact content sensitivity. No test or security control was weakened.

## Residual risks and required decisions

- DEC-0011 is proposed and not effective.
- Exact dependency and image digests, network allowlists, retention duration, and named operators remain unresolved.
- Legal review remains pending for any redistribution or derivative-use intent.
- Runtime evidence for identity, membership, and invitations is absent.
- A passing design validator cannot be used as a G3 approval or implementation authority.
