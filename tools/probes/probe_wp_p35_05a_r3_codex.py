#!/usr/bin/env python3
"""Independent WP-P35-05a R3 probes against the live kernel and PostgreSQL."""

from __future__ import annotations

import io
import json
import logging
import os
import statistics
import sys
import time
import uuid
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import jwt
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from platform_kernel import subject_assertion
from platform_kernel.api import app, legacy_context_header_profile_enabled
from probe_wp_p35_05a_r2_codex import (
    AUDIENCE,
    AUTH_ENV,
    ISSUER,
    assertion,
    configure,
    context_request,
    expect,
    headers,
    keypair,
)


def timed_context_request(
    client: TestClient,
    tenant: str,
    principal: str,
    membership: str,
    token: str,
    correlation_id: str,
):
    started = time.perf_counter_ns()
    response = client.post(
        "/v1/contexts",
        json={"principal_id": principal, "membership_id": membership},
        headers={
            "X-Tenant-ID": tenant,
            "X-Correlation-ID": correlation_id,
            "X-Subject-Assertion": token,
        },
    )
    return response, time.perf_counter_ns() - started


def common_language_probability(left: list[int], right: list[int]) -> float:
    """Probability that a random left observation is greater than a random right one."""
    greater = sum(a > b for a in left for b in right)
    equal = sum(a == b for a in left for b in right)
    return (greater + 0.5 * equal) / (len(left) * len(right))


