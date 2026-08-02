# EVD-P35-05A-MAKER-R5 — WP-P35-05a auth boundary + AUTH-D3 Row 1(a)

**Document ID:** `EVD-P35-05A-MAKER-R5`
**Version:** `5.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-02
**Supersedes:** [`EVD-P35-05A-MAKER-R4`](wp-p35-05a-maker-submission-r4.md) at `119f2d8` — **which was in fact balloted `7ade81a` after this R5 was issued: 23 `CONFIRMED`, 0 `REFUTED`, verifier `codex`.** The "never balloted" note that first appeared here was written before those ballots landed and is corrected in §1.
**Also implements:** [`DEC-P35-AUTH-D3-DOCKET`](../../decisions/DEC-P35-AUTH-D3-DOCKET.md) `D-D3-001` Row 1(a), operator-approved 2026-08-02

**Commit OID:** `ce97561bf21106c35c473bf71c0afee835443a35`
**Tree OID:** `1157ba87f78936f316f5d9741e31758a64c6e806`
**Blob — `api.py`:** `646cf4121a89161e89f432b5da346d211f437389` *(changed: adds tenant-provisioning gate)*
**Blob — `subject_assertion.py`:** `ada0eb1de30f5d78798947744f0219585ff43d07` *(byte-identical to R4 — auth-boundary fixes intact)*
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical **470/470** against PostgreSQL; gateway **47/47**

---

## 1. Why one combined candidate — and the R4-ballot reconciliation

**Correction (2026-08-02).** This section first said "R4 was never balloted." That was written
while a first verifier session was classifier-blocked. It is now false: a reframed defensive
dispatch succeeded and **R4 (`119f2d8`) was balloted at `7ade81a` — 23 `CONFIRMED`, 0 `REFUTED`,
verifier `codex`**, covering the full R4 proposition set. The record stands corrected here and in
R4 §6A.

That does not undo the decision to combine. When AUTH-D3 Row 1(a) was built on top of the R4 tree,
the R4 ballots had not yet been observed. The result is a clean, favourable reconciliation rather
than wasted work:

- **`subject_assertion.py` is byte-identical** between R4 (`119f2d8`) and this candidate
  (`ce97561`): blob `ada0eb1` at both, confirmed by `git rev-parse`. The auth-boundary code Codex
  confirmed is unchanged here.
- **The `api.py` delta is surgically confined** to `provision_tenant`: it adds the
  `X-Subject-Assertion` header parameter and the owner-mismatch gate, and touches nothing else — not
  the bearer-only paths, not context issuance, not assertion verification. So the change cannot
  disturb any Group A proposition; it only *adds* the Group B surface.

**What this means for balloting.** The Group A propositions were `CONFIRMED` by Codex at `119f2d8`.
Because ballots bind to a commit, whether those verdicts carry to `ce97561` is a **verifier's**
judgment, not the maker's (`EBIV` §8) — the byte-identity and additive-delta facts above are
offered as evidence for that judgment, not as a maker ruling. The genuinely new, unballoted surface
is **Group B (`P35-D3a-01..05`)**. A verifier balloting here need re-establish only Group B and may,
on the hash evidence, carry Group A forward.

## 2. This is a defensive verification, not an attack

**Read this framing first.** Every proposition below asserts that the kernel **refuses** an
invalid or unauthorized request and **accepts** a valid one. Verifying a refusal boundary is
defensive security review. There is no exploitation of a third party and no offensive objective —
the work is confirming that forged, expired, over-long, and unauthorized inputs are turned away.

## 3. Proposition group A — auth boundary (carried from R4, `subject_assertion.py` unchanged)

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P35-05aR4-01` | refuse an assertion whose `exp − iat` exceeds 300s, including by a fractional amount with an integer `iat` | `test_a_fractional_lifetime_just_over_the_ceiling_is_refused` |
| `P35-05aR4-02` | accept an assertion whose lifetime equals exactly 300s | `test_an_assertion_within_the_ceiling_is_accepted` |
| `P35-05aR3-01` | return 503, not 500, on a malformed public key | `test_a_malformed_pem_refuses_rather_than_crashing` |
| `P35-05aR3-04` | return an identical 401 (status and body) for a bad-subject and a forged-signature assertion | `test_a_valid_signature_with_a_bad_subject_is_indistinguishable_from_a_bad_signature` |
| `P35-05aR2-01`..`08` | keep protected endpoints bearer-only; legacy profile off by default, refused on production | `test_auth_d1_bearer_only.py` |
| `P35-05a-02`..`11` | verify assertion signature, issuer, audience, expiry, `alg:none`, claim presence and type | `test_subject_assertion_boundary.py` |

## 4. Proposition group B — AUTH-D3 Row 1(a): tenant provisioning *(new)*

Closes the tenant squatting the exposure measurement reproduced. `POST /v1/tenants` names an
`owner_principal_id` that must already exist, so an assertion for *that* principal authenticates
the call — no bootstrap problem.

