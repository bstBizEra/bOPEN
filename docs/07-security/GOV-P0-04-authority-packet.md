# BOPEN-SEC-GOV-P0-04 — External Source-Control & Secrets-Vault Authority Packet

**Version:** 0.1-DRAFT
**Status:** PENDING HUMAN APPROVAL — not normative, does not authorize any action
**Owner:** \<Security Authority — to be named\>
**Issued (draft):** 2026-07-22
**Effective date:** \<YYYY-MM-DD — set by approver on signing\>
**Expiry date:** 2027-01-18
**Decision class:** D2 High-risk (identity, credential, privileged access)
**Governed by:** BOPEN-GOV-001 §4.2, §9, §13; secrets-management.md; privileged-access.md

---

> **DRAFT NOTICE**
> This document is informative until every section is completed, all approvers have
> recorded their explicit written consent in §14, and the document status is changed
> to APPROVED. No credential, token, key, remote URL, or vault reference may be
> copied, created, activated, or committed to source control until that state is reached.

---

## 1. Purpose

Define the bounded authority for bOPEN agents and human makers to interact with:

1. **GitHub** — external source-control hosting and CI/CD pipeline triggers.
2. **Gitea** — internal/self-hosted source-control mirror and private package registry.
3. **1Password** — secrets vault for service-account credentials, tokens, and keys.

This packet satisfies the GOV-P0-04 block. Fields marked **[NEEDS HUMAN INPUT]** are
mandatory. Partial completion keeps the block active.

---

## 2. Scope decision

**Chosen scope: Option A — bOPEN only.**

Authority applies exclusively to repositories and vaults used by the bOPEN platform.
BST products outside bOPEN are not covered by this packet.

**Rationale:** Narrowest viable scope; reduces blast radius; aligns with current
bOPEN-only development phase. BST-wide authority requires a separate packet with
an expanded threat model.

---

## 3. GitHub authority

### 3.1 Organization and repositories

| Field | Value |
|---|---|
| GitHub organization URL | https://github.com/bstBizEra |
| Canonical remote (HTTPS) | https://github.com/bstBizEra/bOPEN.git |
| Repositories in scope | `bOPEN` |
| Repositories explicitly excluded | All other repositories under https://github.com/bstBizEra (wildcard `bstBizEra/*` scope is not granted; bOPEN-only per §2) |

### 3.2 Permission levels

> **[NEEDS HUMAN INPUT]** Replace placeholder rows with real principal names and justifications.
> Agents may only be listed with `read` permission unless an explicit write scope is
> recorded here and in the associated authorized work item.

| Principal (human or service account) | Role / permission | Repositories | Justification |
|---|---|---|---|
| \<Project lead full name\> | admin | bopen | Repository owner and delivery authority |
| \<CI service account name\> | write (push, status) | bopen | CI/CD pipeline and mirror trigger |
| \<Agent service account name\> | read | bopen | Agent read-only repository access |

### 3.3 Service accounts and tokens

> **[NEEDS HUMAN INPUT]** List each token with its exact granted scopes.
> No token scope may exceed what is listed here. Wildcard scopes are not accepted.

| Token / app | Type | Scopes granted | Expiry | Owner |
|---|---|---|---|---|
| \<ci-token-name\> | PAT | `repo:status`, `public_repo` | 2027-01-18 | \<human name\> |
| \<mirror-token-name\> | PAT | `repo` (write — if no finer scope available) | 2027-01-18 | \<human name\> |

---

## 4. Gitea authority

### 4.1 Host and repositories

| Field | Value |
|---|---|
| Gitea host URL | http://localhost:3030 |
| Canonical repository URL | http://localhost:3030/bstBizEra/bopen |
| Repositories in scope | `bopen` |
| Mirror direction | Gitea → GitHub (Gitea is primary; GitHub is the public face) |
| Mirror trigger | Push event (on every push to Gitea) |
| Repositories explicitly excluded | All other repositories under http://localhost:3030/bstBizEra (wildcard `bstBizEra/*` scope is not granted; bOPEN-only per §2) |

> **Security note:** `http://localhost:3030` is non-TLS and is suitable for local
> development only. Before any staging or production deployment, a TLS-terminated
> URL must replace this entry and this packet must be re-approved.
>
> **Casing discrepancy — [NEEDS HUMAN RESOLUTION]:** The Gitea repository is named
> `bopen` (lowercase) while the GitHub repository is named `bOPEN` (mixed case).
> Before the mirror is activated, confirm whether these names should be aligned.
> Mismatched names can cause mirror misconfiguration and must be resolved by the
> named Maker before the Checker signs off.

### 4.2 Permission levels

> **[NEEDS HUMAN INPUT]** Replace placeholder rows with real principal names.

