"""
Phase 1 and Phase 2 producers validated against their own frozen JSON Schemas.

Work package: BOPEN-P35-001
Contracts covered here:
    contracts/schemas/invitation.json
    contracts/schemas/delegated-grant.json
    contracts/schemas/context-switch.json
    contracts/schemas/scim-event.json
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R2 (measured), R4 (adversarial)

WHY THIS FILE EXISTS

`tests/contracts/test_contract_schemas.py` opens the schema documents and asserts things
about them: that a `required` list contains a name, that `additionalProperties` is false.
Assertions of that shape passed at full green while Phase 3's `RateLimitDecision` violated
its own frozen schema, because a schema document is always consistent with itself. The only
question that matters — does the object the code actually produces satisfy the contract? —
was never asked of thirteen of the sixteen schemas.

Every case below runs the real producer, serializes what it returns, and hands the result to
`jsonschema.validate()`. Nothing here hand-builds a dict shaped to please the schema; that
would test the test. No database is required: every producer in scope is in-memory and driven
through `tests/support/phase2_fixtures.build_phase2_env`, which injects a fixed clock and a
counting identifier factory (BOPEN-P2-001 section 17).

WHY FOUR SCHEMAS AND NOT EIGHT

Four of the eight Phase 1/2 schemas have producers that do not conform, so no test for them
appears here. Their divergences are recorded in
`contracts/contract-conformance-baseline.json`, and a test asserting the current broken
behaviour would freeze the defect rather than expose it:

  - audit-event.json          `AuditDispatcher.dispatch` emits `reason_code`, which the schema
                              forbids under `additionalProperties: false`.
                              `AuditDispatcher.emit_lifecycle_event` emits a wholly different
                              Phase 2 envelope (`occurred_at`, `actor_principal_id`,
                              `subject_type`, `outcome`) that no frozen schema describes.
  - authorization-decision.json  `AuthorizationDecision` has no `policy_version` field, which
                              the schema requires. The identifier does not exist anywhere in
                              the codebase, so this is a missing decision, not a rename.
  - membership-transition.json   `TransitionReceipt` names the same concepts differently
                              (`from_state`/`to_state`/`effective_at` against
                              `previous_state`/`new_state`/`transition_timestamp`) and carries
                              fourteen fields the schema forbids. Its `membership_id` also
                              fails `format: uuid`, because `UuidIdentifierFactory` emits
                              prefixed identifiers (`mem_<uuid>`) in production as well as here.
  - membership-transition-matrix.json  Declares `$schema` but no `type` and no `properties`,
                              so it constrains nothing: `jsonschema.validate` accepts `42`,
                              `None` and `{}` against it. It is a pinned data document consumed
                              by `MembershipTransitionContract.load`, not a message shape, and
                              an instance test against it would report green while asserting
                              nothing. `MatrixIsNotAnInstanceSchemaTests` below pins that
                              finding so it cannot be mistaken for coverage.

A NOTE ON `format`

`jsonschema` enforces `format` only when a `FormatChecker` is supplied *and* the relevant
third-party validator is installed. `rfc3339-validator` is absent in this environment, so
`date-time` silently no-ops while `uuid` is live. The checker is passed regardless — it becomes
real if the dependency is ever added — and every timestamp assertion below parses the emitted
string explicitly, so the date-time claim is genuinely checked either way.

A NOTE ON SERIALISATION

Only one Phase 1/2 producer owns a serialisation method: `IssuedContext.public_response()`
(services/platform-kernel/python/platform_kernel/context_service.py:167). `Invitation`,
`DelegatedGrant` and `ScimEvent` are frozen dataclasses with no `to_dict()`, so this module
supplies `encode()`. That helper converts *types only* — enum to value, datetime to ISO-8601,
tuple to list — and derives its keys from `dataclasses.fields()`. It cannot rename, drop or
add a field, and `EncoderFidelityTests` proves it. That restriction is what makes these tests
meaningful: a permissive encoder could paper over exactly the drift being looked for.
"""

from __future__ import annotations

import dataclasses
import json
import sys
import unittest
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402

