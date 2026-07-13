# Repository Structure Study

## High-value paths

| Path | Research purpose |
|---|---|
| `prisma/schema.prisma` | Canonical relational model |
| `prisma/migrations/` | Evolution and constraint history |
| `models/user.ts` | User operations and permission helper entry points |
| `models/team.ts` | Team creation, membership and access resolution |
| `models/invitation.ts` | Invitation issue, lookup, expiry and deletion |
| `models/teamMember.ts` | Membership queries/counting |
| `pages/api/auth/` | Registration and authentication APIs |
| `pages/api/teams/` | Team-scoped administration APIs |
| `pages/api/invitations/` | Invitation lookup |
| `lib/permissions.ts` | Static role-to-resource/action mapping |
| `lib/session.ts` | Session resolution |
| `lib/svix.ts` | Webhook application and event emission |
| `lib/retraced.ts` | Audit integration |
| `components/team/` | Team settings and member UX |
| `components/invitation/` | Invitation UX and validation states |
| `tests/` | Runtime behavior and regression evidence |

## Required trace inventory

For each lifecycle, list entry UI, API route, validation schema, access guard, model functions, schema tables, events, audit calls, metrics and tests.

## Architecture caution

The repository is a single application starter. bOPEN must not infer service decomposition, module registry or platform control-plane architecture merely from folder names.

## R1 verified orientation - 2026-07-13

The R1 validator independently verified 26 path/marker observations in two detached checkouts at the pinned commit. Coverage spans all required layers:

| Lifecycle | UI | API | Validation/model | Schema | Integration | Declared tests |
|---|---|---|---|---|---|---|
| Registration | `pages/auth/join.tsx` | `pages/api/auth/join.ts` | `lib/zod/schema.ts`, user/team/token models | User, Team, TeamMember, VerificationToken | email, metric, optional Slack | signup setup and invitation-assisted signup |
| Login/session | login and session-management components | NextAuth and session routes | `lib/nextAuth.ts`, session/account/lock models | User, Account, Session | metrics only | session and SSO suites |
| Team | team settings/create/remove components | team collection/item routes | team schemas and `models/team.ts` | Team, TeamMember, Role | metrics, selected Retraced calls | team-settings and SSO team cases |
| Membership | member list/role components | members route | member schemas, team/teamMember models | TeamMember unique relation | selected Svix/Retraced calls | list and remove cases |
| Invitation | invitation create/accept/pending components | token and team invitation routes | invitation schemas/model | Invitation | email, Svix and selected Retraced calls | email/link/domain acceptance cases |

This completes RES-P0-04 at E2. It does not prove runtime behavior; detailed missing E3 cases are recorded in EVD-RES-003.
