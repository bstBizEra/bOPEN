# BOPEN-SEC-VAULT-001 — Credential and Connection Registry

**Document ID:** `BOPEN-SEC-VAULT-001`
**Version:** `1.0.0`
**Status:** Active
**Issued:** 2026-07-30
**Owner:** Security Authority
**Governing artifacts:** `AGENTS.md` §13, [`secrets-management.md`](secrets-management.md), `BOPEN-SEC-001`
**Classification:** Registry — contains no secret values

---

## 1. What this document is, and what it deliberately is not

This is the single place to find **what credentials exist, who owns them, where their values
live, and whether they are due for rotation**. One lookup, no hunting through code.

It records: credential ID, purpose, username or identifier, connection target, the store
holding the value, owner, and rotation state.

It does **not** record any secret value, and it must never be edited to add one.

That is not a preference. `docs/` is tracked by git, and `AGENTS.md` §13 states *"Never commit
credentials, tokens, private keys or real personal data."* A password written here would be
copied into every clone, survive in history after deletion, and travel to any future public
mirror — which matters directly, because bOPEN is intended to be released as the open-source
foundation of the BST ecosystem. A registry that points at values is as convenient as one that
contains them, and is the only version that is safe to publish.

Usernames, hostnames, ports and database names are recorded in full. They are configuration,
not secrets.

---

## 2. Where values actually live

| Store | Path or mechanism | Committed |
| :--- | :--- | :--- |
| Local development | `.env.local` at the repository root | No — `.gitignore` excludes `.env` and `.env.*`, allowing only `.env.example` |
| Template | [`.env.example`](../../../.env.example) | Yes — placeholders only |
| CI | Repository or organization secrets in the CI provider | No |
| Production | External secret manager, to be selected by ADR before first deployment | No |

Loading values into a shell:

```bash
# bash / git-bash
set -a; . ./.env.local; set +a
```

```powershell
# PowerShell
Get-Content .env.local | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "env:$($name.Trim())" -Value $value.Trim()
}
```

No tool in this repository reads a credential from a file on its own. `tools/db_bootstrap.py`
and `platform_kernel/db.py` read environment variables only, and both fail with explicit
remediation text when a variable is absent rather than falling back to a default.

---

## 3. Registry

Rotation state values: `current`, `rotate_now`, `not_provisioned`.

### 3.1 Databases

| ID | Purpose | Username | Target | Value store | Env var | Owner | Rotation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CRED-DB-VERIFY-SUPER` | Superuser of the local verification instance. Runs migrations and provisions roles | `postgres` | `127.0.0.1:5433` / `postgres` | `.env.local` | `BOPEN_ADMIN_DATABASE_URL` | Operator | **`rotate_now`** — see §4.1 |
| `CRED-DB-VERIFY-APP` | Unprivileged application role used by the kernel and the isolation suite | `bopen_app` | `127.0.0.1:5433` / `bopen_dev` | `.env.local` | `BOPEN_DATABASE_URL` | Operator | `current` — non-production value by design, see §4.2 |
| `CRED-DB-LARAGON-5432` | PostgreSQL instance listening on 5432, provenance unresolved | `postgres` | `127.0.0.1:5432` | unknown | — | Operator | unresolved — see §4.3 |
| `CRED-DB-PROD` | Production kernel database | not provisioned | not provisioned | external secret manager | `BOPEN_DATABASE_URL` | Security Authority | `not_provisioned` |

The verification instance is a cluster created for `BOPEN-P35-001` at
`C:\laragon\data\bopen-verify`, listening on 127.0.0.1 only, port set in its own
`postgresql.conf`. It is separate from any pre-existing instance on 5432 and can be deleted
without affecting other projects.

`bopen_app` is deliberately **not** a superuser and does not own the tables. A superuser
bypasses Row-Level Security entirely, so an isolation suite run as superuser passes for the
wrong reason. This separation is what makes `FORCE ROW LEVEL SECURITY` observable.

### 3.2 Identity and federation — not yet provisioned

Bound by `BOPEN-IDP-001`. Recorded now so that provisioning has a destination rather than
appearing ad hoc in code later.

| ID | Purpose | Identifier | Value store | Env var | Owner | Rotation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `CRED-IDP-JACKSON-CLIENT` | BoxyHQ Jackson client credentials for the SSO bridge | per-tenant client ID | external secret manager | `BOPEN_JACKSON_CLIENT_SECRET` | Security Authority | `not_provisioned` |
| `CRED-IDP-SCIM-TOKEN` | SCIM 2.0 provisioning bearer token, issued per tenant | per-tenant | external secret manager | — (per-tenant, stored encrypted) | Security Authority | `not_provisioned` |
| `CRED-TOKEN-CONTEXT-SIGNING` | Ed25519 signing key for the context access token carrying `sub`, `tid`, `mid`, `roles`, `scopes` | RFC 7638 JWK thumbprint (`kid`) | `.env.local` (development) / external secret manager (production) | `BOPEN_CONTEXT_TOKEN_KEY` | Security Authority | **development key `current`; production `not_provisioned`** |

`CRED-TOKEN-CONTEXT-SIGNING` is the highest-value secret in the system. It attests which tenant
a request belongs to; forging it defeats every isolation control below it, including the RLS
policies, without ever touching the database. It must be provisioned in an external manager and
never in `.env.local` beyond local development.

Development keys are generated by `python tools/generate_token_key.py`, which prints to stdout
and writes nothing — it cannot create the file someone later commits by accident. The public
half is served at `/.well-known/jwks.json` and is safe to publish; that is what lets the gateway
and satellite products verify a `tid` claim on their own without holding anything that could
also mint tokens.

Rotation is supported by design: `KeyRegistry` resolves verification keys by `kid`, so an
outgoing key can keep verifying while an incoming key signs. Per `BOPEN-IDP-001` §12.4 the
overlap period must be shorter than the maximum token lifetime (5 minutes) plus clock skew
(60 seconds).

### 3.3 Repository and tooling

| ID | Purpose | Identifier | Value store | Owner | Rotation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CRED-GIT-COMMITTER` | Git author identity for agent commits | `BizEra` / `agent@bizera-smartthink.local` | git config — not a secret | Operator | n/a |

