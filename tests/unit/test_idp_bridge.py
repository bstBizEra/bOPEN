"""
MILE-2.4 enterprise IdP and SCIM 2.0 bridge unit tests.

Exit gate (BOPEN-P2-001 12.7): SAML and OIDC positive and mandatory negative paths
pass; SCIM Users and Groups are idempotent and tenant-bound; deprovision revokes
context eligibility; account linking cannot occur by email match alone; raw
protocol messages and tokens are absent from evidence.

Covers INV-P2-011 to INV-P2-014 and scenarios P2-T040 to P2-T053.

All fixtures are sanitized and non-secret; no test requires network access.
"""

import json
import unittest
from datetime import timedelta

from kernel_core.membership import Conflict, NotFoundOrNotAccessible
from kernel_core.types import MembershipState
from platform_kernel.context_service import ContextDenied, SwitchContextCommand
from platform_kernel.idp_bridge import (
    ConnectionStatus,
    DependencyUnavailable,
    DirectoryStatus,
    IdentityLinkDenied,
    IdentityProviderConnection,
    NormalizedAuthResult,
    Protocol_,
    ProtocolValidationFailed,
    SCIMDirectory,
    ScimEvent,
    ScimOrderingConflict,
    GroupRoleMapping,
)
from tests.support.phase2_fixtures import build_phase2_env, onboard_active_member


class IdpBridgeTestBase(unittest.TestCase):
    def setUp(self):
        self.env = build_phase2_env()
        self.bridge = self.env.idp_bridge
        self.store = self.env.identity_store

        self.store.connections["con_saml"] = IdentityProviderConnection(
            connection_id="con_saml", tenant_id="tnt_alpha", protocol=Protocol_.SAML,
            issuer="https://idp.acme.test/saml", broker_connection_ref="broker-ref-1",
            status=ConnectionStatus.ACTIVE, created_by="usr_owner",
        )
        self.store.connections["con_oidc"] = IdentityProviderConnection(
            connection_id="con_oidc", tenant_id="tnt_alpha", protocol=Protocol_.OIDC,
            issuer="https://idp.acme.test/oidc", broker_connection_ref="broker-ref-1",
            status=ConnectionStatus.ACTIVE, created_by="usr_owner",
        )
        self.store.directories["dir_1"] = SCIMDirectory(
            directory_id="dir_1", tenant_id="tnt_alpha",
            broker_directory_ref="broker-ref-1", status=DirectoryStatus.ACTIVE,
        )


