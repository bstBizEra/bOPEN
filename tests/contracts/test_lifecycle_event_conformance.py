"""
The Phase 2 lifecycle audit envelope validated against the schema written to describe it.

Work package: BOPEN-P35-001
Contract covered here:
    contracts/schemas/lifecycle-event.json
Producer under test:
    kernel_core.audit.AuditDispatcher.emit_lifecycle_event (audit.py:120)
Admissibility: BOPEN-GOV-EBIV-001 R1 (executed), R2 (measured), R4 (adversarial)

WHY THIS FILE EXISTS

`AuditDispatcher.emit_lifecycle_event` is the audit spine of all five Phase 2 modules —
invitation, membership, identity/SCIM, context switching and delegation. Until
`contracts/schemas/lifecycle-event.json` was written it had no schema at all. The envelope it
emits was being checked against `audit-event.json`, which describes a different producer
(`AuditDispatcher.dispatch`, audit.py:70) and rejects the lifecycle envelope with seven errors.
That mismatch was recorded in `contracts/contract-conformance-baseline.json` as a producer
defect. It was not one: the producer is coherent and every one of its eight call sites emits
the identical thirteen-key object. What was missing was a contract, so a contract was written
from the producer outward rather than the producer bent toward a foreign contract.

The schema was authored against observed output, not against intent. Where the producer is
loose — `subject_type` is checked by nobody, `reason_code` is drawn from three unrelated
namespaces, `metadata` values are `Any` — the schema says so in its `description` instead of
tightening until a correct producer fails. That failure mode is the exact defect this exercise
exists to remove, and reproducing it in a new file would be worse than leaving the gap.

TWO AUDIT ENVELOPES, TWO VOCABULARIES

`audit-event.json` spells the result of an event `status`, in {SUCCESS, DENIED, ERROR}. This
envelope spells it `outcome`, in {success, deny, failure}. Same idea, different words, both
live. `audit-event.json` is frozen and its producer is in the authorization path, so nothing
here changes it; `TwoAuditEnvelopesTests` below pins the divergence as an executable fact so it
cannot quietly become three vocabularies. The recommendation, argued in the work-package
report rather than decided here, is that `outcome` is the one to keep.

WHAT IS COVERED

Every one of the twenty-five event types in `PHASE2_EVENT_TYPES` is driven through its real
service and validated. Nothing below hand-builds a dict shaped to please the schema — each
instance is the object `emit_lifecycle_event` returned and appended to `AuditDispatcher.logs`,
reached by calling the same public methods production calls. No database: every producer in
scope is in-memory and driven through `tests/support/phase2_fixtures.build_phase2_env`, which
injects a fixed clock and a counting identifier factory (BOPEN-P2-001 section 17).

A NOTE ON `format`

`jsonschema` enforces `format` only when a `FormatChecker` is supplied *and* the relevant
third-party validator is installed. `rfc3339-validator` is absent in this environment, so
`date-time` silently no-ops while `uuid` is live. The checker is passed regardless — it becomes
real if the dependency is ever added — and `occurred_at` is parsed explicitly below, so the
UTC-offset claim is genuinely checked either way.
"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT))

import jsonschema  # noqa: E402

from kernel_core.audit import (  # noqa: E402
    PHASE2_EVENT_TYPES,
    PROHIBITED_METADATA_KEYS,
    AuditContractError,
    AuditDispatcher,
)
from kernel_core.delegation import DelegationDenied, GrantType  # noqa: E402
from kernel_core.membership import (  # noqa: E402
    ActorType,
    KernelError,
    TransitionCommand,
)
from platform_kernel.context_service import SwitchContextCommand  # noqa: E402
from platform_kernel.idp_bridge import (  # noqa: E402
    ConnectionStatus,
    DirectoryStatus,
    GroupRoleMapping,
    IdentityProviderConnection,
    NormalizedAuthResult,
    Protocol_,
    SCIMDirectory,
    ScimEvent,
)
from tests.support.phase2_fixtures import build_phase2_env, onboard_active_member  # noqa: E402

SCHEMA_DIR = ROOT / "contracts" / "schemas"
CORRELATION = "corr-lifecycle-contract"

SAML_ISSUER = "https://idp.acme.test/saml"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def validate(instance: Any, schema: dict) -> None:
    """Validate with a format checker attached. See the module docstring on `format`."""
    jsonschema.validate(
        instance=instance,
        schema=schema,
        format_checker=jsonschema.FormatChecker(),
    )


def lifecycle_events(dispatcher: AuditDispatcher) -> List[Dict[str, Any]]:
    """
    Separate the lifecycle envelope from the authorization envelope in one shared log.

    `AuditDispatcher.logs` is a single list holding output from both `dispatch` and
    `emit_lifecycle_event`, and the two shapes are structurally different documents. Splitting
    on `occurred_at` — a key only the lifecycle envelope has — is what keeps this file from
    accidentally validating an authorization event against the wrong contract and reporting a
    pass. `TwoAuditEnvelopesTests` proves the two are in fact disjoint on that key.
    """
    return [event for event in dispatcher.logs if "occurred_at" in event]


class LifecycleEventDriver:
    """
    Drives every Phase 2 service that emits a lifecycle event, through its public API.

    The alternative — calling `emit_lifecycle_event` directly with arguments chosen by the test
    — would validate the dispatcher against the schema while leaving the interesting question
    unanswered. What the schema has to survive is the *callers*: eight independent call sites
    passing sentinel actors like `anonymous` and `expiry_scheduler`, tenant `unknown` on
    pre-resolution denials, and metadata maps of five different value types. Those are the
    values a contract written from a single happy path would fail on.
    """

    def __init__(self) -> None:
        self.env = build_phase2_env()
        self.env.identity_store.connections["con_saml"] = IdentityProviderConnection(
            connection_id="con_saml", tenant_id="tnt_alpha", protocol=Protocol_.SAML,
            issuer=SAML_ISSUER, broker_connection_ref="broker-ref-1",
            status=ConnectionStatus.ACTIVE, created_by="usr_owner",
        )
        self.env.identity_store.connections["con_oidc"] = IdentityProviderConnection(
            connection_id="con_oidc", tenant_id="tnt_alpha", protocol=Protocol_.OIDC,
            issuer="https://idp.acme.test/oidc", broker_connection_ref="broker-ref-1",
            status=ConnectionStatus.VERIFIED, created_by="usr_owner",
        )
        self.env.identity_store.directories["dir_1"] = SCIMDirectory(
            directory_id="dir_1", tenant_id="tnt_alpha",
            broker_directory_ref="broker-ref-1", status=DirectoryStatus.ACTIVE,
        )
        self.env.identity_store.mappings.append(GroupRoleMapping(
            directory_id="dir_1", group_external_id="grp-eng",
            mapping_policy_version="v1", target_role="member",
        ))

    # -- helpers -----------------------------------------------------------------

    @staticmethod
    def _denied(callable_, *exceptions):
        """Run a path expected to deny. The denial audit event is the point, not the raise."""
        try:
            callable_()
        except exceptions:
            return
        raise AssertionError(f"{callable_} was expected to deny and did not")

    def events(self) -> List[Dict[str, Any]]:
        return lifecycle_events(self.env.audit)

    def events_of(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self.events() if e["event_type"] == event_type]

    # -- catalogue ---------------------------------------------------------------

    def drive_invitations_and_membership(self) -> None:
        env = self.env
        accepted = onboard_active_member(env)          # issued + accepted + transitioned
        self.accepted = accepted

        to_decline = env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="declined@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="lc-decline",
        )
        env.invitation_engine.decline(
            raw_token=to_decline.raw_token, tenant_id="tnt_alpha", correlation_id=CORRELATION,
        )

        self._denied(
            lambda: env.invitation_engine.accept(
                raw_token="not-a-real-token", tenant_id="tnt_alpha", principal_id="usr_nobody",
                correlation_id=CORRELATION, idempotency_key="lc-bad-token",
            ),
            KernelError,
        )                                              # invitation.validation_failed

        # A membership transition denied before any tenant is resolved: the path that emits
        # tenant_id="unknown" and subject_id straight from the command.
        self._denied(
            lambda: env.state_machine.transition(TransitionCommand(
                membership_id=accepted.membership.id, from_state="active",
                to_state="not_a_state", action="suspend",
                actor_type=ActorType.TENANT_ADMIN, actor_id="usr_owner",
                reason_code="POLICY_VIOLATION", expected_version=accepted.membership.version,
                correlation_id=CORRELATION, idempotency_key="lc-bad-transition",
            )),
            KernelError,
        )                                              # membership.transition_denied

    def drive_identity(self) -> None:
        env = self.env
        env.idp_bridge.verify_connection("con_oidc", "usr_security", CORRELATION)

        env.idp_bridge.link_identity(
            connection_id="con_saml", issuer=SAML_ISSUER, subject="saml-subject-alice",
            principal_id="usr_alice", correlation_id=CORRELATION, link_challenge_accepted=True,
        )
        transaction = env.idp_bridge.begin_sso("con_saml", CORRELATION)
        env.idp_bridge.complete_sso(
            NormalizedAuthResult(
                connection_id="con_saml", protocol=Protocol_.SAML, issuer=SAML_ISSUER,
                subject="saml-subject-alice", state=transaction.state,
                assertion_id="assertion-lc-1", nonce=transaction.nonce,
            ),
            CORRELATION,
        )
        self._denied(
            lambda: env.idp_bridge.complete_sso(
                NormalizedAuthResult(
                    connection_id="con_saml", protocol=Protocol_.SAML, issuer=SAML_ISSUER,
                    subject="saml-subject-alice", state="forged-state",
                    assertion_id="assertion-lc-2", nonce=transaction.nonce,
                ),
                CORRELATION,
            ),
            KernelError,
        )                                              # identity.authentication_denied
        self._denied(
            lambda: env.idp_bridge.link_identity(
                connection_id="con_saml", issuer="https://wrong.issuer.test/saml",
                subject="saml-subject-mallory", principal_id="usr_alice",
                correlation_id=CORRELATION, link_challenge_accepted=True,
            ),
            KernelError,
        )                                              # identity.link_denied

    def drive_scim(self) -> None:
        env = self.env
        env.idp_bridge.handle_scim_event(ScimEvent(
            event_id="lc-scim-1", event_type="user.created", directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="User", resource_id="res-bob",
            observed_at=env.clock.now(), external_id="ext-bob",
            user_name="bob@acme.test", sequence=1,
        ), CORRELATION)
        env.idp_bridge.handle_scim_event(ScimEvent(
            event_id="lc-scim-2", event_type="user.updated", directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="User", resource_id="res-bob",
            observed_at=env.clock.now(), external_id="ext-bob", active=True, sequence=2,
        ), CORRELATION)
        env.idp_bridge.handle_scim_event(ScimEvent(
            event_id="lc-scim-3", event_type="group.changed", directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="Group", resource_id="grp-eng",
            observed_at=env.clock.now(), groups=("grp-eng", "grp-unmapped"), sequence=3,
        ), CORRELATION)                                # scim.group_mapping_applied
        env.idp_bridge.handle_scim_event(ScimEvent(
            event_id="lc-scim-4", event_type="user.deprovisioned", directory_id="dir_1",
            tenant_id="tnt_alpha", resource_type="User", resource_id="res-bob",
            observed_at=env.clock.now(), active=False, sequence=4,
        ), CORRELATION)
        self._denied(
            lambda: env.idp_bridge.handle_scim_event(ScimEvent(
                event_id="lc-scim-5", event_type="user.created", directory_id="dir_1",
                tenant_id="tnt_beta", resource_type="User", resource_id="res-x",
                observed_at=env.clock.now(), sequence=1,
            ), CORRELATION),
            KernelError,
        )                                              # scim.event_denied

    def drive_contexts(self) -> None:
        env = self.env
        session = env.session_for("usr_alice")
        env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha", idempotency_key="lc-ctx-1",
        ))                                             # context.issued
        env.context_service.switch(SwitchContextCommand(
            session_id=session.session_id, tenant_id="tnt_alpha", idempotency_key="lc-ctx-2",
        ))                                             # context.switched
        self._denied(
            lambda: env.context_service.switch(SwitchContextCommand(
                session_id=session.session_id, tenant_id="tnt_beta",
                idempotency_key="lc-ctx-3",
            )),
            KernelError,
        )                                              # context.switch_denied
        revoked = env.context_service.revoke_contexts_for_membership(
            self.accepted.membership.id, CORRELATION, "MEMBERSHIP_SUSPENDED",
        )                                              # context.revoked
        assert revoked, "no context was revoked; context.revoked would go unexercised"

    def drive_delegation(self) -> None:
        env = self.env
        grant = env.delegation.create(
            grant_type=GrantType.SUPPORT, source_principal_id="usr_support",
            target_tenant_id="tnt_alpha", approved_roles=("support_reader",),
            approved_scopes=("tenant:read",), reason_code="SUPPORT_INVESTIGATION",
            created_by="usr_manager", correlation_id=CORRELATION, case_reference="CASE-LC",
        )                                              # delegation.created / success
        self._denied(
            lambda: env.delegation.approve(grant.grant_id, "usr_manager", CORRELATION),
            DelegationDenied,
        )                                              # delegation.created / deny
        env.delegation.approve(grant.grant_id, "usr_director", CORRELATION)
        env.delegation.activate(grant.grant_id, "usr_director", CORRELATION)
        env.delegation.revoke(grant.grant_id, "usr_security", CORRELATION)

        env.delegation.create(
            grant_type=GrantType.PARTNER, source_principal_id="usr_partner",
            target_tenant_id="tnt_beta", approved_roles=("partner_reader",),
            approved_scopes=("tenant:read",), reason_code="PARTNER_CONTRACT",
            created_by="usr_manager", correlation_id=CORRELATION,
        )
        env.invitation_engine.issue(
            tenant_id="tnt_alpha", email="expiring@acme.test",
            invited_by_principal_id="usr_owner", correlation_id=CORRELATION,
            idempotency_key="lc-expire",
        )
        # Time is injected, so expiry is exercised without a sleep and without wall-clock
        # dependence (BOPEN-P2-001 section 17).
        env.clock.advance(timedelta(days=120))
        expired_grants = env.delegation.expire_due(correlation_id=CORRELATION)
        expired_invitations = env.invitation_engine.expire_due(correlation_id=CORRELATION)
        assert expired_grants, "no grant expired; delegation.expired would go unexercised"
        assert expired_invitations, "no invitation expired; invitation.expired would go unexercised"

    def drive_everything(self) -> "LifecycleEventDriver":
        self.drive_invitations_and_membership()
        self.drive_identity()
        self.drive_scim()
        self.drive_contexts()
        self.drive_delegation()
        return self


def assert_utc_timestamp(testcase: unittest.TestCase, value: str, field: str) -> None:
    """
    Parse a serialized timestamp, since the installed `jsonschema` cannot.

    The offset assertion carries the weight. An audit record written without a UTC offset is
    ambiguous by the emitting server's offset, and `occurred_at` is the field that orders a
    security investigation. A schema that only claims `format: date-time` in an environment
    where `format` no-ops would be asserting nothing at all here.
    """
    parsed = datetime.fromisoformat(value)
    testcase.assertIsNotNone(
        parsed.tzinfo,
        msg=f"{field} serialized without a UTC offset ({value!r}); the instant is ambiguous.",
    )


class _LifecycleTestCase(unittest.TestCase):
    """Shared fixture: one driver run, one schema load, reused by the reading tests below."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema("lifecycle-event.json")
        cls.driver = LifecycleEventDriver().drive_everything()
        cls.events = cls.driver.events()


