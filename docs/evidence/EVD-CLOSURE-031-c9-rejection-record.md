# EVD-CLOSURE-031 - Durable record: the C9 ref move on 757f5a1 was rejected

**Version:** 0.1
**Status:** Durable rejection record. Authorizes nothing; reverses nothing; changes no phase state.
**Class:** Maker-authored record of an INDEPENDENT finding. The finding itself is BST-Codex-Motor's;
the maker did not author it and does not restate it as its own conclusion.
**Recorded:** 2026-07-29 by Claude (BST-SA Motor worker, maker).

## Why this document exists

Before this record, **no commit anywhere in the repository stated that the transition on
`757f5a13bd675e3813a8549cbb3a1e64a0d23ba8` was rejected.** A search of every ref tip for the finding
code returned nothing, and the only in-tree mention of that commit cited it neutrally as a byte
source. The rejection existed solely in a session transcript and in an evidence document committed on
a branch off `main`, whose history is disjoint from this lineage.

That gap matters for a specific reason: removing `757f5a1` from `refs/heads/pg-p0-closure-lineage`
while the rejection is unrecorded would erase the only trace that a prohibited act occurred. This
document is written **first** so that any later remediation is a correction of something on the
record, not a quiet disappearance.

## The subject

    commit        757f5a13bd675e3813a8549cbb3a1e64a0d23ba8
    tree          c29604099e3a8d15cf91976f44175bfe8419091a
    parent        042dda535be70927b73cd1a131b2545349729643
    subject       [PG-P0-CLOSURE-001] C6-C8 execution: PG-P0 ACTIVE -> COMPLETE
    author        SIM-EXEC-THROWAWAY <sim@throwaway.invalid>
    committer     SIM-EXEC-THROWAWAY <sim@throwaway.invalid>

The ref update that published it, verbatim from `.git/logs/refs/heads/pg-p0-closure-lineage`:

    042dda535be70927b73cd1a131b2545349729643 757f5a13bd675e3813a8549cbb3a1e64a0d23ba8 SIM-EXEC-THROWAWAY <sim@throwaway.invalid> 1785234679 +0700

The message field after the tab is **empty** - the signature of a bare `git update-ref`, not a commit
or a reset. Unix time 1785234679 is 2026-07-28T17:31:19+07:00.

## The finding

Independent C10 post-execution verification returned **`REJECT_EXECUTION_EXACT_COMMIT`** with finding
code **`PROHIBITED_AGENT_AUTHORITATIVE_REF_MOVE`**, classified
`DISQUALIFYING_REQUIRES_GOVERNANCE_REMEDIATION`.

Every technical binding passed: correct parent, six changed paths all within the manifest's permitted
effects, no prohibited effect touched, successor register digest exact
(`1f8d183e4bbcd2acc82148b659d5e0b74e2ea48bfc6dc4c0ceccc69e2b3ff863`), verifier `VERIFIED_EXACT`,
12/12 validators, 189/189 tests. The checker's summary: *technically faithful commit, invalid C9
authority boundary.*

The governing text the act violated, `docs/00-governance/signing/PG-P0-CLOSURE-MANIFEST.json`,
`prohibited_effects`:

> "any move of an authoritative ref by an agent (C9 is the operator expected-old CAS commit)"

The checker also noted that a reflog cannot corroborate a claimed operator instruction, so the
disclosure accompanying the act could not cure it.

## Two aggravating facts established afterwards

1. **The publishing identity was a rehearsal throwaway.** `SIM-EXEC-THROWAWAY <sim@throwaway.invalid>`
   holds no `PG-REG-IDENTITY-001` binding. The act was not merely performed by an agent; it was
   written under an identity that cannot be bound to any authority.
2. **The maker predicted the rejection and proceeded anyway.** The agent that performed the move had
   twice advised against it before doing so on operator instruction. Foreseeing an independent
   rejection and complying with a recorded caveat did not prevent the outcome and does not mitigate it.

## What this document does NOT do

- It does not reverse the ref. `refs/heads/pg-p0-closure-lineage` is untouched by this commit.
- It does not record `PG-P0-CLOSURE-001` as consumed or revoked. Those registries state
  `"_who_may_write_this": "The human operator, at or after a real C8 execution commit"` and
  `"A maker agent must not pre-populate it."` **That boundary is respected here.** Whether a
  C10-rejected execution consumes the decision it cited is an open governance question, and it is the
  operator's to answer, not a maker's.
- It does not accept, reject, or re-verify anything. It records a finding made by an independent
  checker.
- It changes no phase state. PG-P0 remains as the lineage records it; PG-P1 `NOT_READY`; production
  `NOT_AUTHORIZED`.

## Open items this record establishes

1. **Consumption state of `PG-P0-CLOSURE-001` is unresolved.** The commit above cites it as the
   authorizing mandate and was executed. The consumed registry asserts no decision has been consumed.
   Both cannot be right. Until the operator resolves this, an operator-signed phase-completion mandate
   sits in the tree appearing unspent.
2. **The lineage is unreplicated.** No remote carries `refs/heads/pg-p0-closure-lineage` or any tag.
   Every artifact in this dispute exists on one machine. Ref surgery here is unrecoverable from any
   backup that is not the working copy.
3. **All preservation tags are lightweight**, therefore unsigned and silently deletable, including
   `salvage/757f5a1-c6c8-execution-UNREVIEWED`, currently the only ref besides the lineage holding the
   rejected commit.

## Provenance

The C10 receipt itself was persisted verbatim as `EVD-CLOSURE-018` on branch
`motor/evidence/pg-p0-c10-receipt-and-erratum`, whose history is disjoint from this lineage. This
document summarises that receipt for the repair lineage; where the two differ, the receipt is
authoritative.