class ConnectionAndSsoTests(IdpBridgeTestBase):
    def _linked_identity(self, connection_id="con_saml", subject="saml-subject-1"):
        onboard_active_member(self.env, tenant_id="tnt_alpha", principal_id="usr_alice")
        connection = self.store.connections[connection_id]
        return self.bridge.link_identity(
            connection_id=connection_id, issuer=connection.issuer, subject=subject,
            principal_id="usr_alice", correlation_id="corr-link",
            link_challenge_accepted=True,
        )

    def _auth_result(self, transaction, connection_id="con_saml", **overrides):
        connection = self.store.connections[connection_id]
        payload = dict(
            connection_id=connection_id, protocol=connection.protocol,
            issuer=connection.issuer, subject="saml-subject-1",
            state=transaction.state, assertion_id="assertion-1",
            nonce=transaction.nonce,
        )
        payload.update(overrides)
        return NormalizedAuthResult(**payload)

    # -- connection verification -------------------------------------------------

    def test_connection_verification_requires_a_distinct_approver(self):
        self.store.connections["con_draft"] = IdentityProviderConnection(
            connection_id="con_draft", tenant_id="tnt_alpha", protocol=Protocol_.SAML,
            issuer="https://idp.other.test", broker_connection_ref="broker-ref-1",
            created_by="usr_owner",
        )
        with self.assertRaises(Exception):
            self.bridge.verify_connection("con_draft", "usr_owner", "corr-1")

        verified = self.bridge.verify_connection("con_draft", "usr_security", "corr-1")
        self.assertEqual(verified.status, ConnectionStatus.ACTIVE)
        self.assertTrue(self.env.audit.events_of_type("identity.connection_verified"))

    def test_only_active_connections_start_authentication(self):
        self.store.connections["con_saml"] = self.store.connections["con_saml"].__class__(
            **{**self.store.connections["con_saml"].__dict__, "status": ConnectionStatus.SUSPENDED}
        )
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.begin_sso("con_saml", "corr-1")

    # -- P2-T040 / P2-T043 -------------------------------------------------------

    def test_P2_T040_valid_saml_login_requires_active_membership(self):
        identity = self._linked_identity()
        transaction = self.bridge.begin_sso("con_saml", "corr-1")
        resolved = self.bridge.complete_sso(self._auth_result(transaction), "corr-1")

        self.assertEqual(resolved.external_identity_id, identity.external_identity_id)
        self.assertEqual(resolved.principal_id, "usr_alice")
        self.assertTrue(self.env.audit.events_of_type("identity.authentication_succeeded"))

    def test_P2_T043_valid_oidc_login_succeeds(self):
        self._linked_identity(connection_id="con_oidc", subject="oidc-subject-1")
        transaction = self.bridge.begin_sso("con_oidc", "corr-1")
        self.assertIsNotNone(transaction.pkce_challenge)   # PKCE required for OIDC

        resolved = self.bridge.complete_sso(
            self._auth_result(transaction, connection_id="con_oidc", subject="oidc-subject-1"),
            "corr-1",
        )
        self.assertEqual(resolved.principal_id, "usr_alice")

    def test_authentication_denied_when_no_active_membership_exists(self):
        connection = self.store.connections["con_saml"]
        self.bridge.link_identity(
            connection_id="con_saml", issuer=connection.issuer, subject="saml-subject-1",
            principal_id="usr_orphan", correlation_id="corr-link", link_challenge_accepted=True,
        )
        transaction = self.bridge.begin_sso("con_saml", "corr-1")
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.complete_sso(self._auth_result(transaction), "corr-1")

    # -- P2-T041 / P2-T044 -------------------------------------------------------

    def test_P2_T041_issuer_signature_and_time_failures_deny(self):
        self._linked_identity()

        cases = {
            "issuer": {"issuer": "https://evil.test"},
            "signature": {"broker_signature_valid": False},
            "unknown_state": {"state": "not-a-real-state"},
            "missing_subject": {"subject": ""},
        }
        for name, overrides in cases.items():
            with self.subTest(case=name):
                transaction = self.bridge.begin_sso("con_saml", "corr-1")
                with self.assertRaises(ProtocolValidationFailed):
                    self.bridge.complete_sso(
                        self._auth_result(transaction, **overrides), "corr-1"
                    )

    def test_expired_transaction_state_denies(self):
        self._linked_identity()
        transaction = self.bridge.begin_sso("con_saml", "corr-1")
        self.env.clock.advance(timedelta(minutes=11))
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.complete_sso(self._auth_result(transaction), "corr-1")

    def test_P2_T044_oidc_nonce_mismatch_denies(self):
        self._linked_identity(connection_id="con_oidc", subject="oidc-subject-1")
        transaction = self.bridge.begin_sso("con_oidc", "corr-1")
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.complete_sso(
                self._auth_result(
                    transaction, connection_id="con_oidc", subject="oidc-subject-1",
                    nonce="wrong-nonce",
                ),
                "corr-1",
            )

    # -- P2-T042 -----------------------------------------------------------------

    def test_P2_T042_assertion_and_state_replay_are_denied(self):
        self._linked_identity()
        transaction = self.bridge.begin_sso("con_saml", "corr-1")
        self.bridge.complete_sso(self._auth_result(transaction), "corr-1")

        # The single-use state is now consumed.
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.complete_sso(self._auth_result(transaction), "corr-2")

        # A fresh transaction reusing the assertion identifier is also denied.
        second = self.bridge.begin_sso("con_saml", "corr-3")
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.complete_sso(self._auth_result(second), "corr-3")

    # -- P2-T045 / P2-T046 -------------------------------------------------------

    def test_P2_T045_email_match_alone_cannot_link_an_account(self):
        """INV-P2-012."""
        connection = self.store.connections["con_saml"]
        with self.assertRaises(IdentityLinkDenied):
            self.bridge.link_identity(
                connection_id="con_saml", issuer=connection.issuer, subject="saml-subject-1",
                principal_id="usr_alice", correlation_id="corr-1",
                email_snapshot="alice@acme.test",   # matching email is not a basis
            )
        self.assertTrue(self.env.audit.events_of_type("identity.link_denied"))

    def test_unknown_subject_at_callback_denies_rather_than_auto_linking(self):
        onboard_active_member(self.env, tenant_id="tnt_alpha", principal_id="usr_alice")
        transaction = self.bridge.begin_sso("con_saml", "corr-1")
        with self.assertRaises(IdentityLinkDenied):
            self.bridge.complete_sso(self._auth_result(transaction), "corr-1")

    def test_P2_T046_explicit_link_challenge_succeeds(self):
        identity = self._linked_identity()
        self.assertEqual(identity.canonical_key,
                         ("con_saml", "https://idp.acme.test/saml", "saml-subject-1"))
        self.assertTrue(self.env.audit.events_of_type("identity.linked"))

    def test_invitation_verified_link_basis_succeeds(self):
        issued = self.env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="bob@acme.test", invited_by_principal_id="usr_owner",
            correlation_id="corr-1", idempotency_key="issue-bob",
        )
        connection = self.store.connections["con_saml"]
        identity = self.bridge.link_identity(
            connection_id="con_saml", issuer=connection.issuer, subject="saml-subject-bob",
            principal_id="usr_bob", correlation_id="corr-1",
            invitation_token_digest=self.env.hasher.hash(issued.raw_token),
        )
        self.assertEqual(identity.principal_id, "usr_bob")

    def test_INV_P2_011_subject_cannot_be_reassigned_to_another_principal(self):
        self._linked_identity()
        connection = self.store.connections["con_saml"]
        with self.assertRaises(IdentityLinkDenied):
            self.bridge.link_identity(
                connection_id="con_saml", issuer=connection.issuer, subject="saml-subject-1",
                principal_id="usr_mallory", correlation_id="corr-1",
                link_challenge_accepted=True,
            )

    def test_relinking_the_same_principal_is_idempotent(self):
        first = self._linked_identity()
        connection = self.store.connections["con_saml"]
        second = self.bridge.link_identity(
            connection_id="con_saml", issuer=connection.issuer, subject="saml-subject-1",
            principal_id="usr_alice", correlation_id="corr-1", link_challenge_accepted=True,
        )
        self.assertEqual(first.external_identity_id, second.external_identity_id)

    # -- P2-T053 -----------------------------------------------------------------

    def test_P2_T053_broker_unavailable_is_a_controlled_failure(self):
        self.env.broker.set_available(False)
        with self.assertRaises(DependencyUnavailable):
            self.bridge.begin_sso("con_saml", "corr-1")


