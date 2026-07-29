# Control catalog

Evaluate each claim independently. Profiles select mandatory controls; they do
not merge unlike claims into one score.

| Control | Claim | Mandatory evidence |
| --- | --- | --- |
| GIT-OBJ-001 | Commit and tree objects are internally connected | Exact OIDs and `git fsck --connectivity-only` |
| GIT-REF-001 | Target ref equals the expected revision | Frozen ref OID and expected full OID |
| GIT-REF-002 | Ref movement satisfies the requested policy | Reflog/audit events, old/new OIDs, actor binding |
| GIT-SIG-001 | Commit or tag signature is cryptographically valid | Verification result, signer key, trust policy |
| GIT-ID-001 | Git actor maps to an accepted identity | External identity binding and validity window |
| FORGE-POL-001 | Protected-ref policy was effective | Forge repository ID, rules, bypass actors, query time |
| FORGE-REV-001 | Review lineage satisfies policy | Review IDs, immutable revision, approvals, merge actor |
| BUILD-PROV-001 | Build binds source to artifact | Workflow identity, source tree, artifact digest |
| REL-PROV-001 | Release attestation satisfies trust policy | Predicate, signature/bundle, issuer, subject digest |
| AUTH-001 | Organizational authorization is proven | External mandate, eligible actor, action, exact subject |

`local-integrity` requires GIT-OBJ-001 and GIT-REF-001 when an expected commit
is supplied. Signature, identity, forge, release, and authorization claims remain
separate and may be `INDETERMINATE` or `NOT_APPLICABLE`.

For incident and migration audits, additionally record every observed ref
rewrite, source/destination object-format difference, missing retention window,
replace ref, graft, shallow boundary, partial-clone filter, and object alternate.
