"""
MILE-2.3 tenant context switching and SDK contract unit tests.

Exit gate (BOPEN-P2-001 11.6): same-tenant and cross-tenant scenarios pass; old
tenant roles/scopes never appear in a new context; header tampering has no
authorization effect; SDK contract tests pass in both languages; revocation and
membership-state changes prevent issuance.

Covers INV-P2-007 to INV-P2-010 and scenarios P2-T020 to P2-T029.
"""

import json
import re
import unittest
from datetime import timedelta
from pathlib import Path

from bopen_sdk.context import (
    BopenError,
    ContextClient,
    SwitchContextRequest,
    TenantContext,
)
from kernel_core.membership import ActorType, Conflict, TransitionCommand
from platform_kernel.context_service import (
    ContextDenied,
    DeterministicTestSigner,
    SwitchContextCommand,
    TokenValidationError,
)
from tests.support.phase2_fixtures import (
    AUDIENCE,
    ISSUER,
    build_phase2_env,
    onboard_active_member,
)

TS_SDK_PATH = Path(__file__).resolve().parents[2] / "sdk" / "typescript" / "src" / "context.ts"


class ContextSwitchServiceTests(unittest.TestCase):
    def setUp(self):
        self.env = build_phase2_env()
        onboard_active_member(self.env, tenant_id="tnt_alpha", principal_id="usr_alice")
        self.session = self.env.session_for("usr_alice")

    def _switch(self, tenant_id="tnt_alpha", **overrides):
        payload = dict(
            session_id=self.session.session_id,
            tenant_id=tenant_id,
            idempotency_key=f"idem-{tenant_id}",
        )
        payload.update(overrides)
        return self.env.context_service.switch(SwitchContextCommand(**payload))

    # -- P2-T020 -----------------------------------------------------------------

    def test_P2_T020_switch_to_tenant_with_active_membership(self):
        issued = self._switch()
        self.assertEqual(issued.tenant_id, "tnt_alpha")
        self.assertTrue(issued.access_token)
        # D-P2-006 provisional 5-minute lifetime.
        self.assertEqual(issued.expires_at - issued.issued_at, timedelta(minutes=5))

        claims = self.env.validator.validate(issued.access_token)
        self.assertEqual(claims["sub"], "usr_alice")
        self.assertEqual(claims["tid"], "tnt_alpha")
        self.assertEqual(claims["mid"], issued.membership_id)
        self.assertEqual(claims["ctx"], issued.context_id)
        self.assertEqual(claims["sid"], self.session.session_id)

    def test_token_carries_no_personal_profile_data(self):
        """BOPEN-IDP-001 12.3: no email, name, raw group list, secret or assertion."""
        issued = self._switch()
        claims = self.env.validator.validate(issued.access_token)
        for prohibited in ("email", "name", "given_name", "family_name", "groups", "assertion"):
            self.assertNotIn(prohibited, claims)

    def test_audit_records_context_issue_without_the_token(self):
        issued = self._switch()
        blob = json.dumps(self.env.audit.logs, default=str)
        self.assertNotIn(issued.access_token, blob)
        self.assertTrue(self.env.audit.events_of_type("context.issued"))

    # -- P2-T021 / P2-T022 -------------------------------------------------------

    def test_P2_T021_switch_to_unauthorized_tenant_denies_generically(self):
        with self.assertRaises(ContextDenied) as ctx:
            self._switch(tenant_id="tnt_beta")
        self.assertEqual(str(ctx.exception), "Context switch denied")
        self.assertTrue(self.env.audit.events_of_type("context.switch_denied"))

    def test_P2_T021_unknown_tenant_is_indistinguishable_from_unauthorized(self):
        with self.assertRaises(ContextDenied) as unknown:
            self._switch(tenant_id="tnt_does_not_exist")
        with self.assertRaises(ContextDenied) as unauthorized:
            self._switch(tenant_id="tnt_beta")
        self.assertEqual(str(unknown.exception), str(unauthorized.exception))

    def test_P2_T022_header_body_tenant_mismatch_is_denied(self):
        with self.assertRaises(ContextDenied):
            self._switch(tenant_id="tnt_alpha", header_tenant_id="tnt_beta")

    def test_header_tampering_has_no_authorization_effect(self):
        """A matching header cannot grant access the membership does not confer."""
        with self.assertRaises(ContextDenied):
            self._switch(tenant_id="tnt_beta", header_tenant_id="tnt_beta")

    # -- P2-T023 -----------------------------------------------------------------

    def test_P2_T023_stale_expected_context_conflicts(self):
        self._switch()
        with self.assertRaises(Conflict):
            self._switch(expected_context_id="ctx_not_current", idempotency_key="idem-2")

    def test_previous_context_is_superseded_on_switch(self):
        first = self._switch()
        onboard_active_member(
            self.env, tenant_id="tnt_beta", principal_id="usr_alice",
            email="alice@beta.test", correlation_id="corr-beta",
        )
        second = self._switch(
            tenant_id="tnt_beta", expected_context_id=first.context_id, idempotency_key="idem-2",
        )
        self.assertTrue(self.env.sessions.is_superseded(first.context_id))
        self.assertFalse(self.env.sessions.is_superseded(second.context_id))
        self.assertTrue(self.env.audit.events_of_type("context.switched"))

    # -- P2-T024 -----------------------------------------------------------------

    def test_P2_T024_old_tenant_roles_are_never_carried_forward(self):
        """INV-P2-010: context switching never copies authorization data."""
        issued = self.env.invitation_engine.issue(
            tenant_id="tnt_beta", email="alice@beta.test", invited_by_principal_id="usr_owner",
            correlation_id="corr-beta", idempotency_key="issue-beta", requested_roles=("auditor",),
        )
        self.env.invitation_engine.accept(
            raw_token=issued.raw_token, tenant_id="tnt_beta", principal_id="usr_alice",
            correlation_id="corr-beta", idempotency_key="accept-beta",
        )

        first = self._switch(tenant_id="tnt_alpha")
        self.assertEqual(first.roles, ("member",))

        second = self._switch(
            tenant_id="tnt_beta", expected_context_id=first.context_id, idempotency_key="idem-2",
        )
        self.assertEqual(second.roles, ("auditor",))
        self.assertNotIn("member", second.roles)

        claims = self.env.validator.validate(second.access_token)
        self.assertEqual(claims["roles"], ["auditor"])
        self.assertEqual(claims["tid"], "tnt_beta")

    # -- P2-T025 to P2-T028 ------------------------------------------------------

    def test_P2_T025_token_missing_a_mandatory_claim_is_rejected(self):
        claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": "usr_alice"}
        token = self.env.signer.sign(claims)
        with self.assertRaises(TokenValidationError):
            self.env.validator.validate(token)

    def test_P2_T026_expired_session_denies_issuance(self):
        self.env.clock.advance(timedelta(hours=9))
        with self.assertRaises(ContextDenied):
            self._switch()

    def test_revoked_session_denies_issuance(self):
        self.session.revoked = True
        self.env.sessions.save_session(self.session)
        with self.assertRaises(ContextDenied):
            self._switch()

    def test_client_binding_mismatch_denies_issuance(self):
        with self.assertRaises(ContextDenied):
            self._switch(client_id="cli_other")

    def test_P2_T027_unknown_key_or_algorithm_is_rejected(self):
        issued = self._switch()

        foreign = DeterministicTestSigner(kid="attacker-kid", key=b"attacker-key")
        with self.assertRaises(TokenValidationError):
            self.env.validator.validate(foreign.sign({"iss": ISSUER}))

        # alg=none is never accepted.
        none_signer = DeterministicTestSigner(kid=self.env.signer.kid, algorithm="none")
        with self.assertRaises(TokenValidationError):
            self.env.validator.validate(none_signer.sign({"iss": ISSUER}))

        # A tampered payload fails signature verification.
        header, payload, signature = issued.access_token.split(".")
        with self.assertRaises(TokenValidationError):
            self.env.validator.validate(f"{header}.{payload[:-4]}AAAA.{signature}")

    def test_expired_token_is_rejected_beyond_clock_skew(self):
        issued = self._switch()
        self.env.clock.advance(timedelta(minutes=6, seconds=30))
        with self.assertRaises(TokenValidationError):
            self.env.validator.validate(issued.access_token)

    def test_issuer_and_audience_mismatch_are_rejected(self):
        for claim, value in (("iss", "https://evil.test"), ("aud", "https://evil.test")):
            with self.subTest(claim=claim):
                claims = {
                    "iss": ISSUER, "aud": AUDIENCE, "sub": "usr_alice", "tid": "tnt_alpha",
                    "mid": "mem_1", "roles": [], "scopes": [], "iat": 0, "exp": 9999999999,
                    "jti": "j", "sid": "s", "ctx": "c",
                }
                claims[claim] = value
                with self.assertRaises(TokenValidationError):
                    self.env.validator.validate(self.env.signer.sign(claims))

    def test_P2_T028_membership_revocation_denies_new_issuance(self):
        membership = self.env.memberships.find_active("tnt_alpha", "usr_alice")
        issued = self._switch()

        self.env.state_machine.transition(
            TransitionCommand(
                membership_id=membership.id, from_state="active", to_state="revoked",
                action="membership.revoke", actor_type=ActorType.SECURITY_CONTROL,
                actor_id="usr_security", reason_code="SECURITY_REVOCATION",
                expected_version=membership.version, correlation_id="corr-revoke",
                idempotency_key="idem-revoke",
            )
        )

        with self.assertRaises(ContextDenied):
            self._switch(idempotency_key="idem-after-revoke")

        affected = self.env.context_service.revoke_contexts_for_membership(
            membership.id, "corr-revoke", "SECURITY_REVOCATION"
        )
        self.assertIn(issued.context_id, affected)
        self.assertTrue(self.env.sessions.is_superseded(issued.context_id))

    def test_suspended_membership_denies_new_issuance(self):
        membership = self.env.memberships.find_active("tnt_alpha", "usr_alice")
        self.env.state_machine.transition(
            TransitionCommand(
                membership_id=membership.id, from_state="active", to_state="suspended",
                action="membership.suspend", actor_type=ActorType.TENANT_ADMIN,
                actor_id="usr_owner", reason_code="ADMIN_SUSPENSION",
                expected_version=membership.version, correlation_id="corr-suspend",
                idempotency_key="idem-suspend",
            )
        )
        with self.assertRaises(ContextDenied):
            self._switch(idempotency_key="idem-after-suspend")


