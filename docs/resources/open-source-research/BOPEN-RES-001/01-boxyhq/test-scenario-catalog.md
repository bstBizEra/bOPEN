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
