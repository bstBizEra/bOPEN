# Roles and RACI

| Activity | Sponsor | Research Lead | Source Analyst | Security | License/Legal | Architect | Evidence Custodian | Clean Implementer |
|---|---|---|---|---|---|---|---|---|
| Approve scope | A | R | C | C | C | C | I | I |
| Pin upstream | I | A | R | C | C | I | R | I |
| Run clone | I | A | R | C | I | I | C | I |
| Capture evidence | I | A | R | C | I | C | R | I |
| License review | I | C | C | I | A/R | I | C | I |
| Security review | I | C | C | A/R | C | C | I | I |
| Architecture synthesis | I | C | C | C | C | A/R | R | I |
| Gate approval | A | R | C | C | C | R | C | I |
| Clean implementation | I | I | I | C | C | A | C | R |

`A` accountable, `R` responsible, `C` consulted, `I` informed.

## Agent boundary

Research agents may inspect upstream code. Clean implementation agents should receive only approved bOPEN specifications for high-risk components.

## R0 named assignment - 2026-07-13

| Function | Assignment | Evidence responsibility |
|---|---|---|
| Sponsor / gate authority | Repository sponsor; bCodex acting as SARCHI under the instruction to proceed | Scope approval and G0-G2 decision |
| Research lead / architect | ARCHI pane `019f5919-3ca8-7c11-835b-33ca3d2a154e` | Scope, interpretation and clean-room boundary |
| Primary source operator | ENGIN pane `019f5919-7d1a-7dd1-a684-57bf738382aa` | First isolated reproduction |
| Security/evidence reviewer and second operator | REV pane `019f5919-bcf1-7913-962c-72911907d704` | Independent reproduction, secret and provenance checks |
| License/compliance owner | SecB through `bstBizEra/bstAH#138` | Legal interpretation and redistribution review |

SecB assignment satisfies the G0 ownership requirement, but legal approval remains pending. R0 performs research-only inspection and does not authorize redistribution or source reuse.
