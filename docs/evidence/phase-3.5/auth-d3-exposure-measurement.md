# EVD-P35-AUTH-D3-EXPOSURE — What an unauthenticated caller can actually do

**Document ID:** `EVD-P35-AUTH-D3-EXPOSURE-001`
**Version:** `1.0.0`
**Status:** Measurement — input to the pending `AUTH-D3` disposition. **Not a ballot, not a verification.**
**Issued:** 2026-08-01
**Probe author:** Codex (`tools/probes/probe_auth_d3_exposure.py`, 581 lines)
**Probe executed by:** Claude (agent, Motor role)
**Kernel commit:** `119f2d8cf678624c055c8d1be48c770b3936de11`
**Method:** three uvicorn kernels on loopback TCP, live PostgreSQL, real HTTP

---

## 1. Provenance, and why the split matters

**Codex wrote this probe; Claude executed it.** Codex's run wrote the probe at 16:00, executed it,
and then stopped without committing a report — no temp logs remained, no Python process survived,
and the last database write was 16:01. The measurement below is a re-execution.

The split is worth stating because it affects how much this evidence is worth. **The probe was
designed by an agent that did not write the kernel**, so its choice of what to measure is
independent of the maker. Execution is deterministic — the same probe run by either party yields
the same numbers. What is *not* independent is the interpretation in §5, which is the maker's and
should be read as such.

## 2. Headline: a complete unauthenticated path from nothing to an owner token exists

Under the **open profile** (no authenticator configured, `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION=1`
— the documented local/dev default):

```text
zero_to_owner:  principal 201  ->  tenant 201  ->  context 201  ->  token_issued: true
```

And that token is fully functional in the tenant it created:

| Operation | Result |
| :--- | :--- |
| `POST /v1/authorize` | `200`, decision **ALLOW** |
| `GET /v1/resources/{id}` | `200` |
| `POST /v1/resources` | `201` |
| `GET /v1/audit-events` | `200`, 5 events |

**A caller with no credentials of any kind reaches a working owner bearer token in three calls.**

## 3. Tenant isolation holds — and this bounds the severity

| Probe | Result |
| :--- | :--- |
| Read a foreign tenant's resource with a conflicting `X-Tenant-ID` | `403` |
| Read a foreign tenant's resource without a conflicting header | `404` |
| Foreign tenant's audit events visible | **0** |

**The attacker gets a tenant of their own, not yours.** The isolation boundary is doing its job
even where authentication is absent, which is the difference between an abuse problem and a
breach. This should temper the severity assessment rather than inflate it.

## 4. What the profiles actually close

The three scenarios are the substance of the finding. **Neither non-open profile closes principal
creation.**

| | open profile | flag unset | authenticator configured |
| :--- | :--- | :--- | :--- |
| `POST /v1/principals` | **201** | **201** | **201** |
| `POST /v1/tenants` | **201** | `503` | **201** |
| `POST /v1/contexts` | **201** | `503` | `401` |

Three readings:

1. **`AUTH-D1` worked.** With an authenticator configured, context issuance is `401` — *"X-Subject-Assertion is required by this deployment"*. That is the privilege escalation closed, confirmed at the current commit.
2. **Configuring an authenticator does not close tenant provisioning.** `POST /v1/tenants` still returns `201`. A deployment that believes it has enabled authentication has not closed this.
3. **Nothing closes principal creation.** All three profiles return `201`. The flag-unset profile — the closest thing to a safe default — still permits it.

## 5. Abuse surface, measured

### 5.1 No rate limit, no quota, no cost ceiling

```text
40 principals + 20 tenants in 5.847s
429 responses: 0        rate/retry headers: none
```

Nothing throttles creation. Under the ratified hybrid placement model **each tenant eventually
means a database**, so an unauthenticated caller can queue unbounded infrastructure cost. This is
the finding with the sharpest operational consequence.

### 5.2 Tenant squatting works

| Probe | Result |
| :--- | :--- |
| Provision a tenant naming **another principal** as owner | **`201`** |
| Squatted owner's authorization decision | **ALLOW** |
| Naming a **non-existent** principal | `422` |
| Victim's pre-existing tenant after the squat | still `200` / ALLOW |

A caller can create a tenant naming a real principal they do not control as its owner. The
victim's existing tenants are unaffected — so this is unsolicited-tenant pollution and
impersonation-by-association, not takeover.

### 5.3 The account-existence oracle is still reproducible, and now has a second form

| Channel | Existing address | New address |
| :--- | :--- | :--- |
| Status | `409` | `201` |
| Body length | 55 bytes | 168 bytes |
| Median latency | 34.18 ms | 35.43 ms |

`P(existing faster) = 0.647` over 80 pairs, against 0.500 for indistinguishable distributions —
consistent with `EVD-SEC-001` Addendum C, which recorded 0.657 over 150 pairs.

**New:** `unauthenticated_email_reservation: 201`. A caller can *reserve* an address they do not
own. Combined with the global uniqueness constraint on `principals.email`, that is a denial-of-registration
against a specific person — and `principals` has no delete path for the application role
(migration 007), so it is not trivially reversible.

## 6. What this means for the `AUTH-D3` disposition

Advisory. The disposition is the authorities'.

**The exposure is real, unbounded in volume, and bounded in blast radius.** No cross-tenant read
was achieved. The costs are abuse, cost-inflation, squatting and denial-of-registration — not
disclosure of another tenant's data.

That argues for two things:

1. **`AUTH-D3` is not an emergency**, and should not be rushed into accepting the enrollment-credential
   recursion risk on urgency grounds. The research's controls — single-use, ≤10 minutes, ≥112 bits,
   out-of-band, never emailed — remain the right bar.
2. **But two mitigations are cheaper than the enrollment decision and do not depend on it.** Rate
   limiting creation, and closing tenant provisioning to authenticated callers, are both available
   under the already-ratified `AUTH-D1` reasoning — `POST /v1/tenants` names an `owner_principal_id`
   that must already exist, so an assertion for that principal can authenticate it **without solving
   the bootstrap problem at all.**

Only `POST /v1/principals` genuinely requires `AUTH-D3`, because that is the call where no principal
yet exists to assert.

**Neither mitigation is implemented here.** Both are recommendations for the authorities, and the
second amends a work package. Recorded so the decision can be made on measurement.

## 7. Limits of this evidence

1. **The interpretation in §5 and §6 is the maker's**, on the maker's own code. The measurements
   are Codex's design and are reproducible; the severity framing is not independent.
2. Single run per scenario. Latency figures are 80 pairs; the earlier oracle finding used 150.
3. Loopback TCP, single host. No network, proxy or gateway in the path.
4. **Not a ballot.** Nothing here confirms or refutes any proposition.

```text
execution_authority: false
approval_authority: false
production_activation_authority: false
```
