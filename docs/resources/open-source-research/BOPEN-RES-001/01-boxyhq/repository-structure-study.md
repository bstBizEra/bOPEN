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
