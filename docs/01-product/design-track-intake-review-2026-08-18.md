# Design-track intake review — documents 002, 003, 004

**Status:** **REVIEW RECORD — advisory.** Adopts nothing, authorizes nothing.
**Work package:** `BOPEN-WP-DESIGN-INTAKE-001`
**Reviewed at:** `main` = `7c4a595`
**Subjects:** three design documents supplied by the operator on 2026-08-18. **They live outside this
repository** (operator scratch space) and are not committed here. This record holds only the findings.

| | Document |
| :--- | :--- |
| 002 | `BOPEN-FRAPPE-PATTERN-REDESIGN-002` — Platform Experience Layer |
| 003 | `BOPEN-GITHUB-NATIVE-AUTONOMOUS-LOOP-003` — agentic control plane |
| 004 | `BOPEN-STABILITY-AUTONOMOUS-LOOP-GOAL-004` — stability goal charter |

---

## 1. The finding that matters more than the individual defects

**Each of the three documents introduces an identifier namespace that `AGENTS.md` §31.1 had already
renamed away from, for the same reason, in force, on `main`.**

| Doc | Introduces | §31.1 already resolved this as | Prior meaning in the tree |
| :--- | :--- | :--- | :--- |
| 002 | `C0`–`C9` delivery waves | — | review/closure cycles (`C10 review`, `C10 verification returned REJECT`) |
| 003 | `A0`–`A6` autonomy profiles | **`AT0`–`AT4`** | `architecture-gates.md` `A0 scope … A7`; §28.2 URE v1.5 authority levels |
| 004 | `L0`–`L10` test ladder | **`GL-0`–`GL-3`** | `EVD-SEC-001` assurance **Level 3**; `secb_pf` **L0 governance** |

§31.1 is one paragraph and it exists for exactly this:

> Honouring the §30.4 collision rulings: change classes are **`AD0`–`AD5`** (not `G0`–`G5`),
> governance layers are **`GL-0`–`GL-3`** (not `L0`–`L3`), authority tiers are **`AT0`–`AT4`**
> (not `A0`–`A4` …)

Three documents in a row went past it. **That is not three typos; it is the design track and the
governance track drifting apart.** The cheap fix is procedural, not editorial — see §4.

## 2. Collisions, measured with word boundaries

`git grep -E "\bTOKEN\b" github/main`:

| Token | Files | Introduced by | Existing meaning |
| :--- | ---: | :--- | :--- |
| **`P2`** | **33** | 003 build order `P0`–`P4` | phase identifiers — `BOPEN-P2`, `BOPEN-P3`, `BOPEN-P35`, `BOPEN-P36`. 003's *"P2 — bOPEN Platform Experience"* against the repo's Phase 2 = Membership and enterprise onboarding |
| **`G7`** | **19** | 003 gates `G-01`–`G-17` | §3 in-force **"GATE G7 CLEARED"**; §27.3 excluded `G0`–`G7` as *"the most damaging item in v0.9"* |
| **`L0`** | 7 | 004 test ladder | assurance Level 3; SecB framework L0 governance |
| **`A0`** | 4 | 003 autonomy profiles | architecture gates `A0`–`A7`; §28.2 |
| **`E0`** | 4 | (PR #11 §33) | evidence classification `E0`–`E4` |
| **`C2`** | 1 | 003 `riskClass` | review cycle; **and 002's delivery wave** — two new meanings for one token on the same day |

### Replacements, verified free with word boundaries

```text
TL-0 … TL-10   test ladder            ว่าง
AP0  … AP6     autonomy profiles      ว่าง
DW-0 … DW-9    delivery waves         ว่าง
RK-0 … RK-4    risk classes           ว่าง
AG-01… AG-17   autonomy gates         ว่าง
BW-0 … BW-4    build waves            ว่าง
ST-01… ST-13   stability dimensions   ว่าง — 004's own namespace is clean
```

**Two candidate collisions in this review were false positives** and are recorded because the method
matters: `ST-01` matched inside `GAP-VOCAB-REST-01` and `P-ISOLATION-INST-01`; `AG-01` matched inside
`DEVFLAG-01`. A substring search invents collisions. **The check must use `\b` word boundaries.**

## 3. A gap in `ST-12` that this week produced

```text
ST-12  no false promotion, stale evidence acceptance, duplicate execution,
       or unclassified retry promoted as pass
```

Every clause counts a **false pass**. On 2026-08-17 the opposite happened:
`tools/check_contract_conformance.py` returned `FAIL — 3 schemas with neither coverage nor a baseline
entry` because the database timed out, the database-gated instance tests were skipped, and their
coverage vanished with them. The tool's own docstring predicts it:

> *"A coverage number that changes with the environment is not a measurement, and a check that reports
> regression on that basis would be **training its readers to ignore it**."*

**A model that counts only false-pass cannot see a gate becoming noise, and an ignored gate is an
absent gate.** Suggested additions to `ST-12`: *false block; environment-dependent verdict; gate whose
result varies without a change in its subject* — with **gate flakiness** measured alongside escaped
defects in §8.3.

## 4. Suggested procedural control, in place of editing three documents

Before any document introduces an identifier, run one command:

```bash
git grep -l -E "\b<TOKEN>\b" github/main
```

Non-empty means the token is taken. This costs one command and would have caught all three cases
above, plus `E0`–`E4` in PR #11. Pair it with a single instruction: **read §31.1 before naming
anything.** §31.1 is already the identifier map; it only needs to be the *first* thing consulted
rather than the last.

## 5. What the documents get right

- **All three place §20.2 first.** 004 §16 priority 1 is *"§20.2 versus `DEC-P4-ENTRY`"*. That matches
  the independent conclusion recorded in [`KERNEL-AUTONOMY-OBJECTIVE.md`](KERNEL-AUTONOMY-OBJECTIVE.md) §3.
- **004 §16 reproduces, item for item, a backlog derived separately from measurement** — including
  *"Phase 3.6 FK count drift"* (measured: 30 live FKs to `tenants`, 46 textual, against 12 in
  `roadmap.md`) and *"contract coverage depends on mutable DB"* (found by running it). **Two lines of
  work reached the same order without copying each other**, which is better evidence than either.
- **Status blocks are honest.** `AUTHORITY_CONFLICT_UNRESOLVED`,
  `IMPLEMENTATION_NOT_GRANTED_BY_THIS_DOCUMENT`, `PRODUCTION_STABILITY_NOT_PROVEN`.
- **`UNKNOWN` may never become healthy** and *"Generic `FAILED` is not a closure state"* — the same
  discipline that caught several vacuous passes in this repository.
- **002's minimal vertical slice before the admin console** is right, and for a sharper reason than it
  gives: this week proved twice that a gate nothing runs is a gate that does not exist.

## 6. One factual correction

002 declares `Extends: BOPEN-AUTONOMY-TO-PRODUCTION-001` and 003 declares `Integrates:` the same
document. **It is not in this repository** — `git grep` over `github/main` returns nothing. Either add
a path or URL, or state that it lives outside the repository, so a reader can resolve it.

---

Recorded advisory-only. Adopts none of the three documents, authorizes no work package, and confers
no verdict, disposition, merge, release or production authority.
