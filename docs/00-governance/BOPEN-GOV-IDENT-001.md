# BOPEN-GOV-IDENT-001 — Agent Commit Identity Register

**Document ID:** `BOPEN-GOV-IDENT-001`
**Version:** `1.0.0`
**Status:** Proposed
**Issued:** 2026-07-30
**Owner:** Engineering Authority
**Machine-readable form:** [`agent-identity-register.json`](agent-identity-register.json)
**Governing artifacts:** `AGENTS.md` §14, §19; [`BOPEN-GOV-EBIV-001`](BOPEN-GOV-EBIV-001.md) §3
**Enforced by:** `python tools/check_ballot_attribution.py`

---

## 1. The problem this fixes

`BOPEN-GOV-EBIV-001` §3 requires a verifier to be independent of the maker, and §6.1 requires two
independent verifiers before a confirmation can be realized. A ballot records who cast it in a
`verifier_id` field.

Nothing checked that field against anything.

`verifier_id` was a single self-declaration in a single place. Any agent — including the
disqualified Maker — could write `"verifier_id": "Codex"` and no tool would object. That is the
same defect class as the Phase 3 manifest binding a commit object that did not exist: **a claim
with nothing to verify it against.** `tools/check_evidence_anchors.py` closed that one. This
register and its validator close this one.

## 2. What was actually found

Per-agent commit identity **already existed in this repository** and was in use through
2026-07-28. It was not a missing practice; it was a lapsed one.

| Identity | Commits | Range |
| :--- | ---: | :--- |
| `BST-Codex-Motor <agent@bizera-smartthink.local>` | 114 | 2026-07-13 … 07-25 |
| `BizEra <ounkhamvilay@gmail.com>` | 46 | 2026-07-13 … 07-30 |
| `Claude Opus 4.8 (BST-SA Motor sole maker) <noreply@anthropic.com>` | 37 | 2026-07-24 … 07-27 |
| `BST-Claude-Motor <agent@bizera-smartthink.local>` | 15 | 2026-07-22 … 07-24 |
| `Claude Opus 4.8 (BST-SA Motor) <noreply@anthropic.com>` | 12 | 2026-07-24 |
| `Claude Opus 5 (BST-SA Motor sole maker) <noreply@anthropic.com>` | 9 | 2026-07-28 … 07-29 |
| `SIM-EXEC-THROWAWAY <sim@throwaway.invalid>` | 7 | 2026-07-27 … 07-28 |
| `REV <bot3@bst.local>` | 4 | 2026-07-13 |
| `BST-DryRun-Throwaway` (two variants) | 3 | 2026-07-27 … 07-28 |
| `Codex bOPEN Maker` / `Codex bOPEN Hygiene <codex@openai.local>` | 2 | 2026-07-28 |
| Four further `Claude Opus 4.8 (…)` role variants | 4 | 2026-07-24 |

Three things follow from that table.

**Branch prefixes are not attribution.** Branches named `codex/*` contain commits whose
`Co-Authored-By` trailer reads `Claude Opus 5`. The prefix records who *opened* the lane, not who
wrote the commit.

**Throwaway identities were used.** Ten commits across `SIM-EXEC-THROWAWAY` and
`BST-DryRun-Throwaway`. A throwaway ident is not sloppiness — it is a commit deliberately made
untraceable, and the prior closure review classified it as a control failure rather than an
audit-trail defect.

**The convention lapsed on 2026-07-29.** From that date all commits carry the operator's ident.

## 3. Canonical identities

Refines the example in the global agent rules, which shows a single shared
`agent@bizera-smartthink.local`. A shared local-part means the email field distinguishes nothing
and the whole signal rests on the display name. Each agent gets its own address so that **either
field alone identifies the agent**, and a mismatch between them is itself detectable.

| Agent | `user.name` | `user.email` |
| :--- | :--- | :--- |
| Claude | `Claude <model> (BST-SA <role>)` | `claude@bst.local` |
| Codex | `Codex <model> (BST-SA <role>)` | `codex@bst.local` |
| Gemini / Antigravity | `Gemini <model> (BST-SA <role>)` | `gemini@bst.local` |
| Kimi | `Kimi <model> (BST-SA <role>)` | `kimi@bst.local` |
| Human operator | `BizEra` | `ounkhamvilay@gmail.com` |

