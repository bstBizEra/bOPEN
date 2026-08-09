---
name: maker-evidence-audit
description: Adversarially audit your own evidence rows, traceability and submission BEFORE the commit that makes them a candidate. Use whenever you are the maker and are about to record propositions, mechanisms, severity or scope that an independent verifier will later ballot. Catches the specific failure that maker self-assessment cannot see - errors that run in the direction which flatters the build.
---

# Maker Evidence Audit (`maker-evidence-audit`)

A maker cannot see the bias in their own evidence. This skill is the countermeasure that has
actually worked here: an adversarial review, by a party that did not do the work, **before** the
evidence becomes a candidate.

## The failure this exists for

On 2026-08-08/09 a single agent produced ten defects in one session. **Not one was caught by the
agent that made them.** The operator caught three, a subagent one, the independent verifier six.

The distribution was not random. Every error ran in the direction that **made the build look
better or the problem look smaller**:

| Claimed | Actually |
| :--- | :--- |
| `evidence_kind: executed_db` | the test ran no SQL at all |
| mechanism is "SELECT+INSERT-only **grants**" | there are **zero** `GRANT` statements in the migration set |
| `quota_suspend` is tenant-isolated | the cited test never opens that table |
| suite result recorded under a candidate anchor | measured in a dirty workspace with foreign test files |
| "three routes outside `/v1`" | **seven** — four FastAPI docs endpoints were missed |
| "no evidence anything is reachable that should not be" | OpenAPI and interactive docs are proxied publicly today |

An auditor's one-line summary is the reason this skill exists:

> **every error runs in the direction that flatters the build**

## When to invoke

**Before the commit that creates a candidate**, whenever you are about to record:

- traceability rows (`invariant_id`, `invariant_statement`, `mechanism_whose_removal_breaks_it`)
- a maker submission's propositions, checks or severity assessment
- a claim about what a test proves, or what a mechanism defends
- scope qualifiers narrowing a parent invariant

Auditing **after** the commit is far more expensive: corrections change the tree, invalidate the
candidate, and force a re-ballot of everything already verified.

## Operating boundary

- Advisory only. The audit produces findings, never a verdict, and is **not** an EBIV ballot.
- It does **not** substitute for independent verification (`BOPEN-GOV-EBIV-001` §3). A subagent
  sharing the maker's engine is not an independent verifier and may not ballot.
- It confers no approval, merge, release, deployment or production authority (`AGENTS.md` §18).

## Workflow

### 1. Dispatch an auditor that did not do the work

Frame it adversarially and name your own interest. A reviewer asked to "review this" confirms; a
reviewer asked to "find where I overclaimed" finds.

Required elements in the prompt:

- **Read-only.** No file edits, no commits, no test runs that mutate state.
- **Name the bias**: *"I am the maker and I benefit from these errors, so be adversarial rather
  than confirming."*
- **Ask for the specific defect**: where does a row claim more than its cited test establishes?
- **Ask about mechanisms**: does the named `mechanism_whose_removal_breaks_it` exist, and is it
  genuinely load-bearing for that test?
- **Ask about coverage gaps**: what is load-bearing but has no test and no row?
- **Require the test body be read**, not the name or docstring.

### 2. Verify every finding yourself before acting

Do not fix on report. An auditor can be wrong, and acting on an unverified finding is the same
error in the other direction. For each finding, establish it from the repository:

```bash
# does the named mechanism exist at all?
grep -rn "GRANT" infrastructure/database/*.sql

# does the test actually touch what the row claims?
sed -n '/def test_the_cited_test/,/def test_/p' tests/path/to/file.py
```

### 3. Correct before committing, and record what was wrong

Rewrite the rows. Then say in the commit message **what the audit found and in which direction the
errors ran** — a corrected row set that hides having been corrected invites the reader to trust it
more than a verifier will.

### 4. Register gaps as rows, do not omit them

Every coverage gap the audit surfaces becomes a row with status `UNVERIFIED` and a plain statement
of what is not defended.

> A gap the maker discloses is a **finding**.
> A gap the verifier discovers is a **defect in the report as well as in the code**.

### 5. Expect the corrected rows still to be wrong

The audit reduces defects; it does not eliminate them. In the recorded case, nine of twenty rows
were corrected pre-commit and an independent verifier still returned one `INADMISSIBLE` — a
`WITH CHECK` clause named as removal-sensitive when, for a PostgreSQL `FOR ALL` policy, an omitted
`WITH CHECK` reuses `USING`, so removing it breaks nothing.

## Mechanism claims: the highest-yield check

`mechanism_whose_removal_breaks_it` is the column that makes a row falsifiable. Three ways it goes
wrong, all observed:

1. **The mechanism does not exist.** A row named "grants" in a migration set containing no `GRANT`.
   Unremovable, therefore unfalsifiable.
2. **The mechanism exists but is not load-bearing.** Removing
   `notification_attempt.tenant_id ON DELETE CASCADE` alone left its probe green, because the parent
   `notification_dispatch` refused the delete. The chain was load-bearing; the leaf was not.
3. **The mechanism is reused implicitly.** An omitted `WITH CHECK` on a `FOR ALL` policy silently
   reuses `USING`.

**Mutate each mechanism and watch the test go red.** A mechanism whose removal changes nothing is
not the mechanism.

## Vacuous-pass check

A test asserting only an *absence* passes against a tool that never ran. Every negative assertion
needs a positive anchor first — that the check executed and reached a verdict.

```python
def assertEvaluated(self, res):
    self.assertNotEqual(res.returncode, 2, f"tool could not run: {res.stderr}")
    self.assertTrue(res.stdout.strip(), "tool produced no output; nothing was evaluated")
```

The same applies to structural checks: a survey matching nothing passes while checking zero rows.
Assert that the survey found something, and keep a positive control on a known-good example.

## Related

- `AGENTS.md` §18 (skill registry), §25.1 (governed maker cycle)
- `BOPEN-GOV-EBIV-001` §3 (maker exclusion), §8 (maker self-assessment carries no verdict weight)
- `BOPEN-ENG-LOOP-001` §5 (anti-patterns observed in this repository)
