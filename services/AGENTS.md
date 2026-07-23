# Scoped agent instructions — `services/`

**Status:** Draft preparation control  
**Work package:** `SKEL-P0-01`  
**Stable dependency:** No

These instructions apply to every path below `services/`. They supplement repository-level governance and **never weaken** a stricter instruction or signed control.

1. Keep every new artifact additive, draft-marked, and within `SKEL-P0-01` preparation scope.
2. Add **no production business logic** and no stable dependency surface.
3. Do not add secrets, credentials, runtime configuration, migrations, deployments, or environment-specific values.
4. Preserve the separations `Principal ≠ Party`, `Tenant ≠ Organization`, `Membership ≠ Role`, and `Permission ≠ Entitlement`.
5. Any later executable implementation must arrive with negative tests in unit, contract, integration, tenant-isolation, and authorization tiers; the current guards fail closed otherwise.
6. Do not modify signed outcomes, binding inventories, governance registers, research upstreams, or root-ledger genesis.
7. Do not claim approval, acceptance, signing, publication, or production readiness. Human authority and the independent exact-SHA checker remain external gates.

Zone-specific prohibition: HTTP handlers, jobs, database clients, policy engines, integrations, or production service logic.
