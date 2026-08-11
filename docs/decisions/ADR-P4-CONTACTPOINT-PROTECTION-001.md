# ADR-P4-CONTACTPOINT-PROTECTION-001 — ContactPoint endpoint protection and lookup

**Document ID:** `ADR-P4-CONTACTPOINT-PROTECTION-001`  
**Version:** `0.1.0`  
**Status:** `PROPOSED / DRAFT — NOT EFFECTIVE`  
**Issued:** 2026-08-06  
**Owner:** Architecture Authority and Security Authority  
**Producer:** Codex, security/data contract maker; not an independent reviewer  
**Project / Work ID:** `WP-P4-CONTACTPOINT-R1`  
**Baseline:** commit `2842b4b74ece2b34cdf5691bd9bed5ad4fea8680`  
**Governing artifacts:** `BOPEN-TENANT-001`; `BOPEN-AUTHZ-001`; `DEC-P4-ENTRY` §10; `BOPEN-PARTY-002`; repository `AGENTS.md`  
**Dependent draft contract:** `contracts/schemas/contact-point-protection.schema.json`  
**Effective date:** none; an authorized decision and separately authorized implementation package are required

## Decision status and authority boundary

This ADR records a **recommended future choice**, not an accepted decision. It grants no implementation,
key-management, migration, deployment, activation, evidence-acceptance, or production authority. The
normative words below describe the candidate contract that would apply **if** the Architecture Authority
and Security Authority accept it.

The current `WP-P4-CONTACTPOINT-R1` bounded integrity slice addresses endpoint-version binding,
atomic verification invalidation, append-only history, lifecycle separation, and tenant-deletion
resistance. Cryptographic protection, key-provider integration, normalization changes, and protected
lookup are explicitly outside that slice.

Migration 021 therefore MUST NOT silently make this ADR effective. In particular, migration 021 MUST NOT:

- select an encryption algorithm, KMS/HSM provider, key hierarchy, or lookup-key lifecycle;
- encrypt or tokenize existing `endpoint_value` bytes;
- create a globally stable endpoint digest or change endpoint uniqueness to an unapproved normalized form;
- remove plaintext compatibility or claim that endpoint confidentiality findings are closed; or
- make the draft JSON Schema a runtime dependency.

Those actions require acceptance of this ADR, a protected-storage migration plan, key and recovery
runbooks, authorized implementation scope, and independent security evidence.

## Context

Party ContactPoints hold email addresses and telephone numbers. They are tenant-owned sensitive business
data. The current implementation stores `endpoint_value` as plaintext and redacts it from audit records,
but audit redaction alone does not protect database copies, backups, exports, diagnostic queries, or
support access. Exact-value lookup also creates a temptation to store a stable hash; email addresses and
telephone numbers have small, enumerable input spaces, so a global unkeyed digest would permit guessing
and cross-tenant correlation.

Protection is distinct from verification and dispatch policy:

- encryption protects confidentiality;
- a keyed lookup token supports equality lookup;
- normalization defines comparison bytes;
- verification records evidence of endpoint control;
- purpose is classification only; and
- consent, preference, suppression, mandatory-message policy, authorization, and delivery outcome remain
  owned by their respective Notification/policy boundaries.

No protection envelope, lookup match, purpose classification, mask, or successful decryption grants
permission to dispatch.

Every future protected operation remains downstream of the canonical execution chain: authenticated
Principal (or explicitly granted service Principal) -> active Membership or delegated grant ->
server-validated active tenant context -> authorization -> entitlement -> enabled module/capability ->
resource action -> correlated audit/evidence. Client-supplied tenant identifiers never establish that
context. PostgreSQL row-level security remains forced, default-deny defense in depth; cryptography neither
replaces RLS nor permits cross-tenant access.

## Decision drivers

1. Tenant isolation and absence of a cross-tenant correlation key.
2. Confidentiality across database, backup, export, log, cache, and support boundaries.
3. Exact binding between protected bytes, endpoint version, tenant, and ContactPoint identity.
4. Provider-neutral key custody, rotation, compromise response, restore, and crypto-erasure behavior.
5. Conservative normalization that does not invent provider-specific equivalence.
6. Staged migration with fail-closed rollback and independently testable evidence.
7. P0 operability without a new online token-vault dependency.

## Options considered

### Option A — Application envelope encryption plus tenant-scoped keyed lookup (recommended)

The application normalizes the routing value, encrypts the entered and normalized representations with an
AEAD data-encryption key, and stores a tenant-scoped HMAC for equality lookup. Plaintext key material stays
outside PostgreSQL. Provider-specific KMS/HSM operations sit behind an owned bOPEN key-provider port.

This option provides the best balance of tenant isolation, authenticated encryption, provider portability,
rotation, testability, and P0 operating cost.

### Option B — Database-side encryption such as `pgcrypto`

