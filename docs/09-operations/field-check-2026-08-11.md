# Field check — the running system, not the documents, 2026-08-11

**Status:** **OBSERVATION RECORD — advisory.** Not a disposition, not a verdict, not an authorization.
**Ran at:** `6a5511f`, branch `claude/BOPEN-P35-001-runtime-realization`, local development environment
**Run by:** Claude (agent, Motor role) — the maker of most of what is checked here. **Not independently
verified.** `BOPEN-GOV-EBIV-001` §8: a maker's own passing check carries no verdict weight.

Everything below was measured against the live PostgreSQL instance and the loaded application, not
read from a document.

---

## 1. What holds up

### 1.1 Schema and isolation

```text
PostgreSQL          listening on 5432 and 5433
migrations applied  22 of 22, latest 022, none missing
tables              40
ENABLE + FORCE RLS  40 of 40
```

**Every tenant-scoped table forces row-level security.** No table relies on `ENABLE` alone, which
would be bypassed by the table owner.

### 1.2 Evidence survives tenant deletion — on **both** foreign-key paths

`WP-P35-08` changed `tenant_id` from `CASCADE` to `RESTRICT` on eleven tables. A second path was not
covered by that work and was checked here: deleting a tenant could delete a parent entity, and the
parent reference could cascade to the evidence row regardless of the `tenant_id` action.

**It does not.** Every evidence table is `RESTRICT` on both references:

```text
location_history          -> locations             RESTRICT   -> tenants  RESTRICT
location_address_versions -> locations             RESTRICT   -> tenants  RESTRICT
notification_attempt      -> notification_dispatch RESTRICT   -> tenants  RESTRICT
notification_receipt      -> notification_dispatch RESTRICT   -> tenants  RESTRICT
workflow_history          -> workflow_instances    RESTRICT   -> tenants  RESTRICT
party_contact_point_verification_events -> party_contact_points RESTRICT -> tenants RESTRICT
audit_events, lifecycle_events                                -> tenants  RESTRICT
```

13 foreign keys to `tenants` are `RESTRICT`; the remaining 17 are `CASCADE` and are operational data
(`active_contexts`, `memberships`, `notifications`, `parties`, `locations`, `workflow_instances`, …),
which is the intended split.

### 1.3 Live deletion probe

Tenant deletion attempted against real rows, each inside a savepoint and rolled back:

```text
tenant holding audit_events          -> refused by audit_events
tenant holding lifecycle_events      -> refused by lifecycle_events
tenant holding workflow_history      -> refused by workflow_history
tenant holding party_contact_points  -> refused by party_contact_points
tenant holding location_history      -> refused by location_relationships
tenant holding notification_dispatch -> refused by notification_dispatch
tenant holding notification_receipt  -> refused by notification_dispatch
```

Nothing was committed.

> **A first run of this probe deleted three tenants successfully and looked like a failed control.**
> It was not: those tenants held **no rows** in any protected table, so `RESTRICT` had nothing to
> restrict. The database held **94,539 tenants** at that moment and the first five sampled were
> empty — see §2.3 for why there are so many. Recorded because the wrong conclusion was one step
> away, and the probe that would have produced it looked exactly like a valid control.

### 1.4 Canonical suite

```text
Ran 685 tests in 625.276s
OK
FAIL: 0    ERROR: 0    exit 0
```

Inventory reconciles: unit 171 + integration 253 + contracts 101 + isolation 146 + governance 14 =
**685**, the number executed.

**This result is bound to tracked files.** `tools/run_tests.py` uses `loader.discover()`, so an
untracked test file on disk would be collected and counted — an earlier claim of "680 tests" in this
repository had to be withdrawn for exactly that reason. At this run: `git status --porcelain` reports
**0 untracked files**, and tracked test files (51) equal test files on disk (51).

## 2. What does not hold up

### 2.1 `P35-04R-15` is not abstract — the interactive docs are reachable through the gateway

The kernel exposes **45 routes: 38 under `/v1`, 7 outside it.**

```text
/.well-known/jwks.json   /docs   /docs/oauth2-redirect   /health
/openapi.json            /redoc  /readiness
```

Five were probed through the gateway with a dot-segment path. **All five reached the kernel:**

