# bOPEN Architecture Skill Package

**Package:** `bopen-architecture`  
**Canonical ID:** `io.bizera.bopen.architecture`  
**Version:** `0.1.0`  
**Lifecycle stage:** `validated`  
**Distribution status:** internal candidate; not independently approved or signed

This package is a complete, repository-ready Agent Skill for researching, designing, reviewing, and governing bOPEN architecture. It uses the open Agent Skills directory format and adds an authoritative bOPEN governance manifest, schemas, policies, deterministic utilities, evaluation fixtures, and supply-chain records.

## Scope

The skill covers:

- the bOPEN platform kernel and bOPEN-based products;
- global principals, tenant membership, active context, authorization, RLS, ReBAC seams, and entitlements;
- product/module/capability package contracts;
- portal composition and tenant/user/platform context;
- events, transactional outbox, audit, workflow, usage, and provider adapters;
- agent principals, tools, skills, runtime binding, evaluation, and publication controls;
- ADRs, research reports, architecture designs, implementation-control packages, and conformance verdicts.

It does not grant permissions or perform production changes.

## Package layout

```text
bopen-architecture/
├── SKILL.md
├── bopen.skill.yaml
├── agents/openai.yaml
├── schemas/
├── scripts/
├── references/
├── policies/
├── assets/
├── evals/
├── tests/
├── supply-chain/
├── docs/
└── ci/
```

## Install for repository use

Copy the folder to:

```text
<repository>/.agents/skills/bopen-architecture/
```

For user-level installation, copy it to:

```text
$HOME/.agents/skills/bopen-architecture/
```

Invoke it explicitly as `$bopen-architecture`, or let a compatible client select it from the `SKILL.md` description.

## Validate and test

```bash
python -m pip install -r requirements.txt
python scripts/validate_package.py
python -m unittest discover -s tests -v
python scripts/run_static_evals.py
```

Or:

```bash
make validate
make test
make eval
```

## Create an architecture artifact

```bash
python scripts/new_artifact.py \
  --type architecture-design \
  --id BOPEN-ARCH-002 \
  --title "bOPEN Skills Registry Architecture" \
  --output ./BOPEN-ARCH-002.md
```

Check it against the baseline:

```bash
python scripts/check_architecture.py ./BOPEN-ARCH-002.md --strict
```

## Build a release archive

```bash
python scripts/package_release.py --output ../bopen-architecture-0.1.0.zip
```

The packager validates the package, creates provenance and an inventory manifest, writes `SHA256SUMS`, creates a deterministic ZIP, and writes a sibling `.sha256` file.

## Governance status

The package has deterministic static validation and tests. It has **not** received:

- independent architecture/security approval;
- model-level activation precision/recall evaluation across supported runtimes;
- cryptographic signature or transparency-log publication;
- production authorization.

Those are publication gates, not package-authoring steps. See [docs/GOVERNANCE.md](docs/GOVERNANCE.md).

## Source basis

The package distills the approved bOPEN direction supplied with this build, including the global-principal/membership/context model, the owned platform-kernel boundary, the modular-monolith P0 baseline, RLS and default-deny tenant isolation, module and entitlement separation, transactional outbox/audit controls, portal contexts, clean-room research governance, and P0 evidence gates. External format and evaluation references are recorded in [references/source-register.md](references/source-register.md).
