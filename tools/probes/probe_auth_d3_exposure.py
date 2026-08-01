#!/usr/bin/env python3
"""Measure unauthenticated AUTH-D3 reach over real loopback HTTP and PostgreSQL."""

from __future__ import annotations

import json
import os
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOTS = (
    ROOT / "packages" / "kernel-core" / "python",
    ROOT / "services" / "platform-kernel" / "python",
    ROOT / "sdk" / "python",
    ROOT,
)
AUTH_ENV = (
    "BOPEN_SUBJECT_ASSERTION_ISSUER",
    "BOPEN_SUBJECT_ASSERTION_PUBLIC_KEY",
    "BOPEN_SUBJECT_ASSERTION_AUDIENCE",
)
ALLOW_ENV = "BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"


def correlation() -> str:
    return f"corr_{uuid.uuid4()}"


def request_headers(**extra: str) -> dict[str, str]:
    value = {"X-Correlation-ID": correlation()}
    value.update(extra)
    return value


def expect(response: httpx.Response, status: int, label: str) -> None:
    if response.status_code != status:
        raise AssertionError(
            f"{label}: expected {status}, got {response.status_code}: {response.text}"
        )


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@dataclass
class KernelProcess:
    process: subprocess.Popen
    base_url: str
    stdout_path: Path
    stderr_path: Path
    stdout_handle: object
    stderr_handle: object

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.stdout_handle.close()
        self.stderr_handle.close()
        if self.process.returncode not in (0, 1):
            stderr = self.stderr_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(
                f"kernel process exited {self.process.returncode}: {stderr[-2000:]}"
            )
        self.stdout_path.unlink(missing_ok=True)
        self.stderr_path.unlink(missing_ok=True)


def start_kernel(*, allow_unauthenticated: bool, authenticator: dict[str, str] | None) -> KernelProcess:
    port = free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in PYTHON_ROOTS)
    for name in AUTH_ENV:
        env.pop(name, None)
    if allow_unauthenticated:
        env[ALLOW_ENV] = "1"
    else:
        env.pop(ALLOW_ENV, None)
    if authenticator:
        env.update(authenticator)

    stdout_file = tempfile.NamedTemporaryFile(
        prefix="bopen-auth-d3-", suffix=".stdout.log", delete=False
    )
    stderr_file = tempfile.NamedTemporaryFile(
        prefix="bopen-auth-d3-", suffix=".stderr.log", delete=False
    )
    stdout_path = Path(stdout_file.name)
    stderr_path = Path(stderr_file.name)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "platform_kernel.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=stdout_file,
        stderr=stderr_file,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout_file.close()
            stderr_file.close()
            stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"kernel failed to start: {stderr[-2000:]}")
        try:
            response = httpx.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                return KernelProcess(
                    process,
                    base_url,
                    stdout_path,
                    stderr_path,
                    stdout_file,
                    stderr_file,
                )
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    process.terminate()
    process.wait(timeout=5)
    stdout_file.close()
    stderr_file.close()
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    raise RuntimeError(f"kernel did not become ready: {stderr[-2000:]}")


def register_principal(client: httpx.Client, email: str) -> httpx.Response:
    return client.post(
        "/v1/principals",
        json={"email": email, "type": "human"},
        headers=request_headers(),
    )


def provision_tenant(client: httpx.Client, principal_id: str, label: str) -> httpx.Response:
    return client.post(
        "/v1/tenants",
        json={"name": label, "owner_principal_id": principal_id},
        headers=request_headers(),
    )


def establish_context(
    client: httpx.Client, tenant_id: str, principal_id: str, membership_id: str
) -> httpx.Response:
    return client.post(
        "/v1/contexts",
        json={"principal_id": principal_id, "membership_id": membership_id},
        headers=request_headers(**{"X-Tenant-ID": tenant_id}),
    )


def new_owner_chain(client: httpx.Client, run_id: str, label: str) -> dict[str, str]:
    principal_response = register_principal(
        client, f"authd3-{run_id}-{label}@example.com"
    )
    expect(principal_response, 201, f"{label} principal")
    principal_id = principal_response.json()["principal_id"]
    tenant_response = provision_tenant(
        client, principal_id, f"AUTH-D3 {run_id} {label}"
    )
    expect(tenant_response, 201, f"{label} tenant")
    tenant_body = tenant_response.json()
    context_response = establish_context(
        client,
        tenant_body["tenant_id"],
        principal_id,
        tenant_body["owner_membership_id"],
    )
    expect(context_response, 201, f"{label} context")
    context_body = context_response.json()
    if not context_body.get("access_token"):
        raise AssertionError(f"{label}: context response carried no access token")
    return {
        "principal_id": principal_id,
        "tenant_id": tenant_body["tenant_id"],
        "membership_id": tenant_body["owner_membership_id"],
        "context_id": context_body["context"]["context_id"],
        "access_token": context_body["access_token"],
    }


