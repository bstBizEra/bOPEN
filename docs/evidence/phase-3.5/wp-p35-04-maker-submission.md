# EVD-P35-04-MAKER — WP-P35-04 Maker Submission (API Gateway)

**Document ID:** `EVD-P35-04-MAKER`
**Version:** `1.0.0`
**Status:** **WITHDRAWN 2026-08-01 — superseded by [`EVD-P35-04-MAKER-R2`](wp-p35-04-maker-submission-r2.md). Do not ballot.**
**Issued:** 2026-07-31
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-04`, deliverable D-09
**Commit OID:** `c03cd4f423d6afa9ee1441e340f5720f184db08c`
**Tree OID:** `fb8269e6385318718cc537f8593d92ca781eaecb`
**Subtree OID (`apps/gateway`):** `0224d117a37c09f8463c1fd19e0182494c3bc341`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Governing artifacts:** `sdk/headers/HTTP_HEADER_SPEC.md` v1.0, `BOPEN-AUTHZ-001`, `BOPEN-IDP-001` §12, `BOPEN-ARCH-PLAN-001` §2 layer 1
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> **WITHDRAWN.** The commit this record anchors, `c03cd4f…`, contains an unauthenticated SSRF:
> the caller could select the upstream host and have the client's bearer token forwarded to it.
> Found by adversarial sweep 2026-07-31, after this submission was issued with 31 passing tests
> and three mutation probes that all bit.
>
> Codex refused to ballot it (`EVD-P35-CODEX-PREFLIGHT-001` §2, verdict `SUPERSEDED`). Rule on
> [`EVD-P35-04-MAKER-R2`](wp-p35-04-maker-submission-r2.md) at `88e6ed2…` instead.
>
> Retained unedited under the extend-only rule. Everything below was true of `c03cd4f…` and the
> package was still critically defective — which is the most useful thing this file records.

OIDs above were read from git with `git rev-parse` at submission time, not transcribed, per
EBIV R3 and acceptance criterion `A-07`.

> **Anchor corrected before submission.** An earlier draft of this record bound commit
> `0c28b60bbc2fbe7eb42fbba989f57c872671cc22`. That object stopped existing when the commit was
> rewritten to separate the implementation from its documentation, and the anchor was re-read
> from git rather than left pointing at nothing. This is the same class of defect
> `DEC-P35-RUNTIME` §3.3 found in the Phase 3 manifest — an evidence record bound to an object
> that cannot be resolved, and therefore to a claim that cannot be re-verified. Noted here
> because the mechanism that caught it, `tools/check_evidence_anchors.py`, is the point of R3.

---

## 1. What was built

`apps/gateway` — a Hono reverse proxy validating the header contract at the platform edge and
forwarding to the kernel. It closes blueprint layer 1, which `DEC-P35-RUNTIME` §3.1 recorded as
having no implementation: *"API Gateway — TypeScript / Node.js + Hono + Zod — **None.**
`package.json` declares no dependencies."*

Three runtime dependencies, pinned exactly: `hono@4.12.32`, `@hono/node-server@2.0.12`,
`zod@4.4.3`. Node 24 native type stripping runs the TypeScript sources directly, so there is no
build step and no transpiler in the dependency tree.

## 2. Propositions offered for verification

Each is falsifiable at the commit above, with a named test whose named mechanism, if removed,
makes it fail. A verifier should try to break these rather than confirm them.

| ID | Proposition | Test | Mechanism whose removal breaks it |
| :--- | :--- | :--- | :--- |
| `P35-04-01` | An over-length `X-Correlation-ID` is refused, not truncated | `a value longer than 64 is refused, not truncated` | `CORRELATION_ID_MAX` + `.max()` in `headers.ts` |
| `P35-04-02` | A request failing header validation never reaches the kernel | asserted in every negative test via `calls.length === 0` | the early return in `app.ts` before `fetchImpl` |
| `P35-04-03` | `X-Tenant-ID` reaches the kernel byte-identical, prefixed or bare | `the prefixed form reaches the kernel unchanged`, `the bare UUID form…` | verbatim `forwarded.set(name, value)` in `app.ts` |
| `P35-04-04` | The gateway never invents `X-Tenant-ID` on the bearer path | `the gateway does not invent the header when it is absent` | absence of any injection in `app.ts` |
| `P35-04-05` | Identifier acceptance equals the kernel's, no wider and no narrower | `accepts every prefix the kernel accepts`, `rejects a prefix the kernel does not accept` | `ACCEPTED_PREFIXES` mirroring `_PREFIXED_ID` |
| `P35-04-06` | The spec's own documented example identifiers are accepted | `accepts the documented examples from HTTP_HEADER_SPEC.md verbatim` | `UUID_SHAPE` being shape-only, not RFC 9562 |
| `P35-04-07` | A 400 never echoes the offending value | `the violation response does not echo the offending value` | violation objects carrying `header` + `message` only |
| `P35-04-08` | An unreachable kernel yields 502 without describing the kernel | `an unreachable kernel is a 502 that does not describe the kernel` | the bare `catch` in `app.ts` |
| `P35-04-09` | `/gateway/health` does not consult the kernel | `gateway health does not consult the kernel` | the route registered before the catch-all |
| `P35-04-10` | The Zod contract binding cannot drift from the frozen schema unnoticed | `the Zod required set equals the JSON Schema required set`, `every JSON Schema property is known…` | `readFileSync` of `tenant-context.json` at run time |
| `P35-04-11` | Every field the contract requires is genuinely required | `each required field is genuinely required` | per-field removal loop over `TENANT_CONTEXT_REQUIRED` |
| `P35-04-12` | Upstream status codes pass through unreinterpreted | `the upstream status is passed through rather than reinterpreted` | `status: upstream.status` in the `Response` |

## 3. Execution result

```text
node --test test/*.test.ts
tests 31   pass 31   fail 0   skipped 0
```

No kernel process is required: the upstream is injected. That is a limitation, recorded in §6.

## 4. Adversarial probes — EBIV R4

Executed 2026-07-31. Each mutation was applied to the working tree, the suite run, and the tree
restored and re-verified at 31/31.

| # | Mutation | Expected | Observed |
| :--- | :--- | :--- | :--- |
| 1 | `CORRELATION_ID_MAX` 64 → 4096 | `P35-04-01` fails | 30 pass, **1 fail** |
| 2 | Forwarding strips `^(usr\|tnt\|mem\|ctx\|corr)_` | `P35-04-03` fails | 30 pass, **1 fail** |
| 3 | `.strict()` removed from `TenantContext` | additional-property test fails | 30 pass, **1 fail** |

A suite that stays green under these mutations would be measuring nothing. These establish that
it is not.

## 5. Defect found during implementation

`HTTP_HEADER_SPEC.md`'s documented identifiers are **not RFC 9562 conformant**:
`tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c` carries variant nibble `5`, where the RFC requires
`8`, `9`, `a` or `b`.

Zod 4's `z.uuid()` enforces the RFC. Using it made the gateway **stricter than the kernel it
fronts** — a 400 at the edge for requests the kernel would have served, including the examples
this repository publishes. The kernel enforces no such thing: `_PREFIXED_ID` matches
`[0-9a-fA-F]` and Python's `uuid.UUID()` accepts any hex-shaped value.

Resolved by validating shape only, with `P35-04-06` locking it in so the stricter rule cannot
return quietly. **Not resolved:** whether bOPEN identifiers should be RFC-conformant UUIDs, and
whether the published examples should be corrected. That belongs with `D-P35-004`.

## 6. Residual risks and what this does not establish

1. **No end-to-end path is proven.** The suite injects the upstream. A real request through the
   live FastAPI kernel to PostgreSQL and back has not been executed. `A-05`'s executed-evidence
   standard is met for the gateway's own behaviour and **not** for the composed path.
2. **`Authorization` and `X-Tenant-ID` diverge between spec and kernel.** The spec marks both
   mandatory; the kernel does not. The gateway mirrors the kernel, because enforcing the spec
   would delete the legacy `X-Context-ID` path by validation default. The divergence is real and
   undecided — see `README.md` §4.2.
3. **No load, timeout, retry or rate-limit behaviour is specified or tested.** The gateway has no
   timeout on the upstream fetch. A slow kernel therefore ties up a gateway connection for as
   long as the platform default allows.
4. **No TLS.** Transport security is a deployment concern and is not addressed here.
5. **`zod@4.4.3` and `hono@4.12.32` are pinned but not vendored or hash-verified** beyond
   `package-lock.json`.

## 7. Clean-room declaration

No upstream source was inspected, copied, translated or adapted. Header rules derive from
`HTTP_HEADER_SPEC.md` and from the kernel's `api.py`, both bOPEN artifacts. Hono and Zod are
consumed as published libraries through public APIs, not as source to port.
`python tools/check_clean_room.py` — PASS.

## 8. Authority

This is a maker's submission. `BOPEN-GOV-EBIV-001` §8 records that an implementing agent
reporting a passing suite is a self-assessment carrying **no verdict weight** — the standard
exists because exactly that claim was once made and found unsupported.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
