# Initial Evidence Index

| Evidence ID | Class | Source | Observation | Status |
|---|---|---|---|---|
| BOX-E-001 | E2 | `prisma/schema.prisma` @ `abc9b686823cbfb4973c79bc36fea37a3244be6c` | User, Team, TeamMember and Invitation are separate models. | Confirmed |
| BOX-E-002 | E2 | `prisma/schema.prisma` | TeamMember unique constraint is `(teamId,userId)`. | Confirmed |
| BOX-E-003 | E2 | `models/team.ts` | Team creation adds creator as OWNER membership. | Confirmed |
| BOX-E-004 | E2 | `models/invitation.ts` | Invitation token is UUID and default expiry is seven days. | Confirmed |
| BOX-E-005 | E2 | `pages/api/auth/join.ts` | Non-invited signup creates user and team; invited signup uses invitation team. | Confirmed |
| BOX-E-006 | E2 | `pages/api/teams/[slug]/invitations.ts` | Invitation acceptance validates email/domain and creates TeamMember. | Confirmed |
| BOX-E-007 | E2 | `lib/permissions.ts` | Role-to-resource/action permission map is centralized. | Confirmed |
| BOX-E-008 | E2 | Invitation API | Invitation/member lifecycle emits webhook events and selected audit events. | Confirmed |
| BOX-E-009 | E2 | `prisma/schema.prisma` | Team has billing fields and API keys; subscription is separate. | Confirmed |
| BOX-E-010 | E1/E2 | README/package manifest | Stack includes Next.js, Postgres, Prisma, NextAuth and enterprise integrations. | Confirmed |
| BOX-E-011 | E0 | Runtime pending | Active-team context and cross-team denial behavior. | Open |
| BOX-E-012 | E0 | Runtime pending | Subscription-to-capability gating behavior. | Open |

## R1 evidence additions - 2026-07-13

| Evidence ID | Class | Source | Observation | Status |
|---|---|---|---|---|
| BOX-E-013 | E2 | R1 trace contract and two external receipts | 56 case-specific evidence records independently match the pinned source: 46 observations and 10 gap anchors. | Confirmed |
| BOX-E-014 | E2 | Static test-declaration receipts | 42 declarations are present in 9 Git-tracked TypeScript test files; upstream code was not executed. | Confirmed |
| BOX-E-015 | E2 | Identity trace | Human-user identity root, session/token gaps and absent identity audit chain recorded. | Confirmed |
| BOX-E-016 | E2 | Team/membership trace | Owner atomicity, last-owner and cross-team negative gaps recorded. | Confirmed |
| BOX-E-017 | E2 | Invitation trace | Implicit state, replay/concurrency and event/audit gaps recorded. | Confirmed |
| BOX-E-018 | E0 | G3 runtime pack | Database-backed positive/negative lifecycle behavior. | Open |

EVD-RES-003 contains the reviewed R1 synthesis and external manifest hashes.
