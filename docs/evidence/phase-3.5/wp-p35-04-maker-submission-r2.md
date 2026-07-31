# EVD-P35-04-MAKER-R2 — WP-P35-04 Maker Submission, revision 2 (API Gateway)

**Document ID:** `EVD-P35-04-MAKER-R2`
**Version:** `2.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-01
**Supersedes:** [`EVD-P35-04-MAKER`](wp-p35-04-maker-submission.md) at `c03cd4f…`, withdrawn as critically defective
**Raised by:** [`EVD-P35-CODEX-PREFLIGHT-001`](codex-preflight-wp-p35-04-05a.md) §2, verdict `SUPERSEDED`
**Work package:** [`BOPEN-P35-001`](../../work-packages/BOPEN-P35-001-EXECUTION-PLAN.md) — `WP-P35-04`, deliverable D-09

**Commit OID:** `88e6ed2b4f2ab80a6b8ef0e8d570f761d8725b4b`
**Tree OID:** `39da471ae01ade3e3ee619f788d99fabbe1fde3d`
**Subtree OID (`apps/gateway`):** `485f6b3f0814274700cabcf5d5a38943dd6c4e43`
**Blob OID (`src/app.ts`):** `ac8ce6b761fd55f1131d5d3854436e6dec942348`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifiers:** Codex, Gemini or Kimi
**Admissibility standard:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md)

> Zero ballots cast. All OIDs above read with `git rev-parse` at issue time, not transcribed
> (EBIV R3, `A-07`).

---

## 1. Why revision 2 exists

Revision 1 was wrong in a way its own tests could not see.

`EVD-P35-04-MAKER` offered twelve propositions at `c03cd4f…` with 31 passing tests and three
mutation probes. An adversarial sweep on 2026-07-31 then reproduced an **unauthenticated SSRF**
in that commit: `buildUpstreamUrl` resolved the caller's path as a *relative reference*, so a
path beginning `//` discarded the base authority entirely and the caller chose the upstream host.
The gateway forwarded the client's `Authorization` bearer token to it and returned its body.

Codex, holding the verifier seat, checked the anchor before ruling and refused to ballot a
superseded commit. **The stale handoff was the maker's error**, not the verifier's: it was
written before the defect was known and aimed an independent agent at code with an open proxy in
it.

Revision 1 is withdrawn rather than edited. Its propositions were true of a commit that should
not ship, and deleting them would erase the record of a maker submission that passed its own
tests while carrying a critical defect — which is the most useful thing in this file.

## 2. What changed since revision 1

| Defect | Severity | Disposition |
| :--- | :--- | :--- |
| Caller could select the upstream host (SSRF + token exfiltration) | **CRITICAL** | Fixed structurally — §3 |
| `content-encoding` / `content-length` copied onto an already-decompressed body | HIGH | Fixed — response desync closed |
| All but the last `Set-Cookie` dropped | MEDIUM | Fixed via `getSetCookie()` |
| Headers named in `Connection` forwarded (RFC 9110 §7.6.1) | LOW | Fixed — dynamic hop-by-hop set |
| 502 asserted a network diagnosis it had not established | LOW | Reworded |
| Percent-encoding decoded and `..` normalised before forwarding | MEDIUM | **NOT fixed — see §6.1** |

196 lines changed across `src/app.ts` and `test/headers.test.ts`. Tests: **31 → 43**.

## 3. The fix, and why it is structural

```ts
export function buildUpstreamUrl(kernelBaseUrl: string, path: string, search: string): URL {
  const upstream = new URL(kernelBaseUrl);
  const basePath = upstream.pathname.replace(/\/+$/, '');
  upstream.pathname = `${basePath}${path.startsWith('/') ? '' : '/'}${path}`;
  upstream.search = search;
  return upstream;
}
```

The URL is built **from the base object**; only `pathname` and `search` are assigned, and
assigning `pathname` cannot alter an origin. No input can move the request off `kernelBaseUrl`.

