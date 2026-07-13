# EVD-RES-002 - Research R0 control establishment

**Work packages:** `RES-P0-01`, `RES-P0-02`, `RES-P0-03`

**Gates:** G0, G1, G2

**Generated:** 2026-07-13

**Base:** `5ec86dc465da1d8583920cbf4834451efb0c9d13`

**Agent:** bCodex (Senior Architect), with ARCHI/ENGIN/REV three-pane review

## Scope

Establish the controlled research workspace, independently verify the approved BoxyHQ source and license baseline, and reproduce the pinned build/test baseline twice without introducing upstream source into bOPEN.

## Governance receipt

- `DEC-0009` resolves the clone-location conflict in favor of external ephemeral operator workspaces.
- Sponsor/gate authority: repository sponsor with bCodex acting as SARCHI.
- Research lead: ARCHI pane `019f5919-3ca8-7c11-835b-33ca3d2a154e`.
- Primary operator: ENGIN pane `019f5919-7d1a-7dd1-a684-57bf738382aa`.
- Independent security/evidence reviewer and second operator: REV pane `019f5919-bcf1-7913-962c-72911907d704`.
- License/compliance owner: SecB through `bstBizEra/bstAH#138`; legal interpretation remains pending.

## Provenance result

Both isolated operators verified:

| Field | Value |
|---|---|
| Source | `https://github.com/boxyhq/saas-starter-kit.git` |
| Source ID | `SRC-BOX-001` |
| Commit | `abc9b686823cbfb4973c79bc36fea37a3244be6c` |
| Checkout | Detached and clean |
| Public/archive observation | Public; not archived on 2026-07-13 |
| License | Apache-2.0 |
| License SHA-256 | `f9f9a6236f9f12c14ce7294a58575c19fc16bb1c24dcdc91e2ae868b2b21a41a` |
| Lockfile | `package-lock.json` |
| Lock SHA-256 | `b8ec0535883a6bb186a6a633979a497b12f110463da86ae0122ddd3426d219e8` |
| Local patches | None |
| Credential prompting | Disabled |

## Reproduction result

An initial diagnostic with Node `v24.12.0` and npm `11.6.2` failed because npm 11 considered the pinned package-lock inconsistent. The governed baseline therefore pins npm `10.9.2`; both operators then reproduced the same result:

| Command | ENGIN | REV | Interpretation |
|---|---:|---:|---|
| npm 10.9.2 clean install with lifecycle scripts disabled | 0 | 0 | PASS |
| explicit Prisma Client generation | 0 | 0 | PASS |
| format check | 1 | 1 | Known upstream failure on 300 files |
| lint | 0 | 0 | PASS with one warning |
| type check | 0 | 0 | PASS |
| unit tests | 0 | 0 | PASS, 1 suite / 4 tests |
| Next.js production build | 0 | 0 | PASS |

Both final upstream trees remained clean. No `.env` file was created. Both raw evidence stores passed the bOPEN credential-pattern scan, and normalized provenance and baseline results matched.

## External raw evidence custody

Raw source and logs are intentionally not committed. They remain under:

- `C:\laragon\www\bopen-research\ENGIN-R0-20260713`
- `C:\laragon\www\bopen-research\REV-R0-20260713`

Evidence-manifest SHA-256 values:

- ENGIN: `912018130b40ac4469e1e191013358bfd4023ce96c61bf2edb1ca08b1375712e`
- REV: `a2a7612cf1b6a4a454105a2aa9caf25ed50a2e8eb0633eeb116ee580792e3ff8`

Each manifest covers 24 raw evidence files. Wall-clock timestamps, operator IDs and raw build text are not expected to hash identically; normalized contract fields and exit matrices do.

## Gate decision

- **G0: PASS WITH CONDITIONS.** Named roles, isolated roots, no-production-data rule and evidence controls are active. SecB legal interpretation remains pending.
- **G1: PASS WITH CONDITIONS.** Exact source, commit, license and lock integrity were independently reproduced. No redistribution or derivative-use approval is granted.
- **G2: PASS WITH CONDITIONS.** Two operators reproduced the same baseline. npm 10.9.2 and the known upstream format failure are explicit constraints.

G3-G7 remain open. This receipt authorizes R1 research planning only and does not authorize production implementation.

## Clean-room and security declaration

No upstream source, dependency tree, raw log, credential, personal data, database, or environment file was copied into bOPEN. The bOPEN `research/upstream/` directory remains source-free. Only sanitized facts, hashes, decisions and exit outcomes are recorded here.
