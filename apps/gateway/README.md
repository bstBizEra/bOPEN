# bOPEN API Gateway

**Work package:** [`BOPEN-P35-001`](../../docs/work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-04`, deliverable **D-09**
**Blueprint layer:** 1 — API Gateway (`BOPEN-ARCH-PLAN-001` §2)
**Status:** `IMPLEMENTED_UNVERIFIED` — implemented, tested, **no independent ballot cast**
**Maker:** Claude (`claude@bst.local`)
**Eligible verifier:** Codex, Gemini or Kimi (`DEC-P35-DOCKET` §5.2)
**Governing artifacts:** [`HTTP_HEADER_SPEC.md`](../../sdk/headers/HTTP_HEADER_SPEC.md), `BOPEN-AUTHZ-001`, `BOPEN-IDP-001` §12, `AGENTS.md` §9, §10

---

## 1. What it is

A validating reverse proxy in front of the platform kernel. It refuses requests that violate the
header contract at the edge, then forwards everything else unchanged.

It is deliberately **not** a policy decision point. `AGENTS.md` §9 requires authorization
decisions to go through the approved decision interface; a gateway that answered any part of
"who is this, which tenant, may they" would become a second place those questions get answered,
and the two places would eventually disagree.

## 2. Running it

```bash
cd apps/gateway
npm install
BOPEN_KERNEL_BASE_URL=http://127.0.0.1:8000 npm start   # listens on 127.0.0.1:8787
npm test                                                 # 31 tests, no kernel required
```

Node 24+ only. It runs the TypeScript sources directly via native type stripping, so there is no
build step and no transpiler in the dependency tree. Three runtime dependencies, pinned exactly:
`hono`, `@hono/node-server`, `zod`.

The server refuses to start without `BOPEN_KERNEL_BASE_URL` rather than defaulting, and binds to
`127.0.0.1` rather than `0.0.0.0`. The kernel currently honours
`BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`, under which `POST /v1/contexts` mints an owner
token to anyone holding three identifiers — a gateway listening on every interface would publish
exactly that.

## 3. What it refuses to do, and why

Each of these is a case where the obvious convenience would break something specific.

| It does not | Because |
| :--- | :--- |
| Rewrite, inject or normalise `X-Tenant-ID` | On the bearer path the kernel takes the tenant from the token's signed `tid` claim and rejects a header disagreeing with it. A gateway supplying the header would be forging agreement with a claim it cannot verify |
| Strip identifier prefixes before forwarding | `D-P35-004` — bare UUID against `tnt_<uuid>` — is unratified. Normalising would decide it by code default, which `AGENTS.md` §16 prohibits |
| Truncate `X-Correlation-ID` | The kernel rejects over-length values after a 2026-07-30 security review found silent truncation. Truncating here would re-introduce that defect upstream of the audit record, where nothing would show it happened |
| Enforce RFC 9562 UUID validity | See §4.1. It would reject identifiers the kernel accepts, including this repository's own documented examples |
| Mint, refresh or inspect tokens | `BOPEN-IDP-001` §12.4 keeps context-token signing asymmetric so that a verifier cannot also be an issuer. A gateway holding signing material would defeat that |
| Report kernel health from `/gateway/health` | A green gateway would then mean "something answered", and an operator would learn nothing about which component is down from the signal meant to tell them |
| Echo the offending value in a 400 | An error that reflects input is a way to probe what the boundary accepts |
| Map kernel status codes onto its own | A deny would become indistinguishable from a gateway fault in the audit trail |

## 4. Open items this component does not resolve

These are recorded rather than decided. Each is a question the gateway ran into and deliberately
left where it belongs.

### 4.1 The documented example identifiers are not RFC 9562 conformant

`HTTP_HEADER_SPEC.md` gives `tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c`. Its variant nibble is
`5`; RFC 9562 requires `8`, `9`, `a` or `b`. The same holds for the `ctx_` example.

This surfaced during implementation: Zod 4's `z.uuid()` enforces the RFC, and using it made the
gateway **stricter than the kernel it fronts** — a 400 at the edge for requests the kernel would
have served, including the spec's own examples. The kernel does not enforce it either
(`_PREFIXED_ID` matches `[0-9a-fA-F]`, and Python's `uuid.UUID()` accepts any hex-shaped value).

The gateway therefore validates UUID *shape* only, and
`test/headers.test.ts` locks that in with a test asserting the documented examples are accepted.

**Unresolved:** whether bOPEN identifiers should be RFC-conformant UUIDs, and whether the spec's
examples should be corrected. It belongs with `D-P35-004`, not in a gateway regex.

### 4.2 `Authorization` and `X-Tenant-ID` are mandatory in the spec, optional in the kernel

`HTTP_HEADER_SPEC.md` marks both **Mandatory**. The kernel treats `Authorization` as optional
because the legacy `X-Context-ID` path predates the context token, and ignores `X-Tenant-ID`
entirely on the bearer path.

The gateway mirrors the kernel, not the spec. Enforcing the spec strictly would delete the
legacy path by validation default — a behaviour change no ratified decision authorizes, made at
the edge where clients would see it first.

**Unresolved:** whether the spec should be amended to match the implementation, or the legacy
path retired on a schedule. Either is a decision; neither is a gateway change.

### 4.3 Not yet exercised against a live kernel

The suite proves the gateway's own behaviour, with the upstream injected. It does not prove that
a real request survives the full path through the FastAPI kernel to PostgreSQL and back. That is
an end-to-end concern and needs both processes running.

## 5. Evidence

31 tests, no kernel required, `node --test test/*.test.ts`.

Written to `BOPEN-GOV-EBIV-001` R4 — every rule in §3 carries a negative probe asserting the
violating request is refused, because a test that only walks the happy path passes just as well
when the mechanism is deleted.

Three mutation probes were executed on 2026-07-31 to establish the suite can fail:

| Mutation | Result |
| :--- | :--- |
| `CORRELATION_ID_MAX` 64 → 4096 | 1 test failed |
| Forwarding strips the identifier prefix | 1 test failed |
| `.strict()` removed from the `TenantContext` binding | 1 test failed |

The tree was restored after each and re-verified at 31/31.

`test/contracts.test.ts` reads `contracts/schemas/tenant-context.json` from disk at run time, so
the Zod binding cannot pass by agreeing with a stale copy of the contract.

**This is a maker's report and carries no verdict weight** (`BOPEN-GOV-EBIV-001` §8). The
component is `IMPLEMENTED_UNVERIFIED` until an independent verifier who did not author it casts
an admissible ballot.

## 6. Clean-room declaration

No upstream source was inspected, copied, translated or adapted. The header rules derive from
`HTTP_HEADER_SPEC.md` and from the kernel's own `api.py`, both bOPEN artifacts. Hono and Zod are
used as published libraries through their public APIs, not as source to port.
