"""
MILE-2.5 delegated cross-tenant access unit tests.

Exit gate (BOPEN-P2-001 13.6): no grant can be wildcarded across tenants; expiry and
revocation are deterministic; the delegated token carries `dgr` and tenant-bound
claims; a revoked grant fails context issuance; the maker cannot self-approve.

Covers INV-P2-015, INV-P2-016 and scenarios P2-T060 to P2-T065.
"""

import json
import unittest
from datetime import timedelta

from kernel_core.delegation import (
    DelegationDenied,
    GrantState,
    GrantType,
    InvalidRequest,
)
from tests.support.phase2_fixtures import build_phase2_env


class DelegatedAccessTests(unittest.TestCase):
    def setUp(self):
        self.env = build_phase2_env()
        self.service = self.env.delegation

    def _create(self, **overrides):
        payload = dict(
            grant_type=GrantType.SUPPORT,
            source_principal_id="usr_support",
            target_tenant_id="tnt_alpha",
            approved_roles=("support_reader",),
            approved_scopes=("tenant:read",),
            reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager",
            correlation_id="corr-1",
            case_reference="CASE-1234",
        )
        payload.update(overrides)
        return self.service.create(**payload)

    def _activate(self, grant, approver="usr_director"):
        self.service.approve(grant.grant_id, approver, "corr-1")
        return self.service.activate(grant.grant_id, approver, "corr-1")

    # -- P2-T060 -----------------------------------------------------------------

    def test_P2_T060_valid_support_grant_activates_within_exact_bounds(self):
        grant = self._activate(self._create())
        self.assertEqual(grant.state, GrantState.ACTIVE)
        self.assertEqual(grant.target_tenant_id, "tnt_alpha")
        self.assertEqual(grant.approved_scopes, ("tenant:read",))
        self.assertEqual(grant.expires_at - grant.starts_at, timedelta(hours=8))
        self.assertTrue(self.env.audit.events_of_type("delegation.activated"))

    # -- P2-T061 -----------------------------------------------------------------

    def test_P2_T061_wildcard_tenant_or_scope_is_denied(self):
        """INV-P2-015: no wildcard tenant and no wildcard scope."""
        for kwargs in (
            {"target_tenant_id": "*"},
            {"target_tenant_id": "tnt_*"},
            {"approved_scopes": ("*",)},
            {"approved_roles": ("all",)},
            {"approved_scopes": ("tenant:*",)},
        ):
            with self.subTest(**kwargs):
                with self.assertRaises(DelegationDenied):
                    self._create(**kwargs)

    def test_support_grant_requires_a_case_reference(self):
        with self.assertRaises(DelegationDenied):
            self._create(case_reference=None)

    def test_grant_duration_cannot_exceed_the_approved_maximum(self):
        with self.assertRaises(DelegationDenied):
            self._create(duration=timedelta(hours=9))       # D-P2-012 support max 8h
        with self.assertRaises(DelegationDenied):
            self._create(
                grant_type=GrantType.PARTNER, case_reference="CONTRACT-9",
                duration=timedelta(days=91),                 # D-P2-013 partner max
            )

    def test_empty_roles_or_scopes_are_rejected(self):
        with self.assertRaises(InvalidRequest):
            self._create(approved_roles=())
        with self.assertRaises(InvalidRequest):
            self._create(approved_scopes=())

    # -- P2-T062 -----------------------------------------------------------------

    def test_P2_T062_self_approval_is_denied(self):
        grant = self._create(created_by="usr_manager")
        with self.assertRaises(DelegationDenied):
            self.service.approve(grant.grant_id, "usr_manager", "corr-1")

    def test_activation_requires_prior_approval(self):
        grant = self._create()
        with self.assertRaises(DelegationDenied):
            self.service.activate(grant.grant_id, "usr_director", "corr-1")

    # -- P2-T063 / P2-T064 -------------------------------------------------------

    def test_P2_T063_expired_grant_cannot_be_resolved_for_issuance(self):
        grant = self._activate(self._create())
        self.assertIsNotNone(self.service.resolve_usable("usr_support", "tnt_alpha"))

        self.env.clock.advance(timedelta(hours=9))
        self.assertIsNone(self.service.resolve_usable("usr_support", "tnt_alpha"))

        expired = self.service.expire_due("corr-expire")
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0].state, GrantState.EXPIRED)
        self.assertTrue(self.env.audit.events_of_type("delegation.expired"))

    def test_expiry_is_idempotent_and_never_auto_renews(self):
        self._activate(self._create())
        self.env.clock.advance(timedelta(hours=9))
        self.service.expire_due("corr-expire")
        self.assertEqual(self.service.expire_due("corr-expire"), [])

    def test_P2_T064_revoked_grant_denies_future_issuance_immediately(self):
        """INV-P2-016 and D-P2-014 immediate new-issuance deny."""
        grant = self._activate(self._create())
        self.service.revoke(grant.grant_id, "usr_security", "corr-1")

        self.assertIsNone(self.service.resolve_usable("usr_support", "tnt_alpha"))
        revoked = self.env.grants.get(grant.grant_id)
        self.assertEqual(revoked.state, GrantState.REVOKED)
        self.assertEqual(revoked.revoked_by, "usr_security")
        self.assertIsNotNone(revoked.revoked_at)

    def test_revocation_is_idempotent(self):
        grant = self._activate(self._create())
        first = self.service.revoke(grant.grant_id, "usr_security", "corr-1")
        second = self.service.revoke(grant.grant_id, "usr_security", "corr-1")
        self.assertEqual(first.version, second.version)

    def test_grant_is_not_usable_before_it_starts(self):
        grant = self._activate(self._create())
        self.env.clock.set(grant.starts_at - timedelta(minutes=1))
        self.assertIsNone(self.service.resolve_usable("usr_support", "tnt_alpha"))

    def test_grant_is_tenant_specific(self):
        self._activate(self._create(target_tenant_id="tnt_alpha"))
        self.assertIsNone(self.service.resolve_usable("usr_support", "tnt_beta"))

    # -- P2-T065 -----------------------------------------------------------------

    def test_P2_T065_delegation_audit_includes_grant_id_and_excludes_tokens(self):
        grant = self._activate(self._create())
        events = self.env.audit.events_of_type("delegation.activated")
        self.assertTrue(events)
        self.assertEqual(events[0]["metadata"]["grant_id"], grant.grant_id)

        blob = json.dumps(self.env.audit.logs, default=str).lower()
        for prohibited in ("password", "bearer ", "assertion"):
            self.assertNotIn(prohibited, blob)


if __name__ == "__main__":
    unittest.main()