class WholeCatalogueConformanceTests(_LifecycleTestCase):
    """The full Phase 2 event catalogue, produced for real and validated."""

    def test_every_emitted_lifecycle_event_conforms(self):
        """
        The headline claim. If this passes and the coverage tool still reports
        `lifecycle-event.json` as uncontracted, the tool is wrong; if it fails, the schema and
        the producer have drifted and the schema is the thing to re-derive, since the producer
        is the source of truth for its own envelope.
        """
        self.assertTrue(self.events, "the driver emitted no lifecycle events at all")
        for event in self.events:
            with self.subTest(event_type=event["event_type"], event_id=event["event_id"]):
                validate(event, self.schema)

    def test_every_event_type_in_the_schema_enum_is_reachable_from_a_real_service(self):
        """
        A closed enum is only a contract if the code can reach all of it. An unreachable value
        means either dead schema surface or a missing code path, and both are worth knowing —
        this is the check that would have caught `PHASE2_EVENT_TYPES` growing an entry that no
        module ever emits.
        """
        reached = {event["event_type"] for event in self.events}
        declared = set(self.schema["properties"]["event_type"]["enum"])
        self.assertEqual(
            declared - reached, set(),
            msg="schema declares event types no Phase 2 service emits",
        )
        self.assertEqual(
            reached - declared, set(),
            msg="a service emitted an event type the schema does not declare",
        )

    def test_the_schema_enum_is_exactly_the_producers_guard_list(self):
        """
        `emit_lifecycle_event` rejects an unknown `event_type` with `AuditContractError`
        (audit.py:139). If the schema enum and `PHASE2_EVENT_TYPES` were allowed to diverge, one
        of the two would silently become decorative — and the schema is the copy an external
        consumer reads, so it is the copy that must not lie.
        """
        self.assertEqual(
            set(self.schema["properties"]["event_type"]["enum"]), set(PHASE2_EVENT_TYPES),
        )

    def test_the_envelope_shape_is_uniform_across_all_eight_call_sites(self):
        """
        The finding this schema closes rests on the claim that there is *one* envelope, not a
        family of similar ones. Eight call sites across five modules construct these events, and
        a single key set across every emitted event is what makes one schema the right remedy
        rather than an average of several shapes. If this ever fails, the correct response is to
        report the divergence, not to relax the schema until both shapes fit.
        """
        keysets = {frozenset(event) for event in self.events}
        self.assertEqual(
            len(keysets), 1,
            msg=f"lifecycle producers emit {len(keysets)} distinct key sets: {keysets}",
        )
        self.assertEqual(set(self.schema["required"]), next(iter(keysets)))

    def test_required_is_the_whole_property_set_because_the_producer_writes_every_key(self):
        """
        `emit_lifecycle_event` builds one dict literal with thirteen keys and no conditional
        branch, so no property is optional in practice. Declaring a subset as required would
        make the schema weaker than the producer for no benefit; declaring a superset would make
        it unsatisfiable. This pins the choice so a later edit has to be deliberate.
        """
        self.assertEqual(set(self.schema["required"]), set(self.schema["properties"]))

    def test_occurred_at_always_carries_a_utc_offset(self):
        for event in self.events:
            assert_utc_timestamp(self, event["occurred_at"], "occurred_at")

    def test_event_ids_are_unique_across_the_whole_catalogue(self):
        """
        `format: uuid` says an id is well-formed, not that it is unique, and a duplicated audit
        id would let one record silently overwrite another in any store keyed on it. Uniqueness
        is a property of the run rather than of a single instance, so no schema keyword can
        reach it.
        """
        ids = [event["event_id"] for event in self.events]
        self.assertEqual(len(ids), len(set(ids)))


