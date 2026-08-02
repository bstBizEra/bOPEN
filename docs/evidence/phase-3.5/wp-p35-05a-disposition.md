# EVD-P35-05A-DISPOSITION — WP-P35-05a auth boundary, §6.5 disposition surface

**Document ID:** `EVD-P35-05A-DISPOSITION`
**Version:** `1.0.0`
**Status:** **AWAITING_OPERATOR_DISPOSITION** — the verifier verdict is recorded as fact; the §6.5 disposition below is reserved to the operator and is **not** filled by the maker.
**Issued:** 2026-08-02
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing artifacts:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md) (Option B, ratified 2026-08-02)
**Subject:** [`EVD-P35-05A-MAKER-R5`](wp-p35-05a-maker-submission-r5.md); [`DEC-P35-AUTH-D3-DOCKET`](../../decisions/DEC-P35-AUTH-D3-DOCKET.md) `D-D3-001` Row 1(a)

---

## 1. The verifier verdict — recorded as fact, verified from repository objects

The full 27-proposition kernel authentication boundary was balloted by the independent verifier and
**every ballot is admissible and CONFIRMED**. Confirmed against `git` objects and
`docs/evidence/phase-3.5/ballots.jsonl`, not from a self-report:

| Field | Value |
| :--- | :--- |
| Candidate commit | `2c31379ad7ed888ffad04ee0bff07172cc10cfca` |
| Candidate tree | `b76759456196fcb8eebd387b0335bb08620ee99a` |
| `invariant-traceability.csv` blob | `2135601496c8439ae3dbfcb546e3496981065905` |
| Ballot commit | `5158629b849074ce7730b40e52f84f4548f4c1da` (parent `2c31379`) |
| Verifier | `codex` — `Codex gpt-5.6-sol (BST-SA Verifier) <codex@bst.local>`, distinct from the maker |
| Ballot commit touches | `ballots.jsonl` only (+27); no source, no contracts |
| Verdicts | **27 `CONFIRMED`, 0 `REFUTED`, 0 `INADMISSIBLE`** |
| Admissibility | R1–R5 true on every ballot (R2 passes at the traced candidate) |
| Suites | canonical 470/470 (PostgreSQL); gateway 47/47; focused boundary 56/56 |
| Validators | evidence-anchor PASS; ballot-attribution PASS (attribution only — see §3) |

The 27 propositions, exactly: assertion verification `P35-05a-02..11`; lifecycle
`P35-05aR3-01/04`, `P35-05aR4-01/02`; bearer-only / `AUTH-D1` `P35-05aR2-01..08`; tenant
provisioning / `AUTH-D3` Row 1(a) `P35-D3a-01..05`.

**Supersession note.** An earlier R4 candidate (`119f2d8`) carried 23 ballots recorded R2-admissible;
that was incorrect — those propositions were never traced (see R5 §6.5). The admissible verdict is
the 27 at `2c31379`. No disposition should cite the R4 ballots.

## 2. What the verdict closes

- Tenant squatting and unauthenticated owner-binding (`P35-D3a-01..05`) — the last live
  authentication hole named in `DEC-P35-AUTH-D3-DOCKET` Row 1(a).
- The subject-assertion boundary: signature, issuer, audience, expiry, `alg:none`, mandatory
  claims, lifetime ceiling (including the fractional-`NumericDate` defect R4 fixed), and refusal
  opacity.
- Bearer-only enforcement (`AUTH-D1`): a context identifier alone authorizes nothing; a rejected
  token does not downgrade to header identity; the legacy profile is off by default and vetoed on
  production.

## 3. The disclosed-risk record — why this basis is weaker than a quorum

`DEC-P35-TWO-AGENT-QUORUM` §5 requires the weaker basis to be stated on the verdict rather than let
`CONFIRMED` imply parity. Stated:

- **One verifier, not two.** Two blind verifiers catch what one verifier's blind spot misses; that
  property is surrendered here. The mitigation — adversarial sweeps and mutation probes — found real
  defects this work stream but is not a second independent verdict.
- **The verifier is the same agent (Codex) across the whole boundary.** No second engine
  cross-checked its lens.

**What the verdict does NOT establish (carried, out of this scope):**

1. **Replay is bounded, not prevented** — within the 300s lifetime an assertion is still
   replayable; closing it needs a spent-`jti` store (`D-P35-004..010` block it).
2. **`POST /v1/principals` remains unauthenticated** — the enrollment recursion, `D-D3-002`, open
   by design; recommended disposition **B** (out-of-band provisioning) is not yet decided.
3. **`AUTH-D3` Row 1(b) rate-limiting is not implemented** — needs a keying choice (per-source vs
   global vs gateway-layer). Availability hardening, not a confidentiality hole; the bounded
   blast radius (no cross-tenant reach) is unchanged.
4. **One authenticator kernel-wide** — no per-tenant authenticator, no key rotation exercised.

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

Under §6.5 / Option B, confirmation requires the admissible ballot in §1 **plus** an explicit
operator disposition on this disclosed-risk record. The maker records the verdict; the maker does
**not** dispose. This block is left unfilled for the operator.

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: 2c31379ad7ed888ffad04ee0bff07172cc10cfca
  ballot_commit: 5158629b849074ce7730b40e52f84f4548f4c1da
  decision: <PENDING — CONFIRMED_UNDER_TWO_AGENT_PROFILE | REJECTED | DEFERRED>
  disclosed_risk_acknowledged: <PENDING — true/false; the four items in §3 are read and accepted>
  approver: <PENDING — Operator: BizEra <ounkhamvilay@gmail.com> acting as Completion Authority>
  decision_timestamp: <PENDING>
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**On an operator disposition of `CONFIRMED_UNDER_TWO_AGENT_PROFILE`, the follow-through (advisory):**
record the profile verdict in [`manifest.json`](manifest.json) per §6.5.4; mark
`DEC-P35-AUTH-D3-DOCKET` `D-D3-001` Row 1(a) as verified-and-disposed; and leave Row 1(b) and
`D-D3-002` on their own surfaces. None of that is done here.

## 5. Authority

This surface decides nothing and changes no code. It records a verifier verdict and reserves the
disposition to the operator.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