from kernel_core.delegation import GrantType  # noqa: E402
from platform_kernel.context_service import SwitchContextCommand  # noqa: E402
from platform_kernel.idp_bridge import (  # noqa: E402
    ConnectionStatus,
    DirectoryStatus,
    IdentityProviderConnection,
    Protocol_,
    SCIMDirectory,
    ScimEvent,
)
from tests.support.phase2_fixtures import build_phase2_env, onboard_active_member  # noqa: E402

SCHEMA_DIR = ROOT / "contracts" / "schemas"
CORRELATION = "corr-phase12-contract"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate(instance: Any, schema: dict) -> None:
    """Validate with a format checker attached. See the module docstring on `format`."""
    jsonschema.validate(
        instance=instance,
        schema=schema,
        format_checker=jsonschema.FormatChecker(),
    )


def jsonify(value: Any) -> Any:
    """Convert a Python value to its JSON form. Types only — never keys."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (tuple, list)):
        return [jsonify(item) for item in value]
    if isinstance(value, dict):
        return {key: jsonify(item) for key, item in value.items()}
    return value


def encode(instance: Any) -> dict:
    """
    Serialize a frozen dataclass using its own field names, unaltered.

    The producers in this module carry no `to_dict()`, so something has to bridge them to JSON.
    Deriving the key set from `dataclasses.fields()` is what keeps that bridge honest: a helper
    free to rename `from_state` to `previous_state` could make any producer appear to conform,
    and the drift these tests exist to catch is precisely drift in names and value domains.
    """
    return {field.name: jsonify(getattr(instance, field.name))
            for field in dataclasses.fields(instance)}


def assert_utc_timestamp(testcase: unittest.TestCase, value: str, field: str) -> None:
    """
    Parse a serialized timestamp, since the installed `jsonschema` cannot.

    The offset assertion carries the weight. An invitation expiry or a grant expiry written
    without a UTC offset is ambiguous by the server's offset, and both of those fields decide
    when access stops.
    """
    parsed = datetime.fromisoformat(value)
    testcase.assertIsNotNone(
        parsed.tzinfo,
        msg=f"{field} serialized without a UTC offset ({value!r}); the instant is ambiguous.",
    )


class EncoderFidelityTests(unittest.TestCase):
    """The encoder must not be able to rescue a non-conforming producer."""

    def test_encoder_emits_exactly_the_declared_field_names(self):
        """
        If `encode()` could add, drop or rename a key, every conformance verdict in this file
        would be a statement about the encoder rather than about the producer. Pinning the key
        set against `dataclasses.fields()` removes that degree of freedom.
        """
        env = build_phase2_env()
        issued = env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="fidelity@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="fidelity-issue",
        )
        invitation = issued.invitation
        self.assertEqual(
            set(encode(invitation)),
            {field.name for field in dataclasses.fields(invitation)},
            msg="encode() changed the producer's field set; conformance results would be fiction.",
        )

    def test_encoder_preserves_values_rather_than_normalising_them(self):
        """
        Type conversion is allowed; value laundering is not. A tuple must become the same list
        and an enum must become its own `.value`, or a producer emitting an out-of-enum state
        could still validate.
        """
        env = build_phase2_env()
        grant = env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader", "auditor"),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id=CORRELATION, case_reference="CASE-1",
        )
        encoded = encode(grant)
        self.assertEqual(encoded["approved_roles"], ["support_reader", "auditor"])
        self.assertEqual(encoded["grant_type"], GrantType.SUPPORT.value)
        self.assertEqual(encoded["state"], grant.state.value)


class InvitationInstanceTests(unittest.TestCase):
    """contracts/schemas/invitation.json against the real `InvitationEngine`."""

    def setUp(self):
        self.schema = load_schema("invitation.json")
        self.env = build_phase2_env()

    def _issue(self, email: str = "alice@acme.test", key: str = "inv-issue"):
        return self.env.invitation_engine.issue(
            tenant_id="tnt_alpha", email=email, invited_by_principal_id="usr_owner",
            correlation_id=CORRELATION, idempotency_key=key,
        )

    def test_issued_invitation_conforms(self):
        """The record as it first reaches storage — the shape every later state is derived from."""
        instance = encode(self._issue().invitation)
        validate(instance, self.schema)
        self.assertEqual(instance["state"], "invited")
        assert_utc_timestamp(self, instance["issued_at"], "issued_at")
        assert_utc_timestamp(self, instance["expires_at"], "expires_at")

    def test_issued_invitation_carries_a_digest_and_no_raw_token(self):
        """
        INV-P2-002: the raw token is returned exactly once and never persisted. The schema has
        no property that could hold it, and `additionalProperties: false` is what enforces that
        — so a producer that started emitting the token would fail `validate()` rather than
        quietly widen the blast radius of a database read.
        """
        issued = self._issue()
        instance = encode(issued.invitation)
        validate(instance, self.schema)
        self.assertNotIn(issued.raw_token, json.dumps(instance))
        self.assertEqual(instance["token_digest_scheme"], self.env.hasher.scheme)
        self.assertNotIn("token", set(instance) - {"token_digest", "token_digest_scheme"})

    def test_accepted_invitation_conforms(self):
        """
        Acceptance is the one transition that writes `principal_id` and `membership_id`, both
        declared nullable. A conforming record here is what proves the nullable branch and the
        populated branch are the same shape.
        """
        accepted = onboard_active_member(self.env)
        instance = encode(accepted.invitation)
        validate(instance, self.schema)
        self.assertEqual(instance["state"], "active")
        self.assertIsNotNone(instance["principal_id"])
        self.assertIsNotNone(instance["membership_id"])
        assert_utc_timestamp(self, instance["accepted_at"], "accepted_at")

    def test_declined_invitation_conforms(self):
        """`declined` is an Invitation state and not a Membership state; only this schema has it."""
        issued = self._issue(email="declined@acme.test", key="inv-decline")
        declined = self.env.invitation_engine.decline(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", correlation_id=CORRELATION,
        )
        instance = encode(declined)
        validate(instance, self.schema)
        self.assertEqual(instance["state"], "declined")
        assert_utc_timestamp(self, instance["declined_at"], "declined_at")

    def test_expired_invitation_conforms(self):
        """
        Expiry is driven by the injected clock rather than by a sleep, so this exercises the
        fourth and last `state` enum value without making the suite wall-clock dependent.
        """
        self._issue(email="expired@acme.test", key="inv-expire")
        self.env.clock.advance(timedelta(days=30))
        expired = self.env.invitation_engine.expire_due(correlation_id=CORRELATION)
        self.assertTrue(expired, "no invitation expired; the batch job did not run")
        for record in expired:
            instance = encode(record)
            validate(instance, self.schema)
            self.assertEqual(instance["state"], "expired")

    def test_every_state_in_the_schema_enum_is_reachable_from_the_engine(self):
        """
        A closed enum is only a contract if the code can reach all of it. An unreachable value
        means either dead schema surface or a missing transition, and both are worth knowing.
        """
        reachable = set()
        issued = self._issue(email="reach-a@acme.test", key="reach-a")
        reachable.add(encode(issued.invitation)["state"])
        reachable.add(encode(onboard_active_member(
            self.env, principal_id="usr_reach", email="reach-b@acme.test",
        ).invitation)["state"])
        declined = self.env.invitation_engine.decline(
            raw_token=issued.raw_token, tenant_id="tnt_alpha", correlation_id=CORRELATION,
        )
        reachable.add(encode(declined)["state"])
        self._issue(email="reach-c@acme.test", key="reach-c")
        self.env.clock.advance(timedelta(days=30))
        for record in self.env.invitation_engine.expire_due(correlation_id=CORRELATION):
            reachable.add(encode(record)["state"])

        self.assertEqual(reachable, set(self.schema["properties"]["state"]["enum"]))


class DelegatedGrantInstanceTests(unittest.TestCase):
    """contracts/schemas/delegated-grant.json against the real `DelegatedAccessService`."""

    def setUp(self):
        self.schema = load_schema("delegated-grant.json")
        self.env = build_phase2_env()

    def _create_support_grant(self, correlation_id: str = CORRELATION):
        return self.env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader",),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id=correlation_id, case_reference="CASE-77",
        )

    def test_created_grant_conforms(self):
        """A grant enters at `pending` with no approver; both nullable fields are unset here."""
        instance = encode(self._create_support_grant())
        validate(instance, self.schema)
        self.assertEqual(instance["state"], "pending")
        self.assertIsNone(instance["approved_by"])
        assert_utc_timestamp(self, instance["starts_at"], "starts_at")
        assert_utc_timestamp(self, instance["expires_at"], "expires_at")

    def test_partner_grant_conforms(self):
        """
        `grant_type` is a two-value enum and the two values carry different rules — a partner
        grant needs no case reference and gets a 90-day ceiling rather than 8 hours. Testing
        only the support branch would leave half the enum unexercised.
        """
        grant = self.env.delegation.create(
            grant_type=GrantType.PARTNER, source_principal_id="usr_partner",
            target_tenant_id="tnt_beta", approved_roles=("partner_reader",),
            approved_scopes=("tenant:read",), reason_code="PARTNER_CONTRACT",
            created_by="usr_manager", correlation_id=CORRELATION,
        )
        instance = encode(grant)
        validate(instance, self.schema)
        self.assertEqual(instance["grant_type"], "partner")
        self.assertIsNone(instance["case_reference"])

    def test_activated_grant_conforms_and_records_a_distinct_approver(self):
        """
        Separation of duties (P2-T062) lives in `created_by` != `approved_by`. Both are schema
        fields, so a conforming instance is also the evidence that the maker did not self-approve.
        """
        grant = self._create_support_grant()
        self.env.delegation.approve(grant.grant_id, "usr_director", CORRELATION)
        active = self.env.delegation.activate(grant.grant_id, "usr_director", CORRELATION)
        instance = encode(active)
        validate(instance, self.schema)
        self.assertEqual(instance["state"], "active")
        self.assertNotEqual(instance["approved_by"], instance["created_by"])

    def test_revoked_grant_conforms(self):
        """Revocation is the control that stops standing cross-tenant access; its record must be readable."""
        grant = self._create_support_grant()
        self.env.delegation.approve(grant.grant_id, "usr_director", CORRELATION)
        self.env.delegation.activate(grant.grant_id, "usr_director", CORRELATION)
        revoked = self.env.delegation.revoke(grant.grant_id, "usr_security", CORRELATION)
        instance = encode(revoked)
        validate(instance, self.schema)
        self.assertEqual(instance["state"], "revoked")
        self.assertEqual(instance["revoked_by"], "usr_security")
        assert_utc_timestamp(self, instance["revoked_at"], "revoked_at")

    def test_expired_grant_conforms(self):
        """Expiry is automatic and never auto-renews; it is the fourth and last `state` value."""
        self._create_support_grant()
        self.env.clock.advance(timedelta(hours=9))
        expired = self.env.delegation.expire_due(correlation_id=CORRELATION)
        self.assertTrue(expired, "no grant expired; the expiry sweep did not run")
        for record in expired:
            instance = encode(record)
            validate(instance, self.schema)
            self.assertEqual(instance["state"], "expired")

    def test_no_conforming_grant_can_carry_a_wildcard_tenant_or_scope(self):
        """
        INV-P2-015 forbids wildcard tenants and scopes. The schema cannot express that, so the
        service refuses to construct such a grant at all — meaning there is no instance to
        validate. This asserts the refusal, so the absence is a control rather than a gap.
        """
        from kernel_core.delegation import DelegationDenied

        for tenant, roles, scopes in (
            ("*", ("support_reader",), ("tenant:read",)),
            ("tnt_alpha", ("*",), ("tenant:read",)),
            ("tnt_alpha", ("support_reader",), ("*",)),
        ):
            with self.assertRaises(DelegationDenied):
                self.env.delegation.create(
                    grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
                    target_tenant_id=tenant, approved_roles=roles, approved_scopes=scopes,
                    reason_code="SUPPORT_INVESTIGATION", created_by="usr_manager",
                    correlation_id=CORRELATION, case_reference="CASE-77",
                )


class ContextSwitchResponseInstanceTests(unittest.TestCase):
    """
    contracts/schemas/context-switch.json against `IssuedContext.public_response()`.

    Only the `response` half is covered. The `request` half has no producer: there is no HTTP
    route for `POST /v1/session/context:switch` in `platform_kernel.api`, and
    `SwitchContextCommand` is a service-layer command carrying `session_id`, `header_tenant_id`
    and `client_id` — three transport selectors the request schema forbids under
    `additionalProperties: false`. Projecting the command down to the three wire fields would be
    inventing the missing serialiser inside the test. `RequestHalfHasNoProducerTests` records
    the absence instead.
    """

    def setUp(self):
        self.schema = load_schema("context-switch.json")
        self.response_schema = self.schema["properties"]["response"]
        self.env = build_phase2_env()
        self.accepted = onboard_active_member(self.env)

    def test_issued_context_response_conforms(self):
        """
        `public_response()` is the only serialisation method any Phase 1/2 producer owns, and it
        names this schema in its docstring. That claim was never checked until now.
        """
        session = self.env.session_for("usr_alice")
        issued = self.env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha",
            idempotency_key="ctx-switch-1", header_tenant_id="tnt_alpha", client_id="cli_test",
        ))
        instance = issued.public_response()
        validate(instance, self.response_schema)
        self.assertEqual(instance["membership_id"], self.accepted.membership.id)
        self.assertIsNone(instance["delegated_grant_id"])
        assert_utc_timestamp(self, instance["expires_at"], "expires_at")

    def test_response_omits_every_internal_field_the_context_holds(self):
        """
        `IssuedContext` carries `principal_id`, `session_id`, `roles`, `scopes` and `issued_at`
        that the response schema has no home for. `additionalProperties: false` is what stops a
        future edit from returning the role and scope set to the caller, so the check that it
        holds is worth making explicit rather than leaving implied by a passing validate().
        """
        session = self.env.session_for("usr_alice")
        issued = self.env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha", idempotency_key="ctx-switch-2",
        ))
        instance = issued.public_response()
        validate(instance, self.response_schema)
        leaked = {"principal_id", "session_id", "roles", "scopes", "issued_at"} & set(instance)
        self.assertEqual(leaked, set(), msg=f"internal context state reached the response: {leaked}")

    def test_delegated_context_response_conforms(self):
        """
        `delegated_grant_id` is populated on exactly one path — a principal with no membership
        in the target tenant reaching it through an active grant. The nullable field is only
        really tested on the branch that fills it.
        """
        grant = self.env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader",),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id=CORRELATION, case_reference="CASE-77",
        )
        self.env.delegation.approve(grant.grant_id, "usr_director", CORRELATION)
        self.env.delegation.activate(grant.grant_id, "usr_director", CORRELATION)

        session = self.env.session_for("usr_support")
        issued = self.env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha", idempotency_key="ctx-delegated",
        ))
        instance = issued.public_response()
        validate(instance, self.response_schema)
        self.assertEqual(instance["delegated_grant_id"], grant.grant_id)

    def test_response_conforms_inside_the_whole_envelope(self):
        """
        The file is one document with `request` and `response` beneath it, and the root also
        sets `additionalProperties: false`. Validating the sub-schema alone would never notice
        a producer that wrapped its output under a differently named key.
        """
        session = self.env.session_for("usr_alice")
        issued = self.env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha", idempotency_key="ctx-envelope",
        ))
        validate({"response": issued.public_response()}, self.schema)


class RequestHalfHasNoProducerTests(unittest.TestCase):
    """The absence of a request producer, recorded as a check rather than as prose."""

    def test_switch_command_is_not_the_wire_request(self):
        """
        `SwitchContextCommand` is documented as "Request per contracts/schemas/context-switch.json"
        (context_service.py:306), and it is not. It carries three fields the request schema
        forbids. Asserting the mismatch here means the docstring's claim cannot be quietly
        assumed true, and the test flips to a failure the moment a real serialiser appears —
        which is when this file should gain a positive case instead.
        """
        request_schema = load_schema("context-switch.json")["properties"]["request"]
        command = SwitchContextCommand(
            session_id="sid_1", tenant_id="tnt_alpha", idempotency_key="k-1",
            header_tenant_id="tnt_alpha", client_id="cli_test",
        )
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(encode(command), request_schema)
        self.assertEqual(caught.exception.validator, "additionalProperties")
        self.assertEqual(
            {f.name for f in dataclasses.fields(command)} - set(request_schema["properties"]),
            {"session_id", "header_tenant_id", "client_id"},
        )


class ScimEventInstanceTests(unittest.TestCase):
    """
    contracts/schemas/scim-event.json against `platform_kernel.idp_bridge.ScimEvent`.

    `ScimEvent` is an ingress type: nothing in `packages/` or `services/` constructs one, because
    the bridge performs no network or protocol operation yet and the broker adapter is static.
    The instances here are therefore synthetic by necessity — but they are the same instances
    `IdpBridge.handle_scim_event` accepts, and the last two cases push them through it so that
    schema conformance and actual acceptance are checked against each other rather than in
    isolation.
    """

    def setUp(self):
        self.schema = load_schema("scim-event.json")
        self.env = build_phase2_env()
        self.env.identity_store.directories["dir_1"] = SCIMDirectory(
            directory_id="dir_1", tenant_id="tnt_alpha",
            broker_directory_ref="broker-ref-1", status=DirectoryStatus.ACTIVE,
        )
        self.env.identity_store.connections["con_saml"] = IdentityProviderConnection(
            connection_id="con_saml", tenant_id="tnt_alpha", protocol=Protocol_.SAML,
            issuer="https://idp.acme.test/saml", broker_connection_ref="broker-ref-1",
            status=ConnectionStatus.ACTIVE, created_by="usr_owner",
        )

    def _event(self, **overrides) -> ScimEvent:
        base = dict(
            event_id="evt-scim-1", event_type="user.created", directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="User", resource_id="scim-res-1",
            observed_at=self.env.clock.now(), sequence=1,
        )
        base.update(overrides)
        return ScimEvent(**base)

    def test_fully_populated_user_event_conforms(self):
        """Every optional field set at once — the widest instance the type can produce."""
        instance = encode(self._event(
            external_id="ext-1", user_name="bob@acme.test", email_normalized="bob@acme.test",
            display_name="Bob", active=True, groups=("grp-eng", "grp-sales"),
        ))
        validate(instance, self.schema)
        self.assertEqual(instance["groups"], ["grp-eng", "grp-sales"])
        assert_utc_timestamp(self, instance["observed_at"], "observed_at")

    def test_minimal_event_conforms_with_every_optional_field_null(self):
        """
        Seven of the fourteen properties are nullable, and a directory that sends none of them
        is the normal case for a deprovision. If the null branch did not conform, the contract
        would only hold for the richest payloads.
        """
        instance = encode(self._event())
        validate(instance, self.schema)
        for nullable in ("external_id", "user_name", "email_normalized", "display_name", "active"):
            self.assertIsNone(instance[nullable])
        self.assertEqual(instance["groups"], [])

    def test_every_event_type_and_resource_type_in_the_enums_conforms(self):
        """
        Both enums are closed and the bridge dispatches on `event_type`, so an unreachable or
        non-conforming value would be a routing hole rather than a cosmetic one.
        """
        for index, event_type in enumerate(self.schema["properties"]["event_type"]["enum"]):
            resource_type = "Group" if event_type == "group.changed" else "User"
            instance = encode(self._event(
                event_id=f"evt-{index}", event_type=event_type, resource_type=resource_type,
            ))
            validate(instance, self.schema)
            self.assertEqual(instance["event_type"], event_type)

        self.assertEqual(
            set(self.schema["properties"]["resource_type"]["enum"]), {"User", "Group"},
        )

    def test_a_conforming_event_is_accepted_by_the_bridge(self):
        """
        Conformance is only worth something if the conforming instance is the one the code
        takes. This validates first and then provisions from the same object, so the schema and
        the handler cannot drift apart without one of the two assertions failing.
        """
        event = self._event(external_id="ext-1", user_name="bob@acme.test")
        validate(encode(event), self.schema)

        result = self.env.idp_bridge.handle_scim_event(event, CORRELATION)
        membership = self.env.memberships.get(result["membership_id"])
        self.assertEqual(membership.state.value, "active")

    def test_a_conforming_deprovision_event_is_accepted_by_the_bridge(self):
        """
        `active: false` plus `user.deprovisioned` is the leaver control. Both the provision and
        the deprovision instance must conform, or half the lifecycle would be uncontracted.
        """
        created = self._event(external_id="ext-2", resource_id="scim-res-2", sequence=1)
        validate(encode(created), self.schema)
        provisioned = self.env.idp_bridge.handle_scim_event(created, CORRELATION)

        deprovision = self._event(
            event_id="evt-deprov", event_type="user.deprovisioned",
            resource_id="scim-res-2", active=False, sequence=9,
        )
        validate(encode(deprovision), self.schema)
        self.env.idp_bridge.handle_scim_event(deprovision, CORRELATION)

        membership = self.env.memberships.get(provisioned["membership_id"])
        self.assertNotEqual(membership.state.value, "active")

    def test_a_bopen_principal_id_is_never_a_conforming_resource_id(self):
        """
        The schema says `resource_id` is a broker reference and "never a bOPEN Principal ID".
        That is a semantic rule no JSON Schema keyword can express, so the check has to be made
        against the produced instance: the bridge mints its own principal and it must not be
        the value the directory supplied.
        """
        event = self._event(external_id="ext-3", resource_id="scim-res-3")
        validate(encode(event), self.schema)
        result = self.env.idp_bridge.handle_scim_event(event, CORRELATION)
        self.assertNotEqual(result["principal_id"], event.resource_id)


class ValidationIsNotVacuousTests(unittest.TestCase):
    """
    Proof that the four passing schemas actually constrain something.

    `membership-transition-matrix.json` in this same directory declares `$schema` and accepts
    `42`. A green instance test against a schema like that asserts nothing at all, and nothing
    in a pass count distinguishes the two cases. These are the adversarial cases required by
    BOPEN-GOV-EBIV-001 R4: each takes a conforming instance, breaks it in the one way the schema
    is supposed to catch, and requires a rejection.
    """

    def setUp(self):
        self.env = build_phase2_env()

    def _conforming_invitation(self) -> dict:
        return encode(self.env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="vacuity@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="vacuity",
        ).invitation)

    def test_a_missing_required_property_is_rejected(self):
        schema = load_schema("invitation.json")
        instance = self._conforming_invitation()
        validate(instance, schema)
        del instance["token_digest"]
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(instance, schema)
        self.assertEqual(caught.exception.validator, "required")

    def test_an_undeclared_property_is_rejected(self):
        """The exact class of defect `AuditDispatcher.dispatch` exhibits, caught here."""
        schema = load_schema("invitation.json")
        instance = self._conforming_invitation()
        instance["raw_token"] = "raw-invitation-token-0001"
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(instance, schema)
        self.assertEqual(caught.exception.validator, "additionalProperties")

    def test_an_out_of_enum_state_is_rejected(self):
        schema = load_schema("delegated-grant.json")
        grant = self.env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader",),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id=CORRELATION, case_reference="CASE-77",
        )
        instance = encode(grant)
        validate(instance, schema)
        instance["state"] = "suspended"
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(instance, schema)
        self.assertEqual(caught.exception.validator, "enum")

    def test_an_empty_scope_list_is_rejected(self):
        """`minItems: 1` on `approved_scopes` is the schema's least-privilege floor."""
        schema = load_schema("delegated-grant.json")
        grant = self.env.delegation.create(
            grant_type=GrantType.PARTNER, source_principal_id="usr_partner",
            target_tenant_id="tnt_beta", approved_roles=("partner_reader",),
            approved_scopes=("tenant:read",), reason_code="PARTNER_CONTRACT",
            created_by="usr_manager", correlation_id=CORRELATION,
        )
        instance = encode(grant)
        instance["approved_scopes"] = []
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(instance, schema)
        self.assertEqual(caught.exception.validator, "minItems")

    def test_a_leaked_access_token_field_is_rejected_by_the_scim_contract(self):
        """
        The scim-event schema exists partly to keep bearer tokens and raw broker payloads out of
        the ingress record. `additionalProperties: false` is the mechanism; this shows it bites.
        """
        schema = load_schema("scim-event.json")
        instance = encode(ScimEvent(
            event_id="evt-leak", event_type="user.created", directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="User", resource_id="scim-res-9",
            observed_at=self.env.clock.now(),
        ))
        validate(instance, schema)
        instance["bearer_token"] = "ey.leaked.payload"
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(instance, schema)
        self.assertEqual(caught.exception.validator, "additionalProperties")

    def test_the_context_response_rejects_an_unknown_key(self):
        schema = load_schema("context-switch.json")["properties"]["response"]
        onboard_active_member(self.env)
        session = self.env.session_for("usr_alice")
        issued = self.env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha", idempotency_key="vacuity-ctx",
        ))
        instance = issued.public_response()
        validate(instance, schema)
        instance["roles"] = ["owner"]
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(instance, schema)
        self.assertEqual(caught.exception.validator, "additionalProperties")


