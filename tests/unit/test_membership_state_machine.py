"""
MILE-2.2 membership state machine unit tests.

Exit gate (BOPEN-P2-001 10.8): 100% transition matrix coverage; contract and
implementation state sets match exactly; all forbidden transitions fail closed;
concurrency and replay behaviour deterministic; non-active transition triggers
context invalidation.

Covers INV-P2-005, INV-P2-006 and acceptance scenarios P2-T010 to P2-T014.
"""

import unittest

from kernel_core.membership import (
    ActorType,
    Conflict,
    Forbidden,
    InvalidTransition,
    StaleVersion,
    TransitionCommand,
)
from kernel_core.types import Membership, MembershipState
from tests.support.phase2_fixtures import build_phase2_env

# Representative actor and reason for each allowed transition in the pinned matrix.
TRANSITION_CASES = {
    ("invited", "active"): (ActorType.SCIM_DIRECTORY, "SCIM_PROVISION"),
    ("invited", "expired"): (ActorType.EXPIRY_SCHEDULER, "INVITATION_EXPIRED"),
    ("invited", "removed"): (ActorType.TENANT_ADMIN, "ADMIN_REMOVAL"),
    ("active", "suspended"): (ActorType.TENANT_ADMIN, "ADMIN_SUSPENSION"),
    ("active", "revoked"): (ActorType.SECURITY_CONTROL, "SECURITY_REVOCATION"),
    ("active", "expired"): (ActorType.EXPIRY_SCHEDULER, "RELATIONSHIP_EXPIRED"),
    ("active", "left"): (ActorType.PRINCIPAL, "PRINCIPAL_LEFT"),
    ("active", "removed"): (ActorType.TENANT_ADMIN, "ADMIN_REMOVAL"),
    ("suspended", "active"): (ActorType.TENANT_ADMIN, "ADMIN_REINSTATEMENT"),
    ("suspended", "revoked"): (ActorType.SECURITY_CONTROL, "SECURITY_REVOCATION"),
    ("suspended", "removed"): (ActorType.TENANT_ADMIN, "ADMIN_REMOVAL"),
}


