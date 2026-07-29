"""
Phase 2 integrated acceptance suite (BOPEN-P2-001 WP-P2-08).

Verifies the full governed onboarding chain end to end:

    Invite Principal -> Activate Membership -> Authenticate through Enterprise IdP
    -> Synchronize Directory State -> Switch Tenant Context
    -> Grant and Revoke Delegated Access -> Emit Evidence

Milestone-level negative paths live in the unit suites:
    tests/unit/test_invitation_engine.py         MILE-2.1  P2-T001..T009
    tests/unit/test_membership_state_machine.py  MILE-2.2  P2-T010..T014
    tests/unit/test_context_switch.py            MILE-2.3  P2-T020..T029
    tests/unit/test_idp_bridge.py                MILE-2.4  P2-T040..T053
    tests/unit/test_delegated_access.py          MILE-2.5  P2-T060..T065

This suite adds the cross-milestone chain, the prohibited-field scan (P2-T066) and
audit fail-closed behaviour (P2-T067), and asserts invariant traceability.

No test depends on wall clock, randomness, network access or production credentials.
"""

import json
import unittest
from datetime import timedelta

from kernel_core.audit import AuditContractError
from kernel_core.delegation import GrantType
from kernel_core.membership import ActorType, TransitionCommand
from kernel_core.types import MembershipState
from platform_kernel.context_service import ContextDenied, SwitchContextCommand
from platform_kernel.idp_bridge import (
    ConnectionStatus,
    DirectoryStatus,
    IdentityProviderConnection,
    NormalizedAuthResult,
    Protocol_,
    SCIMDirectory,
    ScimEvent,
)
from tests.support.phase2_fixtures import build_phase2_env

CORRELATION = "corr-phase2-chain"