| Principal | Role / permission | Repositories | Justification |
|---|---|---|---|
| \<Project lead full name\> | admin | bopen | Repository owner |
| \<Mirror service account name\> | write | bopen | Pushes mirror events to GitHub via push-event trigger |
| \<Agent service account name\> | read | bopen | Agent read-only access |

### 4.3 Service accounts and tokens

> **[NEEDS HUMAN INPUT]** List each Gitea API token with exact scopes.

| Token | Type | Scopes granted | Expiry | Owner |
|---|---|---|---|---|
| \<gitea-mirror-token\> | API token | `repository:write` | 2027-01-18 | \<human name\> |
| \<gitea-agent-token\> | API token | `repository:read` | 2027-01-18 | \<human name\> |

---

## 5. 1Password authority

### 5.1 Vault and item scope

| Field | Value |
|---|---|
| 1Password account domain | MCP |
| Vault name(s) in scope | `bopen-secrets` |
| Item types accessible | API credentials, SSH keys, service-account tokens |
| Items explicitly excluded | All other vaults on this account |

### 5.2 Service-account scope

> **[NEEDS HUMAN INPUT]** Replace UUID and owner fields with real values.
> Actual credential values must never appear in this document.

| Service account name | 1Password UUID | Vaults accessible | Permissions | Expiry | Owner |
|---|---|---|---|---|---|
| \<bopen-sa-name\> | \<UUID — non-secret identifier only\> | bopen-secrets | read | 2027-01-18 | \<human name\> |

---

## 6. Named human owners

> **[NEEDS HUMAN INPUT]** Fill in full name and email for every role.
>
> CRITICAL: Maker and Checker MUST be different people. This is a non-waivable
> maker-checker control under BOPEN-GOV-001. One person may hold multiple roles
> (e.g. Security Authority + Architecture Authority + Delivery Authority + Operations Owner)
> but the Checker must always be an independent individual separate from the Maker.

| Role | Full name | Contact | Responsibilities |
|---|---|---|---|
| Maker (primary implementer) | \<Project lead full name\> | \<email\> | Executes authorized changes |
| Checker (MUST be a different person from Maker) | \<Different person — [NEEDS HUMAN INPUT]\> | \<email\> | Reviews before merge; independent of maker |
| Security Authority | \<Project lead or delegate\> | \<email\> | Approves this packet; owns credential policy |
| Architecture Authority | \<Project lead or delegate\> | \<email\> | Approves scope and integration design |
| Delivery Authority | \<Project lead or delegate\> | \<email\> | Authorizes associated work items |
| Operations owner | \<Project lead or delegate\> | \<email\> | Owns incident and rotation procedures |

---

## 7. Audit procedure

| Field | Value |
|---|---|
| Audit log destination | Gitea built-in audit log (Admin → Audit Log) |
| Events logged | All authentication, authorization, push, pull, mirror, secret-read events |
| Log retention | 90 days minimum |
| Review cadence | Quarterly |
| Review owner | \<Operations owner full name — [NEEDS HUMAN INPUT]\> |
| Tamper-evidence mechanism | Gitea built-in immutable audit trail; supplement with export to file store if available |

---

## 8. Credential rotation procedure

| Credential type | Rotation cadence | Responsible owner | Procedure reference |
|---|---|---|---|
| GitHub PAT | Monthly | \<human name — [NEEDS HUMAN INPUT]\> | To be created: `docs/09-operations/runbooks/rotate-github-pat.md` |
| Gitea API token | Monthly | \<human name — [NEEDS HUMAN INPUT]\> | To be created: `docs/09-operations/runbooks/rotate-gitea-token.md` |
| 1Password service-account secret | Monthly | \<human name — [NEEDS HUMAN INPUT]\> | To be created: `docs/09-operations/runbooks/rotate-1password-sa.md` |
| SSH deploy keys | Monthly | \<human name — [NEEDS HUMAN INPUT]\> | To be created: `docs/09-operations/runbooks/rotate-deploy-keys.md` |

Rotation must be coordinated: dependent services must be updated atomically.
Stale credentials must be revoked, not merely rotated.

---

## 9. Rollback procedure

| Trigger | Action | Owner | Maximum time-to-rollback |
|---|---|---|---|
| Credential compromise suspected | Revoke immediately; rotate all related secrets | Security Authority | 1 hour |
| Unauthorized push or mirror detected | Revert commits; suspend token; notify owners | Operations owner | 2 hours |
| Mirror divergence detected | Pause mirror; manual reconciliation | Checker | 4 hours |
| 1Password service-account abuse | Freeze account; audit access log; escalate | Security Authority | 1 hour |

Rollback evidence must be filed in `docs/evidence/` linked to this authority packet.

---

## 10. Incident procedure

