# bOPEN skill routing

Resolve every skill through `docs/registers/skill-registry.json`. Installation means discovery, not activation or authority. Prefer one primary specialist and add complementary verification skills only when their boundary is relevant.

## Routing order

1. `bopen-governance-check` — authority, phase, work-item and stop-condition preflight.
2. `bopen-requirement-to-work-item` — convert an approved requirement into bounded work.
3. `bopen-architecture` — cross-cutting architecture baseline and decision framing.
4. Narrow specialist skill — identity, tenancy, authorization, entitlement, RLS, outbox, portal, module or research.
5. Verification specialist — tenant isolation, portal, CI, threat, documentation or evidence.
6. `bopen-sec-qa-lead` — coordinate independent assurance where required.
7. `bopen-release-readiness` then, only when explicitly requested, `bopen-p0-conformance-gate` — compose evidence only; never self-authorize release or gate passage.

## Overlap boundaries

| Primary skill | Complement, not replacement |
| --- | --- |
| `bopen-architecture` | `bopen-adr-governance`, `bopen-clean-room-research`, `bopen-module-boundary-review` |
| `bopen-worktree-management` owns worktree lifecycle | `bopen-git-governance` owns Git policy, review and handoff; `bopen-git-delivery` explicitly orchestrates publication |
| `bopen-evidence-envelope` | `bopen-audit-evidence` designs audit/evidence semantics; envelope packages final proof |
| `bopen-module-contract` | `bopen-module-boundary-review` reviews ownership and dependency direction |
| `bopen-portal-context-ux` | `bopen-portal-verification` tests rendered/runtime behavior; `bopen-tenant-isolation-review` tests isolation |
| `bopen-ci-repair` | `bopen-github-actions-hardening` proactively reviews workflow security |
| `bopen-governance-check` + `bopen-sec-qa-lead` | `bopen-p0-conformance-gate` composes a controlled verdict from independent evidence |

## Explicit-only skills

Do not invoke these implicitly: `bopen-git-delivery`, `bopen-repository-harness`, `bopen-skill-authoring`, `bopen-skill-admission`, `bopen-release-readiness`, and `bopen-p0-conformance-gate`.

All skills in this admission packet remain `candidate` and `inactive`. Their scripts may be inspected and sandbox-tested, but are not eligible for autonomous production execution.