class Phase2OnboardingChainTests(unittest.TestCase):
    def setUp(self):
        self.env = build_phase2_env()
        self.env.identity_store.connections["con_saml"] = IdentityProviderConnection(
            connection_id="con_saml", tenant_id="tnt_alpha", protocol=Protocol_.SAML,
            issuer="https://idp.acme.test/saml", broker_connection_ref="broker-ref-1",
            status=ConnectionStatus.ACTIVE, created_by="usr_owner",
        )
        self.env.identity_store.directories["dir_1"] = SCIMDirectory(
            directory_id="dir_1", tenant_id="tnt_alpha",
            broker_directory_ref="broker-ref-1", status=DirectoryStatus.ACTIVE,
        )

    def test_full_enterprise_onboarding_chain(self):
        env = self.env

        # 1. Invite Principal ----------------------------------------------------
        issued = env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="Alice@ACME.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="chain-issue",
        )
        self.assertEqual(issued.invitation.state.value, "invited")

        # 2. Activate Membership -------------------------------------------------
        accepted = env.invitation_engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id=CORRELATION, idempotency_key="chain-accept",
        )
        self.assertEqual(accepted.membership.state, MembershipState.ACTIVE)
        self.assertEqual(accepted.invitation.membership_id, accepted.membership.id)

        # 3. Authenticate through Enterprise IdP ---------------------------------
        identity = env.idp_bridge.link_identity(
            connection_id="con_saml", issuer="https://idp.acme.test/saml",
            subject="saml-subject-alice", principal_id="usr_alice",
            correlation_id=CORRELATION, link_challenge_accepted=True,
        )
        transaction = env.idp_bridge.begin_sso("con_saml", CORRELATION)
        authenticated = env.idp_bridge.complete_sso(
            NormalizedAuthResult(
                connection_id="con_saml", protocol=Protocol_.SAML,
                issuer="https://idp.acme.test/saml", subject="saml-subject-alice",
                state=transaction.state, assertion_id="assertion-alice-1",
                nonce=transaction.nonce,
            ),
            CORRELATION,
        )
        self.assertEqual(authenticated.external_identity_id, identity.external_identity_id)

        # 4. Synchronize Directory State ----------------------------------------
        provisioned = env.idp_bridge.handle_scim_event(
            ScimEvent(
                event_id="evt-scim-bob", event_type="user.created", directory_id="dir_1",
                tenant_id="tnt_alpha", resource_type="User", resource_id="scim-res-bob",
                observed_at=env.clock.now(), external_id="ext-bob",
                user_name="bob@acme.test", sequence=1,
            ),
            CORRELATION,
        )
        self.assertEqual(
            env.memberships.get(provisioned["membership_id"]).state, MembershipState.ACTIVE
        )

        # 5. Switch Tenant Context ----------------------------------------------
        session = env.session_for("usr_alice")
        context = env.context_service.switch(
            SwitchContextCommand(
                session_id=session.session_id, tenant_id="tnt_alpha",
                idempotency_key="chain-switch", header_tenant_id="tnt_alpha",
                client_id="cli_test",
            )
        )
        claims = env.validator.validate(context.access_token)
        self.assertEqual((claims["sub"], claims["tid"], claims["mid"]),
                         ("usr_alice", "tnt_alpha", accepted.membership.id))

        # 6. Grant and Revoke Delegated Access ----------------------------------
        grant = env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader",),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id=CORRELATION, case_reference="CASE-77",
        )
        env.delegation.approve(grant.grant_id, "usr_director", CORRELATION)
        env.delegation.activate(grant.grant_id, "usr_director", CORRELATION)

        support_session = env.session_for("usr_support")
        delegated = env.context_service.switch(
            SwitchContextCommand(
                session_id=support_session.session_id, tenant_id="tnt_alpha",
                idempotency_key="chain-delegated",
            )
        )
        self.assertEqual(delegated.delegated_grant_id, grant.grant_id)
        self.assertEqual(env.validator.validate(delegated.access_token)["dgr"], grant.grant_id)

        env.delegation.revoke(grant.grant_id, "usr_security", CORRELATION)
        with self.assertRaises(ContextDenied):
            env.context_service.switch(
                SwitchContextCommand(
                    session_id=support_session.session_id, tenant_id="tnt_alpha",
                    idempotency_key="chain-delegated-2",
                )
            )

        # 7. Emit Evidence -------------------------------------------------------
        emitted = {e["event_type"] for e in env.audit.logs}
        for required in (
            "invitation.issued", "invitation.accepted", "membership.transitioned",
            "identity.linked", "identity.authentication_succeeded",
            "scim.user_provisioned", "context.issued",
            "delegation.created", "delegation.activated", "delegation.revoked",
        ):
            self.assertIn(required, emitted, f"missing audit event {required}")

    def test_deprovision_ends_context_eligibility_across_the_chain(self):
        """Leaver control: SCIM deprovision must stop new context issuance."""
        env = self.env
        created = env.idp_bridge.handle_scim_event(
            ScimEvent(
                event_id="evt-create", event_type="user.created", directory_id="dir_1",
                tenant_id="tnt_alpha", resource_type="User", resource_id="scim-res-1",
                observed_at=env.clock.now(), external_id="ext-1", sequence=1,
            ),
            CORRELATION,
        )
        session = env.session_for(created["principal_id"])
        first = env.context_service.switch(
            SwitchContextCommand(session_id=session.session_id, tenant_id="tnt_alpha",
                                 idempotency_key="ctx-1")
        )

        env.idp_bridge.handle_scim_event(
            ScimEvent(
                event_id="evt-deprov", event_type="user.deprovisioned", directory_id="dir_1",
                tenant_id="tnt_alpha", resource_type="User", resource_id="scim-res-1",
                observed_at=env.clock.now(), sequence=9,
            ),
            CORRELATION,
        )

        with self.assertRaises(ContextDenied):
            env.context_service.switch(
                SwitchContextCommand(session_id=session.session_id, tenant_id="tnt_alpha",
                                     idempotency_key="ctx-2")
            )
        membership = env.memberships.find_for("tnt_alpha", created["principal_id"])[0]
        self.assertIn(first.context_id,
                      env.context_service.revoke_contexts_for_membership(
                          membership.id, CORRELATION, "SCIM_DEPROVISION"))

    def test_cross_tenant_isolation_holds_end_to_end(self):
        """A relationship in one tenant grants nothing in another."""
        env = self.env
        issued = env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="alice@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="iso-issue",
        )
        env.invitation_engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id=CORRELATION, idempotency_key="iso-accept",
        )
        session = env.session_for("usr_alice")

        with self.assertRaises(ContextDenied):
            env.context_service.switch(
                SwitchContextCommand(session_id=session.session_id, tenant_id="tnt_beta",
                                     idempotency_key="iso-switch")
            )

    # -- P2-T066 -----------------------------------------------------------------

    def test_P2_T066_prohibited_field_scan_over_all_evidence(self):
        """INV-P2-018: zero secrets, tokens or assertions in audit evidence."""
        env = self.env
        issued = env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="alice@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="scan-issue",
        )
        accepted = env.invitation_engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id=CORRELATION, idempotency_key="scan-accept",
        )
        session = env.session_for("usr_alice")
        context = env.context_service.switch(
            SwitchContextCommand(session_id=session.session_id, tenant_id="tnt_alpha",
                                 idempotency_key="scan-switch")
        )

        blob = json.dumps(env.audit.logs, default=str)
        self.assertNotIn(issued.raw_token, blob)
        self.assertNotIn(context.access_token, blob)

        lowered = blob.lower()
        for prohibited in ("password", "client_secret", "private_key",
                           "authorization_code", "saml_assertion", "bearer "):
            self.assertNotIn(prohibited, lowered)

        # Persisted invitation state never contains the raw token either.
        self.assertNotIn(
            issued.raw_token, json.dumps(env.invitations._items, default=str)
        )
        self.assertIsNotNone(accepted.membership)

    # -- P2-T067 -----------------------------------------------------------------

    def test_P2_T067_audit_contract_violation_fails_closed(self):
        """
        A prohibited field or unknown event type is rejected rather than silently
        recorded. The durable outbox/reconciliation binding is D-P2-015 and remains
        OPEN; this test pins fail-closed behaviour only.
        """
        env = self.env
        with self.assertRaises(AuditContractError):
            env.audit.emit_lifecycle_event(
                event_type="membership.transitioned", correlation_id=CORRELATION,
                actor_id="usr_owner", tenant_id="tnt_alpha", subject_type="membership",
                subject_id="mem_1", outcome="success", reason_code="ADMIN_SUSPENSION",
                metadata={"access_token": "eyJhbGciOiJIUzI1NiJ9.payload.signature"},
            )
        with self.assertRaises(AuditContractError):
            env.audit.emit_lifecycle_event(
                event_type="not.a.catalogued.event", correlation_id=CORRELATION,
                actor_id="usr_owner", tenant_id="tnt_alpha", subject_type="membership",
                subject_id="mem_1", outcome="success", reason_code="ADMIN_SUSPENSION",
            )
        self.assertEqual(env.audit.logs, [])

    def test_every_audit_event_in_the_chain_shares_the_correlation_id(self):
        env = self.env
        issued = env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="alice@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="corr-issue",
        )
        env.invitation_engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", principal_id="usr_alice",
            correlation_id=CORRELATION, idempotency_key="corr-accept",
        )
        self.assertTrue(env.audit.logs)
        for event in env.audit.logs:
            self.assertEqual(event["correlation_id"], CORRELATION)

    def test_phase1_authorization_slice_still_functions(self):
        """Phase 1 regression must remain green (BOPEN-P2-001 section 24)."""
        from platform_kernel.service import PlatformKernelService

        service = PlatformKernelService()
        principal = service.register_principal("owner@acme.test")
        tenant, membership = service.provision_tenant("Acme", principal.id)
        context = service.establish_context(principal.id, tenant.id, membership.id)
        decision, audit_event = service.execute_authorized_read(
            context, "tenant_profile", tenant.id, "corr-p1"
        )
        self.assertEqual(decision.decision.value, "ALLOW")
        self.assertEqual(audit_event["correlation_id"], "corr-p1")