class DelegatedContextTests(unittest.TestCase):
    """INV-P2-007 and INV-P2-016 through the context service."""

    def setUp(self):
        self.env = build_phase2_env()
        self.session = self.env.session_for("usr_support")

    def _grant(self):
        from kernel_core.delegation import GrantType

        grant = self.env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader",),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id="corr-1", case_reference="CASE-1",
        )
        self.env.delegation.approve(grant.grant_id, "usr_director", "corr-1")
        return self.env.delegation.activate(grant.grant_id, "usr_director", "corr-1")

    def test_delegated_context_carries_the_dgr_claim(self):
        grant = self._grant()
        issued = self.env.context_service.switch(
            SwitchContextCommand(
                session_id=self.session.session_id, tenant_id="tnt_alpha",
                idempotency_key="idem-delegated",
            )
        )
        self.assertEqual(issued.delegated_grant_id, grant.grant_id)
        claims = self.env.validator.validate(issued.access_token)
        self.assertEqual(claims["dgr"], grant.grant_id)
        self.assertEqual(claims["tid"], "tnt_alpha")
        self.assertEqual(claims["roles"], ["support_reader"])

    def test_no_grant_and_no_membership_denies(self):
        with self.assertRaises(ContextDenied):
            self.env.context_service.switch(
                SwitchContextCommand(
                    session_id=self.session.session_id, tenant_id="tnt_alpha",
                    idempotency_key="idem-none",
                )
            )

    def test_revoked_grant_denies_issuance_and_invalidates_contexts(self):
        grant = self._grant()
        issued = self.env.context_service.switch(
            SwitchContextCommand(
                session_id=self.session.session_id, tenant_id="tnt_alpha",
                idempotency_key="idem-1",
            )
        )
        self.env.delegation.revoke(grant.grant_id, "usr_security", "corr-revoke")

        with self.assertRaises(ContextDenied):
            self.env.context_service.switch(
                SwitchContextCommand(
                    session_id=self.session.session_id, tenant_id="tnt_alpha",
                    idempotency_key="idem-2",
                )
            )
        affected = self.env.context_service.revoke_contexts_for_grant(
            grant.grant_id, "corr-revoke", "GRANT_REVOKED"
        )
        self.assertIn(issued.context_id, affected)


