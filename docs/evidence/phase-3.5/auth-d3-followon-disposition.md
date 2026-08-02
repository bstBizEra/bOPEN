# EVD-P35-AUTH-D3-FOLLOWON-DISPOSITION — D-D3-002 + Row 1(b), §6.5 disposition surface

**Document ID:** `EVD-P35-AUTH-D3-FOLLOWON-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-02 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed both follow-ons per the recommendation and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-02
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md) (Option B)
**Subject:** [`EVD-P35-AUTH-D3-FOLLOWON-MAKER`](wp-p35-auth-d3-followon-maker.md); [`DEC-P35-AUTH-D3-DOCKET`](../../decisions/DEC-P35-AUTH-D3-DOCKET.md) `D-D3-002`, `D-D3-001` Row 1(b)

---

## 1. The verdicts — recorded as fact, verified from repository objects

Both operator-disposed AUTH-D3 follow-ons are admissibly **CONFIRMED** by the independent verifier.
Confirmed against `git` objects and `ballots.jsonl`, not a self-report.

| Group | Candidate | Ballots | Verifier |
| :--- | :--- | :--- | :--- |
| **A — `D-D3-002` principal enrollment (Option B)** | `7450661` (`api.py` `4a58ddb`, byte-identical at HEAD) | **5/5 `CONFIRMED`** (`P35-D3c-01..05`) | `codex` |
| **B — Row 1(b) gateway rate limiting** | `7fcd86c` (ballot commit `8405460`) | **8/8 `CONFIRMED`** (`P35-D3b-01..08`) | `codex` |

All 13 ballots are admissible (R1–R5 true), attributed to `codex` (distinct from the maker), each
ballot commit touches only `ballots.jsonl`.

## 2. The refutations, and why they matter

Group B was **refuted twice before it was confirmed** — this is the process working, not a failure:

- **R1 (`P35-D3b-05`)** — `POST /v1/%70rincipals` (single percent-encoding) bypassed the limiter: it
  classified the raw path while the kernel routes the decoded one.
- **R2 (`P35-D3b-05`/`-08`)** — `/v1/%2570rincipals` (double-encoding) still bypassed it: the chain
  decodes more than once.
- **R3** — fixed by decoding to a **fixpoint**, sound against any encoding depth. 8/8 confirmed.

Both refutations found real evasions the maker's own probes missed, on a control that *looked*
finished. `DEC-P35-TWO-AGENT-QUORUM` §3: the refutation half is what finds defects.

## 3. What the verdicts close

- **`D-D3-002`** — principal creation is out-of-band, not a public endpoint. The last unauthenticated
  identity-creating endpoint is closed on a configured deployment.
- **Row 1(b)** — `POST /v1/principals` and `/v1/tenants` are rate-limited at the edge, including
  every percent-encoded alias the kernel would route to a creation handler.

## 4. The disclosed-risk record — weaker than a quorum, and the carried gaps

`DEC-P35-TWO-AGENT-QUORUM` §5 requires the weaker basis stated rather than let `CONFIRMED` imply
parity:

- **One verifier, not two.** Two blind verifiers catch what one's blind spot misses.
- **The rate limiter is in-memory and per-instance.** Two gateway instances hold independent
  counters, so the effective global ceiling is per-instance. A shared store is a later concern.
- **Per-source keying trusts `X-Forwarded-For`.** Only as trustworthy as the upstream proxy; the
  global ceiling is the backstop when it is forged.
- **The enumeration oracle is not closed** on the flag-permitted (local) path — `register_principal`
  still answers "is this address registered?" through status, body length and timing.
- **Out-of-band provisioning is a deployment path, not code here** — Option B closes the endpoint;
  the operator/SCIM mechanism that creates principals in production is out of scope.

## 5. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

Under §6.5 / Option B, confirmation requires the admissible ballots in §1 **plus** an explicit
operator disposition on this disclosed-risk record. The maker records; the maker does **not**
dispose. Left unfilled for the operator.

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  group_a_candidate: 7450661   # D-D3-002, 5/5 CONFIRMED
  group_b_candidate: 7fcd86c   # Row 1(b), 8/8 CONFIRMED (ballot 8405460)
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the five items in §4 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-02
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through (this disposition):** the profile verdicts are noted in
[`manifest.json`](manifest.json); `DEC-P35-AUTH-D3-DOCKET` `D-D3-002` and `D-D3-001` Row 1(b) are
marked verified-and-disposed. This completes the AUTH-D3 hardening. The five disclosed gaps in §4
remain as recorded, non-blocking follow-on concerns.

**On a `CONFIRMED_UNDER_TWO_AGENT_PROFILE` disposition (advisory follow-through):** record the profile
verdicts in [`manifest.json`](manifest.json); mark `DEC-P35-AUTH-D3-DOCKET` `D-D3-002` and `D-D3-001`
Row 1(b) as verified-and-disposed. That completes the AUTH-D3 hardening.

## 6. Authority

This surface decides nothing and changes no code.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