class OutcomeAndSubjectVocabularyTests(_LifecycleTestCase):
    """Where the producer is strict, where it is not, and what the schema does about each."""

    def test_both_reachable_outcome_values_are_produced_and_conform(self):
        """
        Denials are the events a security reviewer actually reads, and they run through the
        shortest code paths — the ones most likely to skip a field. Validating only successes
        would leave the half of the envelope that matters least well covered.
        """
        outcomes = {event["outcome"] for event in self.events}
        self.assertEqual(outcomes, {"success", "deny"})
        for event in self.events:
            self.assertIn(event["outcome"], self.schema["properties"]["outcome"]["enum"])

    def test_the_failure_outcome_is_declared_reachable_and_emitted_by_nobody(self):
        """
        `failure` is the third value the producer accepts (audit.py:141) and no Phase 2 call site
        passes it — every one of them classifies as `success` or `deny`. It is kept in the schema
        because the producer accepts it, so an event carrying it would be legitimate and must
        validate; this test records that the gap between "accepted" and "emitted" is known rather
        than overlooked, and constructs the instance through the real dispatcher rather than by
        editing a dict, so the claim is about the producer.
        """
        dispatcher = AuditDispatcher()
        event = dispatcher.emit_lifecycle_event(
            event_type="scim.event_denied", correlation_id=CORRELATION,
            actor_id="scim_directory", tenant_id="tnt_alpha", subject_type="scim_event",
            subject_id="evt-1", outcome="failure", reason_code="UPSTREAM_ERROR",
        )
        validate(event, self.schema)
        self.assertNotIn("failure", {e["outcome"] for e in self.events})

    def test_an_outcome_outside_the_enum_cannot_be_produced_at_all(self):
        """
        The enum is not the only guard: the producer refuses to build the event. Asserting the
        refusal means the schema's closed `outcome` list is backed by code rather than by hope,
        which is the difference between a contract and a comment.
        """
        with self.assertRaises(AuditContractError):
            AuditDispatcher().emit_lifecycle_event(
                event_type="context.issued", correlation_id=CORRELATION, actor_id="usr_a",
                tenant_id="tnt_alpha", subject_type="context", subject_id="ctx_1",
                outcome="ERROR", reason_code="X",
            )

    def test_subject_type_is_left_open_because_the_producer_checks_it_against_nothing(self):
        """
        Eight distinct `subject_type` values appear across the catalogue and the producer
        validates none of them. Enumerating the eight would produce a schema that a legitimate
        ninth subject kind breaks — a contract stricter than its own producer, which is the
        defect this whole exercise exists to remove. This test records the observed vocabulary
        so that widening it stays visible, without turning the observation into a constraint.
        """
        observed = {event["subject_type"] for event in self.events}
        self.assertEqual(observed, {
            "invitation", "membership", "connection", "external_identity",
            "scim_event", "group", "context", "delegated_grant",
        })
        self.assertNotIn("enum", self.schema["properties"]["subject_type"])

    def test_sentinel_actors_and_tenants_conform_because_the_schema_does_not_pretend(self):
        """
        `actor_principal_id` holds `anonymous`, `security_control` and `expiry_scheduler`;
        `tenant_id` holds `unknown` on paths that deny before a tenant resolves. A schema
        applying a principal-id or tenant-id pattern to these would reject correct audit records
        for exactly the denials that most need auditing (INV-P2-017). Naming the sentinels here
        keeps that looseness a documented decision rather than an accident.
        """
        actors = {event["actor_principal_id"] for event in self.events}
        self.assertTrue({"anonymous", "security_control", "expiry_scheduler"} <= actors)
        self.assertIn("unknown", {event["tenant_id"] for event in self.events})
        for event in self.events:
            validate(event, self.schema)


