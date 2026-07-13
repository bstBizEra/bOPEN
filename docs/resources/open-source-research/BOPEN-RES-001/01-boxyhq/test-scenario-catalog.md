# Test Scenario Catalog

| ID | Scenario | Expected evidence |
|---|---|---|
| BOX-T01 | Register without invitation | User, Team and OWNER TeamMember created |
| BOX-T02 | Register with duplicate team slug | Request rejected; no partial records |
| BOX-T03 | Invite by email | Invitation created with role/token/expiry; event/audit emitted |
| BOX-T04 | Accept invitation with matching email | TeamMember created; invitation consumed |
| BOX-T05 | Accept email invitation with different account | Rejected |
| BOX-T06 | Accept domain link with allowed domain | Membership created |
| BOX-T07 | Accept domain link with disallowed domain | Rejected |
| BOX-T08 | Accept expired invitation | Rejected |
| BOX-T09 | Replay accepted invitation | Rejected or idempotent according to design |
| BOX-T10 | Member reads own team | Allowed |
| BOX-T11 | Member modifies team | Denied |
| BOX-T12 | Admin manages invitation | Allowed |
| BOX-T13 | Admin manages payments | Expected denied under observed permission map |
| BOX-T14 | User requests foreign team slug | Denied |
| BOX-T15 | Removed member reuses active session | Denied after membership refresh |
| BOX-T16 | API key accesses another team | Denied |
| BOX-T17 | Team deletion with active integrations | Lifecycle and cleanup evidence captured |
| BOX-T18 | Subscription becomes inactive | Actual access effect documented |
| BOX-T19 | SCIM deactivates member | Membership/session consequences documented |
| BOX-T20 | Webhook/audit provider unavailable | Failure behavior and transaction outcome documented |

## R1 execution classification - 2026-07-13

The upstream runner declares 42 Playwright cases in 9 files. R1 executed only test discovery. Therefore all scenarios above remain E0/E2 leads until a controlled database-backed run produces E3 evidence.

Highest-priority missing declarations or runtime probes are:

- verification and password-reset expiry/replay/failure;
- login lockout threshold and concurrency;
- JWT revocation after credential change;
- cross-user session deletion and cross-team member identifiers;
- last-owner removal/demotion and concurrent owner changes;
- invitation expiry, revocation, replay, concurrent acceptance and accept-versus-revoke;
- event/audit payload, ordering, correlation and integration failure behavior.
