---
name: git-provenance-audit
description: Audit Git repository provenance, object and history integrity, commit and tag signatures, protected-ref policy, pull-request or merge-request lineage, ref rewrites, release attestations, migrations, incidents, identity bindings, and policy drift across native Git, GitHub, GitLab, Gitea, Forgejo, Bitbucket, Azure Repos, and bare repositories. Use for read-only repository assurance, chain-of-custody review, source-to-release verification, governance evidence, suspicious history investigation, or canonical audit-package generation.
---

# Git Provenance Audit

Treat provenance as independent claims. Never equate an object hash, valid
signature, forge badge, approval, successful build, or deployment with another
claim. None alone proves organizational authorization.

## Operating boundary

- Default to read-only inspection. Do not fetch, modify refs, change config,
  install hooks, sign, commit, push, open reviews, or alter forge policy.
- Bind every audit to an explicit repository, revision, target ref, observation
  time, requested control profile, and evidence-access boundary.
- Use `PASS` only when all mandatory evidence for that claim is present and
  satisfies policy.
- Use `INDETERMINATE` for insufficient evidence and `BLOCKED_ACCESS` when
  required evidence cannot be accessed. Missing evidence never passes.
- Redact credentials from URLs, command output, HTTP headers, environment data,
  logs, and reports.
- Treat author and committer names/emails as self-asserted until independently
  bound to accepted identities and trust roots.
- Record authorization as a separate external claim. Provenance may support an
  authorization decision but cannot create authority.

## Choose a mode

| Mode | Required evidence | Primary modules |
| --- | --- | --- |
| `local-integrity` | Local Git repository | integrity, signatures, ref rewrites |
| `forge-provenance` | Local baseline plus read-only forge access | policy, review lineage, identity |
| `release-provenance` | Source, build, artifact, attestation, release | release chain |
| `incident-timeline` | Time-bounded local and forge events | timeline, rewrites, policy state |
| `migration-chain-of-custody` | Source and destination snapshots | migration custody |
| `policy-drift` | Approved policy baseline and current state | policy drift |
| `full` | All applicable sources | all modules |

Read [control-catalog.md](references/control-catalog.md) before a `full`,
incident, migration, or policy-drift audit. Read
[forge-adapters.md](references/forge-adapters.md) before calling a forge API.
Read [release-provenance.md](references/release-provenance.md) for SLSA,
Sigstore, or source-to-artifact claims. Read
[evidence-model.md](references/evidence-model.md) when producing or reviewing an
evidence package. Use [sources.md](references/sources.md) when a platform
capability or normative rule needs current verification.

## Workflow

1. **Scope the claim.** Record repository identity, local path, normalized
   remote, forge and forge repository ID when available, object format, exact
   commit, target ref, expected policy, time window, and access limitations.
2. **Freeze the observation.** Capture the observed ref OID before analysis.
   Do not fetch unless the user separately authorizes a network refresh; if
   refreshed, preserve both pre-fetch and post-fetch observations.
3. **Run the local collector.**

   ```bash
   python3 scripts/audit_git_provenance.py \
     --repo /absolute/path/to/repository \
     --output /absolute/path/to/audit-output \
     --target-ref refs/heads/main \
     --profile local-integrity
   ```

   Add `--expected-commit <full-oid>` when the user supplied a baseline. Add
   `--observed-at <RFC3339-UTC>` for a reproducible audit envelope.
4. **Collect forge evidence.** Use an installed connector or official read-only
   API. Save raw responses separately from normalized facts. Capture repository
   identity, policy/rules, bypass actors, review lineage, checks, merge
   actor/method, audit events, retention limits, API version, pagination, and
   query time. Do not put tokens or headers in evidence.
5. **Collect release evidence when applicable.** Bind source commit and tree to
   workflow identity, artifact digest, provenance predicate, signature/bundle,
   release tag, and deployment authorization. Verify artifact bytes, expected
   identity, issuer, and trust policy, not merely signature validity.
6. **Evaluate controls independently.** Emit one finding per claim using
   [finding.schema.json](assets/finding.schema.json). Do not average or
   overwrite verdicts.
7. **Package evidence.**

   ```bash
   python3 scripts/package_evidence.py \
     --audit-dir /absolute/path/to/audit-output \
     --schema assets/audit-manifest.schema.json
   ```

8. **Report limitations first-class.** State shallow boundaries, partial clone
   filters, alternates, replace refs, missing policy history, retention gaps,
   inaccessible audit logs, unsupported adapter fields, and time uncertainty.
9. **Conclude by claim.** Report object integrity, cryptographic identity,
   workflow provenance, policy enforcement, release provenance, and
   authorization separately. Derive an overall verdict only from the requested
   mandatory control profile.

## Mandatory baseline

Require these fields for a conclusive revision claim:

```text
repository_identity
normalized_remote_url
object_format
commit_oid
tree_oid
parent_oids
target_ref
observed_ref_oid
observed_at_utc
forge_repository_id (or explicit NOT_APPLICABLE)
```

If the commit or target ref is missing, stop that claim with `INDETERMINATE`.
If an expected commit differs from the observed target, emit `FAIL` before
continuing diagnostic collection.

## Verdicts

- `PASS`: all mandatory evidence was obtained and satisfies policy.
- `PASS_WITH_GAPS`: the core claim passes; only declared non-critical evidence
  is unavailable.
- `FAIL`: evidence contradicts a mandatory requirement.
- `INDETERMINATE`: evidence is insufficient to prove or disprove the claim.
- `BLOCKED_ACCESS`: required evidence could not be accessed.
- `NOT_APPLICABLE`: the control does not apply.

Never downgrade a mandatory `FAIL`, `INDETERMINATE`, or `BLOCKED_ACCESS` through
aggregation.

## Handoff

Return:

1. Bound baseline and observation time.
2. Claim-by-claim verdict table.
3. Critical findings and limitations.
4. Evidence package path and checksum root.
5. Remediation recommendations that do not mutate the repository.
6. Separate authorization status: `PROVEN`, `NOT_PROVEN`, or `OUT_OF_SCOPE`.

Do not describe an audit as authoritative when required forge, trust-root,
time, revocation, mandate, or identity-binding evidence is unavailable.
