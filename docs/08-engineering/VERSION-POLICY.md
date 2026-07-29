# bOPEN Version Control & Semantic Versioning Policy v1.0

**Document ID:** `BOPEN-ENG-VER-001`  
**Version:** `1.0.0`  
**Status:** Approved Specification  
**Issued:** 2026-07-29  
**Owner:** Engineering Authority & Architecture Authority  
**Classification:** Mandatory Engineering Governance  

---

## 1. Versioning Standard & Format

All controlled documents, machine-readable contracts, software packages, microservices, database migrations, and release tags in bOPEN MUST adhere to Semantic Versioning (`MAJOR.MINOR.PATCH`):

$$\text{Version} = \text{MAJOR} . \text{MINOR} . \text{PATCH}$$

| Level | Increment Condition | Example Trigger |
| :--- | :--- | :--- |
| **MAJOR (`X.0.0`)** | Breaking changes, incompatible contract/API updates, phase transitions. | Renaming a required contract field, changing authorization default effect. |
| **MINOR (`x.Y.0`)** | Backward-compatible new features, specs, capability modules, or tests. | Adding an optional field to context, introducing a new foundation module. |
| **PATCH (`x.y.Z`)** | Non-breaking bug fixes, doc formatting, typo fixes, or evidence updates. | Correcting doc typos, updating evidence digests, minor verifier fixes. |

---

## 2. Component Versioning Guidelines

### 2.1 Normative Specifications & Controlled Docs (`docs/`)
* Must carry `**Version:** X.Y.Z` metadata header.
* Bumping `MAJOR` requires an approved superseding ADR or executive decision.

### 2.2 Machine-Readable Contracts (`contracts/schemas/`)
* Schema files must declare `$id` with version URI (e.g. `https://bopen.io/schemas/v1/tenant-context.json`) and `"version": "1.0.0"`.

### 2.3 Code Packages & Services (`packages/`, `services/`, `sdk/`)
* Source files must declare `__version__ = "1.0.0"` or `version` in `package.json` / `pyproject.toml`.

### 2.4 Database Migrations (`infrastructure/database/`)
* Migrations must use sequential timestamped version prefixes: `001_v1.0.0_tenant_isolation_baseline.sql`.
