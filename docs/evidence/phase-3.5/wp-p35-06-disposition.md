# EVD-P35-06-DISPOSITION — WP-P35-06 placement seam, §6.5 disposition surface

**Document ID:** `EVD-P35-06-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-03 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-03
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md) (Option B)
**Subject:** [`EVD-P35-06-MAKER`](wp-p35-06-placement-maker.md); [`DEC-P35-TENANCY-MODEL`](../../decisions/DEC-P35-TENANCY-MODEL.md) Option D + §9 (Option C, strict)

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `docs/evidence/phase-3.5/ballots.jsonl` and `git`, not the run's self-report:

| Field | Value |
| :--- | :--- |
| Candidate | `bfb7bf23b16170ac4983497eb997c46c07902087` |
| Ballot commit | `53a061d` (parent `4b2d370`; author `codex@bst.local`; touches `ballots.jsonl` only, +7) |
| Verdicts | **7/7 `CONFIRMED`** (`P35-06-01..07`), 0 `REFUTED` |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker |
| Suite | canonical 488/488 |

No proposition was refuted, so the disposition proceeds.

## 2. What the verdict, once confirmed, would close

The strict fail-closed placement seam (`WP-P35-06`, Option C): a tenant is routed to the database
that holds its data, an **unregistered or unroutable tenant is refused rather than silently served
against the shared pool**, and a dedicated connection is identity-verified before use. This is what
"one tenant, one database" and "tenant privacy is structural" require of the routing layer.

## 3. The refutations that shaped it (recorded — the process working)

Before this submission the A-09 interpretation was corrected by an **independent immune review**: the
tempting small option (default unregistered tenants to the shared pool) was shown to be
*fail-open-to-shared*, re-opening the silent mis-route A-09 exists to close. The operator ratified the
strict option for safety (`DEC-P35-TENANCY-MODEL` §9). No maker echo chamber: the review changed the
design.

## 4. The disclosed-risk record — weaker than a quorum, and the carried items

`DEC-P35-TWO-AGENT-QUORUM` §5 requires the weaker basis stated rather than let `CONFIRMED` imply
parity:

- **One verifier, not two.** A single independent verdict; the maker's suite carries no verdict weight.
- **Resolution is per-`tenant_session` call, not at the request boundary** (`DEC-P35-TENANCY-MODEL`
  §9.3). Same security property; one extra placement read per tenant-scoped call. Boundary resolution
  is a tracked refinement.
- **No dedicated database is provisioned yet** — the resolver routes to one when configured; the
  provisioning path and trial→paid migration are deferred until a paying tenant exists.
- **The entitlement→`tenants` foreign key is scheduled, not added** — it needs the deferred
  `VARCHAR(64)→UUID` type migration (migration 004). Until then the strict resolver enforces the
  registration invariant at the routing boundary.
- **`verify_connection_serves` is exercised structurally**, not against a real dedicated database.

## 5. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

Under §6.5 / Option B, confirmation requires the admissible ballot (§1, once confirmed) **plus** an
explicit operator disposition on this disclosed-risk record. The maker records; the maker does not
dispose. Left unfilled.

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: bfb7bf23b16170ac4983497eb997c46c07902087
  ballot_commit: 53a061d   # Codex, 7/7 CONFIRMED, verified from ballots.jsonl
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the five items in §4 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-03
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through (this disposition):** the profile verdict is noted in
[`manifest.json`](manifest.json); `WP-P35-06` is marked verified-and-disposed. "One tenant, one
database" is now structurally correct and verified at the routing layer. The five disclosed items in
§4 remain as recorded, non-blocking follow-on work (boundary-resolution refinement, dedicated-DB
provisioning, the FK migration, a live dedicated-DB identity probe).

**On a `CONFIRMED_UNDER_TWO_AGENT_PROFILE` disposition (advisory follow-through):** record the profile
verdict in [`manifest.json`](manifest.json); mark `WP-P35-06` verified-and-disposed in the WP doc;
then MILE-4.1 HTTP layer proceeds on the verified seam.

## 6. Authority

This surface decides nothing and changes no code.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
