# EVD-CONTACTPOINT-DISPOSITION — Party ContactPoint extension, §6.5 disposition surface

**Document ID:** `EVD-CONTACTPOINT-DISPOSITION`
**Version:** `1.0.0`
**Status:** **DISPOSED 2026-08-05 — `CONFIRMED_UNDER_TWO_AGENT_PROFILE`.** Operator (`BizEra`, Completion Authority) disposed the verdict and acknowledged the disclosed-risk record. Transcribed by Claude (Motor); not a maker approval.
**Issued:** 2026-08-05
**Maker/Recorder:** Claude (agent, Motor role) — `claude@bst.local`, advisory only
**Governing:** [`BOPEN-GOV-EBIV-001`](../../00-governance/BOPEN-GOV-EBIV-001.md) §6.5; [`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md)
**Subject:** [`EVD-CONTACTPOINT-MAKER`](contactpoint-maker.md); [`DEC-P4-ENTRY`](../../decisions/DEC-P4-ENTRY.md) §10

---

## 1. The verifier verdict — confirmed from repository objects

Confirmed against `ballots.jsonl` and `git`:

| Field | Value |
| :--- | :--- |
| Candidate | `c48727c` |
| Ballot commit | `1a74913` (author `codex@bst.local`) |
| Verdicts | **22/22 `CONFIRMED`** (`CP-INV-*`), 0 `REFUTED` — a clean first pass, no refutation |
| Admissibility | R1–R5 true on every ballot; verifier `codex`, distinct from the maker (Claude); `independent_of_maker=true` |
| Suite | canonical 616/616 against PostgreSQL |

The verifier's independent probe confirmed that resolve-recipient returns a destination ONLY for a
verified, exact-purpose, exact-channel-type, currently-effective contact point of a Party of the
caller's tenant, and returned exactly `dest@example.com` after verification; it refused unverified,
wrong-purpose, wrong-channel, cross-tenant, and future-effective/retired endpoints with a uniform 422;
for a Party with no contact point (whose owning principal HAS an email) it refused and never surfaced
`principals.email` (resolve queries only `party_contact_points`, never `principals`); the append-only
verification history resisted UPDATE/DELETE and survived a contact-point delete (refused by
`ON DELETE RESTRICT`); a cross-tenant contact point attach was refused by the composite FK
`fk_cp_party`; `INV-MIGRATE-COVERAGE-01` stays green with both new tables in the RLS classification and
the migrate tool's `COPY_ORDER`.

## 2. What the verdict closes

The ContactPoint extension — a tenant-scoped, Party-owned registry of typed, purpose-classified,
verifiable endpoints. The keystone is that resolve-recipient never substitutes a fallback and never
uses `principals.email`: a send resolves to a Party's own verified endpoint or it refuses. It clears
`NOTIFY-D-01`, Notification's recipient dependency.

## 3. The disclosed-risk record (acknowledged by the operator)

- **`email` and `phone` only.** `postal` is deferred (depends on the gated/unbuilt Location
  foundation); social/push/webhook deferred.
- **Verification ceremony deferred (CP-D-05).** The one path to `verified` in this slice is a governed,
  audited **administrative assertion** (`verification_method='administrative_assertion'`, recorded in
  the append-only history) — distinct from a challenge (OTP/magic-link), which is a follow-up slice. No
  create/update path can mint a verified endpoint; changing an endpoint value resets verification to
  `unverified`.
- **Retire is a tombstone, not a hard delete** — a retired endpoint keeps its row and its append-only
  verification history and is no longer effective.
- **The resolver returns a per-send snapshot, not a continuing consent.** Party owns the endpoint;
  Notification consumes it (CP-INV-12). This unblocks Notification's recipient dependency
  (`NOTIFY-D-01`); it does not build Notification, which remains gated.
- **One verifier, not two** (two-agent profile).

## 4. Disposition — RESERVED TO THE OPERATOR (Completion Authority)

```yaml
disposition:
  verdict_basis: one_verifier_plus_operator            # EBIV §6.5 two-agent profile
  candidate_commit: c48727c
  ballot_commit: 1a74913   # Codex, 22/22 CONFIRMED, verified from ballots.jsonl
  decision: CONFIRMED_UNDER_TWO_AGENT_PROFILE
  disclosed_risk_acknowledged: true                    # the items in §3 are read and accepted
  approver: "Operator: BizEra <ounkhamvilay@gmail.com>, Completion Authority"
  decision_timestamp: 2026-08-05
  recorded_by: Claude (Motor), transcribing — execution_authority:false approval_authority:false
```

**Recorded follow-through:** the profile verdict is noted in [`manifest.json`](manifest.json); the
ContactPoint extension is verified-and-disposed. Notification and the other gated foundations enter on
their own operator dispositions.

## 5. Authority

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
