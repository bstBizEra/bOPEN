# DEC-P35-AUTH-D3-DOCKET — Disposition surface for the last live authentication hole

**Document ID:** `DEC-P35-AUTH-D3-DOCKET-001`
**Version:** `1.0.0`
**Status:** **CLOSED 2026-08-02 — all three items VERIFIED-AND-DISPOSED (`CONFIRMED_UNDER_TWO_AGENT_PROFILE`).** `D-D3-001` Row 1(a) tenant-provisioning assertion; Row 1(b) gateway rate-limiting (built at the gateway layer, 8/8 confirmed after two encoding-bypass refutations were fixed); `D-D3-002` principal enrollment (Option B, out-of-band, 5/5 confirmed). Evidence: [`auth-d3-followon-disposition.md`](../evidence/phase-3.5/auth-d3-followon-disposition.md). The AUTH-D3 hardening is complete.
**Issued:** 2026-08-02
**Owner:** Architecture & Security Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Consolidates:** [`DEC-P35-AUTH-CLOSURE`](DEC-P35-AUTH-CLOSURE.md) (`AUTH-D3` pending), [`DEC-P35-AUTH-CLOSURE-RESEARCH`](DEC-P35-AUTH-CLOSURE-RESEARCH.md) (enrollment research), [`auth-d3-exposure-measurement`](../evidence/phase-3.5/auth-d3-exposure-measurement.md) (measured exposure)

---

## 1. Why this exists

`AUTH-D3` is the one authentication decision `DEC-P35-AUTH-CLOSURE` left open. Its inputs — the
recommendation, the standards research, and the measured exposure — are in three separate
documents. This docket is one bounded surface so the decision can be made without reassembling
them. **It decides nothing** and touches no code.

`AUTH-D1` (bearer-only protected endpoints) is done. This is the remaining half.

## 2. The exposure, as measured — not as argued

From `auth-d3-exposure-measurement` (Codex-designed probe, executed 2026-08-02 against live
PostgreSQL):

| Fact | Value |
| :--- | :--- |
| Unauthenticated path to a working owner bearer token | **Exists** — `principal 201 → tenant 201 → context 201 → token`, three calls |
| That token's reach | authorize ALLOW, read 200, write 201, audit 200 — **inside its own tenant** |
| Cross-tenant reach | **None.** Foreign resource 403/404, foreign audit 0. Isolation holds |
| Rate limit / quota on creation | **None.** 40 principals + 20 tenants in 5.8s, zero 429s |
| Tenant squatting | **Works** — provision naming another principal owner returns 201; victim's own tenants unaffected |
| Email reservation | Unauthenticated `201` — a denial-of-registration against a named person (email is globally unique, no application-role delete path) |

**The shape of the risk: unbounded in volume, bounded in blast radius.** No cross-tenant data is
reachable. The costs are abuse, cost-inflation (each dedicated-placement tenant eventually means a
database), squatting, and denial-of-registration — not disclosure. That argues against rushing,
and for closing the cheap parts first.

## 3. The docket

The two rows are independent. Row 1 does **not** depend on Row 2, and this is the key finding: most
of the exposure closes without solving the hard problem at all.

### `D-D3-001` — Immediate mitigations that do NOT need the enrollment decision

| Mitigation | Why it needs no `AUTH-D3` |
| :--- | :--- |
| **Rate-limit principal and tenant creation** | A defensive control. The kernel already has `rate_limit_policies` / `rate_limit_counters` (Phase 3). Caps the abuse and cost-inflation vectors regardless of how enrollment is ultimately solved |
| **Require an assertion for tenant provisioning** | `POST /v1/tenants` names an `owner_principal_id` that **must already exist**. An assertion for *that* principal authenticates the call — with no bootstrap problem, because the principal is not being created. This closes squatting and unauthenticated owner-binding |

**Recommended: adopt both.** They close squatting, owner-binding, and the cost/abuse vectors, and
neither waits on the recursion decision below. They **amend `WP-P35-05a`'s scope** (per the
exposure measurement §6), so they are governed work, not a patch — a maker/verifier cycle applies.

