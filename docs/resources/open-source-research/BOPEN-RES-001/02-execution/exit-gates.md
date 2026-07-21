# Exit Gates and Evidence Requirements

## G0
- [x] Sponsor and research lead assigned. See EVD-RES-002.
- [x] Security and license reviewers assigned. SecB legal interpretation remains a recorded condition.
- [x] Isolated workspace approved under DEC-0009.

## G1
- [x] Commit SHA verified independently by ENGIN and REV.
- [x] License file checksum recorded and matched twice.
- [x] Upstream archived/public status recorded with observation date.
- [x] Acquisition/lineage note recorded as provenance context only.

## G2
- [x] Clone reproducible in separate ENGIN and REV roots.
- [x] Build/test logs captured in external raw evidence stores.
- [x] Environment and lock checksums captured and normalized in EVD-RES-002.

## G3
- [ ] Self-registration trace E3/E4.
- [ ] Invitation trace E3/E4.
- [ ] Membership lifecycle trace E3/E4.

## G4
- [ ] Context selection trace E4.
- [ ] Foreign-team access denied.
- [ ] Removed/suspended membership behavior tested.

## G5
- [ ] Security checklist completed.
- [ ] License review completed.
- [ ] Entitlement gap approved.
- [ ] Critical risks resolved/accepted.

## G6
- [ ] ADOPT/ADAPT/REJECT/DEFER matrix approved.
- [ ] Requirement and ADR candidates cite evidence.
- [ ] No unsupported architecture claims remain.

## G7
- [ ] Handoff contains no upstream source.
- [ ] Clean-room reviewer approval recorded.
- [ ] Implementation tests are expressed in bOPEN terminology.

## R0 gate decision - 2026-07-13

| Gate | Decision | Conditions |
|---|---|---|
| G0 | PASS WITH CONDITIONS | Roles, two external workspaces and evidence controls are assigned; SecB legal interpretation remains pending. |
| G1 | PASS WITH CONDITIONS | Origin, exact pin, public/not-archived state, license and lock hashes match twice; redistribution/legal approval is not granted. |
| G2 | PASS WITH CONDITIONS | Two operators reproduce the declared baseline. npm 10.9.2 is required because npm 11 rejects the lock; upstream format check exits 1 while lint, types, four unit tests and build pass. |

G3 through G7 remain open. No implementation handoff is authorized.

## G3 design checkpoint - 2026-07-21

- [x] Non-executing synthetic runtime design contract created.
- [x] Mandatory identity, membership and invitation case inventory made machine-verifiable.
- [x] Secure oracle separated from observed upstream behavior.
- [x] Report semantics capped at `DESIGN_READY_FOR_AUTHORITY_REVIEW`.
- [ ] DEC-0011 runtime authorization approved and effective.
- [ ] Exact dependencies, images, paths, networks, retention and operators bound.
- [ ] ENGIN E3 runtime evidence captured.
- [ ] Independent REV E4 reproduction accepted.

This checkpoint does not alter the three unchecked G3 gate items above.
