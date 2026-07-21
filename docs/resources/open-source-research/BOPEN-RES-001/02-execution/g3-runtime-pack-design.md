# G3 Synthetic Runtime Pack Design

**Document ID:** BOPEN-RES-001-G3-DESIGN

**Version:** 0.1

**Status:** Design ready for authority review; execution not authorized

**Owner:** bCodex (Senior Architect)

**Issue/update date:** 2026-07-21

**Governing artifacts:** BOPEN-RES-001, DEC-0009, DEC-0011 (proposed)

**Dependent artifacts:** RES-P0-05, RES-P0-06, RES-P0-07, EVD-RES-003, EVD-RES-004

**Source:** EVD-RES-003 R1 findings at BoxyHQ pin `abc9b686823cbfb4973c79bc36fea37a3244be6c`

**Timestamp:** 2026-07-21T19:15:00+07:00

**Agent ID:** `/root` (bCodex/Senior Architect)

## Purpose

Define the fail-closed controls and mandatory case inventory for a future isolated, synthetic G3 runtime study. This artifact is a design contract only. It does not install dependencies, start services, load upstream code, access a network, collect runtime evidence, or decide G3.

## Authority boundary

The current authority permits research design and validation. It does not permit runtime execution. Before any runner, container, database, identity provider, event sink, or upstream process is started, the following must all exist:

1. DEC-0011 is approved with named ARCHI, ENGIN, REV, Security, and License owners.
2. A bounded execution authorization identifies the exact upstream pin, design-contract hash, permitted paths, operator identities, start and expiry timestamps, network policy, retention policy, and rollback/cleanup procedure.
3. Dependency locks, license hashes, image digests, and tool versions are resolved and independently verified. A mutable tag is not sufficient.
4. Two isolated DEC-0009 operator roots are assigned. ENGIN produces E3 evidence; REV independently reproduces E4 evidence.
5. Synthetic-only fixtures and secret scanning are verified before execution.

Any absent, expired, mismatched, or ambiguous authority field is a hard stop.

## Isolation design

| Surface | Required control | Current design state |
|---|---|---|
| Upstream source | Detached exact pin in external DEC-0009 root; no source copied into bOPEN | Pin fixed; execution pending authority |
| PostgreSQL | Synthetic database, unique per operator/run, no host or production credentials | Image digest and schema bootstrap pending authority |
| Mail | Local sink with synthetic recipients only and no outbound relay | Digest pending authority |
| CAPTCHA | Deterministic local substitute; no external verification service | Adapter specification pending authority |
| OAuth/SAML | Local synthetic providers, fixed identities, no real IdP federation | Digests and fixtures pending authority |
| Events/audit | Local Svix/Retraced-compatible capture substitutes with fault injection | Digests and observation schema pending authority |
| Network | Deny outbound by default; explicit internal allowlist only | Exact policy pending Security approval |
| Evidence | Sanitized structured receipts only; raw logs remain external | Contract defined; runtime receipts absent |
| Retention | Per-run expiry, verified cleanup receipt, legal hold override only by named authority | Duration pending authority |

## Oracle separation

Each case records two distinct fields:

- `secure_oracle`: the expected security property expressed independently in bOPEN terms;
- `observed_upstream`: the measured result from the pinned study target.

The observed target may securely allow, securely deny, fail and roll back, fail after partial mutation, or be unobservable. An insecure upstream observation is valid research evidence and must not be rewritten to match the oracle. It cannot become a bOPEN requirement without later governed synthesis.

Allowed normalized outcomes are `ALLOW`, `DENY`, `ERROR_ROLLED_BACK`, `ERROR_PARTIAL`, and `UNOBSERVABLE`. Each result requires a stable reason code and correlation identifier.

## Mandatory lifecycle coverage

The machine-readable design contract is authoritative for case IDs and required observations. It must cover at minimum:

- identity: registration, canonicalization/duplicates, verification, authentication, lockout, password reset, session invalidation, account linking/collision/unlinking, and API-key lifecycle;
- tenancy and membership: team creation/update/delete, atomic owner creation, role denial, cross-team denial, removal/leave, last-owner protection, concurrent owner mutation, and immediate session behavior;
- invitations: email and link creation/fetch/acceptance, allowed domains, expiry, revocation, sequential replay, concurrent acceptance, accept-versus-revoke, partial failure, event payload/order/correlation, and audit evidence.

The validator must reject a design that omits any mandatory case, permits real data or external services, uses mutable dependencies, merges oracle and observation, or claims runtime/G3 success.

## Evidence levels and decision rules

| Level | Meaning for this pack |
|---|---|
| E2 | Static design, path, declaration, and contract evidence only |
| E3 | One authorized operator completes deterministic database-backed probes |
| E4 | A separate reviewer independently reproduces the probes and hashes |

Design validation can reach only `DESIGN_READY_FOR_AUTHORITY_REVIEW`. It must always emit `runtime_executed=false`, `g3_pass=false`, and `production_implementation_authorized=false`.

G3 remains open until all mandatory identity, membership, and invitation cases have accepted E3 and independent E4 evidence, every partial/unobservable result is dispositioned, manifests and secret scans pass, and the designated authority records a separate gate decision.

## Cleanup and rollback design

An authorized future run must stop services, remove only its explicitly named synthetic volumes and networks, preserve required sanitized receipts, secret-scan retained evidence, and issue a cleanup receipt bound to the run ID. Cleanup must never use a workspace root, unresolved variable, wildcard target, or shared service. Failure to prove the target path leaves cleanup blocked for manual review.

## Explicit non-claims

This design does not pass G3, complete RES-P0-05/06/07 acceptance, authorize RES-P0-08, select production technology, approve source reuse, resolve license obligations, or authorize production kernel implementation.
