# Decision and Review Model

## Decision drivers

Score material options against the drivers that apply:

| Driver | Questions |
|---|---|
| Boundary integrity | Does the option preserve platform/product/module ownership? |
| Tenant isolation | Can cross-tenant access be prevented and tested? |
| Authorization | Are context, permission, entitlement, and approval distinct? |
| Consistency | What transaction and concurrency guarantees exist? |
| Recoverability | Can partial failure, retry, rollback, and replay be controlled? |
| Operability | Can the system be observed, supported, backed up, and restored? |
| Portability | Are provider-specific assumptions behind owned contracts? |
| Supply chain | Are dependencies, provenance, signatures, and revocation controlled? |
| Cost | What are build, run, migration, and governance costs? |
| Reversibility | Can the decision be changed without unacceptable data or service risk? |
| P0 fit | Is the complexity justified in the current phase? |

Use a 1–5 score only when it clarifies tradeoffs. Do not let arithmetic replace architectural judgment.

## Decision states

- `proposed`: drafted for review;
- `accepted`: approved by the designated authority;
- `superseded`: replaced by a later ADR;
- `deprecated`: retained temporarily but scheduled for removal;
- `rejected`: evaluated and not selected.

## Review verdicts

- `RECOMMEND_APPROVAL`: all mandatory controls pass with sufficient evidence.
- `RECOMMEND_APPROVAL_WITH_CONDITIONS`: no non-waivable control fails; conditions have owner, deadline, and verification.
- `RECOMMEND_RETURN_FOR_REVISION`: material gaps need design changes.
- `RECOMMEND_REJECTION`: the option conflicts with the target architecture or creates unacceptable cost/risk.
- `RECOMMEND_BLOCK`: tenant isolation, authorization, evidence integrity, or another non-waivable control fails.

Every disposition is advisory. An effective decision requires a separate attributable
authority record bound to the reviewed subject.

## Required review findings

Each finding contains:

```text
finding_id
severity: info | low | medium | high | critical
control
observation
risk
required_action
owner
due_date
evidence_needed
status
```

A high or critical finding cannot be closed by narrative acceptance alone. Evidence is required.

## Change control

A material deviation requires an ADR when it changes:

- tenant or principal trust boundaries;
- data isolation profile;
- authorization or entitlement semantics;
- source of truth or ownership of a domain concept;
- module/package contract;
- transaction or event-delivery guarantees;
- provider lock-in or replacement seam;
- approval, audit, retention, or evidence rules;
- P0 topology or production exit gate.
