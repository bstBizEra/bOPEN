# EVD-P2-PROVISIONAL — Phase 2 Provisional Decisions & Authority Deviation Record

**Document ID:** `EVD-P2-PROVISIONAL-001`
**Version:** `1.0`
**Status:** Maker record — awaiting independent check
**Issued:** 2026-07-29
**Work package:** [`BOPEN-P2-001`](../../work-packages/BOPEN-P2-001-EXECUTION-PLAN.md)
**Governing artifact:** [`BOPEN-IDP-001`](../../04-platform/BOPEN-IDP-001.md)
**Maker:** Claude (agent, Motor role)
**Independent checker:** NOT ASSIGNED
**Security reviewer:** NOT ASSIGNED
**Completion authority:** NOT ASSIGNED

---

## 1. Authority deviation — read this first

`BOPEN-P2-001` §26 records the disposition:

> **APPROVED FOR PHASE 2 CONTRACT FREEZE; IMPLEMENTATION HOLD UNTIL ENTRY GATE**

`BOPEN-P2-001` §1 states coding begins only after the entry gate, ADRs, contracts,
token/security profile, test matrix, baseline and authority scope are frozen.
`BOPEN-IDP-001` §21 makes its own effectiveness conditional on resolving the required ADRs.

**Phase 2 implementation nevertheless proceeded**, on explicit operator direction dated
2026-07-29, with the following gate items **unrecorded at the time of writing**:

| §23 entry-gate item | State at implementation time |
|---|---|
| Exact repository, branch, base commit and base tree identified | Branch `chore/remove-graphify-hook-injection`; no baseline receipt recorded |
| Work paths and operations authorized | Not recorded |
| Maker, checker, security reviewer, completion authority named | **Not named** |
| `BOPEN-IDP-001` canonical and approved for Phase 2 | ✅ Satisfied (WP-P2-01 complete) |
| `membership-transition.json` schema and version approved | ⚠️ See §3 deviation |
| `ADR-P2-001`..`ADR-P2-010` resolved | **Not resolved** |
| `D-P2-001`..`D-P2-015` resolved or classified | **All OPEN** — see §2 |
| Token and key-management contract approved | **Not approved** — see §4 |
| Broker version and dependency lock frozen | **Not frozen** (no broker dependency added) |
| Acceptance matrix and evidence plan reviewed | Not recorded |
| No production credentials required | ✅ Satisfied |
| Phase 1 regression suite passes on the baseline | ✅ Verified — 23/23 Phase 1 tests green |

The maker did not, and cannot, record the §23 **GO** decision, approve any ADR, or sign
the checker/security-reviewer/completion-authority roles. Those remain reserved to the
named authorities. This record exists so the deviation is visible to the independent
checker rather than discovered in review.

**Consequence to weigh:** every decision in §2 was made *by implementation default*.
If the Engineering Authority ratifies a different value, the affected code and tests
change. Nothing here should be read as an approved decision.

---

## 2. Provisional decisions taken by implementation default

Each value below is the plan's **own §21 recommended default**. No alternative
architecture was invented.

| ID | Decision | Value implemented | Where |
|---|---|---|---|
| D-P2-002 | Invitation token digest scheme | `sha256-v1` behind a `TokenHasher` port, constant-time compare, scheme persisted per record | `kernel_core/membership.py` |
| D-P2-003 | Invitation lifetime | 7 days (`DEFAULT_INVITATION_LIFETIME`), 30-day hard bound | `kernel_core/membership.py` |
| D-P2-004 | Duplicate invitation policy | One open invitation per (tenant, normalized destination, purpose) | `InvitationEngine.issue` |
| D-P2-005 | Membership terminal-state semantics | No implicit reactivation; terminal states have no outbound transition, enforced by contract loader | `MembershipTransitionContract` |
| D-P2-006 | Context token lifetime | 5 minutes; 60-second max clock skew | `platform_kernel/context_service.py` |
| D-P2-007 | JWT algorithm / key custody | **Deliberately not decided.** `TokenSigner` port only | see §4 |
| D-P2-008 | Context supersession | Latest context wins per session; prior context superseded on switch | `ContextSwitchService.switch` |
| D-P2-009 | SCIM deprovision target state | Per-directory `deprovision_policy`, default `suspended`; hard delete impossible | `platform_kernel/idp_bridge.py` |
| D-P2-010 | SCIM ordering strategy | Provider `sequence` plus monotonic deprovision tombstone | `IdpBridge._guard_ordering` |
| D-P2-012 | Support grant maximum | 8 hours | `kernel_core/delegation.py` |
| D-P2-013 | Partner grant maximum | 90 days (placeholder for contract-defined policy) | `kernel_core/delegation.py` |
| D-P2-014 | Revocation propagation | Immediate new-issuance deny; active contexts superseded via recorded obligation | state machine + context service |
| D-P2-015 | Audit/outbox failure semantics | **Partially implemented.** Fail-closed on audit contract violation; no durable outbox | see §5 |

