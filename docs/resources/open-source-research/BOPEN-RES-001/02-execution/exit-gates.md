# Exit Gates and Evidence Requirements

## G0
- [ ] Sponsor and research lead assigned.
- [ ] Security and license reviewers assigned.
- [ ] Isolated workspace approved.

## G1
- [ ] Commit SHA verified.
- [ ] License file checksum recorded.
- [ ] Upstream archived/public status recorded.
- [ ] Acquisition/lineage note recorded.

## G2
- [ ] Clone reproducible.
- [ ] Build/test logs captured.
- [ ] Environment and lock checksums captured.

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
