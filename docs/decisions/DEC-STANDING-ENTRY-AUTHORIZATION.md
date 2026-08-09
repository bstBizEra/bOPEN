# DEC-STANDING-ENTRY-AUTHORIZATION — pre-authorize entry gates, never dispositions

**Decision ID:** `DEC-STANDING-ENTRY-AUTHORIZATION`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16**
**Issued:** 2026-08-10
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only, **and the party whose waiting this would reduce**
**Governing:** `AGENTS.md` §20.3, §25.1; [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §2, §3

---

## 1. The problem this addresses

On 2026-08-08/09 the operator repeatedly asked an agent to work autonomously. The agent repeatedly
stopped — not because it lacked capability, but because `AGENTS.md` §25.1 step 0 requires an entry
gate before any build, and each one is a separate operator act.

The waiting was real and mostly avoidable. **The decisions that actually required judgment were few;
the round-trips were many.**

## 2. The distinction that makes a standing authorization safe

Two kinds of operator act have been conflated all session:

| | Authorizes | Can it be standing? |
| :--- | :--- | :--- |
| **Entry gate** | *starting* work already decided in principle | **Yes** — the judgment was made when the decision request was disposed |
| **Disposition** | *accepting* that finished work is sound | **No** — it is the judgment, and it is what EBIV exists to reserve |

An entry gate says "build the thing we decided to build." A disposition says "what was built is
correct." Only the second is a verdict, and EBIV §2 is explicit: *"Agents may certify; agents may not
self-authorize."*

## 3. Proposed standing authorization

> **A work package whose scope is fully determined by an already-disposed decision request is
> authorized to enter without a further operator act**, provided every condition below holds. The
> agent records the entry gate by transcription, citing this decision and the disposed decision it
> derives from.

**Conditions, all required:**

1. The governing decision request is **disposed**, not `Proposed`.
2. The work package's scope adds nothing beyond what that decision selected. Any widening — a new
   surface, a second foundation, a schema change not named — voids it.
3. A `§23` baseline is tagged before the change where §23.1 applies.
4. Roles are assigned with **verifier eligibility checked before assignment**, per
   `DEC-P35-VERIFIER-SCOPE` §10.
5. The package touches no normative specification, no `AGENTS.md` section, and no agent's own
   permissions.

## 4. What this does not authorize

Named explicitly, because the value of a standing authorization is entirely in its boundary:

- **No disposition.** Every package still ends at the operator (§25.1 step 8).
- **No merge, release, deployment or production activation** (§20.3).
- **No amendment** of a normative specification, ADR, or `AGENTS.md` (EBIV §2).
- **No permission widening**, including of this authorization.
- **No entry** for a package deriving from a `Proposed` decision — that is the case where the
  judgment has not been made yet, which is exactly what an entry gate would be substituting for.
- **No worktree** outside `§19.1`, which remains a separate per-instance authorization.

## 5. What it would have changed in the recorded session

| Package | Would it have entered without waiting? |
| :--- | :--- |
| `WP-P35-08` (tenant cascade) | **Yes** — `DEC-P4-NOTIFY-TENANT-CASCADE` §7 selected Option 2 and fixed the scope exactly |
| `WP-P35-07` (quorum tooling) | **Yes** — `DEC-P35-QUORUM-TOOL-GAP` §7 selected Option 1 |
| Notification Stage 1 | **Yes** — `DEC-P4-ENTRY` §12 authorized the build |
| A gateway confinement fix | **No** — `DEC-P35-GATEWAY-PREFIX-CONFINEMENT` is still `Proposed`, and choosing between confining a proxy and declaring it open is the judgment itself |
| Threat model / SBOM | **No** — no disposed decision determines their scope |

Three of five would have proceeded. The two that would not are the two where the operator's judgment
was the thing being waited for, which is the test working.

## 6. The conflict of interest, named

**The agent raising this is the party whose waiting it would reduce.** That is a reason to read §4
harder than §3.

The safeguard is that this authorization touches only the *start* of work. Every artifact it lets
begin still faces independent verification and still ends at an operator disposition — and this
session recorded fifteen maker errors, none caught by the maker, which is the argument for keeping
that end intact rather than for trusting the start less.

## 7. What this decision request does not do

It authorizes nothing by itself. Until the operator disposes it, §25.1 step 0 applies unchanged and
every entry gate remains a separate act.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.
