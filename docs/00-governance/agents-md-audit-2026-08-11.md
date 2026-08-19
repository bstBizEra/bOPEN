# Independent audit of `AGENTS.md` — findings register, 2026-08-11

**Status:** **AUDIT RECORD — advisory.** No finding here amends anything.
**Work package:** `BOPEN-WP-GOV-AUDIT-001`
**Audited at:** `c4d2564` (`main`)
**Auditor:** Codex, read-only, dispatched adversarially — `BOPEN-GOV-EBIV-001` §3 excludes the maker,
and Claude authored §§26–30.
**Verification:** every finding below was re-derived from the repository by Claude before being
recorded. Findings the auditor raised that could not be re-derived are marked as such.

---

## 1. Critical — §20.2 declares Phase 4 unauthorized and declares itself supreme

```text
§20.2  "This subsection is the single operative statement of gate state."
§20.2  | Phase 4 — Foundations and satellite products | NOT AUTHORIZED | blocked pending Phase 3.5 |
```

`DEC-P4-ENTRY` line 5: **`AUTHORIZED — MILE-4.1 (2026-08-03) and MILE-4.2 (2026-08-03)`**. Six Phase 4
foundations are recorded disposed.

§1 places `AGENTS.md` above a `DEC`. **A strict reader must conclude Phase 4 work is prohibited**,
including Party, Location, Party ContactPoint and Notification — all built and most disposed. A
permissive reader must ignore a passage that calls itself the single operative statement. Either
reading violates part of the specification.

**Amending §20.2 is a specification amendment** — outside agent authority under §20.3 item 6 and
EBIV §2, and `CONSTITUTIONAL_REQUIRED` under §31.1. Recorded, not fixed.

## 2. High — §29.6 understates the security evidence, and §29.5 conflates two verdicts

§29.6 labels `LC-5` a shell from three-line files. It does not account for:

| Artifact | Lines |
| :--- | ---: |
| `docs/evidence/EVD-SEC-001-kernel-security-review.md` | **640** |
| `docs/07-security/secrets/BOPEN-SEC-VAULT-001.md` | **227** |
| `docs/07-security/pre-publication-credential-scan-2026-08-10.md` | 126 |

The 640-line document is an executed adversarial kernel security review. The assessment was reached
by searching filenames for `*threat*`, `*sbom*`, `*pentest*` and reporting the absence as fact —
**a conclusion shaped by the search key rather than by the evidence.** The same error class produced
the `proposition_id` renumbering defect on 2026-08-10.

§29.5 states *"A §25.1 step-8 disposition is an `LC-8` verdict."* **Incorrect.** EBIV distinguishes
the verifier's verdict from the Completion Authority's disposition; the latter accepts or rejects an
assembled verdict rather than being one. §29 is `PROPOSED`, so nothing rests on the error, and
correcting it touches `AGENTS.md` — `CONSTITUTIONAL_REQUIRED`.

## 3. High — identifier collisions §30.4 missed

| Token | Prior meaning | Status |
| :--- | :--- | :--- |
| `A0`–`A4` | **`docs/03-architecture/architecture-gates.md`: `A0 scope` … `A7 implementation authorization`** | §30.4 recorded only the §28/§30 clash and missed this older repository definition |
| `R0`–`R4` (§28 risk tiers) | EBIV admissibility `R1`–`R5`; revision names "R4" | Not recorded anywhere |
| `LC-*` | — | Leaked into an operational document before promotion; corrected in this change |

§31.1 avoids all three by construction (`AT0`–`AT4`, `AD0`–`AD5`, `GL-0`–`GL-3`). **§28 does not.**

## 4. High — documents that `AGENTS.md` says bind declare themselves proposed

```text
BOPEN-GOV-EBIV-001   Status: Proposed — pending DEC-P35-RUNTIME     §20.3 says it binds
BOPEN-GOV-IDENT-001  Status: Proposed                               §21 makes it mandatory
DEC-GOV-AUTONOMY-001 Status: PROPOSED — RATIFIED UPON THE OPERATOR'S MERGE
```

The third is now satisfied — `aa3d126`, authored by the operator, is on `main` — but the decision
record still carries the pre-ratification status and its "Ratification SHA" field is still the
placeholder *"the operator's merge commit — recorded on the PR at merge"*.

## 5. Medium — the authority for an operator disposition is not §25.1

Cited repeatedly during 2026-08-10 as *"§25.1 step 8 reserves disposition to the Completion
Authority"*. **§25 is `PROPOSED` and states that it "binds nothing."**

What binds is **EBIV §6.5**: one verifier plus *"an explicit Completion Authority disposition… the
operator's disposition stands in for the second verifier."* Every artifact currently awaiting
disposition carries exactly one verifier, so the requirement is real — **the conclusion was right and
the citation was wrong.**

§19.6, in force, reads the other way (*"rather than requiring manual human sign-off receipts"*).
Reaching the correct answer takes three hops: §19.6 → §20.3 → EBIV §6.5.

## 6. Medium — `PROPOSED` sections repeatedly say "adopted"

§§26–30 carry `NOT IN FORCE` banners whose bodies say *"Adopted as vocabulary"*, *"Adopted in full"*,
*"adopted verbatim"*, *"binding constraints"*, `READY_TO_IMPLEMENT`. **A banner does not cure repeated
normative wording**, and a reader scanning the body can infer authority that does not exist.

## 7. Medium — compliance drift, measured

| Rule | Live state |
| :--- | :--- |
| §18 skill registry | `.agents/skills/` holds three packages; §18 lists two. `maker-evidence-audit` unregistered |
| §21.1 identity | History carries throwaway identities, an unclassified `REV <bot3@bst.local>`, and commits where a Codex display name sits on `claude@bst.local` |
| §19.1 worktrees | Seven entries, none matched to an authorization record. **`INDETERMINATE`, not a proven violation** — §19.1 permits authorized worktrees and no authorization registry exists |
| §23 baselines | Three `arch-baseline/*` tags exist; the register documents one |

## 8. Findings about the new machinery itself

Raised by Claude while exercising §31, not by the auditor:

1. **The Authority gate is syntactic.** `check_work_package_ref.py` matches the `BOPEN-WP-*`
   pattern and does not check that the work package exists or is accepted. *"No Ticket, No Work"* is
   enforced against the shape of a string.
2. **`config/delegation_envelope.json` has no revocation field.** §31.2 condition 4 requires the
   envelope be *"unexpired, unrevoked"*; the second half has nothing to evaluate.

Neither is a defect in what the gates do correctly — the classifier returned
`CONSTITUTIONAL_REQUIRED` for `AGENTS.md` and `AUTO_APPROVED` for this change, which is the
distinction the section exists to draw.

## 9. What this record does not do

It amends nothing, disposes nothing, and merges nothing outside `AD0`. Findings 1–4 and 6 require
changes to `AGENTS.md` or to normative documents and are therefore `CONSTITUTIONAL_REQUIRED`;
they are recorded here so the operator can act on them, and are **not** bundled into an autonomous
merge.
