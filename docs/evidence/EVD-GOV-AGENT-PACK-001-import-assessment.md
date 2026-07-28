# EVD-GOV-AGENT-PACK-001 - Agent governance pack import assessment

**Status:** MAKER_EVIDENCE_FOR_PROPOSAL_REVIEW
**Prepared:** 2026-07-28
**Maker:** Codex
**Base commit:** `23df5e23d621ad94c20a890944617df65219b3c7`
**Work branch:** `codex/BOPEN-AGENT-GOV-IMPORT-001`

## Source

Local source package:

`C:\Users\ounkh\Downloads\bopen-agent-governance-pack\bopen-agent-governance-pack`

| Source file | SHA-256 |
| --- | --- |
| `AGENTS.md` | `215B0B6BB761A1C82097771893E9ED3015D1F55CCE74E1B683ED90EBF7847E4C` |
| `APPLY-NOTES.md` | `346128BB6760B49DFC39D06847C1B54F889E460C80F4E0B9D961F6826D17F845` |
| `docs/00-governance/BOPEN-AGENT-TEAM-001.md` | `5C2CDC9F2175AF8CB431B548DA47552ADF1090CBFB6FDDFAE3B60736DD65B908` |
| `docs/00-governance/BOPEN-EVIDENCE-VOTING-001.md` | `A9A547D302AE4179B0CE0D15881896276D64B0077F6FE2B6526033401FD9BF2B` |
| `docs/01-roadmap/BOPEN-PHASE-EXECUTION-001.md` | `B0CF32119F45F421AD785EE7154483DBFB264C283DBA52DD0F76C4A0EEC8E8A0` |
| `docs/03-skills/BOPEN-EVIDENCE-TO-SKILL-001.md` | `9D9322AA26F715F931DD3BC819450DD00A10394EE8DB2B766B351C33113F6C74` |
| `docs/03-skills/BOPEN-SKILL-UPGRADE-PROPOSAL-001.md` | `F0244CA8B5C3B2A239F2E8CDB6D1FDF0E72103637ED5BAF01E5132FC7403C41E` |
| `docs/templates/AGENT-EVIDENCE-RECEIPT.template.json` | `6BE0964937738010DA884D3B82FBEEA2C8CF07CE142812C3EAC37264F7EED70C` |
| `docs/templates/AGENT-TECHNICAL-VOTE.template.json` | `285A31EA627A5DB4ACDB04430FCD01D2BF713AB6661A2F492C3D8799366C765A` |

## Intake findings

1. Every pack artifact declares itself proposed, draft or non-effective.
2. The pack was produced without access to the canonical repository and
   instructs the importer to reconcile paths, authority terms, manifests and
   tests.
3. The source text contains broken encoding sequences. The import normalizes
   punctuation to ASCII without changing normative intent.
4. The source taxonomy uses `docs/01-roadmap` and `docs/03-skills`; the
   repository uses `docs/01-program` and `docs/04-skills`.
5. Replacing root `AGENTS.md` would discard established tenancy, clean-room,
   contract-first, testing and security instructions. The import therefore
   appends only the compatible multi-agent controls.
6. The pack's technical voting protocol is not an authority mechanism.
   Imported text explicitly retains the existing maker/checker/human gate and
   makes the proposal opt-in per authorized work package.
7. The proposed lifecycle does not replace the effective PG-P0 C0-C11 closure
   sequence.

## Adaptation map

| Source | Repository destination | Disposition |
| --- | --- | --- |
| Root `AGENTS.md` | Root `AGENTS.md` section 18 | Compatible rules appended; active baseline preserved |
| `BOPEN-AGENT-TEAM-001.md` | Same governance path | Imported as `PROPOSED_NON_EFFECTIVE` |
| `BOPEN-EVIDENCE-VOTING-001.md` | Same governance path | Imported as proposal with explicit non-authority rule |
| `docs/01-roadmap/BOPEN-PHASE-EXECUTION-001.md` | `docs/01-program/BOPEN-PHASE-EXECUTION-001-PROPOSAL.md` | Path reconciled; PG-P0 exception added |
| `docs/03-skills/BOPEN-EVIDENCE-TO-SKILL-001.md` | `docs/04-skills/BOPEN-EVIDENCE-TO-SKILL-001-PROPOSAL.md` | Path and status reconciled |
| Skill upgrade proposal | `docs/04-skills/BOPEN-SKILL-UPGRADE-PROPOSAL-001.md` | Imported without installing active skills |
| Evidence receipt template | `docs/templates/AGENT-EVIDENCE-RECEIPT.template.json` | Imported as non-effective template |
| Technical vote template | `docs/templates/AGENT-TECHNICAL-VOTE.template.json` | Imported with strengthened non-authority statement |
| `APPLY-NOTES.md` | This evidence record | Instructions incorporated; source file not copied |

## Non-effects

This import does not:

- activate the proposal artifacts;
- create agent authority;
- authorize or complete PG-P0;
- open PG-P1;
- change any register, authority matrix or identity record;
- install proposed skills;
- merge, release, deploy or authorize production.

## Required review

Before promotion, an independent checker must verify:

- exact candidate commit, tree and patch;
- absence of weakened effective controls;
- internal links and repository taxonomy;
- JSON validity and template non-effectiveness;
- manifest regeneration and repository validation;
- that technical recommendations cannot be interpreted as human authority.

## Maker disposition

`READY_FOR_INDEPENDENT_EXACT_CANDIDATE_REVIEW` only after deterministic
manifests and validators pass.
