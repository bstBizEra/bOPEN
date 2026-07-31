# EVD-P35-CODEX-PREFLIGHT-001 - WP-P35-04 and WP-P35-05a verification preflight

**Document ID:** `EVD-P35-CODEX-PREFLIGHT-001`  
**Version:** `1.0.0`  
**Status:** Verification hold - maker resubmission required  
**Observed:** 2026-07-31T17:13:54.544Z  
**Verifier:** Codex (`codex@bst.local`)  
**Repository:** `C:\laragon\www\bopen`  
**Target branch:** `claude/BOPEN-P35-001-runtime-realization`  
**Observed commit:** `88e6ed2b4f2ab80a6b8ef0e8d570f761d8725b4b`  
**Observed tree:** `39da471ae01ade3e3ee619f788d99fabbe1fde3d`  
**Governing standard:** `BOPEN-GOV-EBIV-001` R1-R5; `BOPEN-GOV-IDENT-001`

---

## 1. Purpose and independence boundary

This is a verifier preflight, not a ballot and not a replacement maker submission. Codex did
not edit either implementation, its tests, or the propositions offered by Claude. Editing those
maker artifacts before judging them would compromise the independence the handoff exists to
preserve.

The existing ballot handoff must not be executed as written. Its WP-P35-04 commit predates a
critical security repair, and its WP-P35-05a scope omits authentication paths that remain open.

## 2. WP-P35-04 anchor disposition

| Claim | Observed fact |
|---|---|
| Maker submission commit | `c03cd4f423d6afa9ee1441e340f5720f184db08c` |
| Submitted gateway subtree | `0224d117a37c09f8463c1fd19e0182494c3bc341` |
| Current gateway commit | `88e6ed2b4f2ab80a6b8ef0e8d570f761d8725b4b` |
| Current gateway subtree | `485f6b3f0814274700cabcf5d5a38943dd6c4e43` |
| Difference | 196 changed lines across `app.ts` and `headers.test.ts` |
| Current gateway suite | 43 passed, 0 failed |

The submitted commit contains the relative-URL construction that allowed an unauthenticated
caller to replace the configured upstream origin and receive forwarded bearer credentials.
Commit `88e6ed2...` repairs that defect structurally and adds response-framing, repeated-cookie,
and connection-header controls.

**Preflight verdict:** `SUPERSEDED`. Codex will not ballot `P35-04-01` through `P35-04-12` at
`c03cd4f...`. Claude must issue a successor maker submission bound to `88e6ed2...`, its tree and
gateway subtree, including the 43-test proposition set and the still-open path-normalisation
limitation.

## 3. WP-P35-05a anchor disposition

The WP-P35-05a code has not changed since its submitted commit:

| Path | Blob at `b11e2e8...` | Blob at observed HEAD |
|---|---|---|
| `subject_assertion.py` | `82b8324872fb6e858a9112cd1a1be67d756cabd7` | same |
| `api.py` | `4561e7ffa3120711f0c95f099f68c2f3f7573cc3` | same |

It would therefore be false to re-anchor 05a to HEAD and imply a repair. The original commit is
reachable, but the submission is not ready for a completion-oriented ballot because the live
authentication boundary is narrower than the protected HTTP surface.

### 3.1 Executed legacy-context probe

The probe created a principal, tenant, membership, and context through the real PostgreSQL-backed
HTTP slice. It then configured the external authenticator and called `/v1/authorize` without an
Authorization header, using only `X-Tenant-ID` and `X-Context-ID`.

```text
authenticator_configured= True
authorization_header_sent= False
legacy_context_status= 200
legacy_context_decision= ALLOW
```

`X-Context-ID` is an identifier, not a signed credential. Knowledge of it is currently sufficient
to exercise a protected operation even when the deployment says authentication is configured.

### 3.2 Executed unauthenticated-mutation probe

With the authenticator configured and no assertion supplied:

```text
authenticator_configured= True
principal_without_assertion= 201
tenant_without_assertion= 201
```

WP-P35-05a authenticates context issuance only. It does not authenticate principal registration
or tenant provisioning. The maker submission discloses this narrow scope, but the existing
handoff invites package verification without first resolving whether that scope is acceptable.

**Preflight verdict:** `HOLD_FOR_DECISION`. Do not ballot 05a as a completed authentication
boundary. Resolve `AUTH-D1` and `AUTH-D3` in `DEC-P35-AUTH-CLOSURE`, implement any accepted
changes through a maker, and issue a successor submission. The historical `b11e2e8...` anchor
must remain visible; it must not be relabelled as the repaired candidate.

## 4. Handoff disposition

`HANDOFF-P35-BALLOTS-TO-CODEX` is stale for both packages:

- WP-P35-04 points to a superseded, critically defective commit and expects 31 rather than 43
  gateway tests.
- WP-P35-05a points to the unchanged historical implementation while the required auth-scope
  decisions remain open.

No ballot was appended to `ballots.jsonl`. `check_ballot_attribution.py` therefore continues to
report an empty, unverified state rather than a false verdict.

## 5. Required maker action

1. Claude reissues WP-P35-04 evidence against exact commit `88e6ed2...` and current subtree
   `485f6b3...`.
2. The designated authorities dispose `AUTH-D1` and `AUTH-D3`.
3. The assigned maker implements accepted auth changes and emits a new exact-commit 05a
   submission.
4. A new handoff names only current candidate commits, trees, tests, and propositions.
5. Codex then begins independent adversarial ballots without editing maker code, tests, or
   proposition artifacts.

```text
ballot_cast: false
completion_claimed: false
approval_authority: false
production_activation_authority: false
```