> **DISPOSITION 2026-08-02 — `D-D3-001` Row 1 APPROVED.** Operator (`BizEra`) authorized both
> mitigations. Sequencing note: because the `WP-P35-05a` R4 candidate (`119f2d8`) was never
> balloted (classifier-blocked, not ruled on), these mitigations are built on top of it into one
> combined successor candidate, balloted once — no review is invalidated, and the flaky-verifier
> round-trips are halved.
>
> **(a) tenant-provisioning assertion** is the security fix (impersonation/squatting) and is built
> immediately — it reuses `_authenticated_principal` from `AUTH-D1`. **(b) rate-limiting** is
> resource-exhaustion (bounded blast radius) and needs a keying choice (per-source vs global vs
> gateway-layer); surfaced separately rather than guessed. Recorded by Claude (Motor), transcribing
> the operator decision.
>
> **DISPOSITION 2026-08-02 (follow-up) — Row 1(a) VERIFIED-AND-DISPOSED; Row 1(b) keyed to the
> GATEWAY LAYER.** Row 1(a) (tenant-provisioning assertion) was built, balloted, and confirmed:
> `WP-P35-05a` R5, candidate `2c31379`, 27 propositions incl. `P35-D3a-01..05`, one independent
> verifier (`codex`, ballot `5158629`), `CONFIRMED_UNDER_TWO_AGENT_PROFILE` under EBIV §6.5 — see
> [`wp-p35-05a-disposition.md`](../evidence/phase-3.5/wp-p35-05a-disposition.md). **Row 1(b)
> rate-limiting** is dispositioned by the operator to the **gateway layer** — cap principal/tenant
> creation at the Hono edge so abuse is stopped before it reaches PostgreSQL. It is decided but not
> yet built (governed follow-on work). Recorded by Claude (Motor), transcribing the operator
> decision.

**What remains open after Row 1:** only `POST /v1/principals`. That is the sole endpoint where no
principal yet exists to assert, and therefore the only one that genuinely requires `AUTH-D3`.

### `D-D3-002` — Principal enrollment: the recursion decision

The research (`DEC-P35-AUTH-CLOSURE-RESEARCH`) established the resolving pattern and its trap in
the same breath:

- **The pattern** *(finding 1, 3-0)*: a **self-naming enrollment credential** — Kubernetes
  bootstrap tokens authenticate as `system:bootstrap:<token id>`, deriving identity from the
  credential's own id, no user record and no email. It dissolves the chicken-and-egg without
  touching `DEC-P35-AUTH-BOUNDARY`'s never-bind-by-email rule (which OIDC Core §5.7 and ASVS 6.8.1
  independently vindicate).
- **The trap** *(finding 2, 2-1)*: that credential **is itself an unsigned bearer-by-identifier
  mechanism** — the exact class `AUTH-D1` just retired. It fails closed only under strict controls.

| Option | Disposition | Cost |
| :--- | :--- | :--- |
| **A** | **Enrollment credential, strictly bounded** *(research-recommended)* | Solves it. Requires: CSPRNG, ≥112-bit entropy, single-use, ≤10-minute lifetime, local out-of-band transfer, **never emailed**, explicit enrollment-only scope, no durable credential after redemption. A long-lived or emailed token would be a worse `AUTH-D1` |
| **B** | **Keep principal creation out of the exposed kernel surface** | Principals are provisioned by an out-of-band operator/SCIM path, not a public endpoint. No new bearer-by-identifier credential. Cost: no self-service registration through the kernel |
| **C** | **Accept the exposure with Row-1 mitigations only** | Principal creation stays open but rate-limited. Honest only if the residual — abuse and email-reservation DoS, no cross-tenant reach — is acceptable for the deployment's threat model. Must be a stated decision, not a default |

**Recommended: B until a product need forces A.** The research is explicit that A's credential
reintroduces the retired class and is safe *only* with every control present; B avoids the
recursion entirely at the cost of self-service. C is defensible given the bounded blast radius but
should be chosen, not drifted into.

> **DISPOSITION 2026-08-02 — `D-D3-002` decided: OPTION B.** Operator (`BizEra`, Completion
> Authority) chose **B — keep principal creation out of the exposed kernel surface**: principals are
> provisioned by an out-of-band operator/SCIM path, not a public `POST /v1/principals` endpoint. No
> new bearer-by-identifier credential is introduced, so the class `AUTH-D1` retired is not reopened;
> the cost accepted is no self-service registration through the kernel. This is a decision, not an
> implementation — the enforcement change (closing/guarding the public endpoint) is governed
> follow-on work. Recorded by Claude (Motor), transcribing the operator decision.

## 4. Sequencing

1. `D-D3-001` first — it is cheap, needs no `AUTH-D3` answer, and closes most of the exposure.
   Because it changes `WP-P35-05a`, it runs as a governed maker/verifier cycle, **after** the R4
   ballot settles that package (do not stack on a candidate under review).
2. `D-D3-002` on its own timeline — B needs no build; A needs the full control set; C needs only a
   recorded acceptance.

## 5. What this docket is not

It is not a decision, not an implementation, and not authority to build. `D-D3-001`'s mitigations
are governed changes that need disposition and a maker cycle. `D-D3-002` is an open authority
decision. Recorded so the last live authentication hole has a single surface to be disposed from.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
