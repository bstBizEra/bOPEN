# GL-0 — Root Constitution

Status: **PROPOSED** — ratified on the operator's merge of the
`BOPEN-WP-GOV-AUTONOMY-001` pull request (the Genesis Ratification,
`DEC-GOV-AUTONOMY-001`). Until that merge, this file binds nothing.
Constitutional authority: Operator (vily), until amended by that authority
Amendment rule: **any change to this file is `CONSTITUTIONAL_REQUIRED`** and may
never be enacted by an agent, whatever the ballot outcome
Provenance: adapted from the SecB Project Framework `L0_ROOT_CONSTITUTION.md`
(ratified there at `SECB-WP-FWK-012`) under `AGENTS.md` §30.8 item 1
(bootstrap/payload split). Identifiers renamed per the §30.4 collision
rulings: layers `L0`–`L3` → `GL-0`–`GL-3`, change classes `G0`–`G5` →
`AD0`–`AD5`, authority tiers `A0`–`A4` → `AT0`–`AT4`.

## Why a constitution rather than a file list

Protecting governance by naming files answers the wrong question. The question
is not *which files did this change touch* but **how does it change
authority**. A refactor of a gate that provably decides every case identically
expands nothing; a two-line edit to a ceiling expands everything.

So authority is split into four layers, and each layer names who may change it.

| Layer | Contents | Who may change it |
| --- | --- | --- |
| **GL-0 — Root Constitution** | This file. Trust anchor, absolute ceilings, prohibited actions, quorum rules, the ladder itself | Constitutional authority only |
| **GL-1 — Delegation Envelope** | `config/delegation_envelope.json` — the scope, caps and tier delegated in advance | Agent action inside GL-0 maxima, once the ballot layer is active |
| **GL-2 — Policy Implementation** | Classifier, dual-policy check, gate logic, governance docs | Agent action with evidence and admissible EBIV ballots |
| **GL-3 — Operational Changes** | Documentation, tests, application and sandbox code, CI mechanics | Agent auto-merge by risk class |

An agent operating under this constitution never *creates* authority. It
exercises authority the constitutional authority delegated in advance, and
every exercise is measurable against the envelope. This is the same rule
`BOPEN-GOV-EBIV-001` §2 already states — *agents may certify; agents may not
self-authorize* — expressed as a machine-checkable envelope.

## Absolute ceilings — not waivable by any tier, ballot, or emergency

1. No change may raise a ceiling in this file, lower a quorum, widen the
   prohibited-action list's exceptions, or alter the trust anchor.
2. No agent may advance beyond tier `AT4`, or invent a tier above it.
3. No change exceeding `absolute_ceilings.max_changed_lines_ever` in the
   envelope auto-merges, whatever its class.
4. Tiers `AT3` and `AT4` require an **active** ballot layer. While
   `ballot_layer.state` is `NOT_ACTIVE`, those tiers are unreachable.
5. A pull request is never judged solely by the policy it proposes
   (`scripts/check_dual_policy.py`). Base and head must agree.
6. Evidence, once recorded, is append-only. EBIV ballots bind to their
   `commit_oid`/`tree_oid` and are void anywhere else; disposed evidence
   packages are immutable.

## Prohibited actions — authority verdict `REJECTED`, never weighed

- Disabling, deleting, or neutering an enforcement control or its CI step
- Destroying, rewriting, or detaching evidence from the commit it describes
- Bypassing a verifier, or making a required check optional
- Granting an identity the power to approve its own change
- Reducing a quorum or veto, or removing an expiry, to unblock a specific PR

These are not risks to be balanced against benefit. A change carrying one of
these signatures is refused, and the correct response is to withdraw it.

## Change classes and verdicts (the *authority verdict* vocabulary)

These verdicts name what a **change** needs before it may land. They are a
separate vocabulary from EBIV ballot verdicts (`CONFIRMED` / `REFUTED` /
`INADMISSIBLE`) and from operator dispositions (ACCEPT / REJECT). Always name
the set when quoting a token (`AGENTS.md` §30.4).

| Class | Meaning | Verdict |
| --- | --- | --- |
| `AD0` | Non-governance work wholly inside the envelope | `AUTO_APPROVED` |
| `AD1` | Governance implementation; authority and outcomes unchanged | `AGENT_BALLOT_REQUIRED` |
| `AD2` | Adjustment inside the delegated envelope | `AGENT_BALLOT_REQUIRED` |
| `AD3` | Pre-authorized ladder advance with conditions met | `AUTO_APPROVED_WITH_CONDITIONS` |
| `AD4` | Root authority expansion, or any GL-0/envelope/classifier change | `CONSTITUTIONAL_REQUIRED` |
| `AD5` | Prohibited action per the list above | `REJECTED` |

`HUMAN_REQUIRED` is deliberately **not** in this vocabulary. The verdict names
the *authority level* a change needs, not the species of approver. Today the
constitutional authority is one operator; it may later be a steering
committee, a threshold-signature council, or an external body, and the
verdicts must not have to be renamed when that happens.

## Pre-authorized authority ladder

Tiers, their authority, and the conditions for advancing are recorded in
`config/delegation_envelope.json` under `authority_ladder`. Advancement is
`AD3`: the agent may take a step the constitutional authority defined in
advance, **only** when the recorded conditions are objectively met. It may not
define a new step. This is what makes raising a ceiling an exercise of
delegated authority rather than the creation of new authority.

## Two-epoch activation for gate changes

A change to gate logic merges **inactive** and takes effect in the following
governance epoch. No pull request is ever decided by the gate it introduces.
Today this is enforced by the dual-policy rule — base and head logic must
reach the same verdict — with full epoch machinery deferred.

## What this constitution does not yet have

Stated plainly, because a governance document that overstates its own
enforcement is the failure it exists to prevent (`AGENTS.md` §27.1 records an
external document doing exactly that):

- **No external trust anchor.** The verifier runs inside the repository it
  judges (`AGENTS.md` §30.8 item 2). A change to `.github/` is therefore
  `AD4` — the only available compensating control.
- **No cryptographic signing.** The envelope is `UNSIGNED`; its integrity
  rests on git history and the human merge that ratified it.
- **No ballot council.** Two verifying agents cannot constitute a five-role
  quorum (`AGENTS.md` §30.6; EBIV §6.5 two-agent profile). Every verdict that
  would depend on quorum escalates to the operator instead of resolving.

## Revocation

The constitutional authority may revoke or narrow all delegation at any time,
by statement in session or a comment on the ratification pull request,
effective immediately and without a pull request. Expiry of the envelope has
the same effect by default: delegation lapses rather than persisting
unexamined.