def main() -> int:
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        raise RuntimeError("BOPEN_DATABASE_URL must be loaded from .env.local")

    saved = {
        name: os.environ.get(name)
        for name in (*AUTH_ENV, "BOPEN_ENV", "BOPEN_LEGACY_CONTEXT_HEADER_PROFILE")
    }
    client = TestClient(app, raise_server_exceptions=False)
    results: dict[str, object] = {}
    try:
        configure(None, issuer=None, audience=None)
        os.environ.pop("BOPEN_LEGACY_CONTEXT_HEADER_PROFILE", None)

        # AUTH-D3 remains open. These calls also create real rows used by every later probe.
        principal_response = client.post(
            "/v1/principals",
            json={"email": f"codex-r3-{uuid.uuid4().hex}@example.com", "type": "human"},
            headers=headers(),
        )
        expect(principal_response, 201, "AUTH-D3 principal enrollment")
        principal = principal_response.json()["principal_id"]
        tenant_response = client.post(
            "/v1/tenants",
            json={
                "name": f"Codex R3 probe {uuid.uuid4().hex[:10]}",
                "owner_principal_id": principal,
            },
            headers=headers(),
        )
        expect(tenant_response, 201, "AUTH-D3 tenant enrollment")
        tenant = tenant_response.json()["tenant_id"]
        membership = tenant_response.json()["owner_membership_id"]
        results["auth_d3_public_statuses"] = [
            principal_response.status_code,
            tenant_response.status_code,
        ]

        # P35-05a-11 and bearer controls.
        no_auth_context = context_request(client, tenant, principal, membership)
        expect(no_auth_context, 201, "no-authenticator compatibility")
        envelope = no_auth_context.json()
        context_id = envelope["context"]["context_id"]
        bearer = envelope["access_token"]
        if not bearer:
            raise AssertionError("live context control did not issue a bearer token")

        protected_headers = headers(Authorization=f"Bearer {bearer}")
        authorize_body = {
            "action": "tenant_resource:read",
            "resource_type": "tenant_resource",
            "resource_id": str(uuid.uuid4()),
        }
        expect(
            client.post("/v1/authorize", json=authorize_body, headers=protected_headers),
            200,
            "valid bearer authorization control",
        )
        created = client.post(
            "/v1/resources?resource_name=codex-r3-probe", headers=protected_headers
        )
        expect(created, 201, "valid bearer resource creation control")
        resource_id = created.json()["resource_id"]
        expect(
            client.get(f"/v1/resources/{resource_id}", headers=protected_headers),
            200,
            "valid bearer resource read control",
        )
        expect(
            client.get("/v1/audit-events", headers=protected_headers),
            200,
            "valid bearer audit control",
        )

        legacy = headers(**{"X-Tenant-ID": tenant, "X-Context-ID": context_id})
        protected = {
            "authorize": client.post("/v1/authorize", json=authorize_body, headers=legacy),
            "read": client.get(f"/v1/resources/{resource_id}", headers=legacy),
            "write": client.post("/v1/resources?resource_name=blocked", headers=legacy),
            "audit": client.get("/v1/audit-events", headers=legacy),
        }
        for label, response in protected.items():
            expect(response, 401, f"header-only {label}")
        rejected = client.post(
            "/v1/authorize",
            json=authorize_body,
            headers=legacy | {"Authorization": "Bearer not.a.valid.token"},
        )
        expect(rejected, 401, "rejected bearer fallback")
        results["header_only_protected_statuses"] = {
            label: response.status_code for label, response in protected.items()
        }
        results["rejected_bearer_status"] = rejected.status_code

        os.environ.pop("BOPEN_LEGACY_CONTEXT_HEADER_PROFILE", None)
        if legacy_context_header_profile_enabled():
            raise AssertionError("legacy profile enabled while unset")
        os.environ["BOPEN_LEGACY_CONTEXT_HEADER_PROFILE"] = "1"
        os.environ["BOPEN_ENV"] = "production"
        if legacy_context_header_profile_enabled():
            raise AssertionError("legacy profile enabled in production")
        os.environ["BOPEN_ENV"] = "local"
        if not legacy_context_header_profile_enabled():
            raise AssertionError("legacy profile unavailable in local profile")
        os.environ.pop("BOPEN_LEGACY_CONTEXT_HEADER_PROFILE", None)
        results["legacy_profile"] = {"unset": False, "production": False, "local": True}

        private, public = keypair()
        other_private, _ = keypair()

        # P35-05aR3-01: malformed configured key is an operational refusal, not a crash.
        configure("not a PEM")
        malformed = context_request(client, tenant, principal, membership, "opaque")
        expect(malformed, 503, "malformed PEM")
        results["malformed_pem"] = {
            "status": malformed.status_code,
            "body": malformed.json(),
        }

        configure(public)

        # P35-05aR3-02 and R3-03: attack the exact lifetime boundary over HTTP.
        over_ceiling = context_request(
            client,
            tenant,
            principal,
            membership,
            assertion(private, principal, lifetime=timedelta(seconds=301)),
        )
        expect(over_ceiling, 401, "301-second assertion")
        at_ceiling = context_request(
            client,
            tenant,
            principal,
            membership,
            assertion(private, principal, lifetime=timedelta(seconds=300)),
        )
        expect(at_ceiling, 201, "300-second assertion")

        # NumericDate permits non-integer JSON numbers. The implementation converts both
        # endpoints to int before subtracting, so this genuinely-over-ceiling lifetime is
        # truncated to 300 and accepted. This is the refutation probe for R3-02 as worded.
        fractional_iat = int(time.time())
        private_pem = private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        fractional_over_token = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": principal,
                "iat": fractional_iat,
                "exp": fractional_iat + 300.9,
                "jti": str(uuid.uuid4()),
            },
            private_pem,
            algorithm="EdDSA",
        )
        fractional_over = context_request(
            client, tenant, principal, membership, fractional_over_token
        )
        expect(fractional_over, 201, "300.9-second assertion refutation")
        results["lifetime_boundary"] = {
            "301_seconds": over_ceiling.status_code,
            "300_seconds": at_ceiling.status_code,
            "300.9_seconds": fractional_over.status_code,
        }

        # P35-05aR3-04: equal-length tokens, interleaved order, raw response comparison,
        # logging capture, persistence check, and a timing distribution rather than one sample.
        bad_subject_token = assertion(private, "x" * 36)
        forged_token = assertion(other_private, principal)
        if len(bad_subject_token) != len(forged_token):
            raise AssertionError("R3-04 timing controls produced unequal token lengths")

        bad_subject_corr: list[str] = []
        forged_corr: list[str] = []
        root_logger = logging.getLogger()
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        root_logger.addHandler(handler)
        try:
            first_bad, _ = timed_context_request(
                client, tenant, principal, membership, bad_subject_token, f"corr_{uuid.uuid4()}"
            )
            first_forged, _ = timed_context_request(
                client, tenant, principal, membership, forged_token, f"corr_{uuid.uuid4()}"
            )
            expect(first_bad, 401, "valid signature with non-UUID subject")
            expect(first_forged, 401, "forged signature")
            if first_bad.content != first_forged.content:
                raise AssertionError("R3-04 bodies differ")
            if list(first_bad.headers.raw) != list(first_forged.headers.raw):
                raise AssertionError(
                    f"R3-04 raw headers differ: {first_bad.headers.raw!r} != "
                    f"{first_forged.headers.raw!r}"
                )

            bad_times: list[int] = []
            forged_times: list[int] = []
            for index in range(220):
                bad_corr = f"corr_{uuid.uuid4()}"
                forged_corr_id = f"corr_{uuid.uuid4()}"
                bad_subject_corr.append(bad_corr)
                forged_corr.append(forged_corr_id)
                order = (
                    ((bad_subject_token, bad_corr, bad_times),
                     (forged_token, forged_corr_id, forged_times))
                    if index % 2 == 0
                    else
                    ((forged_token, forged_corr_id, forged_times),
                     (bad_subject_token, bad_corr, bad_times))
                )
                for token, correlation_id, bucket in order:
                    response, elapsed = timed_context_request(
                        client, tenant, principal, membership, token, correlation_id
                    )
                    expect(response, 401, "R3-04 timed refusal")
                    if response.content != first_bad.content:
                        raise AssertionError("R3-04 body changed during timing sweep")
                    if list(response.headers.raw) != list(first_bad.headers.raw):
                        raise AssertionError("R3-04 headers changed during timing sweep")
                    bucket.append(elapsed)
        finally:
            root_logger.removeHandler(handler)

        audit_headers = headers(Authorization=f"Bearer {fractional_over.json()['access_token']}")
        audit_view = client.get("/v1/audit-events?limit=500", headers=audit_headers)
        expect(audit_view, 200, "R3-04 audit side-effect inspection")
        probe_correlations = set(bad_subject_corr + forged_corr)
        persisted = [
            event["correlation_id"]
            for event in audit_view.json()["events"]
            if event["correlation_id"] in probe_correlations
        ]
        if persisted:
            raise AssertionError(f"R3-04 refusals produced audit side effects: {persisted}")

        p_valid_slower = common_language_probability(bad_times, forged_times)
        results["r3_04_equivalence"] = {
            "status": first_bad.status_code,
            "body_hex": first_bad.content.hex(),
            "raw_headers": [
                [name.decode("latin1"), value.decode("latin1")]
                for name, value in first_bad.headers.raw
            ],
            "content_length": len(first_bad.content),
            "log_bytes": len(log_stream.getvalue().encode("utf-8")),
            "audit_side_effects": len(persisted),
            "samples_each": len(bad_times),
            "bad_subject_median_us": round(statistics.median(bad_times) / 1000, 1),
            "forged_median_us": round(statistics.median(forged_times) / 1000, 1),
            "p_bad_subject_slower": round(p_valid_slower, 4),
        }

        # Carried P35-05a-02..10.
        configure(public, audience=None)
        expect(
            context_request(client, tenant, principal, membership),
            503,
            "partial authenticator configuration",
        )
        configure(public)
        expect(
            context_request(
                client,
                tenant,
                principal,
                membership,
                assertion(private, str(uuid.uuid4())),
            ),
            403,
            "assertion principal mismatch",
        )

        refusal_cases = {
            "unknown_key": assertion(other_private, principal),
            "wrong_issuer": assertion(private, principal, issuer="https://other.invalid"),
            "wrong_audience": assertion(private, principal, audience="other-service"),
            "expired": assertion(private, principal, lifetime=timedelta(hours=-2)),
            "missing_claim": assertion(private, principal, omit="jti"),
        }
        now = int(time.time())
        refusal_cases["alg_none"] = jwt.encode(
            {
                "iss": ISSUER,
                "aud": AUDIENCE,
                "sub": principal,
                "iat": now,
                "exp": now + 120,
                "jti": str(uuid.uuid4()),
            },
            key="",
            algorithm="none",
        )
        refusal_statuses = {}
        for label, token in refusal_cases.items():
            response = context_request(client, tenant, principal, membership, token)
            expect(response, 401, label)
            if response.json().get("detail") != "assertion is not valid":
                raise AssertionError(f"{label}: refusal reason disclosed: {response.text}")
            refusal_statuses[label] = response.status_code
        results["assertion_refusal_statuses"] = refusal_statuses

        # Replay remains possible inside the new bound and mints distinct credentials.
        replayable = assertion(private, principal, lifetime=timedelta(seconds=120))
        replay_one = context_request(client, tenant, principal, membership, replayable)
        replay_two = context_request(client, tenant, principal, membership, replayable)
        expect(replay_one, 201, "first assertion use")
        expect(replay_two, 201, "assertion replay inside ceiling")
        distinct_contexts = (
            replay_one.json()["context"]["context_id"]
            != replay_two.json()["context"]["context_id"]
        )
        distinct_tokens = replay_one.json()["access_token"] != replay_two.json()["access_token"]
        if not (distinct_contexts and distinct_tokens):
            raise AssertionError("replay did not mint distinct context credentials")
        results["bounded_replay"] = {
            "statuses": [replay_one.status_code, replay_two.status_code],
            "distinct_contexts": distinct_contexts,
            "distinct_tokens": distinct_tokens,
        }

        print(json.dumps(results, sort_keys=True))
        return 0
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


if __name__ == "__main__":
    raise SystemExit(main())