class MatrixIsNotAnInstanceSchemaTests(unittest.TestCase):
    """
    `membership-transition-matrix.json` is a data document, not a message schema.

    It sits in `contracts/schemas/` beside sixteen real schemas and declares `$schema`, which
    invites the assumption that an instance test against it would mean something. It would not:
    with no `type` and no `properties`, it constrains nothing, and `jsonschema.validate` accepts
    any instance at all. That is a strictly worse outcome than no test, because it reports green.

    These tests pin the finding so the file's absence from the conformance-covered set reads as
    a deliberate conclusion rather than an oversight, and so that adding real constraints to the
    document later fails here and prompts a proper instance test.

    These cases deliberately do NOT go through this module's `validate()` helper.
    `tools/check_contract_conformance.py` measures coverage by wrapping the module-level
    `jsonschema.validate` and recording every schema handed to it, so calling it here would
    report this file as instance-validated and invite its debt entry to be struck — on the
    strength of a call that asserts nothing. A local `Draft202012Validator` reaches the same
    conclusion without lying to the instrument. Do not "simplify" these back to `validate()`.
    """

    def test_the_matrix_declares_no_constraining_keywords(self):
        matrix = load_schema("membership-transition-matrix.json")
        self.assertIn("$schema", matrix)
        self.assertNotIn("type", matrix)
        self.assertNotIn("properties", matrix)

    def test_the_matrix_accepts_any_instance_and_so_cannot_be_a_contract(self):
        matrix = load_schema("membership-transition-matrix.json")
        checker = jsonschema.Draft202012Validator(matrix)
        for absurd in ({}, {"unrelated": True}, "a string", 42, None, []):
            self.assertEqual(
                list(checker.iter_errors(absurd)), [],
                msg=("the matrix rejected something, so it now constrains instances and "
                     "deserves a real conformance test rather than this finding"),
            )

    def test_the_matrix_is_consumed_as_a_document_by_the_transition_contract(self):
        """
        What the file is actually for: `MembershipTransitionContract.load` reads it and pins the
        allowed transition set. That loader — not `jsonschema` — is what validates its content,
        and it is already covered by tests/unit/test_membership_state_machine.py.
        """
        contract = build_phase2_env().contract
        matrix = load_schema("membership-transition-matrix.json")
        self.assertEqual(contract.contract_version, matrix["contract_version"])
        self.assertEqual(set(contract.states), set(matrix["states"]))
        self.assertEqual(
            set(contract.allowed_pairs()),
            {(t["from"], t["to"]) for t in matrix["transitions"]},
        )


if __name__ == "__main__":
    unittest.main()