def bearer_headers(token: str, **extra: str) -> dict[str, str]:
    return request_headers(Authorization=f"Bearer {token}", **extra)


def probability_left_faster(left: list[int], right: list[int]) -> float:
    less = sum(a < b for a in left for b in right)
    equal = sum(a == b for a in left for b in right)
    return (less + 0.5 * equal) / (len(left) * len(right))


def measure_open_profile(run_id: str) -> tuple[dict, dict[str, str]]:
    kernel = start_kernel(allow_unauthenticated=True, authenticator=None)
    try:
        with httpx.Client(base_url=kernel.base_url, timeout=10) as client:
            owner_a = new_owner_chain(client, run_id, "owner-a")
            authorization_body = {
                "action": "tenant_resource:read",
                "resource_type": "tenant_resource",
                "resource_id": str(uuid.uuid4()),
            }
            authorize = client.post(
                "/v1/authorize",
                json=authorization_body,
                headers=bearer_headers(owner_a["access_token"]),
            )
            expect(authorize, 200, "owner authorization")
            if authorize.json()["decision"] != "ALLOW":
                raise AssertionError(f"owner authorization was not ALLOW: {authorize.text}")

            create_resource = client.post(
                "/v1/resources?resource_name=auth-d3-owned",
                headers=bearer_headers(owner_a["access_token"]),
            )
            expect(create_resource, 201, "owner resource creation")
            resource_a = create_resource.json()["resource_id"]
            read_resource = client.get(
                f"/v1/resources/{resource_a}",
                headers=bearer_headers(owner_a["access_token"]),
            )
            expect(read_resource, 200, "owner resource read")
            audit = client.get(
                "/v1/audit-events?limit=500",
                headers=bearer_headers(owner_a["access_token"]),
            )
            expect(audit, 200, "owner audit enumeration")

            owner_b = new_owner_chain(client, run_id, "owner-b")
            b_correlation = correlation()
            create_b = client.post(
                "/v1/resources?resource_name=auth-d3-tenant-b",
                headers={
                    "Authorization": f"Bearer {owner_b['access_token']}",
                    "X-Correlation-ID": b_correlation,
                },
            )
            expect(create_b, 201, "tenant B resource creation")
            resource_b = create_b.json()["resource_id"]

            cross_read_implicit = client.get(
                f"/v1/resources/{resource_b}",
                headers=bearer_headers(owner_a["access_token"]),
            )
            expect(cross_read_implicit, 404, "tenant A token reading tenant B resource")
            cross_read_conflict = client.get(
                f"/v1/resources/{resource_b}",
                headers=bearer_headers(
                    owner_a["access_token"], **{"X-Tenant-ID": owner_b["tenant_id"]}
                ),
            )
            expect(cross_read_conflict, 403, "contradictory tenant claim")
            audit_a_after_b = client.get(
                "/v1/audit-events?limit=500",
                headers=bearer_headers(owner_a["access_token"]),
            )
            expect(audit_a_after_b, 200, "tenant A audit after tenant B write")
            leaked = [
                event
                for event in audit_a_after_b.json()["events"]
                if event["correlation_id"] == b_correlation
            ]
            if leaked:
                raise AssertionError("tenant A enumerated tenant B's audit event")

            # Model a known pre-existing principal with an already-working tenant context.
            victim_principal_response = register_principal(
                client, f"authd3-{run_id}-victim@example.com"
            )
            expect(victim_principal_response, 201, "victim principal")
            victim_principal = victim_principal_response.json()["principal_id"]
            legitimate_tenant = provision_tenant(
                client, victim_principal, f"AUTH-D3 {run_id} victim legitimate"
            )
            expect(legitimate_tenant, 201, "victim legitimate tenant")
            legitimate_body = legitimate_tenant.json()
            legitimate_context = establish_context(
                client,
                legitimate_body["tenant_id"],
                victim_principal,
                legitimate_body["owner_membership_id"],
            )
            expect(legitimate_context, 201, "victim legitimate context")
            legitimate_token = legitimate_context.json()["access_token"]

            squat_tenant = provision_tenant(
                client, victim_principal, f"AUTH-D3 {run_id} victim squat"
            )
            expect(squat_tenant, 201, "known-principal tenant squatting")
            squat_body = squat_tenant.json()
            squat_context = establish_context(
                client,
                squat_body["tenant_id"],
                victim_principal,
                squat_body["owner_membership_id"],
            )
            expect(squat_context, 201, "squatted-tenant owner context")
            squat_token = squat_context.json()["access_token"]
            legitimate_still_works = client.post(
                "/v1/authorize",
                json=authorization_body,
                headers=bearer_headers(legitimate_token),
            )
            expect(legitimate_still_works, 200, "victim's prior tenant context")
            squat_works = client.post(
                "/v1/authorize",
                json=authorization_body,
                headers=bearer_headers(squat_token),
            )
            expect(squat_works, 200, "squatted tenant owner context")

            unknown_owner = provision_tenant(
                client, str(uuid.uuid4()), f"AUTH-D3 {run_id} unknown owner"
            )
            expect(unknown_owner, 422, "unknown owner identifier")

            # Bounded resource-exhaustion lower bound from one client and one source address.
            batch_principals: list[str] = []
            batch_statuses: list[int] = []
            batch_tenant_statuses: list[int] = []
            rate_headers_seen: set[str] = set()
            batch_started = time.perf_counter()
            for index in range(40):
                response = register_principal(
                    client, f"authd3-{run_id}-bulk-{index:03d}@example.com"
                )
                batch_statuses.append(response.status_code)
                rate_headers_seen.update(
                    name.lower()
                    for name in response.headers
                    if "rate" in name.lower() or "limit" in name.lower() or "retry" in name.lower()
                )
                expect(response, 201, f"bulk principal {index}")
                batch_principals.append(response.json()["principal_id"])
            for index, principal_id in enumerate(batch_principals[:20]):
                response = provision_tenant(
                    client, principal_id, f"AUTH-D3 {run_id} bulk tenant {index:03d}"
                )
                batch_tenant_statuses.append(response.status_code)
                rate_headers_seen.update(
                    name.lower()
                    for name in response.headers
                    if "rate" in name.lower() or "limit" in name.lower() or "retry" in name.lower()
                )
                expect(response, 201, f"bulk tenant {index}")
            batch_elapsed = time.perf_counter() - batch_started

            # Network-visible account-existence oracle, alternating arms to distribute drift.
            oracle_existing_email = f"authd3-{run_id}-oracle-{'e' * 32}@example.com"
            oracle_seed = register_principal(client, oracle_existing_email)
            expect(oracle_seed, 201, "oracle seed")
            existing_times: list[int] = []
            new_times: list[int] = []
            existing_lengths: set[int] = set()
            new_lengths: set[int] = set()
            for index in range(80):
                new_email = f"authd3-{run_id}-oracle-{index:032d}@example.com"
                arms = (
                    ((oracle_existing_email, 409, existing_times, existing_lengths),
                     (new_email, 201, new_times, new_lengths))
                    if index % 2 == 0
                    else
                    ((new_email, 201, new_times, new_lengths),
                     (oracle_existing_email, 409, existing_times, existing_lengths))
                )
                for email, expected, timings, lengths in arms:
                    started = time.perf_counter_ns()
                    response = register_principal(client, email)
                    elapsed = time.perf_counter_ns() - started
                    expect(response, expected, "account-existence oracle")
                    timings.append(elapsed)
                    lengths.add(len(response.content))

            reserved_email = f"authd3-{run_id}-reserved@example.com"
            reserve = register_principal(client, reserved_email)
            expect(reserve, 201, "unauthenticated email reservation")
            later_claim = register_principal(client, reserved_email)
            expect(later_claim, 409, "later claim of pre-registered email")

            output = {
                "runtime": {
                    "profile": "no_authenticator_allow_flag_set",
                    "transport": "uvicorn_loopback_tcp",
                    "database_configured": bool(os.environ.get("BOPEN_DATABASE_URL", "").strip()),
                },
                "zero_to_owner": {
                    "principal": 201,
                    "tenant": 201,
                    "context": 201,
                    "token_issued": True,
                },
                "owner_token_reach": {
                    "authorize_status": authorize.status_code,
                    "authorize_decision": authorize.json()["decision"],
                    "create_status": create_resource.status_code,
                    "read_status": read_resource.status_code,
                    "audit_status": audit.status_code,
                    "audit_event_count": len(audit.json()["events"]),
                },
                "cross_tenant": {
                    "foreign_resource_without_conflicting_header": cross_read_implicit.status_code,
                    "foreign_resource_with_tenant_b_header": cross_read_conflict.status_code,
                    "tenant_b_audit_events_visible_to_a": len(leaked),
                },
                "tenant_squatting": {
                    "known_principal_tenant_status": squat_tenant.status_code,
                    "known_principal_context_status": squat_context.status_code,
                    "squat_owner_decision": squat_works.json()["decision"],
                    "prior_tenant_context_status_after_squat": legitimate_still_works.status_code,
                    "prior_tenant_decision_after_squat": legitimate_still_works.json()["decision"],
                    "unknown_principal_tenant_status": unknown_owner.status_code,
                },
                "creation_pressure": {
                    "principal_attempts": len(batch_statuses),
                    "principal_201": batch_statuses.count(201),
                    "tenant_attempts": len(batch_tenant_statuses),
                    "tenant_201": batch_tenant_statuses.count(201),
                    "429_responses": batch_statuses.count(429) + batch_tenant_statuses.count(429),
                    "rate_or_retry_headers": sorted(rate_headers_seen),
                    "elapsed_seconds": round(batch_elapsed, 3),
                },
                "account_existence_oracle": {
                    "pairs": len(existing_times),
                    "existing_status": 409,
                    "new_status": 201,
                    "existing_body_lengths": sorted(existing_lengths),
                    "new_body_lengths": sorted(new_lengths),
                    "existing_median_ms": round(statistics.median(existing_times) / 1_000_000, 3),
                    "new_median_ms": round(statistics.median(new_times) / 1_000_000, 3),
                    "p_existing_faster": round(
                        probability_left_faster(existing_times, new_times), 4
                    ),
                    "unauthenticated_email_reservation": reserve.status_code,
                    "later_same_email": later_claim.status_code,
                },
            }
            reusable = {
                "principal_id": owner_a["principal_id"],
                "tenant_id": owner_a["tenant_id"],
                "membership_id": owner_a["membership_id"],
            }
            return output, reusable
    finally:
        kernel.stop()


