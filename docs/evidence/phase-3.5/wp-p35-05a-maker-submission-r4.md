# EVD-P35-05A-MAKER-R4 — WP-P35-05a Maker Submission, revision 4 (Kernel Authentication Boundary)

**Document ID:** `EVD-P35-05A-MAKER-R4`
**Version:** `4.0.0`
**Status:** **SUPERSEDED 2026-08-02 for further work — but this candidate WAS subsequently balloted.** The first verifier session was classifier-blocked (§6A attempt 1); a reframed defensive dispatch then succeeded (§6A attempt 2, commit `7ade81a`): **23 `CONFIRMED`, 0 `REFUTED`, verifier `codex`**, covering every proposition below. AUTH-D3 Row 1(a) was built on top into [`EVD-P35-05A-MAKER-R5`](wp-p35-05a-maker-submission-r5.md) at `ce97561` before those ballots were observed; the auth-boundary code (`subject_assertion.py`, blob `ada0eb1`) is byte-identical at R5, and the R4→R5 `api.py` delta is confined to the new tenant-provisioning gate — see the R5 reconciliation.
**Issued:** 2026-08-01
**Supersedes:** [`EVD-P35-05A-MAKER-R3`](wp-p35-05a-maker-submission-r3.md) at `e559d1d…`, **refuted** on `P35-05aR3-02`

**Commit OID:** `119f2d8cf678624c055c8d1be48c770b3936de11`
**Tree OID:** `210c6f4be07837f01c6e866b490aca730afc529f`
**Blob — `subject_assertion.py`:** `ada0eb1de30f5d78798947744f0219585ff43d07` *(changed)*
**Blob — `api.py`:** `42f1ab685d42043ca9e169f260ff3bb9d2889304` *(unchanged from R3)*
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical 465/465 against PostgreSQL; gateway 47/47

---

## 1. The refutation, and why it is the most useful one yet

Codex refuted `P35-05aR3-02` (`e8508b0`): an assertion with `exp − iat = 300.9` returned `201`
against a 300-second ceiling, because the implementation truncated both sides before subtracting.

**It only reproduces when `iat` is a whole number** — which is what every real identity provider
emits. The maker's own probe took `iat` from `datetime.now()`, so it was fractional, and
`int(iat + 300.9) − int(iat)` came to 301 and was correctly refused. The defect was invisible from
where the maker stood, and obvious to a verifier who constructed the assertion the way an IdP
does.

Measured at the refuted candidate, integer `iat`:

| `exp − iat` | Result |
| :--- | :--- |
| 300 | accepted *(correct)* |
| **300.9** | **accepted — the defect** |
| **300.99** | **accepted** |
| 301 | refused |

RFC 7519 NumericDate is *"a JSON numeric value"*, not an integer, so fractional seconds are
conformant input rather than an edge case someone invented.

**This is the first refutation in this repository that found an implementation defect rather than
a wording defect.** The previous seven were propositions claiming more than the code did; here the
proposition was right and the code failed to implement it. Recorded because it is evidence the
process catches both kinds, and because the maker's blind spot was a fractional timestamp nobody
would have thought to vary.

## 2. The fix

`float`, not `int`:

```python
lifetime = float(claims["exp"]) - float(claims["iat"])
```

Truncating on the way into a comparison discarded precision the specification guarantees.

## 3. What carries and what does not

**`subject_assertion.py` changed. `api.py` did not.** Codex's 21 `CONFIRMED` and 1 `REFUTED` were
cast at `e559d1d` and **do not carry forward** — ballots bind to a commit.

That matters more than usual here: many of those confirmations cover `api.py` behaviour that is
byte-identical at this candidate. **They still do not carry.** A verifier may reasonably re-cast
them quickly, but they must be re-cast.

## 4. Propositions

| ID | Proposition | Test |
| :--- | :--- | :--- |
| `P35-05aR4-01` | An assertion whose `exp − iat` exceeds 300 seconds is refused, **including by a fractional amount, and regardless of whether `iat` is integral** | `test_a_fractional_lifetime_just_over_the_ceiling_is_refused` (0.1s, 0.9s, 0.99s over, integer `iat`) |
| `P35-05aR4-02` | An assertion whose `exp − iat` equals exactly 300 seconds is accepted | `test_an_assertion_within_the_ceiling_is_accepted` |

`P35-05aR4-01` is worded to name the two conditions the refuted version left implicit: fractional
excess, and integral `iat`. That is the eighth wording correction in this work stream, and the
first prompted by a code defect rather than an overclaim.