class PythonSdkContractTests(unittest.TestCase):
    """P2-T029 (Python side). No network access: the transport is injected."""

    def setUp(self):
        self.calls = []
        self.response = (200, {
            "context_id": "ctx_new", "tenant_id": "tnt_beta", "membership_id": "mem_9",
            "expires_at": "2026-07-29T12:05:00+00:00", "access_token": "opaque.token.value",
            "delegated_grant_id": None,
        })

        def transport(method, url, headers, body):
            self.calls.append((method, url, headers, body))
            return self.response

        self.client = ContextClient(
            base_url="https://api.bopen.test/", auth_token="session-token",
            tenant_id="tnt_alpha", transport=transport,
        )

    def test_switch_sets_approved_headers_and_body(self):
        request = SwitchContextRequest(tenant_id="tnt_beta", idempotency_key="key-1")
        context = self.client.switch_tenant_context(request, correlation_id="corr-1")

        method, url, headers, body = self.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "https://api.bopen.test/v1/session/context:switch")
        self.assertEqual(headers["X-Tenant-ID"], "tnt_beta")
        self.assertEqual(headers["X-Correlation-ID"], "corr-1")
        self.assertEqual(headers["Idempotency-Key"], "key-1")
        self.assertEqual(headers["Authorization"], "Bearer session-token")
        self.assertEqual(body["tenant_id"], "tnt_beta")
        self.assertEqual(body["idempotency_key"], "key-1")
        self.assertIsInstance(context, TenantContext)

    def test_cached_context_is_replaced_only_after_success(self):
        self.response = (403, {"code": "CONTEXT_DENIED"})
        with self.assertRaises(BopenError) as ctx:
            self.client.switch_tenant_context(
                SwitchContextRequest(tenant_id="tnt_beta", idempotency_key="key-1")
            )
        self.assertEqual(ctx.exception.code, "CONTEXT_DENIED")
        self.assertEqual(self.client.tenant_id, "tnt_alpha")   # unchanged
        self.assertIsNone(self.client.context_id)

    def test_typed_error_codes_are_surfaced_by_status(self):
        for status, expected in ((400, "INVALID_REQUEST"), (401, "UNAUTHENTICATED"),
                                 (409, "CONFLICT"), (412, "STALE_VERSION"),
                                 (503, "DEPENDENCY_UNAVAILABLE")):
            with self.subTest(status=status):
                self.response = (status, {})
                with self.assertRaises(BopenError) as ctx:
                    self.client.switch_tenant_context(
                        SwitchContextRequest(tenant_id="tnt_beta", idempotency_key="k")
                    )
                self.assertEqual(ctx.exception.code, expected)

    def test_missing_required_inputs_are_rejected_before_transport(self):
        for request in (
            SwitchContextRequest(tenant_id="", idempotency_key="k"),
            SwitchContextRequest(tenant_id="tnt_beta", idempotency_key=""),
        ):
            with self.subTest(request=request):
                with self.assertRaises(BopenError):
                    self.client.switch_tenant_context(request)
        self.assertEqual(self.calls, [])

    def test_repr_never_leaks_the_token(self):
        context = self.client.switch_tenant_context(
            SwitchContextRequest(tenant_id="tnt_beta", idempotency_key="key-1")
        )
        self.assertNotIn("opaque.token.value", repr(context))
        self.assertIn("<redacted>", repr(context))

    def test_sdk_exposes_no_token_decoding(self):
        """BOPEN-P2-001 11.4: SDKs never decode tokens for authorization."""
        import bopen_sdk.context as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("b64decode", "jwt.decode", "urlsafe_b64decode"):
            self.assertNotIn(forbidden, source)


