# DEC-P35-AUTH-CLOSURE-RESEARCH — External standards evidence for `AUTH-D1` and `AUTH-D3`

**Document ID:** `DEC-P35-AUTH-RESEARCH-001`
**Version:** `1.0.0`
**Status:** Advisory annex — informs disposition, decides nothing
**Issued:** 2026-08-01
**Annex to:** [`DEC-P35-AUTH-CLOSURE`](DEC-P35-AUTH-CLOSURE.md) *(authored by Codex; not edited by this annex)*
**Prepared by:** Claude (agent, Motor role)
**Method:** multi-source web research, 107 agents, five search angles, three-vote adversarial verification per claim

---

## 1. What this is, and what it is not

This annex answers the questions `DEC-P35-AUTH-CLOSURE` raised, from **published specifications
and documented production practice**. It is external evidence about how this class of problem is
solved elsewhere.

**It is not EBIV evidence.** `BOPEN-GOV-EBIV-001` R1 governs claims about *this repository's*
behaviour, established by executing against real infrastructure. Nothing here was executed
against bOPEN. A verifier must not treat any statement below as bearing on whether bOPEN's code
does what it claims.

Each finding carries its adversarial vote. Two are `2-1` — one of three verifiers refuted them —
and §6 records what did **not** survive at all. Both are load-bearing: a research packet that
reports only its successes is the same failure mode as a maker reporting only passing tests.

## 2. `AUTH-D1` — the fail-closed rule is normative, not a preference

Codex recommended option 3: every protected endpoint derives identity from a verified signed
token, with no automatic fallback after verification failure. **The research supports that
directly, and at specification level.**

> **OWASP ASVS 5.0 §6.8.2** requires that the presence *and* integrity of assertion signatures are
> **always** validated, *"rejecting any assertions that are unsigned or have invalid signatures"*.
> *(finding 6, high confidence, vote 3-0)*

There is no conforming reading in which an unsigned opaque identifier remains an acceptable
fallback once signature verification fails. That is the standards basis for retiring the legacy
`X-Context-ID` path without a downgrade route — the design question is only the migration shape,
not whether the end state is correct.

**On the tenant claim specifically** *(finding 7, 3-0)*: the pattern is authenticate first, then
exchange for a scoped token whose tenant claim is **minted server-side after a membership check** —
never trust a client-asserted tenant id. WorkOS implements exactly this, returning an
authentication error rather than a scoped token when the membership check fails. bOPEN already
does the equivalent on the bearer path (`tid` from the signed claim, header not consulted); this
confirms the direction and applies it to the legacy path.

## 3. `AUTH-D3` — the chicken-and-egg has a known solution, and it does not need email

The constraint Codex identified is real: the assertion's `sub` names an existing principal, so it
cannot authenticate the creation of the first principal, and email-as-key is prohibited.

**The resolving pattern is a self-naming enrollment credential** *(finding 1, high confidence,
vote 3-0)*:

> Kubernetes bootstrap tokens authenticate as the username `system:bootstrap:<token id>` in the
> group `system:bootstrappers`. The principal name is produced by **string concatenation from the
> credential's own public id**. Kubernetes has no `User` object at all, so there is provably no
> identity table and no email match anywhere in that path. Authorization is bound to the *group*,
> not to a per-user record.

Verified at code level as well as in the documentation
(`plugin/pkg/auth/authenticator/token/bootstrap/bootstrap.go`): the authenticator fetches the
token Secret, requires `usage-bootstrap-authentication == "true"`, does a constant-time compare of
the secret half, checks expiry, and synthesizes `UserInfo`.

**Why this fits bOPEN.** It dissolves the chicken-and-egg without violating
`DEC-P35-AUTH-BOUNDARY`: the enrollment identity is derived from the credential rather than looked
up, so no principal record and no email are consulted. It is the "separate enrollment trust
domain" option, made concrete.

**NIST agrees on the structure** *(finding 3, vote 2-1)*: SP 800-63B-4 places binding at
enrollment under SP 800-63A's proofing domain, while requiring AAL-appropriate authentication for
every *post*-enrollment binding. Two trust domains, different rules — which is what
`DEC-P35-AUTH-CLOSURE` `AUTH-D3` is really asking about.

**SCIM confirms the ordering constraint structurally** *(finding 10, vote 2-1)*: the internal
resource id is server-assigned, so a create request can never carry it. The problem bOPEN hit is
inherent to provisioning protocols, not a defect in its design.

