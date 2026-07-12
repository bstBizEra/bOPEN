# Clean-Room Boundary

## Zones

### Zone A — Upstream research

Permitted:
- clone and run upstream code;
- inspect code, schema, tests and documentation;
- capture narrowly scoped evidence;
- produce observations and lifecycle traces.

Prohibited:
- adding upstream source to bOPEN production packages;
- removing upstream notices;
- presenting modified upstream code as original bOPEN code.

### Zone B — Architecture synthesis

Permitted inputs:
- reviewed evidence records;
- capability findings;
- gap records;
- security and license review notes.

Outputs:
- bOPEN requirements;
- bOPEN terminology;
- architecture options;
- ADR candidates;
- testable contracts.

### Zone C — Clean implementation

Permitted inputs:
- approved requirements;
- approved contracts and schemas created for bOPEN;
- approved ADRs;
- bOPEN test scenarios.

Prohibited inputs:
- upstream source files;
- copied functions, migrations, UI components or tests;
- translated or mechanically renamed upstream code.

## High-risk trigger

A clean-room reviewer is mandatory where a proposed bOPEN implementation is structurally close to an upstream file, migration, API route, permission table or user flow.

## Provenance statement

Every implementation pull request derived from BOPEN-RES-001 shall state which approved requirement/ADR it implements. It shall not cite an upstream source file as its implementation specification.
