# DEC-P4-LOCATION-BALLOT-ATTRIBUTION — 31 Location ballots are unattributable and do not count toward quorum

**Decision ID:** `DEC-P4-LOCATION-BALLOT-ATTRIBUTION`
**Version:** `1.0.0`
**Status:** **Proposed — decision request raised under `AGENTS.md` §16 (a required attribution record is absent)**
**Issued:** 2026-08-07
**Owner:** Engineering Authority
**Raised by:** Claude (agent, Motor role) — advisory only
**Governing:** `AGENTS.md` §21.3, §21.4; [`BOPEN-GOV-IDENT-001`](../00-governance/BOPEN-GOV-IDENT-001.md); [`BOPEN-GOV-EBIV-001`](../00-governance/BOPEN-GOV-EBIV-001.md) §3

---

## 1. The finding

`tools/check_authority_bootstrap.py` fails `test_ballot_attribution_holds`:

```text
Ran 669 tests in 711.993s
FAILED (failures=1)
```

Commit `b524846` (2026-08-05) — *"evidence: persist Codex Location ballots (31/31 CONFIRMED at
1cde994)"* — is authored by `Claude (BST-SA Motor) <claude@bst.local>` but introduced 31 ballot lines
whose `verifier_id` is `codex`. `check_ballot_attribution.py` binds a ballot to the **git author of
the commit that introduced the line** (`git blame -L`), so all 31 disagree with their own claim.

- `docs/evidence/phase-3.5/ballots.jsonl` lines **367–397**
- All 31: `verdict: CONFIRMED`, candidate `1cde994` (Location foundation, `BOPEN-LOC-001`),
  propositions `LOC-INV-*`
- One implicated commit; no other ballots in the file are affected (346 codex + 51 gemini total)

Claude transcribed Codex's verdicts into the evidence file instead of Codex committing its own
ballots. This is a **transcription-versus-authorship** defect, not a misused identity — the commit
ident is correct; it is the ballots inside it that cannot be bound.

## 2. Why it matters

Per `AGENTS.md` §21.3, **an unattributable ballot does not count toward quorum.** The Location
foundation's verification therefore currently rests on 31 ballots the tool refuses.

Codex is otherwise a validly independent verifier here: `docs/evidence/phase-3.5/manifest.json`
records the Maker as *"Claude (agent, Motor role)"* and lists Codex among the eligible verifiers, so
EBIV §3 is satisfied on the merits. Only the binding is missing.

## 3. Why the register entry does not fix this

`agent-identity-register.json` now carries an `attribution_gaps` record for this commit. **That is
the record, not the remedy.**

`check_ballot_attribution.py` reads only the `canonical`, `legacy_recognised` and `forbidden` fields
of the register. It never consults `attribution_gaps`, and the comparison is an unconditional
equality:

```python
if agent_id != claimed:
    findings.append(Finding("R4", locator, ...))
```

No documentation change clears this check. Recording the gap is still correct and required — the
2026-08-01 gap set the precedent — but the suite stays red until one of the options below is taken.

## 4. Options

| # | Option | Greens the check | Assessment |
| :--- | :--- | :--- | :--- |
| 1 | **Codex re-casts the ballots** — Codex re-runs the probes against `1cde994` and commits its own ballot lines under `codex@bst.local` | Yes | **Recommended.** The verdicts become Codex's own act rather than a transcription, which is what the control is actually asking for |
| 2 | **Codex re-commits the existing 31 lines** — remove and re-add them in a Codex-authored commit so `git blame` resolves to Codex | Yes | Acceptable **only if Codex confirms it performed the probes.** Otherwise it manufactures the appearance of independence the check exists to prevent — see §5 |
| 3 | **Widen the checker** — add an exemption path honouring a transcription record | Yes | **Recommended against, and operator-reserved.** The entire value of this control is that it refuses transcribed independence; an exemption returns the repository to the state §21 was written to end |
| 4 | **Accept as uncountable** — record Location as unverified pending re-verification | No | Honest, and leaves the suite red. Appropriate only if Codex is unavailable |

No option rewrites history. §21.4's reasoning holds: rewriting would invalidate evidence anchors
emitted against these objects and trade a disclosed defect for a silent one.

## 5. The distinction that decides between options 1 and 2

Option 2 is mechanically sufficient and substantively hollow unless one fact is true: that Codex
actually ran the probes it is credited with. If it did, re-committing merely repairs a bookkeeping
error. If it did not — if the verdicts were inferred, copied, or produced by the maker — then option
2 launders a maker self-assessment into an apparently independent ballot, which is the precise
failure `BOPEN-GOV-EBIV-001` §8 and `AGENTS.md` §21 exist to prevent.

That fact is not established by anything in the repository. It should be confirmed by Codex before
option 2 is chosen; if it cannot be confirmed, option 1 is the only sound repair.

## 6. Amendment 2026-08-07 — Option 1 selected; a §19.1 worktree exception is authorized

> **Change note (extend-only).** Recorded **before** the probes run.

**Option 1 is selected**: Codex re-runs the 31 `LOC-INV-*` probes against `1cde994` and commits its
own ballots under `codex@bst.local`. Option 2 was rejected on the §5 reasoning — it is hollow unless
Codex confirms it ran the probes, and otherwise launders a maker self-assessment into an apparently
independent ballot. Option 3 was rejected as control-weakening.