class CausationIdTests(_LifecycleTestCase):
    """`causation_id` is declared, always present, and never populated."""

    def test_no_producer_populates_causation_id(self):
        """
        The parameter defaults to None (audit.py:131) and no caller in `packages/kernel-core` or
        `services/platform-kernel` passes it, so the causal chain the field exists to carry is
        not threaded through. The schema types it nullable rather than dropping it, because the
        producer always writes the key. Pinning the emptiness means the day a caller starts
        supplying it, this test fails and the field's `description` gets revisited instead of
        quietly going stale.
        """
        self.assertEqual({event["causation_id"] for event in self.events}, {None})

    def test_a_populated_causation_id_also_conforms(self):
        """
        The nullable branch is the only one production exercises, so the populated branch is
        only really tested by constructing it. If it did not validate, the field would be
        nullable in name and null-only in fact.
        """
        dispatcher = AuditDispatcher()
        event = dispatcher.emit_lifecycle_event(
            event_type="membership.transitioned", correlation_id=CORRELATION,
            actor_id="usr_owner", tenant_id="tnt_alpha", subject_type="membership",
            subject_id="mem_1", outcome="success", reason_code="INVITATION_ACCEPTED",
            causation_id="cmd-0001",
        )
        validate(event, self.schema)
        self.assertEqual(event["causation_id"], "cmd-0001")


