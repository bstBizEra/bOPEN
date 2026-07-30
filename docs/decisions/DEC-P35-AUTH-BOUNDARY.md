# DEC-P35-AUTH-BOUNDARY — Where the kernel stops and the identity provider starts

**Status:** Advisory. Recommends; does not decide.
**Work package:** WP-P35-05 (enterprise identity bridge)
**Issued:** 2026-07-30
**Depends on:** DEC-P35-PHASE2-STORAGE (all six decisions) — see §6
**Resolves, if adopted:** F2, F6, F9 in [EVD-SEC-001](../evidence/EVD-SEC-001-kernel-security-review.md)
**Method:** multi-source research with adversarial verification (108 agents, claims killed on a 2-of-3 refutation vote), then each surviving finding checked against this repository's code by execution.

---

## 1. What this is for

Three security findings all terminate in the same missing capability: the kernel cannot
authenticate a caller. `POST /v1/contexts` mints an owner token for anyone holding three
non-secret UUIDs (F2), `POST /v1/principals` distinguishes registered from unregistered
addresses (F6), and `POST /v1/tenants` binds a third party as owner without their agreement
(F9). All three are currently held shut by one operator affirmation
(`BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`), which is a refusal, not a fix.

This record establishes the boundary those fixes must be built against, and reports what the
existing Phase 2 code already gets right — which turned out to be most of it.

---

## 2. The architectural recommendation

**bOPEN should not become an identity provider, and should not embed one in-process.** It owns
sessions and principal records; each tenant's IdP is a separately-deployed external authority
reached across a network boundary, behind per-protocol adapters.

That is options (c) and (d) from the brief, not (a). The reasoning is not aesthetic — two
independent lines of evidence converge on it.

**Licensing forces the boundary.** Zitadel's core server is AGPL-3.0-only, and AGPL §13 is
triggered by *remote network interaction with a modified version*, not only by distribution. A
hosted bOPEN, or a satellite product served over HTTP, that embedded modified Zitadel code would
owe Corresponding Source to its remote users. Verified 3-0 against the LICENSE file, Zitadel's
own licensing FAQ, and the GNU text.

The same vendor states where it thinks the boundary falls: *"Communication mechanisms like pipes,
sockets, HTTP-based APIs, and command-line arguments likely indicate separate applications"* and
*"Using generated clients in your application does not require your application to be
AGPL-3.0-licensed."* Zitadel's `proto/` is Apache-2.0 and its client packages are MIT, so
consuming the API surface across a process boundary while running an **unmodified** server is a
viable permissive integration. Embedding is what forfeits that.

**Protocol security forces the same boundary.** A multi-tenant bridge is by construction an OAuth
client of many authorization servers, which is the precondition for the mix-up attack class
(verified 3-0 against RFC 9207 and RFC 9700). The kernel must therefore treat every tenant IdP as
a separately identified and individually untrusted authority — coherent only if the IdP is
external to it.

Neither line depends on the other. That is why this is stated as a recommendation rather than a
preference.

---

## 3. What the code already does correctly

Each research finding was checked against `idp_bridge.py` rather than assumed to apply.

### 3.1 Identity is never keyed on email — already satisfied

The strongest finding in the research (3-0, twice) is that an SSO callback must never key a
principal, or resolve a tenant, on an asserted email address. In Microsoft Entra ID the `email`
claim is mutable and unverified: an administrator of their own tenant can set it to an arbitrary
victim address with no validation. This is the nOAuth class, and Semperis's 2025 retest of 104
Entra Gallery applications still found roughly 9% exploitable.

bOPEN does not do this. `ExternalIdentity.canonical_key` is `(connection_id, issuer, subject)`,
and `find_identity` takes exactly those three. The email is carried as `email_snapshot` — a name
that says what it is — and appears nowhere in any lookup.

The research's recommended key is `(issuer, subject)`, generalizing Entra's `tid + oid`, with the
tenant component called load-bearing. **bOPEN's key is stronger than the recommendation**: it
leads with `connection_id`, so two tenants federating the same issuer cannot collide even if the
subject matches.

### 3.2 Account merging is gated — already satisfied in substance

The research names account merging as the concrete exploitable step: linking an incoming OIDC
identity to a pre-existing account on matching email hands the attacker that account. The control
is two-part — key on `(issuer, subject)`, and if merging is offered at all, require proof of
address ownership before linking.

`link_identity` already refuses on email equality and says so in its own docstring: *"Linking is
permitted only via an accepted link challenge by an authenticated active Principal, or a valid
invitation bound to the same tenant. Email equality alone can never link (INV-P2-012)."* It also
refuses to reassign an existing `(connection, issuer, subject)` — `SUBJECT_ALREADY_BOUND` — and
denies by default when neither basis is present.

### 3.3 Issuer is bound to connection — already satisfied

`result.issuer != connection.issuer` is a typed denial on both the SSO callback and the linking
path.

---

## 4. What is missing, stated by severity

### 4.1 The link challenge is asserted, not proved — DESIGN GAP, not reachable

`link_identity(..., link_challenge_accepted: bool = False)`. The kernel trusts the caller's
boolean that a challenge was accepted. No proof is carried, verified or bound to anything.

This is the same shape as F2 and F9: **an identity claim the kernel acts on but cannot check.**
The research's requirement is *proof of address ownership*; a boolean is not proof.