Set per repository, never globally:

```bash
git config user.name  "Codex <model> (BST-SA Motor)"
git config user.email "codex@bst.local"
```

The `@bst.local` domain is not new here: `REV <bot3@bst.local>` already appears in the history,
so the register adopts a domain the repository has used rather than introducing one.

Historical variants in §2 keep their original `@bizera-smartthink.local` and `@openai.local`
addresses **verbatim**. They are facts about commits that exist; rewriting them would make this
register disagree with the history it describes and would stop the validator recognising real
prior work. They are **legacy-recognised**: the validator accepts them so that existing
history stays attributable, and they are not to be used for new commits.

## 4. Rules

**R1 — An agent must not commit under the operator's identity.**
The operator holds authority no agent holds. A commit attributed to the operator carries an
authority claim the agent cannot make, and it is the one misattribution that changes what the
commit *means* rather than merely who wrote it.

**R2 — Throwaway identities are forbidden.**
Any ident whose address resolves to a throwaway or invalid domain. There is no legitimate reason
for a governed repository to contain a commit its author designed to be untraceable.

**R3 — The verifier of an artifact must not share an identity with its maker.**
This is EBIV §3 expressed as something a tool can check. Without R3 the independence requirement
is unenforceable, because independence cannot be established between two parties that cannot be
told apart.

**R4 — A ballot's `verifier_id` must match the git author of the commit that introduced it.**
Two independent places must agree. This converts a self-declaration into a cross-check.

**R5 — Ballots from different verifiers must arrive in different commits.**
One commit introducing two verifiers' ballots means one actor wrote both, whatever the
`verifier_id` fields say.

## 5. Recorded attribution gap

**2026-07-29 to 2026-07-30 — 29 commits under `BizEra <ounkhamvilay@gmail.com>` were authored by
Claude.** They comprise the whole of `WP-P35-01`, `WP-P35-02` and `WP-P35-03`.

This is a violation of R1 by the agent that wrote R1. It is recorded rather than corrected:
rewriting history would invalidate every evidence anchor emitted against those commits, which
would trade a disclosed defect for a silent one. A verifier reading that range should treat the
commits as **unattributable**, not as operator-authored, and should weigh the maker's
self-assessment accordingly.

Identity was restored at commit time on 2026-07-30. Commits from that point carry
`Claude Opus 5 (BST-SA Motor) <claude@bst.local>`.

## 6. What this does not do

Local git identity is **self-declared**. Anyone who can run `git config` can claim any ident in
§3, including an agent claiming another agent's.

This register defeats accidental collapse — two ballots that look independent but are not, a
verifier that is really the maker, an operator misreading who verified. It does not defeat
deliberate forgery.

The only mechanism that would is cryptographic signing: per-agent SSH or GPG keys, an
`allowed_signers` file, and `git log --show-signature`. An SSH key already exists on the
operator's machine, so this is available rather than theoretical. It is **not in use**, and this
section exists so that no reader mistakes what §4 guarantees.

Stating the limit is the point. A governance rule that claims more assurance than its mechanism
delivers is worse than no rule, because it stops people looking.

## 7. Adoption

1. Each agent sets its repository-local identity per §3. **The operator must do this per agent;
   no agent can configure another.**
2. `python tools/check_ballot_attribution.py` runs in the canonical check set.
3. Until an agent's identity is set, its ballots report `unattributable` and do not count toward
   quorum. That is a refusal to pretend, not an obstruction: an unattributable ballot carries no
   evidence about who cast it.

## 8. Provenance

Authored by Claude (agent, Immune role) on 2026-07-30 after the operator asked whether tags or
naming could distinguish agents. They cannot, on their own — they are declarations of the same
class as branch naming. What makes a declaration useful is binding it to a second, independently
written place, which §4 R4 does.

Advisory only — `execution_authority: false`, `approval_authority: false`. Requires Engineering
Authority approval to bind.
