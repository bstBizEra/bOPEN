"""
Deterministic Phase 2 test fixtures.

BOPEN-P2-001 section 17: no test may depend on wall clock, random nondeterminism,
public network or production credentials. Every component here is injected with a
controllable clock and a counting identifier factory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from kernel_core.audit import AuditDispatcher
from kernel_core.delegation import DelegatedAccessService, InMemoryGrantRepository
from kernel_core.membership import (
    InMemoryIdempotencyStore,
    InMemoryInvitationRepository,
    InMemoryMembershipRepository,
    InMemoryObligationRecorder,
    InvitationEngine,
    MembershipStateMachine,
    MembershipTransitionContract,
    Sha256TokenHasher,
    StaticTenantStateReader,
)
from platform_kernel.context_service import (
    AuthenticationSession,
    ContextSwitchService,
    ContextTokenValidator,
    DeterministicTestSigner,
    InMemorySessionStore,
)
from platform_kernel.idp_bridge import (
    IdpBridge,
    InMemoryIdentityStore,
    StaticBrokerPort,
)

BASE_TIME = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
ISSUER = "https://auth.bopen.test"
AUDIENCE = "https://api.bopen.test"


class FakeClock:
    """Injected clock (BOPEN-IDP-001 section 5)."""

    def __init__(self, start: datetime = BASE_TIME) -> None:
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta

    def set(self, moment: datetime) -> None:
        self._now = moment


class CountingIdentifierFactory:
    """Deterministic identifiers so assertions never depend on randomness."""

    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}

    def new_id(self, prefix: str) -> str:
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}_{self._counters[prefix]:06d}"


class SequentialTokenGenerator:
    """Deterministic raw tokens. Test-only; never a production generator."""

    def __init__(self) -> None:
        self._n = 0

    def generate(self) -> str:
        self._n += 1
        return f"raw-invitation-token-{self._n:04d}"


@dataclass
class Phase2Env:
    clock: FakeClock
    ids: CountingIdentifierFactory
    audit: AuditDispatcher
    memberships: InMemoryMembershipRepository
    invitations: InMemoryInvitationRepository
    tenants: StaticTenantStateReader
    obligations: InMemoryObligationRecorder
    contract: MembershipTransitionContract
    state_machine: MembershipStateMachine
    invitation_engine: InvitationEngine
    grants: InMemoryGrantRepository
    delegation: DelegatedAccessService
    sessions: InMemorySessionStore
    signer: DeterministicTestSigner
    context_service: ContextSwitchService
    validator: ContextTokenValidator
    identity_store: InMemoryIdentityStore
    broker: StaticBrokerPort
    idp_bridge: IdpBridge
    hasher: Sha256TokenHasher

    def session_for(
        self, principal_id: str, client_id: str = "cli_test", lifetime: timedelta = timedelta(hours=8)
    ) -> AuthenticationSession:
        session = AuthenticationSession(
            session_id=self.ids.new_id("sid"),
            principal_id=principal_id,
            client_id=client_id,
            established_at=self.clock.now(),
            expires_at=self.clock.now() + lifetime,
        )
        return self.sessions.save_session(session)


def build_phase2_env(active_tenants=("tnt_alpha", "tnt_beta")) -> Phase2Env:
    clock = FakeClock()
    ids = CountingIdentifierFactory()
    audit = AuditDispatcher()

    memberships = InMemoryMembershipRepository()
    invitations = InMemoryInvitationRepository()
    tenants = StaticTenantStateReader(set(active_tenants))
    obligations = InMemoryObligationRecorder()
    contract = MembershipTransitionContract.load()

    state_machine = MembershipStateMachine(
        contract=contract,
        memberships=memberships,
        tenants=tenants,
        audit=audit,
        obligations=obligations,
        idempotency=InMemoryIdempotencyStore(),
        clock=clock,
        ids=ids,
    )

    hasher = Sha256TokenHasher()
    invitation_engine = InvitationEngine(
        invitations=invitations,
        memberships=memberships,
        state_machine=state_machine,
        audit=audit,
        idempotency=InMemoryIdempotencyStore(),
        clock=clock,
        ids=ids,
        tokens=SequentialTokenGenerator(),
        hasher=hasher,
    )

    grants = InMemoryGrantRepository()
    delegation = DelegatedAccessService(grants=grants, audit=audit, clock=clock, ids=ids)

    sessions = InMemorySessionStore()
    signer = DeterministicTestSigner()
    context_service = ContextSwitchService(
        memberships=memberships,
        sessions=sessions,
        signer=signer,
        audit=audit,
        issuer=ISSUER,
        audience=AUDIENCE,
        delegation=delegation,
        clock=clock,
        ids=ids,
    )
    validator = ContextTokenValidator(
        issuer=ISSUER,
        audience=AUDIENCE,
        known_keys={signer.kid: DeterministicTestSigner.NON_PRODUCTION_KEY},
        clock=clock,
    )

    identity_store = InMemoryIdentityStore()
    broker = StaticBrokerPort()
    idp_bridge = IdpBridge(
        store=identity_store,
        memberships=memberships,
        invitations=invitations,
        state_machine=state_machine,
        audit=audit,
        broker=broker,
        clock=clock,
        ids=ids,
    )

    return Phase2Env(
        clock=clock, ids=ids, audit=audit, memberships=memberships, invitations=invitations,
        tenants=tenants, obligations=obligations, contract=contract, state_machine=state_machine,
        invitation_engine=invitation_engine, grants=grants, delegation=delegation,
        sessions=sessions, signer=signer, context_service=context_service, validator=validator,
        identity_store=identity_store, broker=broker, idp_bridge=idp_bridge, hasher=hasher,
    )


def onboard_active_member(
    env: Phase2Env, tenant_id: str = "tnt_alpha", principal_id: str = "usr_alice",
    email: str = "alice@acme.test", correlation_id: str = "corr-onboard",
):
    """Issue and accept an invitation, returning the resulting acceptance result."""
    issued = env.invitation_engine.issue(
        tenant_id=tenant_id,
        email=email,
        invited_by_principal_id="usr_owner",
        correlation_id=correlation_id,
        idempotency_key=f"issue:{tenant_id}:{email}",
    )
    return env.invitation_engine.accept(
        raw_token=issued.raw_token,
        tenant_id=tenant_id,
        principal_id=principal_id,
        correlation_id=correlation_id,
        idempotency_key=f"accept:{tenant_id}:{principal_id}",
    )