class TypeScriptSdkParityTests(unittest.TestCase):
    """
    P2-T029 (TypeScript side), static contract parity.

    This is a source-level contract check, not an execution test: no Node toolchain
    is provisioned in this repository baseline. Executing the TypeScript SDK is
    recorded as an open item for WP-P2-08.
    """

    def setUp(self):
        self.source = TS_SDK_PATH.read_text(encoding="utf-8")

    def test_frozen_request_and_response_shapes_are_declared(self):
        for field in ("tenantId", "expectedContextId", "idempotencyKey"):
            self.assertRegex(self.source, rf"\b{field}\b")
        for field in ("contextId", "tenantId", "membershipId", "expiresAt"):
            self.assertRegex(self.source, rf"\b{field}\b")

    def test_frozen_method_signature_is_declared(self):
        self.assertIn("switchTenantContext", self.source)
        self.assertIn("Promise<TenantContext>", self.source)

    def test_error_codes_match_the_python_sdk(self):
        from bopen_sdk.context import ERROR_CODES

        declared = set(re.findall(r"'([A-Z_]{4,})'", self.source))
        for code in ERROR_CODES:
            self.assertIn(code, declared, f"TypeScript SDK is missing error code {code}")

    def test_endpoint_path_matches_the_python_sdk(self):
        from bopen_sdk.context import CONTEXT_SWITCH_PATH

        self.assertIn(CONTEXT_SWITCH_PATH, self.source)

    def test_typescript_sdk_does_not_decode_tokens(self):
        for forbidden in ("atob(", "jwtDecode", "JSON.parse(atob"):
            self.assertNotIn(forbidden, self.source)


if __name__ == "__main__":
    unittest.main()
