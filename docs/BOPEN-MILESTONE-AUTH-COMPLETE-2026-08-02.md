# bOPEN Milestone — Authentication boundary + AUTH-D3 hardening complete (2026-08-02)

**Status:** Historical checkpoint — verified and operator-disposed state as of 2026-08-02
**Type:** Milestone checkpoint (state archive)
**Date:** 2026-08-02
**Recorded by:** Claude (agent, Motor role) — transcribing verified state, no verdict authority
**Supersedes for orientation:** [`BOPEN-STATE-ARCHIVE-2026-08-02.md`](BOPEN-STATE-ARCHIVE-2026-08-02.md) (the earlier Phase 3.5-closure checkpoint, taken before the auth boundary was verified)

---

## 1. What this milestone marks

The kernel authentication boundary and the AUTH-D3 hardening are **built, independently verified,
and operator-disposed** under the EBIV two-agent profile (`§6.5`). This is the completion of the
scope the operator set on 2026-08-02 ("Phase 3.5 + AUTH-D3 hardening").

## 2. Verified state (confirmed against repository objects)

| Item | Candidate | Verdict |
| :--- | :--- | :--- |
| Auth boundary (27 propositions: assertion, bearer-only/AUTH-D1, AUTH-D3 Row 1(a)) | `2c31379` (ballot `5158629`) | `CONFIRMED_UNDER_TWO_AGENT_PROFILE` |
| `D-D3-002` principal enrollment (Option B, out-of-band) | `7450661` | `CONFIRMED_UNDER_TWO_AGENT_PROFILE` (5/5) |
| Row 1(b) gateway creation rate limiting | `7fcd86c` (ballot `8405460`) | `CONFIRMED_UNDER_TWO_AGENT_PROFILE` (8/8, after 2 refutations fixed) |

**Suites at this milestone:** canonical **475/475** against live PostgreSQL; gateway **67/67**.
**Verifier:** Codex, independent of the maker. **Basis:** one verifier + operator disposition — a
two-agent profile verdict, weaker than a two-verifier quorum, stated as such on each record.

## 3. Phase 3.5 — closed

All five work packages disposed: `WP-P35-01`..`03` and `05a` `CONFIRMED_UNDER_TWO_AGENT_PROFILE`;
`WP-P35-04` accepted with two standing refutations (gateway path-normalisation, recorded).

## 4. What the process caught (recorded because it is the point)

Row 1(b) was **refuted twice** before it confirmed — a single- then a double-percent-encoding bypass
of the creation rate limit, each a real evasion the maker's own probes missed on a control that
looked finished. Fixed by decoding the classification path to a fixpoint. The refutation half of
EBIV is what found them.

## 5. Carried, non-blocking (disclosed on the disposition records)

Replay bounded not prevented; single authenticator kernel-wide, no key rotation; the enumeration
oracle on the flag-permitted registration path; the rate limiter in-memory per-instance;
`X-Forwarded-For` trust; out-of-band principal provisioning is a decided deployment path, not code.

## 6. What this milestone is NOT

Not production. No products on the kernel yet (Phase 4). No live IdP bridge (`WP-P35-05b`, moved
out). No deployment beyond the local verification cluster. Phase 3.6 (tenant privacy) is planned,
not built.

## 7. Next

Operator-chosen direction after this checkpoint: a runnable end-to-end demonstration
(gateway → kernel → PostgreSQL), then Phase 4 (products) or the remaining production-hardening gaps.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false   # a verified milestone, not a production declaration
```
