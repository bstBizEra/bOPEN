# BoxyHQ Lifecycle Map Against bOPEN

## 1. Registration without invitation

```text
Join UI/API
  -> validate CAPTCHA and account data
  -> ensure email is allowed
  -> ensure user does not exist
  -> ensure team slug is available
  -> create User
  -> create Team
  -> add TeamMember(role=OWNER)
  -> initialize webhook app
  -> optional email verification
```

### bOPEN mapping

```text
Human principal enrollment
  -> user account creation
  -> tenant provisioning request
  -> owner membership creation
  -> initial platform/tenant integration setup
```

### Gap

No explicit tenant provisioning state machine, compensating transaction or isolation-profile assignment is apparent in the initial path.

## 2. Invitation creation

```text
Authenticated team member
  -> resolve team access
  -> authorize team_invitation:create
  -> validate email or allowed domains
  -> reject existing member/invitation
  -> create Invitation(role, token, expiry)
  -> send email when applicable
  -> emit invitation.created
  -> send audit event
```

### bOPEN mapping

Invitation is a pre-membership grant proposal, not a membership itself.

## 3. Invitation acceptance

```text
Authenticated user
  -> fetch token
  -> verify expiry
  -> verify invited email or allowed domain
  -> add/upsert TeamMember with invitation role
  -> emit member.created
  -> remove email invitation
```

### bOPEN extensions

- explicit invitation states;
- accepted/revoked/expired timestamps;
- one-time token hash rather than recoverable token where appropriate;
- replay and concurrent-accept protection;
- tenant and membership status checks;
- policy evaluation before activation;
- acceptance audit with correlation ID.

## 4. Membership administration

Team members are uniquely related by `(teamId, userId)`. Role is stored on the membership. bOPEN will preserve the relationship pattern but externalize role assignment and effective access.

## 5. Team-scoped action

The expected pattern is:

```text
session
  -> team slug/request scope
  -> membership lookup
  -> permission check
  -> action
  -> event/audit
```

This must be validated end to end during G4.

## 6. Commercial lifecycle

The schema supports subscription, service, price and team billing identifiers, while permission resources include team payments. Research must determine whether access is actually gated by subscription and where the customer/team association is enforced.

## 7. Deletion/offboarding

Team deletion, member leave/removal, invitation revocation, SSO/SCIM deprovisioning and subscription cancellation must be traced separately. Cascade deletion in the schema is not sufficient lifecycle governance for bOPEN.