This reduces application code but places plaintext and key use inside the database trust boundary,
complicates external key custody and rotation, and risks secrets appearing in SQL/session/diagnostic
surfaces. It is not recommended for this data class.

### Option C — External token vault

The database stores only opaque provider tokens. This minimizes endpoint material in PostgreSQL, but adds
an online availability dependency, coordinated backup/restore obligations, latency, provider lock-in, and
more complex dedicated-tenant migration. It remains a future option if regulatory or threat evidence
justifies the operational cost.

### Option D — Plaintext with storage-volume encryption and redaction

This preserves current simplicity but does not protect against privileged database reads, logical backups,
exports, or accidental query disclosure. It is not an acceptable production target for sensitive endpoint
values.

## Recommended candidate contract

### Encryption and binding

- Content encryption SHOULD use application-layer envelope encryption with `AES-256-GCM`, a fresh random
  96-bit nonce per encryption, and a 128-bit authentication tag.
- The key-encryption key MUST remain in an external KMS/HSM or equivalent governed key service. PostgreSQL
  MAY store a wrapped tenant data-encryption key, never the unwrapped key.
- Authenticated additional data MUST canonically bind `tenant_id`, `contact_point_id`, `endpoint_version`,
  `endpoint_type`, `normalization_profile`, and `contract_version`.
- Entered/display form and normalized routing form MUST exist only inside the encrypted payload. Ciphertext,
  nonce, tag, and opaque key references are not API response fields.
- Encryption failure, unknown key version, authentication-tag failure, or AAD mismatch MUST fail closed and
  MUST NOT fall back to plaintext or `principals.email`.

### Tenant-scoped lookup

- Equality lookup SHOULD use `HMAC-SHA-256` under a lookup key distinct from every encryption key.
- Lookup keys MUST be tenant-scoped. The digest input MUST use an unambiguous canonical encoding of:

  ```text
  bopen/contact-point/lookup/v1
  || tenant_id
  || endpoint_type
  || normalization_profile
  || normalized_routing_value
  ```

- Global unkeyed hashes, global deterministic ciphertext, cross-tenant uniqueness, and lookup tokens in
  logs/events/telemetry MUST be prohibited.
- A lookup match is equality evidence only. It is not verification, consent, authorization, or permission
  to dispatch.

### Normalization v1

The proposed profiles are deliberately conservative and versioned:

- `email-rfc5321-conservative-v1`: preserve local-part bytes and case; lowercase and convert the domain to
  its validated IDNA A-label form; reject control characters, leading/trailing whitespace, quoted or
  ambiguous forms, and unsupported SMTPUTF8 instead of guessing. Provider-specific rules such as Gmail dot
  removal or local-part case folding MUST NOT be applied.
- `phone-e164-v1`: accept only `+` followed by 7–15 ASCII digits; reject national-format input without an
  explicit, governed region context. Formatting punctuation is display input, not routing identity.

Changing normalization profile creates a new endpoint version and requires fresh verification. Syntax or
normalization success never establishes deliverability or control.

### Redaction and masking

- Raw entered, normalized, decrypted, ciphertext, nonce, tag, lookup digest, and key-reference values MUST
  NOT appear in logs, audit payloads, domain events, status endpoints, error messages, analytics, caches,
  default exports, or ordinary CRUD responses.
- Transactional-outbox and other event envelopes MUST carry only safe ContactPoint identifiers, version,
  reason code, and correlation metadata. They MUST NOT carry endpoint values, masks, ciphertext, lookup
  tokens, key references, or decryption results.
- Ordinary CRUD SHOULD return an explicit mask only, using a versioned profile such as
  `email-domain-visible-v1` (`***@example.test`) or `phone-last4-v1` (`*******1234`). A mask remains
  sensitive tenant data and MUST NOT be used as an identifier.
- Decryption and resolve are distinct higher-trust actions. They require server-validated tenant context,
  active principal/service grant, authorization, entitlement/module state, purpose-scoped resource access,
  and correlated audit evidence.

### Key lifecycle

- Encryption and lookup keys have separate purposes and lifecycle states:
  `active -> decrypt_only -> retired`, with `compromised` and irreversible `destroyed` terminal handling.
- KEK rotation SHOULD rewrap tenant data keys without rewriting every endpoint. Data-encryption-key rotation
  SHOULD put the old key into `decrypt_only` while protected rows are re-encrypted under the new active key.
- Lookup-key rotation requires a governed tenant maintenance window or an explicitly designed dual-index
  protocol. The implementation MUST recompute tokens, detect duplicates under the new profile, and switch
  atomically; it MUST NOT assume tokens from different key versions are comparable.
- A key MUST NOT be destroyed while any retained ciphertext, backup, evidence obligation, legal hold, or
  rollback window still requires it. Crypto-erasure is an explicit governed deletion decision, not normal
  key retirement.

### Backup, restore, and rollback

