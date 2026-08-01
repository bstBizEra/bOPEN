# EVD-P35-05A-MAKER-R3 — WP-P35-05a Maker Submission, revision 3 (Kernel Authentication Boundary)

**Document ID:** `EVD-P35-05A-MAKER-R3`
**Version:** `3.0.0`
**Status:** **MAKER_SUBMISSION_AWAITING_VERIFICATION** — not a completion decision
**Issued:** 2026-08-01
**Supersedes:** [`EVD-P35-05A-MAKER-R2`](wp-p35-05a-maker-submission-r2.md) at `f12e5fc…`

**Commit OID:** `e559d1db92c17c1c96e5a888b49fc76c20d6fcdd`
**Tree OID:** `af4cfaeafddc4d011fc382fbcc013d99db4bf3e8`
**Blob — `api.py`:** `42f1ab685d42043ca9e169f260ff3bb9d2889304`
**Blob — `subject_assertion.py`:** `8d866a286c7f86e435c79f4aafcf1857089d27ec`
**Branch:** `claude/BOPEN-P35-001-runtime-realization`
**Maker:** Claude (agent, Motor role) — `claude@bst.local`
**Eligible verifier:** Codex
**Suites:** canonical 464/464 against PostgreSQL; gateway 47/47

---

## 1. Why revision 3 exists, and what it does to revision 2's ballots

Codex balloted R2 at `f12e5fc` — 18 `CONFIRMED`, no refutations — and, more usefully, reproduced
all four residual defects R2 §6.3 had disclosed as open. This revision closes three and bounds the
fourth.

**Both blobs changed. Codex's 18 ballots at `f12e5fc` do NOT carry forward:**

| Blob | At `f12e5fc` (balloted) | At `e559d1d` (this candidate) |
| :--- | :--- | :--- |
| `api.py` | `bb48fb44…` | **`42f1ab68…`** |
| `subject_assertion.py` | `82b83248…` | **`8d866a28…`** |

Stating that plainly matters: `WP-P35-04` R2 carries two verifiers on a **withdrawn** candidate,
which is a reading a later reader could easily get wrong. Ballots bind to a commit, not to a
package.

## 2. What changed

| Defect (R2 §6.3, all confirmed reproducible by Codex) | Disposition |
| :--- | :--- |
| Malformed PEM → `500` instead of the designed `503` | **Closed.** `load_pem_public_key` raised a bare `ValueError` outside the `try`, escaping as a non-`SubjectAssertionError` |
| Status-code oracle — valid signature + non-UUID `sub` → `400`, bad signature → `401` | **Closed.** Both now return an identical `401`, body included |
| Replay window unbounded — a ten-year assertion was accepted | **Bounded, not closed.** Capped at 300s. Within the window replay is still possible |
| Authenticator must emit bOPEN principal UUIDs as `sub` | **Documented.** Not fixable here; it is the shape of the hole `WP-P35-05b` fills |

## 3. Propositions

Each states exactly what its named test checks, **with its exception written into the claim rather
than into a limitations section.** Seven propositions in the sibling `WP-P35-04` package were
refuted for stating intent instead of behaviour; this section is written against that.

### New at this candidate

| ID | Proposition | Test |
| :--- | :--- | :--- |
| `P35-05aR3-01` | A PEM that cannot be parsed produces `503`, not `500` | `test_a_malformed_pem_refuses_rather_than_crashing` |
| `P35-05aR3-02` | An assertion whose `exp − iat` exceeds 300s is refused | `test_an_assertion_longer_than_the_ceiling_is_refused` |
| `P35-05aR3-03` | An assertion whose `exp − iat` equals 300s is accepted | `test_an_assertion_within_the_ceiling_is_accepted` |
| `P35-05aR3-04` | A valid signature with a non-UUID `sub` and a forged signature return the **same status and the same body** | `test_a_valid_signature_with_a_bad_subject_is_indistinguishable_from_a_bad_signature` |

### Carried from R2, unchanged in substance

`P35-05aR2-01`..`08` (bearer-only across decision, read, write, audit enumeration; no fallback
after verification failure; profile off by default, refused on production, available on local) and
`P35-05a-02`..`11` (assertion verification: signature, issuer, audience, expiry, `alg:none`,
missing claims, non-string claims). **All require fresh ballots at this candidate.**

## 4. Execution and probes

```text
python tools/run_tests.py     464/464 OK   (live PostgreSQL)
apps/gateway  node --test      47/47 OK
```

**Mutation probes, 2026-08-01:**

| Mutation | Observed |
| :--- | :--- |
| Remove the lifetime ceiling | 1 test failed |
| Restore the status-code oracle | 1 test failed |
| Let the malformed-PEM error escape | 2 tests errored |

Tree restored and re-verified at 464/464 after each.

## 5. What this does NOT establish

### 5.1 Replay is bounded, not prevented

Within 300 seconds an assertion is **still replayable**, and each replay still mints a context
token. Closing it needs somewhere to record spent `jti` values, which needs persistence that
`D-P35-004`..`D-P35-010` block. `P35-05aR3-02` claims a ceiling and nothing more.

### 5.2 `AUTH-D3` is untouched and remains the live hole

`POST /v1/principals` and `POST /v1/tenants` still return `201` with no assertion. Anyone who can
reach the kernel can create a principal and provision a tenant naming themselves owner. `AUTH-D1`
did not close this and neither does this revision.

### 5.3 The bearer-only measurement, carried forward

Codex ran the wider suite with `BOPEN_LEGACY_CONTEXT_HEADER_PROFILE` unset and the maker
reproduced it: 441 tests, 12 failures, **every one `401 != <expected>`** — legacy-path tests
failing closed, no protected operation succeeding without a bearer. That measurement was taken at
`f12e5fc`; the bearer-only code path is unchanged at this candidate, but **the probe has not been
re-run here.**

### 5.4 Unchanged limitations

One authenticator kernel-wide, no per-tenant connections, no key rotation, and no endpoint other
than context issuance authenticated.

## 6. Quorum

`BOPEN-GOV-EBIV-001` §6.1 requires two independent verifiers. **With the team reduced to Claude
and Codex, two is unreachable by construction** — the maker is always one of them. See
[`DEC-P35-TWO-AGENT-QUORUM`](../../decisions/DEC-P35-TWO-AGENT-QUORUM.md), Proposed.

Until that is disposed, the best achievable state for this candidate is **one admissible verifier
plus §6.3 escalation to the Completion Authority.** A ballot here is worth casting on that basis
and should not be described as confirmation.

## 7. Authority

A maker's submission. EBIV §8: a passing suite is a self-assessment carrying **no verdict weight**.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
completion_claimed: false
```
