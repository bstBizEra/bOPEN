# EVD-RES-003 - R1 Core Relationship Lifecycle Trace

**Document ID:** EVD-RES-003

**Version:** 1.0

**Status:** Accepted research evidence; G3 open

**Owner:** bCodex (Senior Architect)

**Issue/update date:** 2026-07-13

**Governing artifacts:** BOPEN-RES-001, DEC-0009

**Work packages:** RES-P0-04, RES-P0-05, RES-P0-06, RES-P0-07
**Source/commit:** `boxyhq/saas-starter-kit` at `abc9b686823cbfb4973c79bc36fea37a3244be6c`

## Procedure

1. ARCHI traced repository paths for registration, login/session, team, membership and invitation lifecycles in the pinned external checkout.
2. ENGIN independently traced identity and principal behavior, then ran the existing Jest suite, schema validation, lint/type checks and a no-execution Playwright inventory.
3. REV independently traced team, membership and invitation behavior, then ran the existing Jest suite, lint/type checks and static transaction/test probes.
4. The tracked R1 validator verified 26 sanitized path/marker observations against each detached, clean checkout.
5. The tracked runner cleared ambient secret-bearing variables and executed only `playwright test --list`. It did not provision a database or execute application tests.
6. Each operator evidence store was secret-scanned and manifest-verified under the DEC-0009 external research root.

## Reproduced receipts

| Operator | Source observations | Declared Playwright tests | Runtime executed | Secret scan | Manifest SHA-256 |
|---|---:|---:|---:|---|---|
| ENGIN-R1-20260713 | 26 | 42 in 9 files | No | 3 payloads, 0 findings | `022ecae4aee03776cba113859c760ea7affcaf8053e669590aaffbbe33bb5b64` |
| REV-R1-20260713 | 26 | 42 in 9 files | No | 3 payloads, 0 findings | `612bb8fec5bfba53d7583580a335ff4aebdad6cae5675257fd5ab96000326a83` |

Each manifest contains four records: the R1 trace receipt, Playwright list receipt, sanitized test-list log and secret-scan receipt. Raw upstream source remains external and is not included.

## Confirmed observations

### Identity and principal

- `User` is the identity root; provider accounts and sessions attach to it, while API keys attach to teams. No broader service, workload, agent, device or system-principal abstraction is present.
- Identity lifecycle surfaces emit optional metrics but no complete actor/tenant/target/outcome/reason/correlation audit chain.
- Email input is validated but not consistently canonicalized before lookup and storage.
- Email verification uses settled parallel operations without checking both outcomes before reporting success.
- Password reset error handling reads a status property that differs from the imported Next.js error shape, converting intended client errors to a fallback server error.
- Password-reset requests disclose missing accounts, permit multiple live tokens, and store reset/verification tokens directly rather than by digest.
- JWT sessions are not revoked by password change/reset. Linked-account collision/unlink behavior, lockout concurrency and API-key authentication/use are not covered by runtime tests.
- API keys are hashed management records, but no observed call site authenticates with them; expiry, last-used, scope, actor and revocation metadata are not enforced as a machine-principal lifecycle.

### Tenant and membership

- Team creation, owner membership creation and webhook application setup are sequential rather than transactionally atomic.
- Last-owner protection is observed for leave, but not equivalently for direct owner removal or demotion; count and mutation are separate operations.
- Team and membership tests declare positive list, update, create and removal paths, but do not prove cross-team denial, role-specific denial, immediate removed-session denial or owner-invariant concurrency.
- Event and audit coverage is asymmetric: some update/remove operations emit events or audits, while team creation, owner creation and member leave do not form a complete correlated lifecycle record.

### Invitation

- Invitation state is implicit. Email acceptance deletes a row, link acceptance retains it, and manual deletion represents revocation; there is no explicit accepted/revoked status, actor, version or consumption marker.
- Acceptance performs invitation lookup, membership upsert, event emission and optional deletion as separate operations.
- Concurrent acceptance or accept-versus-revoke can duplicate events, fail after partial mutation or leave a reusable token. Link invitations can be replayed and re-emit `member.created`.
- Acceptance emits `member.created` but no corresponding acceptance audit. Event/audit calls can no-op when integrations are disabled, and existing tests do not assert payload, ordering, correlation or failure behavior.
- Declared tests cover email/link invitation creation, new/existing-user acceptance, domain allow/deny and member removal. They do not cover expiry, revocation, replay, simultaneous acceptance, races, duplicate events or audit evidence.

## Work-package decision

| Work package | Result | Decision |
|---|---|---|
| RES-P0-04 | Complete at E2 | Required UI, API, validation, model, schema, integration and test paths are indexed for every R1 lifecycle. |
| RES-P0-05 | Trace complete; acceptance partial | Positive declarations exist, but verification, reset, lockout, linked-account and API-key negative runtime cases remain open. |
| RES-P0-06 | Trace complete; acceptance partial | State paths and constraints are mapped, but atomic owner invariants and cross-tenant/role negatives are not executed. |
| RES-P0-07 | Trace complete; acceptance not satisfied | Required end-to-end, event/audit, replay and concurrency evidence is absent. |

## Gate decision

**G3 remains OPEN.** Test discovery is E2 evidence of declared coverage, not E3 evidence of behavior. Passing G3 requires isolated synthetic runtime services and independently reproduced positive and negative database-backed probes. This evidence does not authorize production implementation or promote any observation into a bOPEN normative decision.

## Required G3 runtime pack

- isolated synthetic PostgreSQL database and deterministic application build;
- local mail sink and deterministic CAPTCHA substitute;
- synthetic OAuth/SAML providers where identity variants are tested;
- controlled Svix/Retraced substitutes that capture payload, ordering, correlation and failure behavior;
- database and JWT session variants;
- registration canonicalization/duplicate/partial-failure cases;
- verification, reset, lockout, session revocation and linked-account negatives;
- team owner atomicity, role denial and cross-team member-ID negatives;
- invitation expiry, revocation, sequential replay, concurrent acceptance and accept-versus-revoke probes.

## Clean-room declaration

No upstream source, production credential, personal data, database or raw secret-bearing runtime output was copied into bOPEN. The two source checkouts and evidence stores remain under `C:\laragon\www\bopen-research`. Only paths, symbol names, hashes, counts, observations and test declarations are recorded here.