1. **Detect** — Automated alert or human report triggers incident.
2. **Contain** — Revoke or suspend affected credential/access immediately.
3. **Assess** — Security Authority determines blast radius (repos, vaults, tenants affected).
4. **Notify** — Affected tenant owners, Delivery Authority, and Operations Authority notified
   within 2 hours.
5. **Remediate** — Root-cause fix deployed; credential rotated; audit log reviewed.
6. **Evidence** — Incident record filed in `docs/07-security/incident/` with timeline,
   impact, and remediation proof.
7. **Review** — Post-incident review within 5 business days; findings fed back to this packet.

**Escalation contact:**
\<Project lead full name, role, email — [NEEDS HUMAN INPUT]\>

---

## 11. Compensating controls

All items must be checked before this packet is submitted for approval:

- [ ] All secrets stored in 1Password vault `bopen-secrets`; never in source control.
- [ ] Agent credential policy: agents receive read-only tokens unless write is explicitly
      listed in §3.2 / §4.2 and the associated work item.
- [ ] Branch protection rules enabled on `bopen` repository (require PR + independent review before merge).
- [ ] No force-push to protected branches (`main`, `release/*`).
- [ ] Mirror events logged in Gitea audit log and reviewed quarterly.
- [ ] Secret scanning enabled on https://github.com/bstBizEra/bopen.
- [ ] Tenant-isolation invariant: no cross-tenant credential sharing.

---

## 12. Risk register

| Risk | Likelihood | Impact | Mitigation | Residual risk |
|---|---|---|---|---|
| Token leak via log or artifact | Medium | High | Secret scanning; audit logs; no secrets in source | Low |
| Mirror creates divergent history | Low | Medium | Gitea-primary direction locked; push-event trigger; quarterly divergence review | Low |
| Service account scope creep | Medium | High | Explicit scope tables §3.3 / §4.3 / §5.2; monthly rotation review | Low |
| Expired token blocks CI | Medium | Medium | Monthly rotation calendar; alert on expiry <7 days | Low |
| 1Password outage blocks deployments | Low | High | Break-glass procedure to be documented in runbook | Medium |
| Non-TLS Gitea URL (localhost:3030) intercepted | Medium | High | Restricted to local dev; must be upgraded to TLS before staging or production; re-approval required | Medium — MUST resolve before staging |

---

## 13. Acceptance criteria

This packet is complete and ready for approval when ALL of the following are satisfied:

- [ ] All **[NEEDS HUMAN INPUT]** fields are replaced with real values.
- [ ] §6: Maker and Checker are confirmed to be different people with different emails.
- [ ] §3.3 and §4.3: All token names and exact scopes are listed; no wildcards without sign-off.
- [ ] §5.2: Service-account UUID is a real non-secret identifier; no credential values present.
- [ ] §11: All 7 compensating control items are checked.
- [ ] §12: Non-TLS Gitea risk has a resolution plan or TLS upgrade is confirmed before staging.
- [ ] §14: All three approvers have recorded an explicit signed decision with date.
- [ ] Document status changed from PENDING HUMAN APPROVAL to APPROVED.

---

## 14. Approval

> All three signatures are required. A partial signature set does not lift the GOV-P0-04 block.

### Architecture Authority

**Name:** \<Full name — [NEEDS HUMAN INPUT]\>
**Date:** \<YYYY-MM-DD\>
**Decision:** [ ] Approved  [ ] Rejected  [ ] Approved with conditions
**Conditions / notes:**

---

### Security Authority

**Name:** \<Full name — [NEEDS HUMAN INPUT]\>
**Date:** \<YYYY-MM-DD\>
**Decision:** [ ] Approved  [ ] Rejected  [ ] Approved with conditions
**Conditions / notes:**

---

### Delivery Authority

**Name:** \<Full name — [NEEDS HUMAN INPUT]\>
**Date:** \<YYYY-MM-DD\>
**Decision:** [ ] Approved  [ ] Rejected  [ ] Approved with conditions
**Conditions / notes:**

---

## 15. Document control

| Field | Value |
|---|---|
| Artifact ID | BOPEN-SEC-GOV-P0-04 |
| Governed by | BOPEN-GOV-001, BOPEN-SEC-001-DRAFT |
| Supersedes | None |
| Next review | 2027-01-18 (expiry) or sooner on incident |
| Change log | v0.1-DRAFT 2026-07-22 — agent draft populated from project lead interview; awaiting human completion of [NEEDS HUMAN INPUT] fields and three-authority approval. 2026-07-22 — corrected GitHub repo name to `bOPEN`; wildcard `bstBizEra/*` declined on both GitHub and Gitea (conflicts with §2 bOPEN-only scope). 2026-07-22 — Gitea canonical URL set to http://localhost:3030/bstBizEra/bopen; casing discrepancy flagged (Gitea: `bopen` vs GitHub: `bOPEN`) — requires human resolution before mirror activation. |