def measure_flag_unset(run_id: str, reusable: dict[str, str]) -> dict:
    kernel = start_kernel(allow_unauthenticated=False, authenticator=None)
    try:
        with httpx.Client(base_url=kernel.base_url, timeout=10) as client:
            principal = register_principal(
                client, f"authd3-{run_id}-flag-unset@example.com"
            )
            expect(principal, 201, "flag-unset principal")
            principal_id = principal.json()["principal_id"]
            tenant = provision_tenant(
                client, principal_id, f"AUTH-D3 {run_id} flag unset"
            )
            expect(tenant, 503, "flag-unset tenant")
            context = establish_context(
                client,
                reusable["tenant_id"],
                reusable["principal_id"],
                reusable["membership_id"],
            )
            expect(context, 503, "flag-unset context")
            duplicate = register_principal(
                client, f"authd3-{run_id}-flag-unset@example.com"
            )
            expect(duplicate, 409, "flag-unset account oracle")
            return {
                "runtime": {"profile": "no_authenticator_allow_flag_unset"},
                "principal_status": principal.status_code,
                "tenant_status": tenant.status_code,
                "context_status": context.status_code,
                "duplicate_principal_status": duplicate.status_code,
            }
    finally:
        kernel.stop()


def measure_authenticator_configured(run_id: str) -> dict:
    private = Ed25519PrivateKey.generate()
    public_pem = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    authenticator = {
        AUTH_ENV[0]: "https://authd3-assessment.invalid",
        AUTH_ENV[1]: public_pem,
        AUTH_ENV[2]: "bopen-authd3-assessment",
    }
    kernel = start_kernel(allow_unauthenticated=True, authenticator=authenticator)
    try:
        with httpx.Client(base_url=kernel.base_url, timeout=10) as client:
            principal = register_principal(
                client, f"authd3-{run_id}-configured@example.com"
            )
            expect(principal, 201, "configured-authenticator principal")
            principal_id = principal.json()["principal_id"]
            tenant = provision_tenant(
                client, principal_id, f"AUTH-D3 {run_id} configured authenticator"
            )
            expect(tenant, 201, "configured-authenticator tenant")
            tenant_body = tenant.json()
            context = establish_context(
                client,
                tenant_body["tenant_id"],
                principal_id,
                tenant_body["owner_membership_id"],
            )
            expect(context, 401, "configured-authenticator context without assertion")
            return {
                "runtime": {"profile": "authenticator_configured_allow_flag_set"},
                "principal_status": principal.status_code,
                "tenant_status": tenant.status_code,
                "context_status": context.status_code,
                "context_body": context.json(),
            }
    finally:
        kernel.stop()


def main() -> int:
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        raise RuntimeError("BOPEN_DATABASE_URL must be loaded from .env.local")
    if not os.environ.get("BOPEN_CONTEXT_TOKEN_KEY", "").strip():
        raise RuntimeError("BOPEN_CONTEXT_TOKEN_KEY must be loaded from .env.local")

    run_id = uuid.uuid4().hex[:10]
    open_profile, reusable = measure_open_profile(run_id)
    flag_unset = measure_flag_unset(run_id, reusable)
    configured = measure_authenticator_configured(run_id)
    print(
        json.dumps(
            {
                "run_id": run_id,
                "open_profile": open_profile,
                "flag_unset": flag_unset,
                "authenticator_configured": configured,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