class MembershipStateMachineTests(unittest.TestCase):
    def setUp(self):
        self.env = build_phase2_env()

    def _seed(self, state: str, tenant_id: str = "tnt_alpha") -> Membership:
        membership = Membership(
            id=self.env.ids.new_id("mem"),
            tenant_id=tenant_id,
            principal_id="usr_alice",
            role="member",
            state=MembershipState(state),
            version=1,
        )
        return self.env.memberships.save(membership)

    def _command(self, membership, to_state, **overrides):
        actor, reason = TRANSITION_CASES[(membership.state.value, to_state)]
        definition = self.env.contract.resolve(membership.state.value, to_state)
        payload = dict(
            membership_id=membership.id,
            from_state=membership.state.value,
            to_state=to_state,
            action=definition["action"],
            actor_type=actor,
            actor_id="actor-1",
            reason_code=reason,
            expected_version=membership.version,
            correlation_id="corr-1",
            idempotency_key=f"idem-{membership.id}-{to_state}",
            invitation_id="inv_000001",
            reinstatement_preconditions_checked=True,
        )
        payload.update(overrides)
        return TransitionCommand(**payload)

    # -- contract integrity ------------------------------------------------------

    def test_contract_state_set_matches_implementation_enum(self):
        """Contract and implementation state sets must match exactly (10.8)."""
        self.assertEqual(
            self.env.contract.states,
            frozenset(s.value for s in MembershipState),
        )

    def test_terminal_states_have_no_outbound_transition(self):
        """INV-P2-006: terminal states cannot reactivate implicitly."""
        for from_state, _to in self.env.contract.allowed_pairs():
            self.assertNotIn(from_state, self.env.contract.terminal_states)

    def test_every_case_in_this_suite_covers_the_whole_matrix(self):
        self.assertEqual(sorted(TRANSITION_CASES), self.env.contract.allowed_pairs())

    # -- P2-T010: every allowed transition ---------------------------------------

    def test_P2_T010_every_allowed_transition_succeeds(self):
        for (from_state, to_state), (_actor, reason) in TRANSITION_CASES.items():
            with self.subTest(transition=f"{from_state}->{to_state}"):
                env = build_phase2_env()
                self.env = env
                membership = self._seed(from_state)
                receipt = env.state_machine.transition(self._command(membership, to_state))

                self.assertEqual(receipt.to_state, to_state)
                self.assertEqual(receipt.reason_code, reason)
                self.assertEqual(receipt.resulting_version, membership.version + 1)
                self.assertEqual(
                    env.memberships.get(membership.id).state, MembershipState(to_state)
                )
                events = env.audit.events_of_type("membership.transitioned")
                self.assertTrue(any(e["subject_id"] == membership.id for e in events))

    # -- P2-T011: every absent transition ----------------------------------------

    def test_P2_T011_every_absent_transition_is_rejected(self):
        """INV-P2-005: any transition absent from the contract must fail closed."""
        absent = self.env.contract.absent_pairs()
        self.assertEqual(len(absent), 31)   # 7*6 ordered pairs minus 11 allowed

        for from_state, to_state in absent:
            with self.subTest(transition=f"{from_state}->{to_state}"):
                env = build_phase2_env()
                self.env = env
                membership = self._seed(from_state)
                command = TransitionCommand(
                    membership_id=membership.id,
                    from_state=from_state,
                    to_state=to_state,
                    action="membership.activate",
                    actor_type=ActorType.TENANT_ADMIN,
                    actor_id="actor-1",
                    reason_code="ADMIN_REMOVAL",
                    expected_version=membership.version,
                    correlation_id="corr-1",
                    idempotency_key=f"idem-absent-{from_state}-{to_state}",
                )
                with self.assertRaises(InvalidTransition):
                    env.state_machine.transition(command)

                # State is unchanged and the denial is audited.
                self.assertEqual(
                    env.memberships.get(membership.id).state, MembershipState(from_state)
                )
                self.assertTrue(env.audit.events_of_type("membership.transition_denied"))

    # -- P2-T012 / concurrency ---------------------------------------------------

    def test_P2_T012_stale_membership_version_is_rejected(self):
        membership = self._seed("active")
        with self.assertRaises(StaleVersion):
            self.env.state_machine.transition(
                self._command(membership, "suspended", expected_version=99)
            )

    def test_competing_version_writes_allow_at_most_one_commit(self):
        membership = self._seed("active")
        first = self.env.state_machine.transition(self._command(membership, "suspended"))
        self.assertEqual(first.resulting_version, 2)

        # A second writer holding the stale version cannot commit.
        with self.assertRaises(Conflict):
            self.env.state_machine.transition(
                self._command(membership, "revoked", idempotency_key="idem-second")
            )

    def test_equivalent_replay_returns_the_prior_receipt(self):
        membership = self._seed("active")
        command = self._command(membership, "suspended")
        first = self.env.state_machine.transition(command)
        second = self.env.state_machine.transition(command)
        self.assertIs(first, second)
        self.assertEqual(self.env.memberships.get(membership.id).version, 2)

    def test_same_idempotency_key_with_different_payload_conflicts(self):
        membership = self._seed("active")
        self.env.state_machine.transition(
            self._command(membership, "suspended", idempotency_key="shared-key")
        )
        refreshed = self.env.memberships.get(membership.id)
        with self.assertRaises(Conflict):
            self.env.state_machine.transition(
                self._command(refreshed, "revoked", idempotency_key="shared-key")
            )

    # -- authorization and conditions --------------------------------------------

    def test_actor_type_outside_the_allowlist_is_forbidden(self):
        membership = self._seed("active")
        with self.assertRaises(Forbidden):
            self.env.state_machine.transition(
                self._command(membership, "left", actor_type=ActorType.SCIM_DIRECTORY)
            )

    def test_reason_code_outside_the_transition_definition_is_rejected(self):
        membership = self._seed("active")
        with self.assertRaises(Exception) as ctx:
            self.env.state_machine.transition(
                self._command(membership, "suspended", reason_code="NOT_A_REAL_REASON")
            )
        self.assertEqual(ctx.exception.code, "INVALID_REQUEST")

    def test_inactive_tenant_blocks_transitions_requiring_tenant_active(self):
        membership = self._seed("active")
        self.env.tenants.deactivate("tnt_alpha")
        with self.assertRaises(Forbidden):
            self.env.state_machine.transition(self._command(membership, "suspended"))

    def test_reinstatement_requires_explicit_precondition_check(self):
        membership = self._seed("suspended")
        with self.assertRaises(Forbidden):
            self.env.state_machine.transition(
                self._command(membership, "active", reinstatement_preconditions_checked=False)
            )

    def test_command_from_state_must_match_stored_state(self):
        membership = self._seed("active")
        with self.assertRaises(Conflict):
            self.env.state_machine.transition(
                self._command(membership, "suspended", from_state="suspended")
            )

    # -- P2-T013: side effects ---------------------------------------------------

    def test_P2_T013_non_active_transition_records_context_invalidation(self):
        """BOPEN-P2-001 10.6 mandatory side effects."""
        for to_state in ("suspended", "revoked", "expired", "left", "removed"):
            with self.subTest(target=to_state):
                env = build_phase2_env()
                self.env = env
                membership = self._seed("active")
                receipt = env.state_machine.transition(self._command(membership, to_state))
                self.assertTrue(receipt.context_invalidation)
                self.assertEqual(len(env.obligations.open_for(membership.id)), 1)

    def test_activation_records_no_invalidation_obligation(self):
        membership = self._seed("invited")
        receipt = self.env.state_machine.transition(self._command(membership, "active"))
        self.assertFalse(receipt.context_invalidation)
        self.assertEqual(len(self.env.obligations.obligations), 0)

    def test_invalidation_obligations_are_idempotent(self):
        membership = self._seed("active")
        command = self._command(membership, "suspended")
        self.env.state_machine.transition(command)
        self.env.state_machine.transition(command)   # replay
        self.assertEqual(len(self.env.obligations.obligations), 1)

    # -- P2-T014 -----------------------------------------------------------------

    def test_P2_T014_revoked_membership_cannot_reactivate(self):
        membership = self._seed("revoked")
        command = TransitionCommand(
            membership_id=membership.id,
            from_state="revoked",
            to_state="active",
            action="membership.activate",
            actor_type=ActorType.TENANT_ADMIN,
            actor_id="actor-1",
            reason_code="INVITATION_ACCEPTED",
            expected_version=membership.version,
            correlation_id="corr-1",
            idempotency_key="idem-reactivate",
        )
        with self.assertRaises(InvalidTransition):
            self.env.state_machine.transition(command)


if __name__ == "__main__":
    unittest.main()
