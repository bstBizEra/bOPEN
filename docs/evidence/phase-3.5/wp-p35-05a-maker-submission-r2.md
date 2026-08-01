# EVD-P35-05A-MAKER-R2 — WP-P35-05a Maker Submission, revision 2 (Kernel Authentication Boundary)

**Document ID:** `EVD-P35-05A-MAKER-R2`
**Version:** `2.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-01
**Supersedes:** [`EVD-P35-05A-MAKER`](wp-p35-05a-maker-submission.md) at `b11e2e8…`, held under Codex's `HOLD_FOR_DECISION`
**Implements:** [`DEC-P35-AUTH-CLOSURE`](../../decisions/DEC-P35-AUTH-CLOSURE.md) `AUTH-D1`, ACCEPTED 2026-08-01 (option 3)

**Commit OID:** `f12e5fc0fc91e5a7c5dcc6076ee6a996c0c850f5`
**Tree OID:** `3443000a2eeae35913f6b7fa8952927b9f951d2a`
**Blob — `api.py`:** `bb48fb442d9f0558a90cd247e81e54dd71ed1d08`
**Blob — `subject_assertion.py`:** `82b8324872fb6e858a9112cd1a1be67d756cabd7` *(unchanged from `b11e2e8…`)*
**Blob — `HTTP_HEADER_SPEC.md`:** `c1717223309a200bd5926431c14df0cd0e8b35fc`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifiers:** Codex, Gemini
**Suites:** canonical 441/441 against PostgreSQL; gateway 47/47

> Zero ballots at this candidate. OIDs read with `git rev-parse` at issue time (EBIV R3, `A-07`).
>
> **Provenance note.** `AGENTS.md` §23.0 discloses eight commits made under another agent's git
> identity. `f12e5fc` is **not** among them — it carries `Claude (BST-SA Motor) <claude@bst.local>`
> correctly. Both eligible verifiers are unaffected.

---

## 1. Why revision 2 exists

Codex placed revision 1 on `HOLD_FOR_DECISION` and was right to. The submission described a
"kernel authentication boundary" while a member of any tenant could act as the tenant owner
without a token, and Codex refused to re-anchor it to a later commit because the blobs were
byte-identical and re-anchoring would have implied a repair that had not happened.

`AUTH-D1` was then disposed — option 3, protected endpoints bearer-only — and this revision is its
implementation.

## 2. The defect this closes

Reproduced independently on 2026-07-31 by a Claude subagent sweep and by Codex's preflight, both
against live PostgreSQL:

> With an authenticator configured and **no `Authorization` header**, `/v1/authorize` returned
> `200 ALLOW` for a caller presenting only `X-Tenant-ID` and another member's `X-Context-ID`.

The identifier required no attack to obtain: `establish_context` writes it into
`audit_events.resource_id`, and `GET /v1/audit-events` returns it to **every member of the
tenant**. A member could read an owner's context id from the audit trail and then act as the
owner, with the audit record attributing the acts to the victim.

**Possession of an identifier is not authentication.** That is now enforced.

## 3. What changed

Sequenced as `DEC-P35-AUTH-CLOSURE` §4 requires — contract, then failing tests, then code.

| Order | Change |
| :--- | :--- |
| 1 | `HTTP_HEADER_SPEC` → **v1.1**. `Authorization` is the only authoritative header; `X-Tenant-ID` and `X-Context-ID` are marked non-authoritative and may narrow or cross-check a signed claim, never create one |
| 2 | Seven negative tests written **before** the code, failing as designed (4 security probes, 3 for a function that did not yet exist) |
| 3 | `resolve_context` refuses with 401 when no bearer token is presented |
| 4 | `legacy_context_header_profile_enabled()` — off by default, refused when `BOPEN_ENV=production`, separately named |

## 4. Propositions

Each states exactly what its named test checks. **No proposition here claims a property broader
than its test** — five propositions in the sibling `WP-P35-04` package were refuted for precisely
that, and the discipline is applied deliberately.

| ID | Proposition | Test |
| :--- | :--- | :--- |
| `P35-05aR2-01` | With the legacy profile unset, a context id + tenant id cannot obtain an authorization decision | `test_a_context_id_alone_cannot_obtain_an_authorization_decision` |
| `P35-05aR2-02` | …cannot read a tenant resource | `test_a_context_id_alone_cannot_read` |
| `P35-05aR2-03` | …cannot create a tenant resource | `test_a_context_id_alone_cannot_write` |
| `P35-05aR2-04` | …cannot enumerate audit events | `test_a_context_id_alone_cannot_enumerate_audit_events` |
| `P35-05aR2-05` | A rejected bearer token does not fall back to header-asserted identity | `test_a_rejected_token_does_not_fall_back_to_the_header` |
| `P35-05aR2-06` | The legacy profile is disabled when its variable is unset | `test_the_legacy_profile_is_off_unless_explicitly_set` |
| `P35-05aR2-07` | The legacy profile is refused when `BOPEN_ENV=production`, even when its variable is set | `test_the_legacy_profile_cannot_be_enabled_on_a_production_profile` |
| `P35-05aR2-08` | The legacy profile is available when `BOPEN_ENV=local` and its variable is set | `test_the_legacy_profile_is_available_for_local_development` |

Propositions `P35-05a-02`..`11` from revision 1 (assertion verification: signature, issuer,
audience, expiry, `alg:none`, missing claims, non-string claims) are carried at this candidate
unchanged — `subject_assertion.py` is byte-identical to `b11e2e8…`. **They require fresh ballots;
revision 1 received none.**

## 5. Execution and probes

```text
python tools/run_tests.py     441/441 OK   (live PostgreSQL)
apps/gateway  node --test     47/47 OK
```

**Mutation probes, 2026-08-01:**

| Mutation | Observed |
| :--- | :--- |
| Remove the bearer-only gate from `resolve_context` | **5 tests failed** |
| Make `legacy_context_header_profile_enabled()` return `True` unconditionally | **1 test failed** (the production refusal) |

Tree restored and re-verified at 441/441 after each.

## 6. What this does NOT establish — read before balloting

### 6.1 The green suite is not evidence the legacy path is gone

The 433 pre-existing tests predate `AUTH-D1` and exercise the legacy path, so `.env.local` sets
`BOPEN_LEGACY_CONTEXT_HEADER_PROFILE=1` locally. **Bearer-only behaviour is proven only by
`tests/integration/test_auth_d1_bearer_only.py`, which unsets it.** A verifier should not read
441/441 as covering this change; it does not. Verifying with the variable unset across the wider
suite is a probe the maker has not run.

### 6.2 `AUTH-D3` is untouched and still open

`POST /v1/principals` and `POST /v1/tenants` **still return `201` with no assertion.** `AUTH-D1`
did not close them and this submission does not claim to. Reproduced by both engines; pending
authority disposition.

### 6.3 Defects from the 2026-07-31 sweep that remain unfixed

| Finding | State |
| :--- | :--- |
| Replay window unbounded — no ceiling on `exp`; a 10-year assertion was accepted | **Open** |
| A malformed PEM produces `500`, not the designed `503`; the maker's own test used `assertRaises(Exception)` and could not tell them apart | **Open** |
| Status-code oracle — a valid signature with a non-UUID `sub` returns `400` while a bad signature returns `401` | **Open** |
| Undisclosed precondition — the authenticator must emit bOPEN principal UUIDs as `sub`; no mainstream OIDC provider does | **Open**, and no HTTP test exercises a *successful* issuance |

None is closed by `AUTH-D1`. They are listed so a verifier attacks them rather than rediscovering
them.

### 6.4 Unchanged from revision 1

One authenticator kernel-wide, no per-tenant connections, no key rotation, and no endpoint other
than context issuance authenticated.

## 7. Authority

A maker's submission. EBIV §8: a passing suite is a self-assessment carrying **no verdict weight**.
Quorum needs two verifiers (§6.1); fewer escalates and never auto-passes (§6.3).

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
