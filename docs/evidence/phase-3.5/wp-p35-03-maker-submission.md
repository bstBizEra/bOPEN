# EVD-P35-03-MAKER — WP-P35-03 Maker Submission (Context Access Token)

**Document ID:** `EVD-P35-03-MAKER`
**Version:** `1.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-07-30
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-03`, deliverable D-08
**Commit OID:** `767cb8143fa296f8ef92c7ea1be21dd376c0fe9f`
**Tree OID:** `f4859ff001d5ee926df7e2f8127baaf63d8d761c`
**Maker:** Claude (agent, Motor role)
**Governing artifact:** `BOPEN-IDP-001` §12
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> Zero ballots cast. Verifier seats issued to Codex, Gemini and Kimi. Status stays
> `IMPLEMENTED_UNVERIFIED`.

---

## 1. What changed

`X-Tenant-ID` is now **redundant** rather than merely unauthoritative. On the bearer path the
tenant comes from the token's signed `tid` claim and the header is not consulted at all.

The difference is not cosmetic. Previously the tenant was *asserted by the caller and then
checked against a database row*. Now it is *attested by a signature*. That is what lets a
gateway, or any satellite product, verify the claim on its own against
`/.well-known/jwks.json` — without calling back into the kernel, and without holding anything
that could also mint a token. Symmetric signing would have made every verifier an issuer, which
is why `BOPEN-IDP-001` §12.4 mandates asymmetric keys and why there is no HMAC fallback.

## 2. Scope

One of the four token classes in §12.1: the **context access token**. Not implemented: the
authentication session token, the refresh/rotation handle, and delegation evidence — all Phase 2.

No IdP integration. This token carries a context that Phase 1 already established; it does not
authenticate anyone.

## 3. Refusals that are deliberate

| Refusal | Why it is refused rather than accommodated |
| :--- | :--- |
| `alg` read from the token | `jwt.decode` always receives an explicit allowlist. Algorithm confusion and `alg=none` fail by the same mechanism, so there is no special case to forget |
| Unknown `kid` resolved by fallback | Falling back to the current signing key would accept tokens minted under a retired or attacker-named key during a rotation window |
| Clock skew configurable upward | Clamped to the 60 s §12.5 allows, so a deployment cannot widen the window expired tokens stay usable by setting an environment variable |
| Specific failure reason in the response | Distinguishing expired from bad-signature from unknown-key is a free probe channel. The reason goes to an audit record, not to the caller |
| Token value in an error or log | §12.4. A log line containing a valid token is a credential in the log |
| Skipping the stored-context read | The token attests the tenant, not that the context is still live. Skipping it leaves a five-minute window where a revoked context keeps working |

Ed25519 was chosen over RS256 and ES256 because it has no parameter choices to get wrong: no
curve selection, no padding mode, no key size, no malleable signature encoding. For a claim this
critical, the absence of options is the feature.

## 4. A defect mutation testing found in my own test

`MUT-J` removed the unknown-`kid` rejection — and the suite **stayed green**.

`test_a_token_signed_by_an_unknown_key_is_refused` signs with a foreign key *and* names a foreign
`kid`. With the `kid` check removed, key resolution falls back to the real signing key, the
foreign signature fails, and the token is refused anyway. The test was passing on the signature
check alone. **It was not testing what its name claimed**, and the `kid` control had no test
isolating it.

`test_a_correctly_signed_token_with_a_foreign_kid_is_refused` now signs with the *real* key and
names a *foreign* `kid`, so it fails exactly when the control it names is removed.

This is worth recording rather than quietly fixing. A test that passes for the wrong reason is
indistinguishable from one that passes for the right reason until something removes the control
and nothing goes red. It is the same failure shape as the Phase 3 suite reporting 169/169 while
`RateLimitDecision` violated its schema — and I reproduced it in work written specifically to
prevent it. A verifier should assume more of these exist.

## 5. Mutation probes