**Not currently reachable.** `link_identity` is called from tests only and is not exposed on the
HTTP surface — verified by grep across `api.py` and `sdk/`. So this is a constraint on WP-P35-05,
not a finding against running code, and it is recorded here rather than in EVD-SEC-001 for that
reason. Whoever wires this endpoint must replace the boolean with a verifiable artifact before it
becomes reachable.

### 4.2 `domain_hints` is declared and never read — dead control

`IdentityProviderConnection.domain_hints` exists as a field and is referenced nowhere else in the
repository. Home-realm discovery is unimplemented.

That is not a vulnerability, but it is the hazard this repository has hit before: a field that
looks like a control and does nothing. When it is implemented, the research is specific about
what it must do — email/UPN-domain-to-IdP mapping is the pattern shipped at hyperscale, but
resolution must run *domain → VERIFIED FEDERATED domain → that tenant's IdP*. **The
verified-domain step is the gating control, and the email domain must be a routing hint only,
never the trust decision.** Verified 3-0 against Microsoft's home-realm-discovery documentation
and PortSwigger's 2025 research on email parsing.

### 4.3 SAML: the control must be stated more precisely than "process only signed elements"

XML signature wrapping and parser differentials remain exploitable in maintained SAML libraries
through 2025–2026 — CVE-2025-25291 and CVE-2025-25292 in ruby-saml, and GitHub Security Lab's
parser-differential work. Verified 3-0.

The required control is **single parse, single DOM, and consume only the subtree resolved by the
verified signature's `Reference`.** "Process only signed elements" is necessary and not
sufficient, because two parsers disagreeing about the same bytes is what defeats it.

bOPEN has no SAML parser today — `NormalizedAuthResult` arrives from a broker with
`broker_signature_valid` already set. That means this requirement lands on the broker adapter,
and it also means **the trust boundary is the broker**: a boolean the kernel does not verify,
which is 4.1's shape again at a different layer.

### 4.4 RFC 9207 `iss` belongs in the adapter

The mix-up countermeasure is the `iss` parameter in the *authorization response*, complemented by
per-connection issuer-to-tenant binding and distinct per-connection redirect/ACS URIs. bOPEN has
the second; the first has no home yet because the authorization response is handled by the broker.

---

## 5. What the research did not answer

Stated plainly, because a gap presented as a finding is worse than a gap.

**Questions 4, 5 and 6 produced no claims that survived adversarial verification.** That is:
registration/consent oracle closure, the session and refresh-token model, and the standards
conformance audit of the existing Ed25519 implementation against RFC 8725 and RFC 9700.

This does not mean the answers are unknowable — it means this run did not establish them to the
standard applied to §2 and §3. They remain open work. In particular, **F6 has no verified remedy
yet**, only the untested assumption recorded in `api.py` that asynchronous verification closes it.

**Finding 10 is an explicit non-result, and it collides with an approved decision.** The licensing
status of BoxyHQ Jackson and its successor Ory Polis is UNRESOLVED — all four supporting claims
were refuted — and must be re-verified against a pinned commit before either is treated as a
study-and-port candidate.

`DEC-0003` in the register selects **"PostgreSQL RLS, BoxyHQ Jackson IdP, ReBAC"** and is marked
**Approved**. Jackson was clean-room inspected under BOPEN-RES-001 when its license was different
from what it is now. So an approved technology selection names a component whose current terms
this research could not establish.

That is not a claim that DEC-0003 is wrong. It is a claim that the evidence underneath it has
aged, and that re-verification against a pinned commit is owed before WP-P35-05 builds on it. The
verification is cheap; discovering the answer after the adapter is written is not.

---

## 6. Sequencing — this cannot go first

WP-P35-05 cannot land before Phase 2 has storage. IdP connections, SSO transactions and
authentication sessions must survive a restart and be shared across workers, and today all three
live in per-process dictionaries: zero of eight Phase 2 concepts has a table.

Measured consequence, and it is availability rather than security: the dict-backed SSO transaction
store fails **closed** across workers. A callback landing on a worker that never issued the state
is denied because the transaction is absent, not because it was consumed — so replay is refused
either way, but SSO login succeeds only when the callback returns to the issuing worker.

The six decisions in `DEC-P35-PHASE2-STORAGE` are therefore not parallel work. They are upstream.

---

## 7. Decisions this record does not take

- Which IdP, or whether to run one at all. §2 says where the boundary is, not what sits behind it.
- Whether to accept AGPL for a separately-deployed unmodified server. That is a licensing posture
  for an open-source product, and it is the operator's.
- Whether bOPEN offers account merging at all. Not offering it removes 3.2's entire attack surface
  and is a product decision.
- The identifier format, `delegated_grants.target_tenant_id`, and the classification of
  `group_role_mappings` — all in `DEC-P35-PHASE2-STORAGE` §2.1, Addendum B §B.4.

---

## 8. Provenance

Research: 108 agents, 4.66M tokens, claims retained only on surviving a 2-of-3 adversarial
refutation vote. Primary sources preferred — RFC 9207, RFC 9700, project LICENSE files, Microsoft
identity-platform documentation, CVE advisories.

Code audit: executed against this repository on 2026-07-30. Reachability of `link_identity`
established by search across `api.py` and `sdk/`; identity key read from `canonical_key` and
`find_identity`; `domain_hints` usage counted across all Python sources.

Advisory only — `execution_authority: false`, `approval_authority: false`.