- Database backups MAY contain ciphertext and wrapped tenant keys but MUST NOT contain KMS/HSM master keys
  or unwrapped data/lookup keys.
- Restore evidence MUST demonstrate key-provider disaster-recovery access, key-manifest reconciliation,
  successful authorized decryption, wrong-tenant and wrong-AAD refusal, and lookup reconstruction.
- Protected-storage rollout MUST be staged: expand schema, deploy dual-read/controlled-write behavior,
  backfill under an authorized key service, reconcile, close the plaintext path, then contract the schema.
- After protected writes or immutable evidence exist, rollback is forward-only by compensating migration.
  It MUST NOT repopulate plaintext from ciphertext, restore destructive cascades, delete evidence, or reuse a
  nonce/key pair. Key destruction and loss of external recovery material are irreversible.

## Consequences

### Positive

- A database or logical-backup disclosure does not directly disclose endpoint plaintext.
- Tenant-specific lookup keys prevent a single digest from correlating the same endpoint across tenants.
- Versioned normalization and AAD make comparison and encryption semantics explicit and reviewable.
- Provider integration remains replaceable and key rotation can be evidenced independently.

### Negative and tradeoffs

- The application gains key-provider, caching, rotation, backfill, and recovery complexity.
- Equality lookup still leaks within-tenant repetition to an actor that has both table access and the
  relevant lookup token set; authorization and RLS remain mandatory.
- Masking deliberately reveals limited routing information and therefore remains classified data.
- Losing KMS/HSM recovery material makes ciphertext unrecoverable; backups alone are insufficient.
- Lookup-key rotation is operationally heavier than encryption-key rotation.

## Verification and evidence required before acceptance or activation

- Architecture and Security Authority disposition on this ADR and the draft schema.
- Threat model covering database administrator, backup, log/export, compromised service, cross-tenant, key
  compromise, nonce reuse, and restore failures.
- Known-answer and mutation tests for AEAD/AAD; tenant/key/version separation tests for lookup tokens.
- Normalization fixtures covering case, IDNA, Unicode refusal, controls, ambiguity, and international phone
  input.
- Tests proving raw values and protected metadata do not reach CRUD, logs, audit, events, errors, exports,
  caches, or analytics.
- Key rotation, compromise, backup/restore, loss-of-key, and forward-only rollback drills.
- Exact migration/backfill candidate, data reconciliation report, and independent review evidence.

Acceptance criteria and the production exit gate remain closed until every required control has executed
evidence bound to an exact candidate. A green unit suite, this proposed ADR, or schema validation alone is
not evidence of key custody, runtime isolation, backup recovery, or production readiness.

## Affected elements

- Party ContactPoint repository and API contracts.
- Future protected-storage and backfill migrations after migration 021.
- Key-provider port, tenant key registry, runtime secret resolution, and operational runbooks.
- Dedicated-tenant placement copy order, backup/restore, exports, logs, audit, and Notification resolver.
- Verification events only as consumers of an opaque endpoint-version binding; they MUST NOT own raw values,
  crypto keys, consent, suppression, or delivery outcomes.

## Risks and unresolved decisions

- Authorized KMS/HSM provider, regional placement, availability target, key-cache lifetime, and support model.
- Whether AES-256-GCM remains the accepted suite or an approved provider-neutral alternative is required.
- Retention periods for superseded ciphertext and lookup material, legal-hold interaction, and crypto-erasure
  authority.
- Final masks and whether any UI may reveal more under a separately authorized sensitive-read capability.
- SMTPUTF8 and national-phone support remain deferred pending explicit profiles.
- Exact dual-read/backfill choreography and the migration number following the integrity-only migration 021.

## Review, supersession, and required next action

Review is triggered by a provider selection, new endpoint type, normalization-profile change, regulatory
requirement, cryptographic guidance change, key compromise, material restore failure, or move to an external
token vault. A later accepted ADR may supersede this record only by naming this ID and providing migration,
recovery, and evidence consequences.

Next, the Architecture Authority and Security Authority must accept, revise, or reject the proposed choice.
Only after acceptance may an implementation owner draft the protected-storage work package and migration.

## Evidence index

| Claim | Evidence | Status / limit |
| :--- | :--- | :--- |
| Current endpoint is plaintext; audit redaction is present | `infrastructure/database/019_party_contact_points.sql`; `services/platform-kernel/python/platform_kernel/api.py` at baseline | Repository fact; not a production runtime probe |
| Endpoint protection remained a tracked refinement | `docs/decisions/DEC-P4-ENTRY.md` §10, `CP-D-07` | Approved prior decision; this ADR does not supersede it while proposed |
| Protection and consent/suppression are separate | `docs/01-product/MILE-4.2-party-contactpoint-extension-review.md`, `CP-REV-F02`/`F06` | Advisory review input; not decision authority |
| Draft machine-readable envelope | `contracts/schemas/contact-point-protection.schema.json` | Draft only; must not be consumed as effective contract |
