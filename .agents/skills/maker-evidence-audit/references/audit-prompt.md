# Audit dispatch template

Fill the bracketed fields. Keep the adversarial framing and the self-interest disclosure — they are
what makes the difference between a reviewer that confirms and one that finds.

---

Read-only audit. Do NOT modify any file, do NOT run the test suite, do NOT touch the database, do
NOT commit. Repo: `[repo path]`

I am the maker of `[work package / artifact]` and I have just written `[N]` traceability rows
claiming what it verifies. **Your job is to find where I have OVERCLAIMED** — where a registered row
asserts more than the test actually establishes.

Overclaiming in an evidence record is the specific failure this repository's EBIV standard exists to
catch, **and I am the party who benefits from it**, so please be adversarial about my rows rather
than confirming them.

## Sources to read

1. `docs/evidence/[phase]/invariant-traceability.csv` — my new rows, prefixed `[PREFIX]`. Each has
   `invariant_statement`, `test_id`, `mechanism_whose_removal_breaks_it`, `invariant_source`.
2. `[the test file the rows cite]` — read the **test bodies**, not the names or docstrings.
3. `[the implementation or migration]` — the mechanisms I name.
4. `[the research or spec defining the parent invariants]` — the statements my rows cite.

## Check specifically

**A.** For each row, does the `invariant_statement` say strictly no more than the cited test proves?

**B.** Does the named `mechanism_whose_removal_breaks_it` actually exist, and is it plausibly the
thing that makes that test fail if removed? Flag any mechanism that does not exist, or that is not
load-bearing because something else — a parent constraint, a reused clause — carries the behaviour.

**C.** Are my scope qualifiers honest? I used narrowed ids rather than claiming the parent invariant
outright, because the parent covers surfaces this work does not build. Is any qualifier still too
broad? Is any parent cited where this work in fact defends none of it?

**D.** Are there mechanisms in the implementation that are load-bearing but have **no test and no
row** — coverage gaps I should disclose rather than leave for a verifier to find?

## Report

A concise list. For each finding: the row id, what I claimed, what the evidence actually supports,
and the specific correction. **If a row is sound, do not list it.**

Conclude with an overall judgement: are these rows safe to submit for independent verification, or
do they need correction first?

---

## Notes on wording that matters

**Do not** write "review these rows" or "check my work". Both produce confirmation.

**Do** name the direction of the expected error. The most useful audit received began its verdict
with *"the defect distribution is not random — every error runs in the direction that flatters the
build"*, which was only possible because the prompt asked for overclaiming specifically.

**Defensive framing** is required when the artifact concerns a security boundary. Phrase every ask
as *confirm behaviour B holds / is refused / is preserved by observing the results* — never *find a
way to break / bypass / slip past*. A cybersecurity classifier will kill a dispatch whose body
carries adversarial verbs even when the preamble says the objective is defensive, and the symptom is
a session that runs the whole suite and then produces nothing.
