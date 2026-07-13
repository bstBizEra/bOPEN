# Source Register

| Source ID | Source | Pin / version | Type | Authority | Use |
|---|---|---|---|---|---|
| SRC-BOX-001 | GitHub `boxyhq/saas-starter-kit` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Upstream source | Primary | Main study clone |
| SRC-BOX-002 | Repository `LICENSE` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | License text | Primary | License baseline |
| SRC-BOX-003 | Repository `README.md` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Upstream documentation | Primary | Feature and setup claims |
| SRC-BOX-004 | `package.json` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` / 1.6.0 | Build manifest | Primary | Stack and dependency baseline |
| SRC-BOX-005 | `prisma/schema.prisma` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Data model | Primary | User/team/member/invitation mapping |
| SRC-BOX-006 | `models/team.ts` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Source code | Primary | Team and membership operations |
| SRC-BOX-007 | `models/invitation.ts` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Source code | Primary | Invitation issue/expiry operations |
| SRC-BOX-008 | `pages/api/auth/join.ts` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Source code | Primary | Registration and team creation flow |
| SRC-BOX-009 | `pages/api/teams/[slug]/invitations.ts` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Source code | Primary | Invitation and membership acceptance |
| SRC-BOX-010 | `lib/permissions.ts` | `abc9b686823cbfb4973c79bc36fea37a3244be6c` | Source code | Primary | RBAC resource/action map |
| SRC-CTX-001 | User-provided Multi-Tenant Portal Research | July 2026 | Prior research baseline | Internal | bOPEN concept and candidate selection |
| SRC-ORY-001 | Ory notice `https://www.ory.sh/blog/ignite-your-saas-journey-with-the-best-free-and-open-source-saas-starter-kit` | Observed `2026-07-13`; quarterly refresh required | Provenance context | Primary/official | Lineage and dependency-monitoring note only; not a requirement source |

## R0 integrity receipt - 2026-07-13

`SRC-BOX-001` was independently verified by ENGIN and REV at detached commit `abc9b686823cbfb4973c79bc36fea37a3244be6c`. Both operators matched license SHA-256 `f9f9a6236f9f12c14ce7294a58575c19fc16bb1c24dcdc91e2ae868b2b21a41a` and package-lock SHA-256 `b8ec0535883a6bb186a6a633979a497b12f110463da86ae0122ddd3426d219e8`. GitHub was observed as public and not archived on 2026-07-13. Legal interpretation remains with SecB.

## Source rule

Formal evidence must identify a pinned source path. Unpinned web summaries and third-party reviews may be used only as leads, never as the sole basis for a bOPEN requirement.
