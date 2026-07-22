# SKILLS.md — bOPEN Shared Skill Registry Index v0.2

**Document ID:** BOPEN-SKILL-001  
**Version:** 0.2  
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

## Installed candidate catalog

The complete machine-readable list is `docs/registers/skill-registry.json`. It binds
34 repo-local packages by canonical ID, version, owner, risk class, path,
dependencies, activation decision and package digest. Every entry remains
`candidate` with `activation: inactive`.

Use `.agents/SKILL-ROUTING.md` to choose the narrowest specialist and distinguish
orchestrators from mandatory specialist controls. The registry validator rejects missing,
duplicate, renamed, path-escaped, digest-drifted, dependency-invalid,
manifest-mismatched, implicitly invocable or workflow-ineligible skills.

Admission of the full-pack candidates is additive:

- the richer existing `bopen-architecture` package remains canonical;
- `bopen-threat-model` is a merged successor candidate retaining confused-deputy and
  human residual-risk acceptance controls;
- Git delivery, repository harness, skill authoring/admission, release readiness and
  P0 conformance remain explicit-only;
- focused identity, tenancy, authorization, entitlement, RLS, event/outbox, portal and
  bPro skills complement rather than replace existing architecture and verification skills.

## Universal repository distribution

The canonical cross-harness package location is `.agents/skills/<skill-name>/`, and
`docs/registers/skill-registry.json` is the machine-readable catalog. Codex, Claude
Code, Antigravity, Copilot and admitted harnesses MUST consume the same registered
package version through their checked runtime-specific discovery adapter; user-scoped copies
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