class MetadataBoundaryTests(_LifecycleTestCase):
    """`metadata` is open by necessity and closed where INV-P2-018 can be expressed."""

    def test_metadata_is_always_present_and_sometimes_empty(self):
        """
        Three call sites pass no metadata at all and the producer substitutes `{}`. If the schema
        required a non-empty object, those three denial events — all of them SCIM and invitation
        rejections — would fail to validate while being entirely correct.
        """
        self.assertTrue(all(isinstance(e["metadata"], dict) for e in self.events))
        self.assertTrue(any(e["metadata"] == {} for e in self.events))

    def test_the_observed_metadata_value_types_are_wider_than_string(self):
        """
        Integers (`resulting_version`, `transitions`), nulls (`delegated_grant_id`) and
        arrays (`applied_roles`) all appear. A schema declaring
        `additionalProperties: {"type": "string"}` would have looked tidier and rejected four
        real events, which is why `metadata` stays open and says so in its description.
        """
        value_types = set()
        for event in self.events:
            for value in event["metadata"].values():
                value_types.add(type(value).__name__)
        self.assertTrue({"int", "NoneType", "list"} <= value_types)

    def test_the_prohibited_key_list_matches_the_producers_own(self):
        """
        The schema's `propertyNames` list is a copy of `PROHIBITED_METADATA_KEYS`, and a copy
        that drifts is worse than no copy: it would read as an INV-P2-018 control while
        permitting whichever key the producer had since added.
        """
        declared = set(self.schema["properties"]["metadata"]["propertyNames"]["not"]["enum"])
        self.assertEqual(declared, set(PROHIBITED_METADATA_KEYS))

    def test_the_producer_refuses_a_credential_key_before_the_schema_ever_sees_it(self):
        """
        The first line of INV-P2-018 defence is the producer, not the contract. Showing the
        refusal here is what makes the schema's `propertyNames` a second line rather than the
        only one — and the reason the schema being strictly weaker (exact-case match, no value
        scanning) is acceptable.
        """
        for key in ("access_token", "saml_assertion", "private_key"):
            with self.subTest(key=key):
                with self.assertRaises(AuditContractError):
                    AuditDispatcher().emit_lifecycle_event(
                        event_type="identity.linked", correlation_id=CORRELATION,
                        actor_id="usr_a", tenant_id="tnt_alpha",
                        subject_type="external_identity", subject_id="eid_1",
                        outcome="success", reason_code="LINKED", metadata={key: "value"},
                    )

    def test_no_emitted_event_carries_a_credential_shaped_value_anywhere(self):
        """
        INV-P2-018 is about values as much as keys, and the value half is what no JSON Schema
        keyword can express. The invitation engine mints raw tokens on the same code path that
        emits `invitation.issued`, so this checks the whole serialized catalogue rather than
        trusting that the token stayed in the return value.
        """
        serialized = json.dumps(self.events)
        self.assertNotIn("raw-invitation-token", serialized)
        for prohibited in PROHIBITED_METADATA_KEYS:
            for event in self.events:
                self.assertNotIn(prohibited, {k.lower() for k in event["metadata"]})