**A §19.1 worktree exception is authorized**, scoped as follows.

`AGENTS.md` §19.1 requires agents to work in the primary workspace and forbids uncoordinated
parallel worktrees absent governance authorization. The primary workspace cannot serve here: it
carries an unrelated in-flight change-set (modified `tests/isolation/test_rls_database_behavior.py`
and `tools/migrate_tenant_to_dedicated.py`; untracked `021_notification_foundation.sql` and
`tests/isolation/test_notification_isolation.py`), so a suite run there exercises a tree that is not
`dfc5d220`. Decisively, a ballot must anchor to a `commit_oid` and `tree_oid`, and uncommitted work
has neither — verifying in the workspace as it stands could only produce a ballot claiming an anchor
it did not verify, which is the same class of defect being repaired.

| Field | Value |
| :--- | :--- |
| **Scope** | One detached worktree at `1cde994`, **probe execution only** |
| **Prohibited in the worktree** | Any commit, branch, push, or edit of tracked files |
| **Where ballots are written** | The primary workspace, committed under `codex@bst.local` |
| **Lifetime** | Removed after the run |
| **Approver** | Operator — `BizEra <ounkhamvilay@gmail.com>` — Architecture Authority |
| **Recorded by** | Claude (agent, Motor role), transcribing an operator decision |

The exception is narrow by construction: the worktree exists so the candidate can be observed
unmixed, and it never becomes a second place where work lands. It does not generalize to other
tasks.

**Closed 2026-08-07.** The re-cast completed at `64a2bfa` and the worktree was removed. Compliance
verified before removal: `HEAD` still at `1cde994`, **0** commits made in it, **0** tracked-file
edits. The exception is spent; any further worktree needs its own authorization.

Repair outcome: Codex re-ran the probes and committed 31 ballots under `codex@bst.local`. The
re-cast was substantive, not a re-commit — all 31 lines changed `ballot_id`, `probe_command` and
`probe_observation`, with `probe_command` moving from the generic `python tools/run_tests.py` to the
specific modules Codex executed, and each ballot carrying its own `verifier_lens`.
`check_ballot_attribution.py` now reports `PASS`, and `test_ballot_attribution_holds` no longer
fails.

**This closes attribution only, not quorum.** Candidate `1cde994` still has one verifier. The
checker's own output warns that its `PASS` *"attests attribution only... and must not be quoted as
though it did"* attest quorum. Confirmation under `BOPEN-GOV-EBIV-001` §6.5 additionally requires an
explicit Completion Authority disposition, which is the operator's act and is not supplied by this
repair. The tooling gap behind the shortfall is raised separately as
[`DEC-P35-QUORUM-TOOL-GAP`](DEC-P35-QUORUM-TOOL-GAP.md).

## 7. What this decision request does not do

It does not dispose the Location foundation, re-open its work package, alter any verdict, or change
`check_ballot_attribution.py`. It records a control failure and asks for a disposition.

Raised advisory-only. Confers no implementation, approval, merge, release or production authority.

## 8. Correction 2026-08-07 — `check_authority_bootstrap.py` does **not** have the defect attributed to it

> **Change note (extend-only).** Correcting a false statement made by this agent, recorded because
> it reached commit messages that cannot be edited.

The commit messages of `0d058df` and `fb128aa` both state that `tools/check_authority_bootstrap.py`
*"exits 0 even when it reports FAILED — the wrapper does not propagate the unittest result, a
separate harness defect."*

**That is wrong. The tool has no such defect.** `tools/check_authority_bootstrap.py` line 108 calls
`sys.exit(1)` whenever any check fails, and the first background run did report `exit=1`. The
misreading came from the shell command the agent wrapped around it, which ended in `tail`, so the
exit code observed was `tail`'s and not the script's.

Two behaviours of the tool that are correct but easy to misread, recorded so the next reader does
not repeat the mistake:

1. **A passing run prints only three lines.** `run_script` calls `subprocess.run(...,
   capture_output=True)`, so a child's output is retained and surfaced **only** when that child
   exits non-zero. `bOPEN Authority Bootstrap Check: PASS` with no test output means the 669-test
   suite ran and passed — not that it was skipped.
2. **`Ran 669 tests ... FAILED` appearing in the output is the captured failure text**, printed
   because a check failed. Its presence indicates the tool working, not the tool leaking.

The practical advice that accompanied the false claim — read the summary line rather than the exit
code — remains sound, and was applied to reach the verified results below. Only the stated reason
was wrong.

**Clean serialized verification, 2026-08-07 23:38:42–23:50:34 (11m52s):**
`bOPEN Authority Bootstrap Check: PASS`. This also settles the three errors seen in the earlier
contended run (`test_cross_tenant_idempotency_key_reuse_is_isolated_not_refused`,
`test_full_phase3_entitlement_metering_flow`, `test_window_bounds_bracket_the_reservation`): they
were artifacts of two suites contending for the one shared PostgreSQL — that run took 22552s against
a 712s baseline — and do not reproduce when the suite runs alone. They were not product defects.

The claim was not propagated into the Codex dispatch instruction; the damage is confined to the two
commit messages named above, which this section corrects.
