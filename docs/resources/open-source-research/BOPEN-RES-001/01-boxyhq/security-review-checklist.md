# Security Review Checklist

## Identity and session

- [ ] Password hashing parameters reviewed.
- [ ] Account lockout behavior tested.
- [ ] Verification token storage and replay tested.
- [ ] Session invalidation after password/member/tenant changes tested.
- [ ] OAuth account linking and email trust boundaries reviewed.

## Tenant isolation

- [ ] Every team-scoped endpoint resolves membership server-side.
- [ ] Slug substitution negative tests pass.
- [ ] Direct object reference tests pass.
- [ ] Database queries include trusted team identifiers.
- [ ] No client-provided `teamId` is accepted without verification.

## Invitations

- [ ] Token entropy and storage reviewed.
- [ ] Expiry enforced.
- [ ] Email/domain restrictions tested.
- [ ] Concurrent acceptance tested.
- [ ] Replay and revocation tested.
- [ ] Role escalation through tampered payload tested.

## Authorization

- [ ] Permission checks cover all modifying routes.
- [ ] Owner/admin boundary tested.
- [ ] Last-owner removal tested.
- [ ] Billing permission separation tested.
- [ ] API key permissions and rotation tested.

## Enterprise identity

- [ ] SSO tenant binding tested.
- [ ] SCIM create/update/deactivate behavior traced.
- [ ] JIT provisioning and duplicate identity handling tested.
- [ ] IdP/domain takeover risks reviewed.

## Integrations and supply chain

- [ ] Webhook signing and replay protection reviewed.
- [ ] Audit failure behavior reviewed.
- [ ] Payment webhook verification reviewed.
- [ ] Dependency scan recorded.
- [ ] Secret scanning recorded.
- [ ] Container/config defaults reviewed.