class ScimSyncTests(IdpBridgeTestBase):
    def _event(self, event_type="user.created", **overrides):
        payload = dict(
            event_id=f"evt-{event_type}-1", event_type=event_type, directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="User", resource_id="scim-res-1",
            observed_at=self.env.clock.now(), external_id="ext-1",
            user_name="alice@acme.test", sequence=1,
        )
        payload.update(overrides)
        return ScimEvent(**payload)

    # -- P2-T047 -----------------------------------------------------------------

    def test_P2_T047_user_create_provisions_through_the_state_machine(self):
        result = self.bridge.handle_scim_event(self._event(), "corr-1")
        self.assertEqual(result["status"], "created")

        membership = self.env.memberships.get(result["membership_id"])
        self.assertEqual(membership.state, MembershipState.ACTIVE)
        self.assertEqual(result["receipt"].reason_code, "SCIM_PROVISION")
        self.assertTrue(self.env.audit.events_of_type("scim.user_provisioned"))

    def test_P2_T047_create_replay_creates_no_duplicate(self):
        """INV-P2-013."""
        first = self.bridge.handle_scim_event(self._event(), "corr-1")
        replay = self.bridge.handle_scim_event(self._event(), "corr-1")
        self.assertEqual(replay["status"], "replayed")

        # A distinct event id for the same directory resource returns the existing map.
        again = self.bridge.handle_scim_event(self._event(event_id="evt-dup"), "corr-1")
        self.assertEqual(again["status"], "existing")
        self.assertEqual(again["principal_id"], first["principal_id"])
        self.assertEqual(len(self.env.memberships.find_for("tnt_alpha", first["principal_id"])), 1)

    def test_conflicting_external_id_reuse_is_rejected(self):
        self.bridge.handle_scim_event(self._event(), "corr-1")
        with self.assertRaises(Conflict):
            self.bridge.handle_scim_event(
                self._event(event_id="evt-conflict", resource_id="scim-res-2", external_id="ext-1"),
                "corr-1",
            )
        self.assertTrue(self.env.audit.events_of_type("scim.event_denied"))

    # -- P2-T048 -----------------------------------------------------------------

    def test_P2_T048_active_false_deprovisions_and_invalidates_contexts(self):
        created = self.bridge.handle_scim_event(self._event(), "corr-1")
        principal_id = created["principal_id"]

        session = self.env.session_for(principal_id)
        issued = self.env.context_service.switch(
            SwitchContextCommand(session_id=session.session_id, tenant_id="tnt_alpha",
                                 idempotency_key="idem-ctx")
        )

        self.bridge.handle_scim_event(
            self._event(event_id="evt-update", event_type="user.updated", active=False, sequence=2),
            "corr-2",
        )

        membership = self.env.memberships.find_for("tnt_alpha", principal_id)[0]
        self.assertEqual(membership.state, MembershipState.SUSPENDED)   # D-P2-009 default

        # New issuance is denied and the obligation was recorded.
        with self.assertRaises(ContextDenied):
            self.env.context_service.switch(
                SwitchContextCommand(session_id=session.session_id, tenant_id="tnt_alpha",
                                     idempotency_key="idem-ctx-2")
            )
        self.assertEqual(len(self.env.obligations.open_for(membership.id)), 1)
        affected = self.env.context_service.revoke_contexts_for_membership(
            membership.id, "corr-2", "SCIM_DEPROVISION"
        )
        self.assertIn(issued.context_id, affected)

    def test_deprovision_event_records_a_tombstone(self):
        created = self.bridge.handle_scim_event(self._event(), "corr-1")
        self.bridge.handle_scim_event(
            self._event(event_id="evt-deprov", event_type="user.deprovisioned", sequence=5),
            "corr-2",
        )
        membership = self.env.memberships.find_for("tnt_alpha", created["principal_id"])[0]
        self.assertEqual(membership.state, MembershipState.SUSPENDED)
        self.assertTrue(self.env.audit.events_of_type("scim.user_deprovisioned"))

    # -- P2-T049 -----------------------------------------------------------------

    def test_P2_T049_stale_update_cannot_reactivate_a_deprovisioned_relationship(self):
        """INV-P2-014."""
        created = self.bridge.handle_scim_event(self._event(), "corr-1")
        self.bridge.handle_scim_event(
            self._event(event_id="evt-deprov", event_type="user.deprovisioned", sequence=5),
            "corr-2",
        )

        with self.assertRaises(ScimOrderingConflict):
            self.bridge.handle_scim_event(
                self._event(event_id="evt-stale", event_type="user.updated",
                            active=True, sequence=3),
                "corr-3",
            )

        membership = self.env.memberships.find_for("tnt_alpha", created["principal_id"])[0]
        self.assertEqual(membership.state, MembershipState.SUSPENDED)

    def test_out_of_order_event_is_rejected(self):
        self.bridge.handle_scim_event(self._event(), "corr-1")
        self.bridge.handle_scim_event(
            self._event(event_id="evt-2", event_type="user.updated", sequence=10), "corr-2"
        )
        with self.assertRaises(ScimOrderingConflict):
            self.bridge.handle_scim_event(
                self._event(event_id="evt-3", event_type="user.updated", sequence=4), "corr-3"
            )

    def test_a_later_update_can_reinstate_after_suspension(self):
        created = self.bridge.handle_scim_event(self._event(), "corr-1")
        self.bridge.handle_scim_event(
            self._event(event_id="evt-off", event_type="user.updated", active=False, sequence=2),
            "corr-2",
        )
        self.bridge.handle_scim_event(
            self._event(event_id="evt-on", event_type="user.updated", active=True, sequence=3),
            "corr-3",
        )
        membership = self.env.memberships.find_for("tnt_alpha", created["principal_id"])[0]
        self.assertEqual(membership.state, MembershipState.ACTIVE)

    # -- P2-T050 / P2-T051 -------------------------------------------------------

    def test_P2_T050_mapped_group_applies_an_approved_role(self):
        self.store.mappings.append(
            GroupRoleMapping(directory_id="dir_1", group_external_id="grp-admins",
                             mapping_policy_version="1.0.0", target_role="tenant_admin")
        )
        result = self.bridge.handle_scim_event(
            self._event(event_id="evt-grp", event_type="group.changed", resource_type="Group",
                        resource_id="grp-admins", groups=("grp-admins",), sequence=1),
            "corr-1",
        )
        self.assertEqual(result["applied_roles"], ["tenant_admin"])
        self.assertTrue(self.env.audit.events_of_type("scim.group_mapping_applied"))

    def test_P2_T051_unmapped_group_has_no_authorization_effect(self):
        result = self.bridge.handle_scim_event(
            self._event(event_id="evt-grp", event_type="group.changed", resource_type="Group",
                        resource_id="grp-unknown", groups=("grp-unknown",), sequence=1),
            "corr-1",
        )
        self.assertEqual(result["applied_roles"], [])
        self.assertEqual(result["ignored_groups"], ["grp-unknown"])
        self.assertEqual(self.env.audit.events_of_type("scim.group_mapping_applied"), [])

    # -- P2-T052 -----------------------------------------------------------------

    def test_P2_T052_directory_tenant_mismatch_denies(self):
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.handle_scim_event(self._event(tenant_id="tnt_beta"), "corr-1")
        self.assertTrue(self.env.audit.events_of_type("scim.event_denied"))

    def test_unknown_directory_denies(self):
        with self.assertRaises(NotFoundOrNotAccessible):
            self.bridge.handle_scim_event(self._event(directory_id="dir_missing"), "corr-1")

    def test_unauthenticated_scim_source_denies(self):
        with self.assertRaises(ProtocolValidationFailed):
            self.bridge.handle_scim_event(self._event(), "corr-1", credential_ref="untrusted")

    def test_update_for_unmapped_resource_denies(self):
        with self.assertRaises(NotFoundOrNotAccessible):
            self.bridge.handle_scim_event(
                self._event(event_id="evt-orphan", event_type="user.updated", active=True), "corr-1"
            )

    # -- INV-P2-018 --------------------------------------------------------------

    def test_no_credential_or_assertion_appears_in_evidence(self):
        self.bridge.handle_scim_event(self._event(), "corr-1")
        blob = json.dumps(self.env.audit.logs, default=str).lower()
        for prohibited in ("password", "assertion", "authorization_code", "client_secret"):
            self.assertNotIn(prohibited, blob)


if __name__ == "__main__":
    unittest.main()
