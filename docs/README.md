# bOPEN Documentation System

## Document classes

| Class | Meaning |
|---|---|
| Normative | Approved requirement, architecture, policy or contract |
| Draft normative | Candidate specification not yet binding |
| ADR | Durable architecture decision |
| Operational | Runbook, procedure or environment control |
| Evidence | Test, research or review record |
| Informative | Explanation or orientation with no normative force |

## Control rules

- Each controlled artifact has an ID, version, status and owner.
- Approved documents supersede earlier versions explicitly.
- Drafts cannot authorize production implementation.
- Machine-readable contracts identify status and version.
- Traceability links requirements to decisions, work packages, implementation and evidence.
- `DOCUMENT-MANIFEST.json` is generated/validated by tooling.

## Navigation

- [`00-governance/`](00-governance/) — document, agent and decision governance (see [`AGENT-ALIGNMENT.md`](00-governance/AGENT-ALIGNMENT.md) & [`multi-agent-orchestration.md`](00-governance/multi-agent-orchestration.md))
- [`01-product/`](01-product/) — product vision, matrix, roadmap & phase outline (see [`CAPABILITY-MATRIX.md`](01-product/CAPABILITY-MATRIX.md), [`FUTURE-DEVELOPMENT-PLAN.md`](01-product/FUTURE-DEVELOPMENT-PLAN.md) & [`PHASE-OUTLINE-SPEC.md`](01-product/PHASE-OUTLINE-SPEC.md))
- [`02-requirements/`](02-requirements/) — product requirements
- [`03-architecture/`](03-architecture/) — platform architecture, tech matrix & master plan (see [`TECHNOLOGY-MATRIX.md`](03-architecture/TECHNOLOGY-MATRIX.md) & [`FINAL-TECH-PLAN.md`](03-architecture/FINAL-TECH-PLAN.md))
- [`04-platform/`](04-platform/) — platform domain specifications
- [`05-foundation/`](05-foundation/) — reusable business foundations
- [`06-contracts/`](06-contracts/) — API, event, module, policy and agent contracts
- [`07-security/`](07-security/) — security and supply-chain controls
- [`08-engineering/`](08-engineering/) — repository, delivery standards & language matrix (see [`PROGRAMMING-LANGUAGES-MATRIX.md`](08-engineering/PROGRAMMING-LANGUAGES-MATRIX.md))
- [`09-operations/`](09-operations/) — environments and runbooks
- [`10-products/`](10-products/) — product composition and onboarding
- [`adr/`](adr/) — architecture decisions
- [`work-packages/`](work-packages/) — execution authorization
- [`resources/`](resources/) — controlled research resources
