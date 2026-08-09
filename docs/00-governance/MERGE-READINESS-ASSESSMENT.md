# Merge readiness assessment — `claude/BOPEN-P35-001-runtime-realization` → `main`

**Document ID:** `BOPEN-GOV-MERGE-READY-001`
**Version:** `1.0.0`
**Status:** **Advisory assessment — decides nothing, authorizes nothing**
**Issued:** 2026-08-09
**Owner:** Engineering Authority
**Prepared by:** Claude (agent, Motor role) — advisory only
**Governing:** `AGENTS.md` §15, §20.3, §21; `BOPEN-GOV-EBIV-001`; `BOPEN-GOV-IDENT-001`

> Merge, release, deployment and production activation are outside agent authority regardless of
> vote (`AGENTS.md` §20.3). This assessment exists so the decision can be taken with the branch's
> actual state visible. **It is not a recommendation to merge.**

---

## 1. Scale

| | |
| :--- | :--- |
| Commits ahead of `main` | **318** |
| `main` last touched | **2026-07-13** (`a908bbe`) |
| Branch last touched | 2026-08-09 |
| Working tree | 3 modified files, all operator-owned and uncommitted |

Nearly a month of Phase 3.5 and Phase 4 work exists only on this branch. `main` predates the
Phase 3.5 insertion entirely.

| Kind | Commits |
| :--- | ---: |
| `docs` | 178 |
| `feat` | 44 |
| `fix` | 28 |
| `test` | 21 |
| `chore` | 17 |
| `evidence` | 11 |
| `verify` | 8 |
| other (`ebiv`, `revert`, `demo`) | 5 |

## 2. Identity compliance — three defects that a merge would carry into `main`

`check_ballot_attribution.py` passes, because it binds *ballots*. It does not audit *commit*
identity across a range. This does:

| Commits | Status | Identity |
| ---: | :--- | :--- |
| 169 | registered | `Claude (BST-SA Motor) <claude@bst.local>` |
| 62 | registered | `Claude Opus 5 (BST-SA Motor) <claude@bst.local>` |
| 36 | registered | `BizEra <ounkhamvilay@gmail.com>` — but see §2.2 |
| 20 + 11 + 6 + 5 | registered | `Codex …<codex@bst.local>` (four display variants) |
| 3 + 1 | registered | `Gemini …<gemini@bst.local>` |
| 1 | legacy | `Codex bOPEN Hygiene <codex@openai.local>` |
| **2** | **UNREGISTERED** | `Codex gpt-5.6-sol (BST-SA Verifier) <claude@bst.local>` |
| **2** | **FORBIDDEN** | `SIM-EXEC-THROWAWAY <sim@throwaway.invalid>` |

### 2.1 Two commits carry a forbidden identity

```text
23df5e2  2026-07-28  [REPO-HYGIENE] Ignore root-level agent handoff …
177d559  2026-07-28  [REPO-HYGIENE] Ignore graphify-out/ scan output
```

`agent-identity-register.json` lists `SIM-EXEC-THROWAWAY <sim@throwaway.invalid>` under
`forbidden`, with the reason: *"A throwaway identity is a commit deliberately made untraceable.
Recorded as a control failure … not merely an audit-trail defect."*

Both are `.gitignore` hygiene changes — trivial in content. **The content is not the issue.**
Merging places commits made under a deliberately untraceable identity into `main`, where the
register's `forbidden` list says they do not belong.

### 2.2 Two commits have a name/email mismatch

```text
3d57f90  2026-08-03  Codex gpt-5.6-sol (BST-SA Verifier) <claude@bst.local>
fbc5da9  2026-08-03  Codex gpt-5.6-sol (BST-SA Verifier) <claude@bst.local>
```

The display name says Codex; the address says Claude. `AGENTS.md` §21.1 exists precisely so that
*"either field alone identifies the agent, and a disagreement between them is itself detectable"*.
These two are detectably disagreeing and are **not recorded in any `attribution_gaps` entry**.

### 2.3 The recorded attribution gap undercounts by seven — **RETRACTED, see §7**

`agent-identity-register.json` records the 2026-07-29..30 gap as **29 commits** authored by Claude
under the operator's identity. The unmerged range carries **36** commits under
`BizEra <ounkhamvilay@gmail.com>` on those two dates — 7 on 07-29 and 29 on 07-30.

Either the register undercounts by seven, or seven of them are genuinely operator-authored and the
other 29 are the recorded gap. **The repository does not say which.** Until it does, seven commits
in the merge range have unestablished authorship.

## 3. Verification state — what would land verified, and what would not

| Artifact | Ballots | Disposed |
| :--- | :--- | :--- |
| 12 artifacts (auth, placement, Party, Workflow, UOM, ContactPoint, Location, …) | one verifier each | **yes**, under `CONFIRMED_UNDER_TWO_AGENT_PROFILE` |
| Notification Stage 1 | 19 `CONFIRMED`, 1 `INADMISSIBLE` | **no** |
| `WP-P35-08` tenant-cascade remediation | 16 `CONFIRMED`, 0 refuted | **no** — draft prepared, unsigned |
| Everything else | none | n/a |

**No candidate in the repository meets `BOPEN-GOV-EBIV-001` §6.1's two-verifier quorum.** The 12
disposed artifacts rest on the §6.5 two-agent profile: one verifier plus an operator disposition.
That is the ratified rule, and it is what a merge would be carrying.

