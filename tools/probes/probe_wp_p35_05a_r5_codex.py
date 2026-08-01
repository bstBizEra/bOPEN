#!/usr/bin/env python3
"""Independent defensive probes for the WP-P35-05a R5 refusal boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = "ce97561bf21106c35c473bf71c0afee835443a35"
TREE = "1157ba87f78936f316f5d9741e31758a64c6e806"
API_BLOB = "646cf4121a89161e89f432b5da346d211f437389"
ASSERTION_BLOB = "ada0eb1de30f5d78798947744f0219585ff43d07"
ISSUER = "https://codex-r5-verifier.invalid"
AUDIENCE = "bopen-kernel-codex-r5"

sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))

from platform_kernel import subject_assertion  # noqa: E402
from platform_kernel.api import app  # noqa: E402


AUTH_ENV = (
    subject_assertion.ENV_ASSERTION_ISSUER,
    subject_assertion.ENV_ASSERTION_PUBLIC_KEY,
    subject_assertion.ENV_ASSERTION_AUDIENCE,
)


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def bind_candidate() -> dict[str, str]:
    observed = {
        "commit": git("rev-parse", f"{CANDIDATE}^{{commit}}"),
        "tree": git("rev-parse", f"{CANDIDATE}^{{tree}}"),
        "api_blob": git("rev-parse", f"{CANDIDATE}:services/platform-kernel/python/platform_kernel/api.py"),
        "assertion_blob": git(
            "rev-parse",
            f"{CANDIDATE}:services/platform-kernel/python/platform_kernel/subject_assertion.py",
        ),
    }
    expected = {
        "commit": CANDIDATE,
        "tree": TREE,
        "api_blob": API_BLOB,
        "assertion_blob": ASSERTION_BLOB,
    }
    if observed != expected:
        raise RuntimeError(f"candidate binding mismatch: {observed!r}")

    result = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            CANDIDATE,
            "--",
            "services",
            "packages",
            "contracts",
            "tests",
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("live executable or test bytes differ from the R5 candidate")
    return observed


def private_pem(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def public_pem(key: Ed25519PrivateKey) -> str:
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def assertion(
    key: Ed25519PrivateKey,
    subject: str,
    *,
    lifetime: float = 120,
    issued_at: int | None = None,
) -> str:
    iat = int(time.time()) if issued_at is None else issued_at
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": subject,
            "iat": iat,
            "exp": iat + lifetime,
            "jti": str(uuid.uuid4()),
        },
        private_pem(key),
        algorithm="EdDSA",
    )


def expect(response: object, status: int, label: str) -> None:
    actual = getattr(response, "status_code")
    if actual != status:
        body = getattr(response, "text", "")
        raise AssertionError(f"{label}: expected {status}, got {actual}: {body}")


def correlation_headers(**extra: str) -> dict[str, str]:
    return {"X-Correlation-ID": str(uuid.uuid4()), **extra}


def register_principal(client: TestClient, label: str) -> str:
    response = client.post(
        "/v1/principals",
        json={"email": f"codex-r5-{label}-{uuid.uuid4().hex}@example.com", "type": "human"},
        headers=correlation_headers(),
    )
    expect(response, 201, f"register {label} principal")
    return response.json()["principal_id"]


def provision(
    client: TestClient,
    owner: str,
    token: str | None,
    *,
    label: str,
):
    headers = correlation_headers()
    if token is not None:
        headers["X-Subject-Assertion"] = token
    return client.post(
        "/v1/tenants",
        json={"name": f"Codex R5 {label} {uuid.uuid4().hex[:10]}", "owner_principal_id": owner},
        headers=headers,
    )


def establish_context(
    client: TestClient,
    tenant: str,
    principal: str,
    membership: str,
    token: str,
):
    return client.post(
        "/v1/contexts",
        json={"principal_id": principal, "membership_id": membership},
        headers=correlation_headers(
            **{"X-Tenant-ID": tenant, "X-Subject-Assertion": token}
        ),
    )


@contextmanager
def preserved_environment(*names: str) -> Iterator[None]:
    saved = {name: os.environ.get(name) for name in names}
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def configure_authenticator(key: Ed25519PrivateKey) -> None:
    os.environ[subject_assertion.ENV_ASSERTION_ISSUER] = ISSUER
    os.environ[subject_assertion.ENV_ASSERTION_PUBLIC_KEY] = public_pem(key)
    os.environ[subject_assertion.ENV_ASSERTION_AUDIENCE] = AUDIENCE


def main() -> int:
    if not os.environ.get("BOPEN_DATABASE_URL", "").strip():
        raise RuntimeError("BOPEN_DATABASE_URL must be sourced from .env.local")

    binding = bind_candidate()
    client = TestClient(app, raise_server_exceptions=False)
    signing_key = Ed25519PrivateKey.generate()
    forged_key = Ed25519PrivateKey.generate()
    results: dict[str, object] = {"binding": binding}

    with preserved_environment(
        *AUTH_ENV,
        "BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION",
    ):
        configure_authenticator(signing_key)
        owner = register_principal(client, "owner")
        other = register_principal(client, "other")

        # Group B: every invalid or unauthorized provisioning path must refuse.
        no_assertion = provision(client, owner, None, label="no-assertion")
        expect(no_assertion, 401, "configured authenticator without assertion")

        wrong_subject = provision(
            client,
            owner,
            assertion(signing_key, other),
            label="wrong-subject",
        )
        expect(wrong_subject, 403, "assertion for a principal other than owner")

        accepted = provision(
            client,
            owner,
            assertion(signing_key, owner),
            label="valid-owner",
        )
        expect(accepted, 201, "assertion for named owner")

        forged = provision(
            client,
            owner,
            assertion(forged_key, owner),
            label="forged",
        )
        expect(forged, 401, "forged provisioning assertion")

        os.environ["BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION"] = "1"
        dev_flag = provision(client, owner, None, label="dev-flag")
        expect(dev_flag, 401, "development flag with configured authenticator")

        tenant = accepted.json()["tenant_id"]
        membership = accepted.json()["owner_membership_id"]

        # Group A: exercise the inherited R4 boundary through live HTTP and PostgreSQL state.
        integer_iat = int(time.time())
        fractional = establish_context(
            client,
            tenant,
            owner,
            membership,
            assertion(signing_key, owner, lifetime=300.1, issued_at=integer_iat),
        )
        expect(fractional, 401, "300.1-second assertion with integer iat")

        exact = establish_context(
            client,
            tenant,
            owner,
            membership,
            assertion(signing_key, owner, lifetime=300, issued_at=integer_iat),
        )
        expect(exact, 201, "exactly 300-second assertion")

        os.environ[subject_assertion.ENV_ASSERTION_PUBLIC_KEY] = "not a PEM public key"
        malformed_key = establish_context(
            client, tenant, owner, membership, "syntactically-opaque"
        )
        expect(malformed_key, 503, "malformed configured public key")
        configure_authenticator(signing_key)

        bad_subject = establish_context(
            client,
            tenant,
            owner,
            membership,
            assertion(signing_key, "x" * 36),
        )
        bad_signature = establish_context(
            client,
            tenant,
            owner,
            membership,
            assertion(forged_key, owner),
        )
        expect(bad_subject, 401, "valid signature with malformed subject")
        expect(bad_signature, 401, "forged context assertion")
        if bad_subject.content != bad_signature.content:
            raise AssertionError(
                "bad-subject and bad-signature 401 bodies are distinguishable"
            )

        # Refutation sensitivity: weakening the lifetime ceiling makes the over-limit
        # request succeed, proving the negative probe is coupled to the claimed mechanism.
        original_ceiling = subject_assertion.MAX_ASSERTION_LIFETIME
        subject_assertion.MAX_ASSERTION_LIFETIME = 301
        try:
            weakened_lifetime = establish_context(
                client,
                tenant,
                owner,
                membership,
                assertion(signing_key, owner, lifetime=300.1, issued_at=int(time.time())),
            )
        finally:
            subject_assertion.MAX_ASSERTION_LIFETIME = original_ceiling
        expect(weakened_lifetime, 201, "weakened lifetime-ceiling sensitivity control")

        results["group_a"] = {
            "fractional_300_1": fractional.status_code,
            "exact_300": exact.status_code,
            "malformed_key": malformed_key.status_code,
            "bad_subject": {
                "status": bad_subject.status_code,
                "body_hex": bad_subject.content.hex(),
            },
            "bad_signature": {
                "status": bad_signature.status_code,
                "body_hex": bad_signature.content.hex(),
            },
            "weakened_lifetime_control": weakened_lifetime.status_code,
        }
        results["group_b"] = {
            "no_assertion": no_assertion.status_code,
            "wrong_subject": wrong_subject.status_code,
            "valid_owner": accepted.status_code,
            "forged": forged.status_code,
            "dev_flag": dev_flag.status_code,
        }

    print(json.dumps(results, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