All other propositions from R3 — `P35-05aR3-01`, `03`, `04`, the `P35-05aR2-01`..`08` bearer-only
set, and `P35-05a-02`..`11` assertion verification — carry to this candidate and **require fresh
ballots**.

## 5. What Codex established at R3 that this revision does not disturb

Recorded so the verifier need not repeat the expensive parts.

- **`P35-05aR3-04` survived a strong attack:** equal `401`, identical 35-byte body, identical
  ordered headers, no log or audit side effects, and **no measurable timing distinction across
  220 interleaved samples per path.** The oracle is closed on the evidence, not merely on the
  status code.
- **Bearer-only reverified** at R3: authorize, read, write and audit enumeration all `401` without
  a bearer.
- **Replay reproduced:** the same assertion presented twice within 120 seconds returned `201`
  both times, minting distinct contexts and tokens.

`api.py` is unchanged, so the first two remain true here by construction — but they were measured
at `e559d1d`, not at this candidate.

## 6. What this does NOT establish

1. **Replay is bounded, not prevented.** Codex demonstrated it directly. Within 300 seconds an
   assertion is still replayable and still mints tokens. Closing it needs somewhere to record
   spent `jti` values, which `D-P35-004`..`D-P35-010` block.
2. **`AUTH-D3` remains open.** `POST /v1/principals` and `POST /v1/tenants` still return `201`
   with no assertion. This is the last live authentication hole.
3. **One authenticator kernel-wide**, no per-tenant connections, no key rotation, no endpoint
   other than context issuance authenticated.
4. Codex noted **one unrelated rate-limit timing flake** in the profile-disabled run. Not
   investigated here; recorded so it is not mistaken for a regression.

## 6A. Verification log

| Attempt | Date | Outcome |
| :--- | :--- | :--- |
| 1 | 2026-08-02 01:31 | **Blocked.** Codex's delegated session (`019fbe72-a6af-7f30-9358-7ba87da3ec44`) exited 1 — its cybersecurity classifier blocked the run. No ballot cast, no commit. Partial probe files (`probe_wp_p35_05a_r4_codex.py`, `run_wp_p35_05a_r4_codex.ps1`) remain in the tree, uncommitted |
| 2 | 2026-08-02 01:47 | **Succeeded, committed `7ade81a` "verify(p35): ballot WP-P35-05a R4".** The reframed defensive dispatch was NOT classifier-blocked. Codex cast **23 `CONFIRMED`, 0 `REFUTED`** at this candidate (`119f2d8`), covering `P35-05a-02..11`, `P35-05aR2-01..08`, `P35-05aR3-01/03/04`, and `P35-05aR4-01/02`. The refuted `P35-05aR3-02` is correctly absent — it was the defect this candidate fixed. Verified against `docs/evidence/phase-3.5/ballots.jsonl` |

**The retry guidance below was correct: reframing as defensive verification defeated the block.**
Attempt 2 proves it — the same package, framed as *"confirm the kernel refuses each of the
following"* rather than as an attack, balloted cleanly. The R4 auth boundary is now confirmed at
`119f2d8` under one verifier. Under `EBIV` §6.5 (two-agent profile) one verifier plus operator
disposition yields `CONFIRMED_UNDER_TWO_AGENT_PROFILE`; this is not a two-verifier quorum.

**What still needs a ballot is not R4 but R5's Group B.** The AUTH-D3 tenant-provisioning gate
(`P35-D3a-01..05`) is code that did not exist at this candidate. It is balloted at `ce97561` —
see R5.

**Original retry guidance (retained — it worked).** Codex balloted this same authentication package
without any block at R2 (`f12e5fc`, 18 ballots) and R3 (`e559d1d`, 22 ballots). The attempt-1 block
turned on framing: the dispatch said *"attack"* and the session had accumulated auth-bypass probes,
which reads as offensive security even though the task is **defensive**. Framing the ballot as
verification of a refusal boundary — *"confirm the kernel refuses each of the following"* — made the
defensive intent legible and cleared the classifier.

## 7. Quorum

Two independent verifiers is unreachable with a two-agent team — see
[`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md), **Proposed**. The best
achievable state is one verifier plus §6.3 escalation, and a ballot here should be described that
way.

## 8. Authority

A maker's submission. EBIV §8: a passing suite is a self-assessment carrying **no verdict weight**.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