class ValidationIsNotVacuousTests(_LifecycleTestCase):
    """
    Proof that this schema constrains something.

    `membership-transition-matrix.json` sits in the same directory declaring `$schema` and no
    `type`, so `jsonschema.validate` accepts `42` and `None` against it; a green instance test
    against a schema like that asserts nothing, and nothing in a pass count distinguishes the
    two cases. These are the adversarial cases required by BOPEN-GOV-EBIV-001 R4: each takes a
    real conforming event, breaks it in the one way the schema is supposed to catch, and
    requires a rejection with the expected validator naming the cause.
    """

    def _conforming_event(self) -> Dict[str, Any]:
        event = dict(self.driver.events_of("invitation.issued")[0])
        validate(event, self.schema)
        return event

    def _rejects(self, event: Dict[str, Any], validator: str) -> None:
        with self.assertRaises(jsonschema.ValidationError) as caught:
            validate(event, self.schema)
        self.assertEqual(caught.exception.validator, validator)

    def test_a_non_object_instance_is_rejected(self):
        """
        The floor `membership-transition-matrix.json` fails to clear. Without `type: object` a
        schema accepts a bare integer, and every other assertion in this file would be resting on
        a document that constrains nothing.
        """
        for absurd in ({}, 42, "a string", None, []):
            with self.subTest(instance=absurd):
                with self.assertRaises(jsonschema.ValidationError):
                    validate(absurd, self.schema)

    def test_a_missing_required_property_is_rejected(self):
        event = self._conforming_event()
        del event["outcome"]
        self._rejects(event, "required")

    def test_an_undeclared_property_is_rejected(self):
        """
        The exact class of defect `AuditDispatcher.dispatch` exhibits against `audit-event.json`,
        caught here. `additionalProperties: false` is also what stops a future edit from adding
        an unreviewed field to the audit stream without the contract noticing.
        """
        event = self._conforming_event()
        event["ip_address"] = "203.0.113.7"
        self._rejects(event, "additionalProperties")

    def test_an_event_type_outside_the_phase_2_catalogue_is_rejected(self):
        event = self._conforming_event()
        event["event_type"] = "invitation.rescinded"
        self._rejects(event, "enum")

    def test_the_authorization_envelopes_status_vocabulary_is_rejected_here(self):
        """
        `SUCCESS` is a valid `status` in `audit-event.json` and is not a valid `outcome` here.
        A consumer that mapped one envelope onto the other by copying the field would produce
        exactly this instance, and it must not validate — the two vocabularies being genuinely
        incompatible is the whole reason the divergence needs recording rather than assuming.
        """
        event = self._conforming_event()
        event["outcome"] = "SUCCESS"
        self._rejects(event, "enum")

    def test_a_second_envelope_revision_is_rejected_until_the_schema_declares_it(self):
        event = self._conforming_event()
        event["event_version"] = 2
        self._rejects(event, "const")

    def test_a_credential_key_in_metadata_is_rejected(self):
        """
        `propertyNames` is the only INV-P2-018 control this schema can carry. The producer would
        never emit this instance, so the check has to introduce it — which is the point: the
        schema must still bite for any consumer that receives the envelope from a producer other
        than `emit_lifecycle_event`.
        """
        event = self._conforming_event()
        event["metadata"] = dict(event["metadata"], refresh_token="ey.forged.payload")
        self._rejects(event, "not")

    def test_an_empty_correlation_id_is_rejected(self):
        """
        `minLength: 1` is a schema-side floor, not a producer guarantee — nothing in
        `emit_lifecycle_event` checks it. It is worth keeping because an audit record with an
        empty correlation id cannot be joined to the request that caused it, which defeats the
        field's only purpose.
        """
        event = self._conforming_event()
        event["correlation_id"] = ""
        self._rejects(event, "minLength")

    def test_a_non_uuid_event_id_is_rejected(self):
        """
        `format` is only live for `uuid` in this environment (see the module docstring), so this
        is the one format assertion that genuinely bites today. `event_id` is unprefixed here
        while Phase 2 entity ids are not, and a prefixed value arriving in this field would mean
        the dispatcher had started reusing the identifier factory.
        """
        event = self._conforming_event()
        event["event_id"] = "evt_000001"
        self._rejects(event, "format")


