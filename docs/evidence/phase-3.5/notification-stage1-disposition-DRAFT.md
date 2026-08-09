# Notification Stage 1 disposition — DRAFT, UNSIGNED

> **THIS IS NOT A DISPOSITION.** A maker-prepared draft carrying no verdict and no authority until
> the operator records the decision. `AGENTS.md` §25.1 step 8 reserves disposition to the Completion
> Authority, which is not an agent role, and `BOPEN-GOV-EBIV-001` §3 disqualifies the maker — Claude
> authored the migration, the tests, the registrations and the traceability.
>
> It exists so the operator can see what accepting would mean. **Delete this banner only when
> signing.**

**Artifact:** Notification foundation Stage 1 (`BOPEN-NOTIFY-001`, migration `021`)
**Candidate:** `d3a5be25ce6e37d26b740579e58c4c1c4c3fbf52`
**Tree:** `ba2eb5d09cebba7a1ce9c2f4f0a6d9aeacfde239`
**Authorization:** `DEC-P4-ENTRY` §12, recorded before the build (`d4b40ef`)
**Maker:** Claude · **Independent verifier:** Codex, ballot commit `bd42b2e`

---

## 1. Evidence

| | |
| :--- | :--- |
| Ballots | **19 `CONFIRMED`, 1 `INADMISSIBLE`, 0 `REFUTED`** |
| Canonical suite at candidate | `Ran 680 tests in 623.203s` / `OK` / 0 FAIL-ERROR |
| Schema | 8 tables, **all under `ENABLE` + `FORCE ROW LEVEL SECURITY`** |
| Registration (§25.1 step 3) | Both places — `TENANT_SCOPED_TABLES` and trial→paid `COPY_ORDER`, parents before children |
| Verifier eligibility | Zero Codex-authored lines in any reviewed file |

## 2. What accepting would mean — the disclosed-risk record

### 2.1 One proposition is inadmissible, not confirmed

`NOTIFY-S1-ISO-WRITE-01` was recorded `INADMISSIBLE` on **R5**. The behaviour holds — the
cross-tenant write is refused with `InsufficientPrivilege`, SQLSTATE 42501 — but the row names the
`WITH CHECK` clause as the mechanism whose removal breaks the test, and for a PostgreSQL `FOR ALL`
policy an omitted `WITH CHECK` **reuses `USING`**. Removing the named clause admits nothing.

**Accepting means accepting 19 verified propositions, not 20.** The twentieth behaviour is sound and
its attribution is not.

### 2.2 Eight gaps are disclosed and unverified

| Gap | |
| :--- | :--- |
| `notification_provider_health` deny-by-default | asserted structurally; **no behavioural probe** |
| `notification_quota_suspend` | **no probe of any kind** — the emergency-suspension table |
| `WITH CHECK` on dispatch / quota / fairness | probed only on `notifications` |
| `unq_receipt_dedup` cross-tenant oracle | **deliberate**, and the verifier judged the disclosure *incomplete* about cross-tenant availability and key-space poisoning |
| Duplicate attempts | no uniqueness on `(tenant_id, dispatch_id, attempt_no)` |
| Three of six CHECK vocabularies | unprobed |
| Stage-1 boundary | prose only; no test proves the deferred surface is absent |

### 2.3 The tenant-cascade defect it carried is **fixed**, but that fix is itself undisposed

Verification found that deleting a tenant erased `notification_attempt` and `notification_receipt` —
the append-only guarantee did not survive tenant deletion. **That is now closed by migration `022`**
(`WP-P35-08`, 16/16 `CONFIRMED`).

But `WP-P35-08` **has not been disposed**. Accepting Notification Stage 1 today accepts an artifact
whose most serious known defect is repaired by a package the operator has not yet accepted.

### 2.4 Scope

Stage 1 is schema, forced RLS and tenant isolation. **Not built and explicitly deferred:** the
worker/claimer plane, callback ingest, provider adapters, the elevated
`bopen_notify_claimer` / `bopen_notify_callback` roles and their grants, templates, recipient
resolution, retry/cancel, export and cache surfaces.

The rows are Stage-1 scoped for this reason — `NOTIFY-INV-01` alone spans read, infer, request,
retry, cancel, template, resolve, callback, export, cache and observe, and Stage 1 builds none of
those surfaces.

### 2.5 The evidence rows were corrected before submission

An adversarial audit found **nine of twenty** first-draft rows wrong, every error running in the
direction that flattered the build — including an `executed_db` claim on a test running no SQL and a
mechanism ("grants") appearing nowhere in the migration set. The submitted rows are a second
attempt, and one of them was still found inadmissible.

## 3. If accepted, the verdict is

`CONFIRMED_UNDER_TWO_AGENT_PROFILE` — **not** bare `CONFIRMED`. EBIV §6.5.2 requires the label
because this rests on one independent verifier plus an operator disposition, and the two verdicts
must not be conflated.

## 4. Fields the operator must supply

```
Decision           : ACCEPT / REJECT / ACCEPT WITH RECORDED CONDITIONS
Verdict label      : CONFIRMED_UNDER_TWO_AGENT_PROFILE
Scope              : 19 of 20 propositions; NOTIFY-S1-ISO-WRITE-01 excluded as INADMISSIBLE
Disclosed risks    : acknowledged (§2.1-§2.5) / with exceptions: ______
Sequencing         : does this depend on WP-P35-08 being disposed first?  YES / NO
Approver           : BizEra <ounkhamvilay@gmail.com>
Decision timestamp : ______
```

**This draft is not evidence of a decision and must not be cited as one.**
