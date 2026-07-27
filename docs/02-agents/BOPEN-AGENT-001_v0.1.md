# BOPEN-AGENT-001 — Multi-Agent Authority, Roles and Harness Operating Model v0.1

**Status:** Draft; advisory only

## 1. Principle

Use multiple harnesses to create diversity of implementation and review, not competing
sources of truth. All harnesses inherit root governance and work through registered work
items, isolated worktrees, evidence envelopes and maker–checker separation.

## 2. Agent role catalog

### Governance Lead

Maintains authority, gates, registers, exceptions and conformance readiness.

### Product and Requirements Analyst

Converts goals and stakeholder needs into testable requirements and acceptance criteria.

### Domain Architect

Defines bounded contexts, entities, state machines and domain ownership.

### Platform Architect

Protects kernel boundaries, module contracts, provider seams and evolution strategy.

### Security Architect

Threat models identity, authorization, credentials, supply chain and operational risks.

### Tenant-Isolation Architect/Verifier

Owns context propagation, RLS patterns and cross-tenant negative verification.

### Data Architect

Owns canonical schemas, migration, classification, retention, residency and quality.

### Backend Maker

Implements bounded server, database, API, job and event changes.

### Portal Maker

Implements platform, user, tenant, work and developer portal experiences.

### Integration Engineer

Implements provider adapters, API clients, webhooks and external contracts.

### Test Engineer

Builds unit, component, contract, integration, E2E and regression coverage.

### Evidence Auditor

Checks traceability, reproducibility, completeness and hashes.

### Release Coordinator

Assembles release artifacts and readiness, but does not self-authorize production.

### Operations Engineer

Owns monitoring, backup, restoration, incident, capacity and rollback readiness.

## 3. Registration fields

```yaml
agent_id:
display_name:
harness:
provider:
model_or_runtime:
owner:
roles: []
allowed_repositories: []
allowed_paths: []
allowed_tools: []
network_policy:
credential_policy:
data_classification_limit:
approval_mode:
evidence_destination:
effective_from:
expires_at:
status:
```

## 4. Separation of duties

Material implementation and final review must be performed by different registered
actors. High-risk changes require specialized verification and human approval.

## 5. Session contract

Every session begins with a context receipt and ends with a handoff. A session that
cannot provide evidence has not completed governed work.
