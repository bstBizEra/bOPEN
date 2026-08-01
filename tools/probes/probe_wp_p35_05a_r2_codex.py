#!/usr/bin/env python3
"""Independent WP-P35-05a R2 HTTP probes against the configured PostgreSQL instance."""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from platform_kernel import subject_assertion
from platform_kernel.api import app, legacy_context_header_profile_enabled


ISSUER = "https://codex-verifier.invalid"
AUDIENCE = "bopen-codex-verifier"
AUTH_ENV = (
    subject_assertion.ENV_ASSERTION_ISSUER,
    subject_assertion.ENV_ASSERTION_PUBLIC_KEY,
    subject_assertion.ENV_ASSERTION_AUDIENCE,
)


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


def keypair() -> tuple[Ed25519PrivateKey, str]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return private, public


def assertion(
    private: Ed25519PrivateKey,
    subject: str,
    *,
    issuer: str = ISSUER,
    audience: str = AUDIENCE,
    lifetime: timedelta = timedelta(minutes=2),
    omit: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if omit:
        claims.pop(omit)
    private_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return jwt.encode(claims, private_pem, algorithm="EdDSA")


def headers(**extra: str) -> dict[str, str]:
    result = {"X-Correlation-ID": corr()}
    result.update(extra)
    return result


def expect(response, status: int, label: str) -> None:
    if response.status_code != status:
        raise AssertionError(f"{label}: expected {status}, got {response.status_code}: {response.text}")


def configure(public_key: str | None, *, issuer: str | None = ISSUER,
              audience: str | None = AUDIENCE) -> None:
    values = dict(zip(AUTH_ENV, (issuer, public_key, audience)))
    for name, value in values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def context_request(client: TestClient, tenant: str, principal: str, membership: str,
                    token: str | None = None):
    request_headers = headers(**{"X-Tenant-ID": tenant})
    if token is not None:
        request_headers["X-Subject-Assertion"] = token
    return client.post(
        "/v1/contexts",
        json={"principal_id": principal, "membership_id": membership},
        headers=request_headers,
    )


def main() -> int:
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        raise RuntimeError("BOPEN_DATABASE_URL must be loaded from .env.local")

    saved = {name: os.environ.get(name) for name in (*AUTH_ENV, "BOPEN_ENV",
                                                      "BOPEN_LEGACY_CONTEXT_HEADER_PROFILE")}
    client = TestClient(app, raise_server_exceptions=False)
    results: dict[str, object] = {}
    try:
        configure(None, issuer=None, audience=None)
        os.environ.pop("BOPEN_LEGACY_CONTEXT_HEADER_PROFILE", None)

        # AUTH-D3 control: both enrollment routes remain public and create real database rows.
        principal_response = client.post(
            "/v1/principals",
            json={"email": f"codex-{uuid.uuid4().hex}@example.com", "type": "human"},
            headers=headers(),
        )
        expect(principal_response, 201, "AUTH-D3 principal enrollment")
        principal = principal_response.json()["principal_id"]
        tenant_response = client.post(
            "/v1/tenants",
            json={"name": f"Codex probe {uuid.uuid4().hex[:10]}",
                  "owner_principal_id": principal},
            headers=headers(),
        )
        expect(tenant_response, 201, "AUTH-D3 tenant enrollment")
        tenant = tenant_response.json()["tenant_id"]
        membership = tenant_response.json()["owner_membership_id"]
        results["auth_d3_public_statuses"] = [principal_response.status_code,
                                               tenant_response.status_code]

        # P35-05a-11 control: with no authenticator, the prior flag-guarded issuance path works.
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
        expect(client.post("/v1/authorize", json=authorize_body, headers=protected_headers),
               200, "valid bearer control")
        created = client.post("/v1/resources?resource_name=codex-probe",
                              headers=protected_headers)
        expect(created, 201, "valid bearer resource creation control")
        resource_id = created.json()["resource_id"]
        expect(client.get(f"/v1/resources/{resource_id}", headers=protected_headers),
               200, "valid bearer resource read control")
        expect(client.get("/v1/audit-events", headers=protected_headers),
               200, "valid bearer audit control")

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

        # Carried propositions P35-05a-02..10, through the live HTTP boundary.
        configure(public, audience=None)
        expect(context_request(client, tenant, principal, membership), 503,
               "partial authenticator configuration")
        configure(public)
        expect(context_request(client, tenant, principal, membership,
                               assertion(private, str(uuid.uuid4()))),
               403, "assertion principal mismatch")

        refusal_cases = {
            "unknown_key": assertion(other_private, principal),
            "wrong_issuer": assertion(private, principal, issuer="https://other.invalid"),
            "wrong_audience": assertion(private, principal, audience="other-service"),
            "expired": assertion(private, principal, lifetime=timedelta(hours=-2)),
            "missing_claim": assertion(private, principal, omit="jti"),
        }
        now = datetime.now(timezone.utc)
        refusal_cases["alg_none"] = jwt.encode(
            {"iss": ISSUER, "aud": AUDIENCE, "sub": principal,
             "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=2)).timestamp()),
             "jti": str(uuid.uuid4())},
            key="", algorithm="none",
        )
        refusal_statuses = {}
        for label, token in refusal_cases.items():
            response = context_request(client, tenant, principal, membership, token)
            expect(response, 401, label)
            if response.json().get("detail") != "assertion is not valid":
                raise AssertionError(f"{label}: refusal reason was disclosed: {response.text}")
            refusal_statuses[label] = response.status_code
        results["assertion_refusal_statuses"] = refusal_statuses

        # Disclosed residual defects. These are observations, not claims in this submission.
        ten_year = context_request(
            client, tenant, principal, membership,
            assertion(private, principal, lifetime=timedelta(days=3650)),
        )
        expect(ten_year, 201, "ten-year assertion remains accepted")

        configure("not a PEM")
        malformed_pem = context_request(client, tenant, principal, membership, "opaque")
        expect(malformed_pem, 500, "malformed PEM remains an unhandled server error")

        configure(public)
        non_uuid = context_request(client, tenant, principal, membership,
                                   assertion(private, "external-subject-opaque"))
        bad_signature = context_request(client, tenant, principal, membership,
                                        assertion(other_private, principal))
        expect(non_uuid, 400, "valid non-UUID subject oracle")
        expect(bad_signature, 401, "bad-signature oracle control")
        results["open_defects"] = {
            "ten_year_assertion": ten_year.status_code,
            "malformed_pem": malformed_pem.status_code,
            "valid_non_uuid_sub": non_uuid.status_code,
            "bad_signature": bad_signature.status_code,
            "sub_must_be_bopen_uuid": non_uuid.status_code == 400,
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
