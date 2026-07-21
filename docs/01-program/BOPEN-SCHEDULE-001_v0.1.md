# SCHEDULE.md — bOPEN Target Program Schedule v0.1

**Timezone:** Asia/Bangkok  
**Start date:** 20 July 2026  
**Planning method:** Gate-based. Dates are targets, not permission to bypass entry or
exit gates.

| Stage | Target dates | Duration | Primary outcome |
|---|---|---:|---|
| G0 Governance bootstrap | 20 Jul–2 Aug 2026 | 2 weeks | Governance pack, authority, registers, technology decision backlog |
| P0 Platform skeleton | 3–30 Aug 2026 | 4 weeks | Repository, CI, evidence, principal/tenant skeleton, RLS proof |
| P1 Core multi-tenant kernel | 31 Aug–11 Oct 2026 | 6 weeks | Identity adapter, tenants, memberships, context, authz, audit/outbox |
| P2 Module and capability platform | 12 Oct–22 Nov 2026 | 6 weeks | Product/module/capability registries, entitlements, SDK and contracts |
| P3 Common business foundation | 23 Nov 2026–3 Jan 2027 | 6 weeks | Party, organization, location, document, asset and shared workflow primitives |
| P4 bPro reference integration | 4 Jan–14 Feb 2027 | 6 weeks | bPro reference flows, portal integration and module-factory validation |
| C0 Independent conformance | 15–28 Feb 2027 | 2 weeks | Security, isolation, recovery, supply-chain and evidence verdict |
| R0 Pilot decision | 1–7 Mar 2027 | 1 week | Human authorization for controlled pilot or remediation decision |

## Weekly operating cadence

### Monday

- Goal and gate review
- Work-item authorization
- Worktree assignment
- Risk and dependency review

### Tuesday–Thursday

- Bounded implementation
- Continuous tests and evidence capture
- Mid-cycle architecture/security consultation for material findings

### Friday

- Independent review
- Verification matrix update
- Integration readiness
- Lessons and blocked-item disposition

## Monthly governance cadence

- Technology and ADR review
- Security and tenancy review
- Module registry review
- Skills promotion and retirement review
- Risk, exception and evidence audit
- Schedule and capacity reforecast

## Gate rule

A phase may start preparation before the prior phase exits, but mutation of controlled
scope requires its own entry-gate authorization. Failed mandatory gates move the phase
to `BLOCKED_REMEDIATION`; dates are reforecasted rather than controls waived.
