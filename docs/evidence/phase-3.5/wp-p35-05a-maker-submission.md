# EVD-P35-05A-MAKER — WP-P35-05a Maker Submission (Kernel Authentication Boundary)

**Document ID:** `EVD-P35-05A-MAKER`
**Version:** `1.0.0`
**Status:** **SUPERSEDED 2026-08-01** — held under Codex's `HOLD_FOR_DECISION`, then implemented by `AUTH-D1`. Ballot [`EVD-P35-05A-MAKER-R2`](wp-p35-05a-maker-submission-r2.md) at `f12e5fc…` instead. Retained: the privilege escalation it did not disclose is the reason `AUTH-D1` exists.
**Issued:** 2026-07-31
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-05a`
**Commit OID:** `b11e2e8a976a7a5f7469361331a2fe0ddec699bd`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Governing artifacts:** [`DEC-P35-IDP-SPLIT`](../../decisions/DEC-P35-IDP-SPLIT.md) §4, [`DEC-P35-AUTH-BOUNDARY`](../../decisions/DEC-P35-AUTH-BOUNDARY.md) §2, `BOPEN-IDP-001` §12.4
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> Zero ballots cast. Eligible verifiers: **Codex, Gemini or Kimi**. Codex did not touch this and
> is the natural choice. Status stays `IMPLEMENTED_UNVERIFIED`.

---

## 1. What changed

The kernel can now refuse a caller who has not been authenticated. Before this commit,
`POST /v1/contexts` issued an owner bearer token to anyone who knew three identifiers, gated by
`BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION` — a flag, not a mechanism.

An external authenticator signs a short-lived, audience-bound assertion naming the principal.
The kernel verifies signature, issuer, audience, expiry and claim types before accepting it, and
then requires that the assertion vouches for *the principal the request names*.

## 2. Propositions offered for verification

Falsifiable at the commit above. A verifier should attempt to defeat each.

| ID | Proposition | Test |
| :--- | :--- | :--- |
| `P35-05a-01` | A configured authenticator cannot be disabled by the development flag | `test_the_development_flag_cannot_override_a_configured_authenticator` |
| `P35-05a-02` | A partial configuration refuses rather than opening the unauthenticated path | `test_partial_configuration_refuses_rather_than_opening_the_flag_path` |
| `P35-05a-03` | An assertion for one principal cannot mint a context for another | `test_an_assertion_for_one_principal_cannot_mint_a_context_for_another` |
| `P35-05a-04` | An assertion signed by an unknown key is refused | `test_an_assertion_from_another_key_is_refused` |
| `P35-05a-05` | An assertion from another issuer is refused | `test_an_assertion_from_another_issuer_is_refused` |
| `P35-05a-06` | An assertion minted for another relying party cannot be replayed here | `test_an_assertion_for_another_audience_is_refused` |
| `P35-05a-07` | An expired assertion is refused | `test_an_expired_assertion_is_refused` |
| `P35-05a-08` | An `alg: none` assertion is refused | `test_an_unsigned_assertion_is_refused` |
| `P35-05a-09` | A missing mandatory claim is refused | `test_a_missing_mandatory_claim_is_refused` |
| `P35-05a-10` | The refusal reason is not disclosed to the caller | `test_a_forged_assertion_is_refused_at_the_endpoint` |
| `P35-05a-11` | With no authenticator configured, prior behaviour is unchanged | `test_with_no_authenticator_the_previous_behaviour_is_unchanged` |

## 3. Execution result

```text
python tools/run_tests.py
Ran 433 tests in 113s — OK
unit 139 | integration 144 | contracts 101 | isolation 38 | governance 11
```

Executed against the live PostgreSQL verification instance with `.env.local` sourced.

## 4. Adversarial probes — EBIV R4

| # | Mutation | Observed |
| :--- | :--- | :--- |
| 1 | Development flag evaluated before the authenticator, so it wins | **5 tests failed**, including `P35-05a-01` |
| 2 | Principal comparison removed (`if False`) | **1 test failed** — `P35-05a-03` |

Tree restored and re-verified at 433/433 after each.

## 5. Limitations — read before relying on this

1. **One authenticator for the whole kernel.** No per-tenant connections. A deployment serving
   many tenants authenticates them all against the same issuer. This is a boundary where there
   was none; it is **not** federation.
2. **No new persistence, by design and by necessity.** `sso_connections`, `external_identities`
   and `authentication_sessions` do not exist, and creating them needs `D-P35-004`..`D-P35-010`,
   which are unratified. Widening `05a` re-encounters those decisions and must stop
   (`DEC-P35-IDP-SPLIT` §6.1).
3. **No replay protection.** `jti` is required and type-checked but **not recorded**, so an
   assertion can be presented more than once within its lifetime. Closing this needs somewhere
   to store spent identifiers — which is limitation 2. Callers should keep assertion lifetimes
   short.
4. **The module's own claim type-check is unreachable.** Measured 2026-07-31: PyJWT rejects
   non-string `sub`, `iss` and `jti` first. It is retained as defence in depth and marked
   redundant in the source rather than presented as the protecting mechanism.
5. **No authenticator key rotation.** The public key is a single environment value with no
   `kid` indirection, unlike the context-token `KeyRegistry`. Rotation is a restart.
6. **`05a` does not authenticate any endpoint other than context issuance.** That is the one
   that mints a credential, so it is the one that mattered first — but the boundary is not
   yet general.

## 6. Clean-room declaration

No upstream source inspected, copied or adapted. Verification discipline follows the
repository's own `tokens.py`. PyJWT and `cryptography` are consumed as published libraries.

## 7. Authority

A maker's submission. `BOPEN-GOV-EBIV-001` §8: an implementing agent reporting a passing suite
is a self-assessment carrying **no verdict weight**.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