### 3.1 Concrete parameters, if an enrollment credential is adopted

Converged across NIST and OWASP *(finding 4, vote 3-0)*:

| Property | Requirement |
| :--- | :--- |
| Generation | CSPRNG / approved RBG |
| Entropy | ≥112 bits, or ≥40 bits if paired with a subscriber-entered identifier (NIST); ≥20 bits for OOB codes (ASVS) |
| Lifetime | Hard cap, **10 minutes** |
| Use | **Single-use**, consumed on redemption |
| Channel | Manual or *local* out-of-band transfer — **never email** |
| Durability | **Must not become a durable credential** (ASVS 6.4.1) |

### 3.2 The warning that matters most

*(finding 2, vote 2-1 — one verifier refuted, recorded rather than dropped)*

> An enrollment token **is itself an unsigned bearer-by-identifier credential** — the same class
> `AUTH-D1` exists to retire.

Solving `AUTH-D3` with an enrollment token therefore reintroduces, in a bounded form, the exact
pattern being eliminated. It fails closed **only** through the compensating controls in §3.1 plus
an explicit usage opt-in flag and tightly-scoped group authorization. Kubernetes documents that a
shared bootstrap token is a shared HMAC signing key permitting man-in-the-middle of TLS trust
establishment, and Synacktiv's AKS write-up records the real exploited path.

If this route is taken, the enrollment credential must be held to §3.1 in full. A long-lived or
reusable enrollment token would be a worse version of the defect Codex just reproduced.

## 4. The email prohibition is vindicated, not idiosyncratic

*(finding 5, high confidence, vote 3-0)*

> **OIDC Core §5.7**: `iss` + `sub` is the **only** guaranteed-unique End-User identifier;
> `email`, `phone_number`, `preferred_username` and `name` **MUST NOT** be used as unique
> identifiers, whether from the ID Token or the UserInfo Endpoint.
>
> **ASVS 5.0 §6.8.1** independently prescribes *"IdP ID (serving as a namespace) + the user's ID
> in the IdP"* as the binding key.

`DEC-P35-AUTH-BOUNDARY`'s rule — bind by connection, issuer and subject, never by email — is the
specification's rule. This is worth recording because that constraint has repeatedly made bOPEN's
problem harder than the vendor patterns assume, and it now has a citation rather than only a
decision behind it.

**Consequence for borrowed patterns** *(finding 8, vote 3-0)*: WorkOS AuthKit makes email the
enforced uniqueness key and performs automatic identity linking on it. **Only its
authenticate-then-provision *ordering* is transferable to bOPEN; its binding rule is prohibited
here.** Auth0's organization invitations *(finding 9, vote 3-0)* derive enrollment authority from
a separate privileged management trust domain — the right shape — but do not resolve the
first-tenant case either.

## 5. What this suggests for disposition

Advisory only.

| Row | Suggestion |
| :--- | :--- |
| `AUTH-D1` | **Disposable now.** Codex's option 3 has direct normative backing (§2). The open question is migration shape, not end state |
| `AUTH-D3` | Self-naming enrollment credential in a separate trust domain (§3), held to §3.1 parameters in full, with §3.2 recorded as the risk it carries |

`AUTH-D1` does not depend on `AUTH-D3` and can be disposed independently.

## 6. What did not survive verification

*(finding 11)*

Recorded because a research packet that reports only its successes is the same failure mode as a
maker reporting only passing tests.

- **Keycloak out-of-band first-admin claims — all three refuted 0-3.** Do not cite Keycloak's
  bootstrap-admin behaviour as precedent; the specific claims did not hold.
- **"Kubernetes bootstrap tokens are scope-declared enrollment-only credentials" — refuted 0-3.**
  They are *usage*-flagged, which is weaker. The distinction matters if §3.1's opt-in flag is
  relied on as a scope guarantee; it is not one.
- Several further plausible-sounding claims about expiry semantics did not survive.

Findings 2, 3 and 10 carry `2-1` votes — one of three verifiers refuted each. They are reported
with that vote rather than promoted to consensus.

## 7. Limits

1. **Nothing here was executed against bOPEN.** External practice is not evidence about this
   codebase.
2. Adversarial verification was performed by agents of the same model family. Independence is
   weaker than EBIV requires of a ballot, which is why this is an annex and not evidence.
3. Vendor documentation was preferred only where a specification was silent; where both existed,
   the specification governs.
4. This annex does not edit `DEC-P35-AUTH-CLOSURE`. Codex authored that record and its
   recommendations stand as written.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