class Phase2InvariantTraceabilityTests(unittest.TestCase):
    """
    BOPEN-P2-001 section 17 requires 100% invariant-to-test traceability. This test
    fails if an invariant has no recorded owning test, so the mapping cannot silently
    rot.
    """

    INVARIANT_OWNERS = {
        "INV-P2-001": "tests/unit/test_invitation_engine.py",
        "INV-P2-002": "tests/unit/test_invitation_engine.py",
        "INV-P2-003": "tests/unit/test_invitation_engine.py",
        "INV-P2-004": "tests/unit/test_invitation_engine.py",
        "INV-P2-005": "tests/unit/test_membership_state_machine.py",
        "INV-P2-006": "tests/unit/test_membership_state_machine.py",
        "INV-P2-007": "tests/unit/test_context_switch.py",
        "INV-P2-008": "tests/unit/test_context_switch.py",
        "INV-P2-009": "tests/unit/test_context_switch.py",
        "INV-P2-010": "tests/unit/test_context_switch.py",
        "INV-P2-011": "tests/unit/test_idp_bridge.py",
        "INV-P2-012": "tests/unit/test_idp_bridge.py",
        "INV-P2-013": "tests/unit/test_idp_bridge.py",
        "INV-P2-014": "tests/unit/test_idp_bridge.py",
        "INV-P2-015": "tests/unit/test_delegated_access.py",
        "INV-P2-016": "tests/unit/test_delegated_access.py",
        "INV-P2-017": "tests/integration/test_phase2_membership_onboarding.py",
        "INV-P2-018": "tests/integration/test_phase2_membership_onboarding.py",
    }

    def test_all_eighteen_invariants_have_an_owning_test_file(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        expected = {f"INV-P2-{n:03d}" for n in range(1, 19)}
        self.assertEqual(set(self.INVARIANT_OWNERS), expected)

        for invariant, relative in self.INVARIANT_OWNERS.items():
            with self.subTest(invariant=invariant):
                self.assertTrue((root / relative).is_file(), f"{relative} is missing")


if __name__ == "__main__":
    unittest.main()
