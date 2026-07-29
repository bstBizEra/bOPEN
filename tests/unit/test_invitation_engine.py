"""
MILE-2.1 principal invitation engine unit tests.

Exit gate (BOPEN-P2-001 9.7): all invitation invariants pass; the token value never
appears in persistence, logs, exceptions, snapshots or evidence; concurrency proves
only one acceptance wins; expiry uses injected time; audit events are correlated.

Covers INV-P2-001 to INV-P2-004 and scenarios P2-T001 to P2-T009.
"""

import json
import unittest
from datetime import timedelta

from kernel_core.membership import (
    Conflict,
    InvalidRequest,
    InvitationExpired,
    InvitationInvalid,
    InvitationState,
)
from kernel_core.types import MembershipState
from tests.support.phase2_fixtures import build_phase2_env


class InvitationEngineTests(unittest.TestCase):
    def setUp(self):
        self.env = build_phase2_env()
        self.engine = self.env.invitation_engine

    def _issue(self, tenant_id="tnt_alpha", email="alice@acme.test", key="idem-issue-1", **kw):
        return self.engine.issue(
            tenant_id=tenant_id,
            email=email,
            invited_by_principal_id="usr_owner",
            correlation_id="corr-1",
            idempotency_key=key,
            **kw,
        )

    # -- P2-T001 -----------------------------------------------------------------

    def test_P2_T001_issue_valid_invitation(self):
        issued = self._issue()
        invitation = issued.invitation

        self.assertEqual(invitation.state, InvitationState.INVITED)
        self.assertEqual(invitation.tenant_id, "tnt_alpha")
        self.assertTrue(issued.raw_token)
        # INV-P2-002: only a digest is persisted.
        self.assertNotEqual(invitation.token_digest, issued.raw_token)
        self.assertEqual(invitation.token_digest, self.env.hasher.hash(issued.raw_token))
        self.assertEqual(invitation.token_digest_scheme, "sha256-v1")
        # D-P2-003 provisional 7-day lifetime.
        self.assertEqual(invitation.expires_at - invitation.issued_at, timedelta(days=7))

    def test_INV_P2_001_destination_is_normalized_and_tenant_bound(self):
        issued = self._issue(email="  Alice@ACME.test  ")
        self.assertEqual(issued.invitation.email_normalized, "alice@acme.test")

    def test_INV_P2_002_raw_token_never_appears_in_persistence_or_audit(self):
        issued = self._issue()
        raw = issued.raw_token

        persisted = json.dumps(self.env.invitations._items, default=str)
        self.assertNotIn(raw, persisted)

        audit_blob = json.dumps(self.env.audit.logs, default=str)
        self.assertNotIn(raw, audit_blob)

    def test_invalid_destination_and_empty_roles_are_rejected(self):
        with self.assertRaises(InvalidRequest):
            self._issue(email="not-an-email")
        with self.assertRaises(InvalidRequest):
            self._issue(key="idem-roles", requested_roles=())

    def test_lifetime_outside_approved_bounds_is_rejected(self):
        with self.assertRaises(InvalidRequest):
            self._issue(key="idem-long", lifetime=timedelta(days=365))
        with self.assertRaises(InvalidRequest):
            self._issue(key="idem-neg", lifetime=timedelta(seconds=-1))

    # -- P2-T002 -----------------------------------------------------------------

    def test_P2_T002_equivalent_issue_replay_returns_same_invitation(self):
        first = self._issue(key="shared")
        second = self._issue(key="shared")
        self.assertIs(first, second)

    def test_duplicate_open_invitation_is_rejected(self):
        """D-P2-004 provisional: one open invitation per tenant + destination + purpose."""
        self._issue(key="idem-a")
        with self.assertRaises(Conflict):
            self._issue(key="idem-b")

    # -- P2-T003 -----------------------------------------------------------------

    def test_P2_T003_accept_activates_invitation_and_membership_atomically(self):
        issued = self._issue()
        result = self.engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id="corr-1", idempotency_key="idem-accept",
        )

        self.assertEqual(result.invitation.state, InvitationState.ACTIVE)
        self.assertEqual(result.membership.state, MembershipState.ACTIVE)
        self.assertEqual(result.invitation.membership_id, result.membership.id)
        self.assertEqual(result.invitation.principal_id, "usr_alice")
        self.assertEqual(result.receipt.reason_code, "INVITATION_ACCEPTED")

        types = [e["event_type"] for e in self.env.audit.logs]
        self.assertIn("invitation.accepted", types)
        self.assertIn("membership.transitioned", types)
        for event in self.env.audit.logs:
            self.assertEqual(event["correlation_id"], "corr-1")

    # -- P2-T004 -----------------------------------------------------------------

    def test_P2_T004_only_one_acceptance_wins(self):
        """INV-P2-003: acceptance is single-use."""
        issued = self._issue()
        self.engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id="corr-1", idempotency_key="idem-first",
        )
        with self.assertRaises(InvitationInvalid):
            self.engine.accept(
                raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_bob",
                correlation_id="corr-2", idempotency_key="idem-second",
            )
        self.assertIsNone(self.env.memberships.find_active("tnt_alpha", "usr_bob"))

    def test_equivalent_acceptance_replay_returns_prior_result(self):
        issued = self._issue()
        first = self.engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id="corr-1", idempotency_key="idem-accept",
        )
        second = self.engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id="corr-1", idempotency_key="idem-accept",
        )
        self.assertIs(first, second)

    def test_failed_activation_rolls_the_invitation_back(self):
        """Atomicity: nothing commits if membership activation fails."""
        issued = self._issue()
        self.env.tenants.deactivate("tnt_alpha")   # blocks the tenant_active condition

        with self.assertRaises(Exception):
            self.engine.accept(
                raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
                correlation_id="corr-1", idempotency_key="idem-accept",
            )

        invitation = self.env.invitations.get(issued.invitation.invitation_id)
        self.assertEqual(invitation.state, InvitationState.INVITED)
        self.assertIsNone(self.env.memberships.find_active("tnt_alpha", "usr_alice"))

    # -- P2-T005 to P2-T007 ------------------------------------------------------

    def test_P2_T005_expired_invitation_is_denied(self):
        issued = self._issue()
        self.env.clock.advance(timedelta(days=8))
        with self.assertRaises(InvitationExpired):
            self.engine.accept(
                raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
                correlation_id="corr-1", idempotency_key="idem-accept",
            )

    def test_P2_T006_declined_invitation_cannot_be_accepted(self):
        issued = self._issue()
        self.engine.decline(issued.raw_token, "tnt_alpha", "corr-1")
        with self.assertRaises(InvitationInvalid):
            self.engine.accept(
                raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
                correlation_id="corr-1", idempotency_key="idem-accept",
            )

    def test_P2_T007_tenant_mismatch_denies_without_disclosure(self):
        issued = self._issue(tenant_id="tnt_alpha")
        with self.assertRaises(InvitationInvalid) as ctx:
            self.engine.validate(issued.raw_token, "tnt_beta", "corr-1")
        # Generic message: the real tenant is never disclosed.
        self.assertNotIn("tnt_alpha", str(ctx.exception))

    def test_unknown_token_denies_generically_without_enumeration(self):
        with self.assertRaises(InvitationInvalid) as ctx:
            self.engine.validate("not-a-real-token", "tnt_alpha", "corr-1")
        self.assertEqual(str(ctx.exception), "Invitation is not valid")
        self.assertTrue(self.env.audit.events_of_type("invitation.validation_failed"))

    # -- P2-T008 / P2-T009 -------------------------------------------------------

    def test_P2_T008_decline_is_terminal_and_audited(self):
        issued = self._issue()
        declined = self.engine.decline(issued.raw_token, "tnt_alpha", "corr-1")
        self.assertEqual(declined.state, InvitationState.DECLINED)
        self.assertIsNotNone(declined.declined_at)
        self.assertTrue(self.env.audit.events_of_type("invitation.declined"))

    def test_P2_T009_expiry_scheduler_is_idempotent_and_uses_injected_time(self):
        self._issue(key="idem-1", email="a@acme.test")
        self._issue(key="idem-2", email="b@acme.test")

        self.assertEqual(self.engine.expire_due("corr-expire"), [])   # nothing due yet

        self.env.clock.advance(timedelta(days=8))
        first = self.engine.expire_due("corr-expire")
        self.assertEqual(len(first), 2)
        self.assertTrue(all(i.state == InvitationState.EXPIRED for i in first))

        second = self.engine.expire_due("corr-expire")   # replay
        self.assertEqual(second, [])

    def test_expiry_batch_limit_is_bounded(self):
        for n in range(3):
            self._issue(key=f"idem-{n}", email=f"user{n}@acme.test")
        self.env.clock.advance(timedelta(days=8))
        self.assertEqual(len(self.engine.expire_due("corr-expire", limit=2)), 2)
        with self.assertRaises(InvalidRequest):
            self.engine.expire_due("corr-expire", limit=0)


if __name__ == "__main__":
    unittest.main()