| ID | The kernel must… | Test |
| :--- | :--- | :--- |
| `P35-D3a-01` | refuse tenant provisioning with **no** assertion when an authenticator is configured | `test_provisioning_without_an_assertion_is_refused_when_authenticator_configured` |
| `P35-D3a-02` | refuse (403) an assertion vouching for a principal **other than** the named owner | `test_an_assertion_for_a_different_principal_cannot_bind_this_owner` |
| `P35-D3a-03` | provision when the assertion vouches for the named owner | `test_an_assertion_for_the_named_owner_provisions` |
| `P35-D3a-04` | refuse a forged assertion (401) | `test_a_forged_assertion_is_refused` |
| `P35-D3a-05` | not let the development flag reopen provisioning when an authenticator is configured | `test_the_development_flag_cannot_reopen_provisioning_when_authenticator_configured` |

**Attack angle for the verifier:** try to bind a victim as owner while holding an assertion only for
yourself — `P35-D3a-02` claims that returns 403. And check whether the dev flag can override a
configured authenticator here as it could not for context issuance.

## 5. Execution and probes

```text
python tools/run_tests.py     470/470 OK   (live PostgreSQL)
apps/gateway  node --test      47/47 OK
```

Mutation probe, 2026-08-02: removing the owner-mismatch check (`asserted_principal != owner_id`)
breaks the squatting test. R4's probes (lifetime ceiling, oracle, PEM) remain valid — `subject_assertion.py` is unchanged.

## 6. What this does NOT establish

1. **`POST /v1/principals` is still unauthenticated.** That is the enrollment chicken-and-egg —
   no principal exists yet to assert — and it is `D-D3-002`, not Row 1. Principal creation remains
   open by design of this scope.
2. **Rate-limiting (Row 1(b)) is not implemented.** It needs a keying decision (per-source vs
   global vs gateway-layer) and is surfaced separately. The resource-exhaustion vector the exposure
   measured is not closed here.
3. **Replay is still bounded, not prevented** (R4 §6.1 carries).
4. Two-agent profile: one verifier plus operator disposition confirms (`EBIV` §6.5). Not a
   two-verifier quorum.

## 6.5 Admissibility remediation (2026-08-02) — why this candidate moves

Codex balloted this candidate at `ce97561` and reported all nine propositions behaving correctly
(Group A `401`/`201`/`503`/identical-`401`; Group B `401`/`403`/`201`/`401`/`401`), suite 470/470 on
an isolated rerun — **but cast all nine `INADMISSIBLE` on `EBIV` R2**: the propositions were absent
from the mandatory `invariant-traceability.csv`. That was a maker/recorder omission, not a boundary
defect.

The gap was real and wider than these nine: the entire subject-assertion / AUTH-D1 / AUTH-D3
boundary had **no invariant rows** in `docs/evidence/phase-3.5/invariant-traceability.csv`. The
earlier R4 ballot recorded R2=`True` for the same propositions against the same CSV, which was
itself incorrect — those propositions were never traced. **No admissible verdict exists on this
boundary yet, at R4 or R5.**

**Remediation, in two commits.** The **whole** boundary is now traced — all 27 propositions, not
only the nine Codex balloted — so the re-ballot can cover the full set in one pass rather than
surface the same R2 gap on the remainder later:

- First commit `edefa97` traced the nine balloted propositions: `INV-ASSERTION-LIFETIME-CEILING-01`,
  `-LIFETIME-BOUND-01`, `-KEY-SAFE-01`, `-OPAQUE-01`, `INV-PROVISION-OWNER-ASSERTED-01`,
  `-OWNER-BINDING-01`, `-OWNER-VOUCHED-01`, `-FORGERY-01`, `-DEVFLAG-01`.
- This commit traces the remaining eighteen carried propositions: `P35-05a-02..11` (assertion
  verification — `INV-ASSERTION-PARTIAL-CONFIG-01`, `-SUBJECT-BINDING-01`, `-SIGNATURE-01`,
  `-ISSUER-01`, `-AUDIENCE-01`, `-EXPIRY-01`, `-ALG-01`, `-CLAIMS-01`, `-REFUSAL-OPAQUE-01`,
  `-NO-AUTHENTICATOR-01`) and `P35-05aR2-01..08` (bearer-only / AUTH-D1 —
  `INV-BEARER-AUTHZ-01`, `-READ-01`, `-WRITE-01`, `-AUDIT-01`, `-NO-FALLBACK-01`,
  `INV-LEGACY-OFF-DEFAULT-01`, `-NO-PROD-01`, `-LOCAL-01`). It also corrects two of the first nine
  rows whose `evidence_kind` was `executed_http` but whose tests drive `verify_subject_assertion`
  directly — `executed_python` is accurate.

Each row names its executed test and the mechanism whose removal breaks it. **No source code
changed** — `subject_assertion.py` (`ada0eb1`) and `api.py` (`646cf41`) are byte-identical to
`ce97561`. Only the recording gap that failed R2 is closed.

**This is a recorder action, not a verdict** (`EBIV` §8). The candidate for a fresh ballot is the
commit carrying this second remediation; Codex re-ballots there, where R2 can pass for the full
27-proposition boundary, and only then does a verdict exist for operator disposition. No recorded
debt remains on this boundary.

## 7. Authority

A maker's submission. `EBIV` §8: a passing suite carries no verdict weight.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