class TwoAuditEnvelopesTests(_LifecycleTestCase):
    """
    The `status`/`outcome` divergence and the `reason_code` surplus, pinned as facts.

    Neither is resolved here. `audit-event.json` is frozen and its producer sits in the
    authorization path, so this file records what is true of both envelopes and changes neither.
    The value of asserting it is that the divergence stops being tribal knowledge: if someone
    later unifies the vocabularies, or lets a third one appear, these fail.

    The cases touching `audit-event.json` deliberately do NOT go through this module's
    `validate()` helper. `tools/check_contract_conformance.py` measures coverage by wrapping the
    module-level `jsonschema.validate` and recording every schema handed to it, so calling it
    here would report `audit-event.json` as instance-validated and invite its debt entry to be
    struck — on the strength of assertions that its producer does *not* conform. A local
    `Draft202012Validator` reaches the same verdicts without lying to the instrument. Do not
    "simplify" these back to `validate()`.
    """

    def setUp(self):
        self.audit_event_schema = load_schema("audit-event.json")
        self.audit_event_checker = jsonschema.Draft202012Validator(self.audit_event_schema)

    def test_the_two_envelopes_disagree_on_the_name_of_the_result_field(self):
        lifecycle_props = set(self.schema["properties"])
        legacy_props = set(self.audit_event_schema["properties"])
        self.assertIn("outcome", lifecycle_props)
        self.assertNotIn("outcome", legacy_props)
        self.assertIn("status", legacy_props)
        self.assertNotIn("status", lifecycle_props)

    def test_the_two_envelopes_disagree_on_the_values_of_the_result_field(self):
        """
        Not merely a rename: the sets differ in size and in meaning. `ERROR` has no counterpart
        in {success, deny, failure} that a mechanical mapping could pick — `failure` is the
        nearest, and it is emitted by nobody. Any unification is a decision about semantics, not
        a search-and-replace.
        """
        self.assertEqual(
            set(self.audit_event_schema["properties"]["status"]["enum"]),
            {"SUCCESS", "DENIED", "ERROR"},
        )
        self.assertEqual(
            set(self.schema["properties"]["outcome"]["enum"]),
            {"success", "deny", "failure"},
        )

    def test_the_two_envelopes_disagree_on_the_name_of_the_time_and_actor_fields(self):
        """
        Three renames, not one, and the lifecycle side matches
        `docs/06-contracts/events/event-envelope.md` while the legacy side does not. That is the
        substance of the recommendation to keep the lifecycle vocabulary: it is the one the
        platform envelope already documents.
        """
        for lifecycle_name, legacy_name in (
            ("occurred_at", "timestamp"), ("actor_principal_id", "actor_id"),
        ):
            self.assertIn(lifecycle_name, self.schema["properties"])
            self.assertNotIn(lifecycle_name, self.audit_event_schema["properties"])
            self.assertIn(legacy_name, self.audit_event_schema["properties"])
            self.assertNotIn(legacy_name, self.schema["properties"])

    def test_a_lifecycle_event_does_not_validate_against_the_authorization_schema(self):
        """
        The mistake this whole finding began with, made deliberately so it is recorded rather
        than rediscovered. A reviewer reaching for `audit-event.json` to check a lifecycle event
        gets a wall of errors and can reasonably conclude the producer is broken. It is not; the
        envelopes are different documents, and now both have one.
        """
        event = self.driver.events_of("invitation.issued")[0]
        errors = list(self.audit_event_checker.iter_errors(event))
        self.assertTrue(errors, "the lifecycle envelope satisfied the authorization schema")
        self.assertIn(
            "required", {error.validator for error in errors},
            msg="the mismatch is no longer about missing fields; the finding has changed shape",
        )

    def test_an_authorization_event_does_not_validate_against_this_schema_either(self):
        """
        The converse, which matters for the same reason: this schema must not be reached for by
        someone holding a `dispatch` event. The two are disjoint in both directions, so neither
        can serve as the other's contract.
        """
        dispatcher = AuditDispatcher()
        legacy = dispatcher.dispatch(
            actor_id="usr_alice", tenant_id="tnt_alpha", action="membership:read",
            resource_type="membership", resource_id="mem_1", status="SUCCESS",
            correlation_id=CORRELATION,
        )
        self.assertNotIn("occurred_at", legacy)
        with self.assertRaises(jsonschema.ValidationError):
            validate(legacy, self.schema)

    def test_reason_code_is_emitted_by_both_producers_and_declared_by_only_one_schema(self):
        """
        `AuditDispatcher.dispatch` writes `reason_code` (audit.py:91) and `audit-event.json` has
        no reason property at all, so `additionalProperties: false` rejects it — one error, a
        pure surplus. This file changes neither side; it asserts the asymmetry so the report's
        conclusion (the schema is the incomplete one, since the field is the *why* behind every
        authorization decision and nothing else in that envelope carries it) rests on an
        executable fact rather than on a reading.
        """
        legacy = AuditDispatcher().dispatch(
            actor_id="usr_alice", tenant_id="tnt_alpha", action="membership:read",
            resource_type="membership", resource_id="mem_1", status="DENIED",
            correlation_id=CORRELATION, reason_code="MEMBERSHIP_ROLE_DENIED",
        )
        self.assertIn("reason_code", legacy)
        self.assertNotIn("reason_code", self.audit_event_schema["properties"])
        self.assertFalse(self.audit_event_schema["additionalProperties"])

        self.assertIn("reason_code", self.schema["properties"])
        self.assertTrue(all("reason_code" in event for event in self.events))

        errors = list(self.audit_event_checker.iter_errors(legacy))
        self.assertEqual(
            [error.validator for error in errors], ["additionalProperties"],
            msg="reason_code is no longer the only thing dispatch gets wrong against its schema",
        )
        self.assertEqual(
            set(legacy) - set(self.audit_event_schema["properties"]), {"reason_code"},
            msg="reason_code is no longer the sole surplus field; the finding has changed shape",
        )


if __name__ == "__main__":
    unittest.main()
