# Release provenance

Evaluate source, build, artifact, attestation, release, and deployment as
separate links.

Require:

1. exact source commit and tree;
2. trusted workflow or builder identity;
3. artifact digest computed from obtained bytes;
4. provenance predicate and subject digest;
5. signature or transparency-log bundle;
6. expected issuer, identity and trust policy;
7. release tag/ref and forge release record;
8. separate deployment authorization when claimed.

A valid Sigstore signature proves only what its verified certificate and bundle
bind. A SLSA predicate proves only the represented build claim at its declared
level. Neither proves code review, organizational approval, release permission,
or deployment authorization without the corresponding evidence.

Report missing artifact bytes, unavailable transparency evidence, unsupported
predicate fields, unverifiable builder identity, and time/revocation uncertainty
as first-class limitations.