| Probe | Control removed | Detected | Test that caught it |
| :--- | :--- | :---: | :--- |
| `MUT-J` | Unknown-`kid` rejection | ✓ | `test_a_correctly_signed_token_with_a_foreign_kid_is_refused` |
| `MUT-K` | Mandatory-claim check | ✓ | `test_a_token_missing_a_mandatory_claim_is_refused` |
| `MUT-L` | Tenant-conflict check | ✓ | `test_a_contradictory_tenant_header_is_refused_not_reconciled` |
| `MUT-M` | Stored-context re-read on the token path | ✓ | `test_revoking_the_context_invalidates_an_unexpired_token` |

`MUT-J` was **not** detected before the new test was added. The other three were detected on
first run.

These mutate *code*, not schema — the previous probes (`MUT-A`–`MUT-I`) weakened database
policies. Both kinds are needed: a policy probe cannot reach a defence written in Python, and a
code probe cannot reach one written in SQL.

## 6. Test coverage

18 adversarial tests. Canonical suite **217/217**.

Attacks covered: `alg=none`, tampered `tid` claim, foreign signing key, foreign `kid` with a
valid signature, missing `kid`, expired token, wrong audience, missing mandatory claim,
cross-tenant audit read with a valid token, contradictory `X-Tenant-ID`, use after revocation,
truncated signature, and JWKS hygiene including that the Ed25519 private scalar `d` never appears
in the published document.

## 7. Open items and divergences

**`sid` does not mean what §12.2 says it means.** The spec defines `sid` as the authentication
session identifier. Phase 1 has no authentication session distinct from the context, so `sid` is
set to the context identifier. Fabricating an unrelated value would put something in an audit
trail that corresponds to nothing. Kimi is asked in the handoff to rule on this before Phase 2
sessions exist rather than after.

**`Authorization: Bearer` is accepted, not required.** `HTTP_HEADER_SPEC.md` makes it mandatory.
The `X-Context-ID` path predates it, and removing that path would break any caller written
against the earlier surface. What is never done is accepting an unverified bearer value. Making
the header mandatory is a one-line change once callers have migrated, and is left as a decision
rather than taken silently.

**Key rotation is supported but untested.** `KeyRegistry` resolves by `kid` so an outgoing key can
verify while an incoming key signs, but no test exercises an actual rotation with two live keys.
Recorded as a gap.

**Revocation costs a database read per request.** The stored context is re-read on every request
so revocation is immediate. That is the correct trade at this stage and a measurable cost later.

**`A-06` remains unmet.** Migration 003's rollback has still never been executed.

**Findings F-4 through F-7 remain open.** Entitlement-module defects, out of scope.

## 8. Verification status

| Field | Value |
| :--- | :--- |
| Ballots cast | 0 |
| Quorum required | 2 (EBIV §6.1) |
| Seats issued | Codex (reproducibility), Gemini (contract/architecture), Kimi (cross-artifact) |
| Disqualified | Claude — Maker |
| Handoffs | [Codex](../../00-governance/handoffs/HANDOFF-P35-PARALLEL-TO-CODEX.md), [Gemini & Kimi](../../00-governance/handoffs/HANDOFF-P35-VERIFY-TO-GEMINI-KIMI.md) |

### Where to attack this deliverable

1. **Find a fifth control with no isolating test.** `MUT-J` proved my probes were not exhaustive.
   Try removing the `nbf` check, the `roles`/`scopes` type check, the `typ` header, the audience
   check — anything whose removal the suite might not notice.
2. **Can a token be replayed across kernel instances with different `BOPEN_TOKEN_AUDIENCE`?**
   The audience is validated, but only against this process's configuration.
3. **`jti` is emitted and never checked.** There is no replay cache. Within the five-minute
   lifetime, a captured token is reusable. I judged that acceptable for a bearer token of this
   lifetime; say so if you disagree.
4. **The registry is process-local.** Multiple kernel replicas each load the key from the same
   environment variable. Confirm nothing assumes a single process.

## 9. Reproduction

```bash
python -m pip install -r requirements.txt
python tools/generate_token_key.py          # prints an .env.local line; writes nothing
set -a; . ./.env.local; set +a
python tools/run_tests.py                   # 217/217
curl http://127.0.0.1:8080/.well-known/jwks.json
```

## 10. Provenance

Authored by Claude (agent, Motor role) on 2026-07-30. Advisory only —
`execution_authority: false`, `approval_authority: false`.

Anchors emitted by `python tools/check_evidence_anchors.py --emit`.