```text
/v1/../docs                   -> 200   kernel saw /docs
/v1/../openapi.json           -> 200   kernel saw /openapi.json
/v1/../.well-known/jwks.json  -> 200   kernel saw /.well-known/jwks.json
/v1/%2E%2E/redoc              -> 200   kernel saw /redoc
/v1/../health                 -> 200   kernel saw /health
```

`DEC-P35-GATEWAY-PREFIX-CONFINEMENT` is therefore not an architectural preference. **It decides
whether the interactive API documentation and the complete OpenAPI schema are served through the
gateway**, and whether the `/v1` prefix means anything at all. The refutation `P35-04R-15` describes
this exact behaviour and has stood open since 2026-08-01.

### 2.2 No Python packaging

There is no `pyproject.toml` or `setup.py` at the repository root or in any service.
`tools/run_tests.py` hardcodes four `sys.path` inserts to compensate.

**Correction to a claim made during this check.** It was first recorded that the service "cannot be
started by a standard invocation". **That is wrong.** With the platform-correct path separator,
`PYTHONPATH="packages/kernel-core/python;services/platform-kernel/python;sdk/python;."` imports
cleanly and `platform_kernel.api:app` exists, so `uvicorn platform_kernel.api:app` works. The first
attempt used `:` as the separator, which is not the separator on this platform, and the failure was
in the attempt rather than in the repository.

**What remains true and much smaller:** deployment must supply four path entries by hand, in the
right order, with no installable artifact declaring them. That is a packaging gap in the
**production-readiness and deployment area** — described by `AGENTS.md` §29's `LC-11`/`LC-12`, which
is **`PROPOSED`, not in force** — and not a blocker on running the service.

### 2.3 The development database grows by roughly 850 tenants per suite run

Counts were taken twice, before and after the canonical suite, and the difference is the finding:

| | before the suite | after | delta |
| :--- | ---: | ---: | ---: |
| `tenants` | 94,539 | 95,383 | **+844** |
| `audit_events` | 51,186 | 51,822 | **+636** |
| `lifecycle_events` | 3,726 | 3,744 | +18 |
| `location_history` | 1,838 | 1,912 | +74 |

**Nothing cleans up.** At ~844 tenants per run the current 95,383 implies on the order of a hundred
suite runs' worth of residue, and it is a measurable drag on inspection already: a per-tenant scan
across thirteen protected tables produced 5.8 MB of output and exceeded two minutes.

Not a correctness defect — every isolation test passes against this data, and a suite that leaves its
fixtures behind is testing against a more realistic table size, not a less realistic one. But two
consequences are real: the numbers in this document are **observations of a moving system, not
constants**, and any future measurement of tenant-scoped query performance will be measuring a
database no deployment will ever look like.

### 2.4 Configuration lives in `.env.local`, which is correct but undocumented

No `.env` exists. The live configuration is `.env.local`, holding eight keys. It is ignored at
`.gitignore:14` and has never been committed — consistent with
[the credential scan](../07-security/pre-publication-credential-scan-2026-08-10.md). `.env.example`
documents `.env`, not `.env.local`, so a new operator following the example would set up a file the
running system does not read.

## 3. What this check does NOT establish

1. **It is a development environment.** Nothing here says anything about production behaviour, load,
   resilience, or an environment that does not exist yet. `AGENTS.md` §29.6 makes the same point
   about its `LC-9`–`LC-11` stages, but §29 is **`PROPOSED`, not in force**, so nothing here rests
   on it — and §29.6's own assessment of the security evidence is understated (see
   [the AGENTS.md audit](../00-governance/agents-md-audit-2026-08-11.md) §2).
2. **The suite passing carries no verdict weight** (EBIV §8), and this run was made by the maker.
3. **The gateway probes used an injected `fetchImpl`,** not a running kernel over HTTP. They prove
   what path the gateway forwards, which is the claim being made, and not what a deployed kernel
   would answer.
4. **Two claims made during this check were wrong and are corrected above** — the tenant-deletion
   control (§1.3) and the packaging claim (§2.2). Both were caught by continuing to check rather than
   by reading back what had been written.

Recorded advisory-only. Confers no verdict, no disposition, no merge, release or production
authority.