`D-P2-001` (broker name/version) and `D-P2-011` (group-to-role mapping owner) were **not**
decided: the broker is a port with a deterministic test adapter, and group mappings are
data supplied to the bridge, not code.

---

## 3. Deviation — transition matrix file location

`BOPEN-IDP-001` §6.5 states the canonical transition matrix is governed by
`membership-transition.json`. The repository already contained
`contracts/schemas/membership-transition.json` as a **JSON Schema for transition
events** (`previous_state`/`new_state`/`triggered_by`), not a transition matrix.

Rather than overwrite an existing contract that Phase 1 tests depend on, the pinned
matrix was added as a **new** file:

```
contracts/schemas/membership-transition-matrix.json   (contract_version 1.0.0)
```

Both files now exist and serve different roles. **The Architecture Authority should
confirm this split or direct a merge.** The implementation rejects any transition absent
from the matrix file, satisfying the §6.5 intent.

The matrix pins 11 allowed transitions across the 7-state closed set; the remaining
31 ordered state pairs are proven to fail closed.

---

## 4. Security boundary — token signing is NOT resolved

`BOPEN-IDP-001` §12.4 requires asymmetric signing with key material managed outside
source control, a versioned JWKS endpoint, and key rotation. **None of that is decided
or implemented.** ADR-P2-006 is open.

What exists is `DeterministicTestSigner`: a symmetric HMAC-SHA256 signer using a
clearly-marked non-production constant, present solely so the acceptance suite can
exercise algorithm, key-identifier, signature-tampering and expiry negative paths
offline. It is confined to the test boundary and must not reach any deployed path.

`ContextTokenValidator` does enforce the durable rules: `alg=none` rejected, algorithm
allowlist, unknown `kid` rejected, issuer/audience/time validation, all twelve mandatory
claims required, and prohibited profile claims rejected.

No production secret, key or credential was added to the repository.

---

## 5. Known gaps carried into WP-P2-08

| Gap | Impact | Owner |
|---|---|---|
| ADR-P2-001..010 unresolved | Every §2 default is unratified | Engineering Authority |
| Durable audit outbox absent (D-P2-015) | Audit failure fails closed, but there is no reconciliation queue | Engineering |
| TypeScript SDK is contract-checked, not executed | No Node toolchain in this baseline; parity verified by source-level assertions only | Engineering |
| Persistence is in-memory | No PostgreSQL RLS binding for Phase 2 entities; Phase 1 RLS baseline untouched | Data Authority |
| Repositories are deterministic test adapters | Concurrency proven by version compare-and-swap, not by database-level locking | Engineering |
| No formatting/lint/type-check tooling run | The plan requires them at WP-P2-08; not configured in this repository | Engineering |
| Independent check and security review not performed | Maker cannot self-certify these | Checker / Security Reviewer |

---

## 6. Verification actually performed

| Check | Result |
|---|---|
| `python -m unittest discover -s tests/unit` | **124 passed** |
| `python -m unittest discover -s tests/integration` | **11 passed** |
| `python -m unittest discover -s tests/contracts` | **2 passed** |
| `python -m unittest discover -s tests/isolation` | **3 passed** |
| `python -m unittest discover -s tests/governance` | **5 passed** |
| `python tools/validate_repository.py` | PASS (26 mandatory paths) |
| `python tools/check_clean_room.py` | PASS |
| All 9 contract schemas parse as JSON | PASS |
| Membership transition matrix coverage | 11/11 allowed, 31/31 absent proven to fail closed |
| Invariant traceability | 18/18 invariants mapped to an owning test file |

Total: **145 tests, 0 failures.** Phase 1 regression remains green.

Coverage percentage was **not** measured; no coverage tool is configured. The plan's
100% branch-coverage targets for transition lookup and token claim validation are
therefore **asserted by test construction, not measured**. This is an open item.

---

## 7. Maker statement

This record is a maker artifact. It certifies only what was built and what was run.
It does not certify readiness, approve any decision, or authorize production. The
Phase 2 entry gate remains unrecorded and the §24 definition of done is unmet.
