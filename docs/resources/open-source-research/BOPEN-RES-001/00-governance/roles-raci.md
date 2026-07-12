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