## 4. Known defects that a merge would move into `main`

| Defect | State |
| :--- | :--- |
| **`88e6ed2` — `P35-04R-15` refutation undischarged.** `/v1/../admin` reaches the kernel as `/admin`; answered by a code comment and a `KNOWN LIMITATION` test, which §6.2 says cannot discharge a refutation | Open — `DEC-P35-GATEWAY-PREFIX-CONFINEMENT` |
| **FastAPI documentation endpoints proxied publicly.** `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc` reachable through the gateway's catch-all; no governing artifact says they should be | Open — same decision |
| **`/readiness` discloses exception type** on an unauthenticated endpoint | Open — same decision |
| **Tenant deletion has no application-level path and no audit treatment**, though §8 requires audit for privileged access | Open — `WP-P35-08` §11.4 |
| **`119f2d8` is an orphan** carrying 23 ballots; a `git gc` makes them permanently unresolvable | Open — `DEC-P35-ORPHAN-CANDIDATE-ANCHOR` |
| **`check_ballot_attribution.py` cannot express §6.5**, so it reports 28/28 short and cannot see refutations | Open — `DEC-P35-QUORUM-TOOL-GAP`; the fix was built and reverted as unverifiable |
| **`NOTIFY-S1-ISO-WRITE-01` inadmissible** — mechanism named is not removal-sensitive | Open |
| 13 decision requests | Proposed |

## 5. Options

| # | Option | Assessment |
| :--- | :--- | :--- |
| 1 | **Merge the branch whole** | Fastest. Carries §2's identity defects and §4's eight open items into `main` in one act, and makes `main` the place they live |
| 2 | **Resolve §2 first, then merge whole** | The identity defects are the only items that are *about the commits themselves* rather than about the code. §4's items are recorded, owned and visible; §2's are not |
| 3 | **Merge in verified slices** | Only what carries ballots and dispositions goes first. Clean in principle, but the branch is not organised in slices — 318 commits interleave docs, evidence and code across four foundations, and separating them now would be reconstruction, not selection |
| 4 | **Do not merge; keep `main` at the bootstrap pack** | Honest about verification state, and the status quo. Its cost compounds: every day the divergence grows and the eventual merge gets larger |

**No option is recommended here.** Merge authority is the operator's under §20.3, and the choice
between carrying known-open findings into `main` and leaving a month of work unmerged is a judgment
about risk appetite, not a technical determination.

## 6. What this assessment does not do

It does not merge, does not dispose, does not discharge any refutation, and does not resolve any
identity defect. It records the branch's state so the decision can be taken with that state visible.

**It has not been independently verified.** The identity survey, the counts and the defect list are
one agent's work, and §2.3's discrepancy in particular should be checked before it is relied on.

---

## 7. Correction 2026-08-10 — §2.3's headline is retracted

§6 said the §2.3 discrepancy should be checked before being relied on. It was checked by Codex and
**the maker's headline was wrong.**

> *"The history count is indeed 36, but the register's 29 matches one contiguous July 30 range
> (`f59bbd2..713c4a5`) that contains the Phase 3.5 package work; the seven July 29 commits precede
> that scoped range. So the assessment's 'register undercounts' headline is not supported."*

Verified independently rather than accepted:

```text
git rev-list --count f59bbd2^..713c4a5   →  29
git log f59bbd2^..713c4a5 --format=%an   →  29 × BizEra
```

**Twenty-nine commits, all under the operator identity, in one contiguous range.** The register's
count is exact and scoped, not an undercount. `BOPEN-GOV-IDENT-001` describes that range as the
whole of `WP-P35-01`..`03`, and the seven 2026-07-29 commits precede it — they are Phase 2 and
Phase 3 work, a different body of commits entirely:

```text
2221f2d  docs(phase3): add Phase 3 completion decision and evidence
b0fb4f6  feat(phase3): deliver Capability Registry, Commercial …
6aa892b  feat(evidence): add machine-readable Phase 3 entry gate …
bd71a78  fix(governance): harmonize status registers …
b582fc1  feat(governance): evidence-driven Phase 3 entry gate …
e65baf1  [BOPEN-P2-001] Enter Phase 2 and implement MILE-2.1 …
fcae7a9  Preserve in-progress repo reorganisation before session …
```

### 7.1 What survives the retraction

The register is accurate. **The seven 2026-07-29 commits still have unestablished authorship** —
they carry the operator identity, they are outside the only recorded gap, and nothing says whether
they were written by the operator or by an agent. That is a smaller finding than §2.3 claimed and it
is not nothing: §21.2.1 makes a commit attributed to the operator carry an authority claim an agent
cannot make.

**§2.1 and §2.2 are unaffected** — the two forbidden-identity commits and the two name/email
mismatches were verified directly and do not depend on this count.

### 7.2 The error pattern, again

§2.3 framed an exact scoped record as a defect in the record. The maker had the range boundary
available and did not check it before writing "undercounts by seven" as a heading.

That is the fourth time in this session that a maker assessment ran in the direction which made a
finding look larger or a build look better, and the fourth time an independent check corrected it.
Recorded here rather than quietly edited, because the pattern is the more useful finding.
