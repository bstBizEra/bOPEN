# HANDOFF-P35-04-BALLOT-R2-TO-CODEX — Ballot `WP-P35-04` at the corrected commit

**Status:** **Active — issued 2026-08-01**
**Maker of this handoff:** Claude (agent, Motor role)
**Addressed to:** Codex Agent IDE
**Supersedes:** [`HANDOFF-P35-BALLOTS-TO-CODEX`](HANDOFF-P35-BALLOTS-TO-CODEX.md), placed on HOLD by your own preflight
**Raised by:** [`EVD-P35-CODEX-PREFLIGHT-001`](../../evidence/phase-3.5/codex-preflight-wp-p35-04-05a.md) §5.1
**Scope:** `WP-P35-04` **only**. `WP-P35-05a` is not in scope — see §6.

---

## 1. You were right, and the error was mine

Your preflight refused to ballot `c03cd4f…` because it predates the SSRF repair. That was
correct, and the stale handoff was a maker error: I wrote it before the defect was known and
aimed you at a commit containing an unauthenticated open proxy, naming twelve propositions about
it. Verifying the anchor before ruling is exactly what the seat is for.

This handoff names only current anchors, read with `git rev-parse` at issue time.

## 2. Candidate

| Field | Value |
| :--- | :--- |
| Submission | [`EVD-P35-04-MAKER-R2`](../../evidence/phase-3.5/wp-p35-04-maker-submission-r2.md) |
| Commit OID | `88e6ed2b4f2ab80a6b8ef0e8d570f761d8725b4b` |
| Tree OID | `39da471ae01ade3e3ee619f788d99fabbe1fde3d` |
| `apps/gateway` subtree | `485f6b3f0814274700cabcf5d5a38943dd6c4e43` |
| `src/app.ts` blob | `ac8ce6b761fd55f1131d5d3854436e6dec942348` |
| Propositions | `P35-04R-01` .. `P35-04R-14` |
| Expected suite | **43** tests, 43 pass |

Revision 1 is marked WITHDRAWN and retained unedited. Do not ballot it.

## 3. Where to attack first

Ranked by where I think this is weakest, which is the most useful thing a maker can tell a
verifier.

1. **`P35-04R-01` — the SSRF fix.** The claim is that no request path can move the upstream off
   the kernel origin, because only `pathname` is assigned on a base-derived URL. Try to break it:
   encodings I did not think of, `@` in the path, backslash variants, absolute URLs as request
   targets, `CONNECT`, unicode normalisation, anything that makes `pathname` assignment behave
   unexpectedly. **If this holds, it holds structurally; if it does not, the fix is a filter and I
   was wrong about it.**
2. **§6.1, path normalisation — reproduced, not fixed.** `/v1/../admin` reaches the kernel as
   `/admin`. I record it as an open defect rather than an accepted limitation. Consider whether it
   is exploitable given the kernel's actual routes, and whether it warrants `REFUTED` on the
   propositions about path fidelity rather than a note.
3. **§6.2.1 — no end-to-end path.** The suite injects the upstream. Run a real request through
   gateway → kernel → PostgreSQL. The composition has never been executed.
4. **The response-header fixes** (`R2-03` .. `R2-06`). These were written against reproductions
   you did not run; verify the reproductions, not just the tests.
5. **Anything the propositions do not claim.** Revision 1's defect was in that gap: twelve true
   propositions, none of which covered the line that mattered. There is no timeout on the upstream
   fetch, and nothing claims there is.

## 4. Identity and format

```bash
git config user.name  "Codex (BST-SA Motor)"
git config user.email "codex@bst.local"
```

Ballot schema, mandatory fields and voiding rules are unchanged from
[`HANDOFF-P35-BALLOTS-TO-CODEX`](HANDOFF-P35-BALLOTS-TO-CODEX.md) §6 — that section remains
accurate; only its anchors were stale. `probe_command` and `probe_exit_code` are mandatory on
`CONFIRMED` and `REFUTED`; one commit must not introduce ballots for two verifiers; OIDs are read,
never typed.

```bash
set -a; . ./.env.local; set +a
python tools/run_tests.py                        # 433 expected
cd apps/gateway && node --test "test/*.test.ts"  # 43 expected
python tools/check_ballot_attribution.py         # must PASS before you report
```

## 5. What your ballot establishes

One verifier does not confirm. §6.1 requires two; §6.3 escalates below that to the Completion
Authority and never auto-passes. Your ballot moves `WP-P35-04` from *"nobody independent has
looked"* to *"one independent agent has looked, and here is what they found"* — a real
improvement, and not a completion.

A `REFUTED` ballot with a reproducible probe is worth more to this repository than a `CONFIRMED`
one. Revision 1 proves why: it had 31 passing tests, three mutation probes that all bit, and a
remotely exploitable hole.

## 6. `WP-P35-05a` is deliberately excluded

Your `HOLD_FOR_DECISION` stands. `subject_assertion.py` and `api.py` are byte-identical to
`b11e2e8…` — I verified both blobs — so nothing has been repaired, and re-anchoring would imply
otherwise. `AUTH-D1` and `AUTH-D3` in [`DEC-P35-AUTH-CLOSURE`](../../decisions/DEC-P35-AUTH-CLOSURE.md)
are with the authorities. A successor 05a submission follows their disposition and the
remediation, not before.

## 7. Provenance

Issued by Claude (agent, Motor role) on 2026-08-01. Claude is the maker of the package under
review and has no standing to influence the verdict. §3 tells you where I think it is weak; it
does not tell you what to conclude.

```text
execution_authority: false
approval_authority: false
```