No API keys, package registry tokens, or webhook secrets are in use at this commit.

---

## 4. Exposure and rotation notes

### 4.1 `CRED-DB-VERIFY-SUPER` requires rotation

This value was transmitted in an agent chat session on 2026-07-30 in order to unblock
`WP-P35-01`. It is therefore present in that session transcript, which is retained outside
this repository and outside the operator's control.

It was never written to any file in this repository. `initdb` consumed it through a temporary
file under the session scratchpad which was deleted in the same command.

Treat it as disclosed and rotate it:

```bash
# from the verification instance
ALTER ROLE postgres WITH PASSWORD '<new value>';
```

Then update `.env.local`. Nothing else references it.

**Standing rule:** do not paste a secret into an agent conversation. Write it to `.env.local`
and name the variable instead. An agent needs the variable name, not the value.

### 4.2 `CRED-DB-VERIFY-APP` is intentionally weak

The default is `bopen_local_dev` — a clearly non-production placeholder, per
`secrets-management.md` ("Local examples use non-secret placeholders"). It is acceptable only
because the instance binds 127.0.0.1 and holds synthetic data. Override it with
`BOPEN_APP_PASSWORD` before this pattern is used anywhere reachable from a network.

### 4.3 `CRED-DB-LARAGON-5432` is unresolved

A PostgreSQL server accepts connections on 5432, but the `CRED-DB-VERIFY-SUPER` value is
rejected by it, and both laragon data directories (`postgresql-17`, `postgresql-17.10`) show
a clean shutdown in July with no subsequent start. The running server is therefore neither of
them and its origin is not established.

This is recorded rather than resolved because guessing at credentials for an unidentified
service is not a safe activity. If it is not needed, stopping it removes an unknown listener;
if it is needed by another project, it should be identified and added to this registry.

---

## 5. Verification

Secret hygiene is checked mechanically, not by review alone:

```bash
# gitleaks is present at C:\laragon\bin\gitleaks\gitleaks.exe
gitleaks detect --source . --redact --no-banner
```

`--redact` matters: without it a finding report reproduces the secret it found, and that
report is often pasted into an issue or a chat.

A finding in `docs/` is a defect in this document, not a false positive.

---

## 6. Provenance

Authored by Claude (agent, Immune role) on 2026-07-30 at operator request for a single
credential registry under `docs/`.

The request was for a vault holding usernames and passwords. This document holds usernames
and pointers; values are held in `.env.local`, which git excludes. The substitution is
deliberate and is explained in §1. If a genuine encrypted vault inside the repository is
wanted instead — for example SOPS or `git-crypt` with an age or GPG recipient set — that
requires an ADR selecting the mechanism and a key-custody decision, and should not be
improvised.

`execution_authority: false`, `approval_authority: false`. Rotation of
`CRED-DB-VERIFY-SUPER` is an operator action.