A denylist of dangerous prefixes would have had to anticipate every encoding — `//host`,
`///host`, `/\host` (WHATWG folds `\` to `/` for special schemes), `//user:pass@host`. This
anticipates none. That difference is the proposition in `P35-04R-01`, and a verifier should
attack it by finding an input that still escapes.

## 4. Propositions offered for verification

Falsifiable at `88e6ed2…`. Twelve propositions carried forward from revision 1 remain valid and
are renumbered `P35-04R-03`..`P35-04R-14`; the four below are new.

| ID | Proposition | Test | Mechanism whose removal breaks it |
| :--- | :--- | :--- | :--- |
| `P35-04R-01` | No request path can move the upstream request off the kernel origin | `"//evil.example/x" cannot move the request off the kernel origin` (+4 sibling vectors) | `buildUpstreamUrl` assigning `pathname` on a base-derived URL |
| `P35-04R-02` | A base path prefix survives instead of being discarded | `a base path prefix is preserved rather than discarded` | same |
| `P35-04R-03` | `content-encoding` is not copied from upstream | `content-encoding is not copied…` | `BODY_FRAMING` exclusion |
| `P35-04R-04` | Upstream `content-length` is not copied onto a different body | `the upstream content-length is not copied…` | `BODY_FRAMING` exclusion |
| `P35-04R-05` | Every `Set-Cookie` survives, not only the last | `every Set-Cookie survives, not only the last` | `getSetCookie()` + `append` |
| `P35-04R-06` | A header named in `Connection` is not forwarded | `a header named in Connection is not forwarded` | `hopByHopFor` |
| `P35-04R-07` | An over-length `X-Correlation-ID` is refused, not truncated | `a value longer than 64 is refused, not truncated` | `CORRELATION_ID_MAX` + `.max()` |
| `P35-04R-08` | A request failing header validation never reaches the kernel | `calls.length === 0` in every negative test | early return before `fetchImpl` |
| `P35-04R-09` | `X-Tenant-ID` reaches the kernel byte-identical, prefixed or bare | `the prefixed form reaches the kernel unchanged` | verbatim `forwarded.set` |
| `P35-04R-10` | The gateway never invents `X-Tenant-ID` on the bearer path | `the gateway does not invent the header when it is absent` | absence of injection |
| `P35-04R-11` | Identifier acceptance equals the kernel's, no wider, no narrower | `accepts every prefix the kernel accepts` / `rejects a prefix the kernel does not accept` | `ACCEPTED_PREFIXES` |
| `P35-04R-12` | The spec's own documented examples are accepted | `accepts the documented examples from HTTP_HEADER_SPEC.md verbatim` | `UUID_SHAPE` being shape-only |
| `P35-04R-13` | A 400 never echoes the offending value | `the violation response does not echo the offending value` | violations carrying `header` + `message` only |
| `P35-04R-14` | Upstream status codes pass through unreinterpreted | `the upstream status is passed through rather than reinterpreted` | `status: upstream.status` |

## 5. Execution result and probes

```text
node --test test/*.test.ts
tests 43   pass 43   fail 0
```

**Mutation probe, 2026-08-01.** Restoring the vulnerable relative-reference form
(`new URL(path + search, kernelBaseUrl)`) breaks **7 of 43** tests. Tree restored and
re-verified at 43/43.

Earlier probes from revision 1 remain valid for the propositions they cover: relaxing
`CORRELATION_ID_MAX` breaks 1; stripping identifier prefixes on forward breaks 1; removing
`.strict()` from the contract binding breaks 1.

## 6. Residual risks

### 6.1 Path normalisation — known, reproduced, not fixed

Hono runs `decodeURI` on any path containing `%`, then `new URL` applies dot-segment
normalisation. Observed:

| Client sent | Kernel received |
| :--- | :--- |
| `/v1/../admin` | `/admin` |
| `/v1/%2E%2E/admin` | `/admin` |
| `/v1/x%2E%2E%2F%2E%2E/etc` | `/v1/x..%2F../etc` |

The revision-1 test named *"the request path and method reach the kernel unchanged"* passed only
because its fixture contained no `.` or `%`. **The test's name claimed more than the test
checked.**

Consequence: anything in a deployment that authorizes or routes on the raw request target — an
ingress restricting the gateway to `/v1/*` — is undone one hop later, and a kernel route whose
path parameter legitimately contains an encoded `..` receives a different value than was sent.

Not fixed here because preserving the raw request target requires deciding which layer owns path
semantics, which is a contract question rather than a patch. **A verifier should treat this as an
open defect, not as an accepted limitation.**

### 6.2 Carried forward from revision 1

1. **No end-to-end path proven.** The suite injects the upstream; no request has been executed
   through the live FastAPI kernel to PostgreSQL and back.
2. **No timeout on the upstream fetch.** A slow kernel ties up a gateway connection indefinitely.
3. **No TLS.** Transport security is a deployment concern, unaddressed here.
4. Dependencies pinned but not vendored or hash-verified beyond `package-lock.json`.

### 6.3 What revision 1 teaches about this submission

Revision 1 had 31 passing tests, three mutation probes that all bit, a documented limitations
section, and a critical remotely-exploitable defect. Its probes were real and its propositions
were true — they simply did not cover the line that mattered.

This revision has more tests and one more probe. That is not evidence it is correct. It is the
same kind of evidence revision 1 had.

## 7. Clean-room declaration

No upstream source inspected, copied or adapted. Header rules derive from `HTTP_HEADER_SPEC.md`
and the kernel's `api.py`. Hono and Zod consumed as published libraries.
`python tools/check_clean_room.py` — PASS.

## 8. Authority

A maker's submission. `BOPEN-GOV-EBIV-001` §8: an implementing agent reporting a passing suite is
a self-assessment carrying **no verdict weight**. One verifier does not confirm — §6.1 requires
two, §6.3 escalates below that.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
