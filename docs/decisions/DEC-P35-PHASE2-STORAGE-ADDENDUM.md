# DEC-P35-PHASE2-STORAGE-ADDENDUM - Mapping and grant ambiguity

**Document ID:** `DEC-P35-PHASE2-STORAGE-ADD-001`  
**Version:** `0.1.0`  
**Status:** Proposed advisory addendum - authority decision pending  
**Issued:** 2026-07-31  
**Owner:** Architecture Authority  
**Required concurrence:** Engineering Authority, Security Authority, Product Authority for delegation  
**Parent decision:** [`DEC-P35-PHASE2-STORAGE`](DEC-P35-PHASE2-STORAGE.md) sections 2.5 and 2.6  
**Assisted docket:** [`DEC-P35-DOCKET-001`](DEC-P35-DOCKET.md) decisions `D-P35-008` and `D-P35-009`  
**Governing artifacts:** `BOPEN-IDP-001`, `ADR-0017`, `ADR-0018`, `BOPEN-GOV-EBIV-001`

---

## 1. Purpose and boundary

The parent decision identifies two storage semantics that cannot safely be selected by
unordered row retrieval:

1. whether policy version participates in the group-role mapping lookup key;
2. how context issuance behaves when delegated grants overlap.

This addendum supplies evidence-backed advisory recommendations for those two items. It does
not decide them, authorize a migration, amend an approved contract, or activate Phase 3.5.

## 2. Executed reproduction

An in-process probe against the live implementation inserted two records for each ambiguous
key and then reversed insertion order:

```text
mapping_forward= v1
mapping_reverse= v2
grant_forward= support_reader
grant_reverse= support_writer
```

The result proves both current resolvers select the first row rather than a
contract-defined outcome. The probe changed no repository or database state.

## 3. Group-role mapping recommendation

`BOPEN-IDP-001` section 10.4 defines the lookup input as:

```text
directory_id + group_external_id
    -> mapping_policy_version
    -> approved bOPEN role/team target
```

`ADR-0017` is more explicit: the mapping is keyed by
`(directory_id, group_external_id)` and stamped with `mapping_policy_version`. The policy
version is provenance for an authorization revision, not a caller-selected lookup
coordinate.

**Recommend one effective mapping per `(directory_id, group_external_id)` pair.**

- Make the pair the unique effective business key.
- Require `mapping_policy_version` on every revision and include it in audit evidence.
- Replace an effective mapping only through an explicit, version-checked transition.
- Preserve prior revisions in append-only audit/history storage rather than as simultaneously
  selectable effective rows.
- Invalidate affected active contexts when a revision narrows authorization, as required by
  `ADR-0017`.
- Treat zero matches as inert and more than one effective match as a consistency fault that
  denies role derivation.

This preserves policy attribution without asking a SCIM event to choose a policy version it
does not author and cannot safely select.

## 4. Delegated-grant overlap recommendation

`BOPEN-IDP-001` sections 12.3 and 14 require one `dgr` reference in a delegated context and
derive that context's roles and scopes from the referenced active grant. Combining two grants
would create a new, unspecified authorization object; choosing one by row order is
nondeterministic.

**Recommend prohibiting overlapping usable intervals for the same
`(source_principal_id, target_tenant_id)` pair.**

- Permit multiple historical, pending, revoked, expired, or non-overlapping future grants.
- Enforce the overlap rule when a grant is activated, not when a draft is created.
- Serialize competing activations and enforce the rule in PostgreSQL, not only in application
  code.
- Reject an activation that would overlap another active usable grant with a typed,
  non-enumerating conflict.
- If legacy or corrupt data presents more than one usable grant, context issuance fails closed;
  it does not merge roles/scopes and does not select a winner.
- A legitimate second support or partner relationship remains representable as a pending or
  future grant and can activate after the current usable interval ends.

This is the smallest rule consistent with the singular `dgr` contract, least privilege, and
deterministic authorization. A future requirement for simultaneous grants would need a new
contract defining composition and audit semantics before relaxing it.

## 5. Alternatives and consequences

| Item | Alternative | Reason not recommended |
|---|---|---|
| Mapping | Include `mapping_policy_version` in the effective lookup key | A SCIM event does not select the policy version; multiple effective rows still need an ordering rule |
| Mapping | Latest timestamp wins | Time is not an authorization-policy selector and creates race-sensitive outcomes |
| Grants | Merge roles and scopes from every usable grant | Creates a composite grant absent from the contract and expands privilege |
| Grants | Prefer support or partner grants | Grant type is not a normative authorization-precedence rule |
| Grants | Earliest expiry or newest approval wins | Deterministic but semantically arbitrary and vulnerable to privilege replacement |
| Grants | Reject overlapping drafts | Needlessly blocks preparation of a successor grant before the current one expires |

## 6. Acceptance consequences if adopted

The eventual implementation would require falsifiable tests proving:

- reversing physical row order cannot change an effective group-role mapping;
- a stale mapping version cannot overwrite a newer effective revision;
- two concurrent mapping revisions produce at most one effective row;
- a second overlapping grant cannot activate;
- two concurrent activations produce at most one usable grant;
- ambiguous legacy grants deny context issuance;
- non-overlapping successor grants remain representable;
- every mapping application and delegated action records the exact policy or grant reference.

The tests and implementation belong to an accepted work package and must be authored by the
Maker, then checked independently. They are not created by this advisory addendum.

## 7. Authority record

```text
Decision: Pending
Approver: Pending
Security concurrence: Pending
Product concurrence for delegation: Pending
execution_authority: false
approval_authority: false
production_activation_authority: false
```
