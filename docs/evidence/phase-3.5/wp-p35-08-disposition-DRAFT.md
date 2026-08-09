# WP-P35-08 disposition — DRAFT, UNSIGNED

> **THIS IS NOT A DISPOSITION.** It is a maker-prepared draft. It carries no verdict and no
> authority until the operator records the decision themselves. `AGENTS.md` §25.1 step 8 and
> `BOPEN-GOV-EBIV-001` reserve disposition to the Completion Authority, which is not an agent role,
> and the maker of this package is disqualified from it twice over.
>
> It exists so the operator can see exactly what accepting would mean before deciding, not so the
> deciding is done for them. **Delete this banner only when signing.**

**Work package:** `WP-P35-08` — append-only evidence survives tenant deletion
**Candidate:** `0412b85f02f3cd3249d46cb3b7031029de3a9f81`
**Tree:** `7a4eb96b16ba60ef71c67140cbf7218a3fc608db`
**Maker:** Claude (agent, Motor role)
**Independent verifier:** Codex — ballot commit `bf878c6`
**Baseline:** `arch-baseline/2026-08-08-pre-tenant-cascade-restrict`

---

## 1. What the evidence shows

| | |
| :--- | :--- |
| Ballots | **16 `CONFIRMED`, 0 `REFUTED`, 0 inadmissible** |
| Canonical suite at candidate | `Ran 685 tests in 690.860s` / `OK` (verifier's own run) |
| Removal sensitivity | Down migration executed: `CASCADE|11` → suite `FAILED (failures=11)`; re-applied: `RESTRICT|11` → `OK` |
| Verifier eligibility | Zero Codex-authored lines across migrations 013/014, 019–022 and both test files |
| Governance validators | Authority bootstrap, repository validation, clean-room, evidence anchors, ballot attribution — all passing |

The defect this package closes was reproduced live before the fix: deleting a tenant erased its
recorded delivery evidence. Eleven tables across four foundations carried the same shape.

## 2. What accepting this would mean — the disclosed-risk record

Under EBIV §6.5 a disposition acknowledges the disclosed risks. These are what would be accepted:

1. **Tenant offboarding now has a prerequisite and no path.** A tenant holding evidence cannot be
   deleted, and no archival or release capability exists. This is the intended consequence of
   Option 2, but it means tenant deletion is now blocked in practice with nothing built to unblock
   it.

2. **Tenant deletion has no application-level path at all.** `bopen_app` cannot delete a tenant —
   `tenants` has no DELETE policy — so deletion is a superuser act bypassing every isolation policy.
   `AGENTS.md` §8 requires audit treatment for privileged access, and none exists for this act.
   Recorded as an out-of-scope gap; accepting this disposition does not resolve it.

3. **R-1 does not isolate each table's own edge.** It proves a tenant holding evidence cannot be
   deleted; R-7 proves each table's own declaration. The verifier examined the pairing and judged it
   sufficient as worded, but the pairing is what is being accepted, not eleven independent proofs.

4. **R-7 is migration-syntax based.** A future SQL style outside its regex conventions would silently
   stop being covered. The verifier recorded this as a maintenance risk.

5. **The migration was applied to the shared database before verification.** A reader inspects a
   database already carrying the change; the prior state is reachable only through the baseline tag.

## 3. Defects found during this package, and their state

| Found by | Defect | State |
| :--- | :--- | :--- |
| Maker (mutation) | R-1 probes bind to the parent chain, not the leaf | Recorded in `WP-P35-08` §12; mechanism column corrected before submission |
| Maker (pre-build) | R-2 as originally written was false — `bopen_app` cannot delete a tenant at all | Corrected in §11 before any test was made to pass |
| **Verifier** | `schema_migrations` did not record version 022 — the maker applied it with `psql -f`, bypassing the ledger | **Fixed** by re-running `tools/db_bootstrap.py --apply`; `022` now recorded with checksum |
| Verifier | R-6 (down migration never executed) | **Closed by the verifier**, who executed it |

## 4. If accepted, the verdict is

`CONFIRMED_UNDER_TWO_AGENT_PROFILE` — **not** bare `CONFIRMED`. EBIV §6.5.2 requires the label,
because this rests on one independent verifier plus an operator disposition rather than §6.1's two
verifiers, and the two verdicts must not be conflated.

## 5. Fields the operator must supply

```
Decision           : ACCEPT / REJECT / ACCEPT WITH RECORDED CONDITIONS
Verdict label      : CONFIRMED_UNDER_TWO_AGENT_PROFILE
Disclosed risks    : acknowledged (§2 items 1-5) / with exceptions: ______
Approver           : BizEra <ounkhamvilay@gmail.com>
Decision timestamp : ______
```

**This draft is not evidence of a decision and must not be cited as one.** If the operator rejects,
or accepts with conditions, this file is superseded rather than edited.
