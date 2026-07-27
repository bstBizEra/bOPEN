# SKILLS.md — bOPEN Skill Governance and Approved Starter Set v0.1

**Document ID:** BOPEN-SKILL-001  
**Version:** 0.1  
**Status:** PROPOSED  
**Owner:** Architecture and Governance  
**Updated:** 2026-07-22  
**Governing artifacts:** BOPEN-GOV-001; BOPEN-SKILL-REGISTRY-001  
**Evidence:** `.agents/skills/` package validation and repository validation output

## Skill policy

A skill is a reusable, version-controlled procedure containing instructions and optional
scripts, references or templates. Skills support execution; they do not grant authority.

Every skill must declare:

- name, purpose and trigger;
- allowed and prohibited scope;
- required inputs;
- workflow;
- expected outputs;
- verification;
- evidence;
- failure and stop conditions;
- owner, version and review date.

## Initial approved skill candidates

| Skill | Purpose | Primary users |
|---|---|---|
| `bopen-architecture` | Design, research, review and govern bOPEN platform architecture and implementation controls | All approved harnesses |
| `bopen-governance-check` | Validate authority, scope, gates and controlling artifacts | All harnesses |
| `bopen-requirement-to-work-item` | Convert an approved requirement into a bounded work contract | Claude, Codex |
| `bopen-module-contract` | Create or validate a module manifest and document set | Claude, Codex |
| `bopen-tenant-isolation-review` | Review tenant context, RLS and negative tests | Claude, Codex verifier |
| `bopen-evidence-envelope` | Produce a complete evidence record | All harnesses |
| `bopen-release-readiness` | Assess gates without granting release authority | Claude, other checker |
| `bopen-portal-verification` | Verify portal routes, context and visible restricted states | Antigravity |
| `bopen-doc-sync` | Detect behavior/documentation drift | Codex, Claude |
| `bopen-threat-model` | Produce bounded threat scenarios and mitigations | Claude |
| `bopen-ci-repair` | Diagnose and repair CI within an authorized work item | Codex, Copilot |

## Universal repository distribution

The canonical cross-harness package location is `.agents/skills/<skill-name>/`, and
`docs/registers/skill-registry.json` is the machine-readable catalog. Codex, Claude
Code, Antigravity, Copilot and admitted harnesses MUST consume the same registered
package version through their runtime-specific discovery adapter; user-scoped copies
are caches or adapters, not independent sources of truth.

Repository availability does not grant authority. A `candidate` with
`activation: inactive` is available for controlled evaluation and advisory use only;
it is not approved, signed, published, production-active or permission-bearing.

## Skill lifecycle

```text
CANDIDATE
→ REVIEWED
→ SANDBOXED
→ EVALUATED
→ APPROVED
→ PUBLISHED
→ MONITORED
→ UPDATED / DEPRECATED / REVOKED
```

A skill may not self-promote. Production-impacting scripts require code review,
sandbox evaluation, dependency review and explicit approval.
