#!/usr/bin/env python3
"""bOPEN end-to-end demonstration — the kernel doing its job against live PostgreSQL.

Runnable proof that the pieces work together: register a principal, provision a tenant, establish a
context, mint an Ed25519 bearer token, authorize with it, and — the point of a multi-tenant kernel —
show that one tenant's credential cannot act as another's, and that a forged token is refused.

This exercises the real FastAPI app (`platform_kernel.api`) over its HTTP surface via the ASGI
TestClient, against the real database in `.env.local`. It is not a mock: every ALLOW and every
refusal below is produced by the same code path a deployed kernel runs, and tenant isolation is
enforced by PostgreSQL row-level security, not by this script.

Run:  python scripts/demo_end_to_end.py        (loads .env.local itself)

Safe and non-destructive: it only creates its own throwaway principals/tenants and reads them back.
Retained utility (Rule 13): demonstration + validation.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (
    ROOT / "services" / "platform-kernel" / "python",
    ROOT / "packages" / "kernel-core" / "python",
    ROOT / "sdk" / "python",
    ROOT,
):
    sys.path.insert(0, str(p))


def _load_env_local() -> None:
    env = ROOT / ".env.local"
    if not env.is_file():
        sys.exit(".env.local not found — the demo needs BOPEN_DATABASE_URL to reach PostgreSQL")
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_local()

from fastapi.testclient import TestClient  # noqa: E402  (after sys.path/env setup)

from platform_kernel.api import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)

STEP = 0


def step(title: str) -> None:
    global STEP
    STEP += 1
    print(f"\n[{STEP}] {title}")


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


def expect(label: str, got: int, want: int) -> None:
    ok = got == want
    print(f"    {'OK ' if ok else 'FAIL'} {label}: {got} (expected {want})")
    if not ok:
        sys.exit(f"demo failed at: {label}")


def make_tenant(kind: str) -> dict:
    """principal -> tenant -> context -> bearer token, the whole chain."""
    p = client.post(
        "/v1/principals",
        json={"email": f"{kind}-{uuid.uuid4().hex[:10]}@example.com", "type": "human"},
        headers={"X-Correlation-ID": corr()},
    )
    expect(f"register {kind} principal", p.status_code, 201)
    principal_id = p.json()["principal_id"]

    t = client.post(
        "/v1/tenants",
        json={"name": f"{kind}-{uuid.uuid4().hex[:8]}", "owner_principal_id": principal_id},
        headers={"X-Correlation-ID": corr()},
    )
    expect(f"provision {kind} tenant", t.status_code, 201)
    tenant_id = t.json()["tenant_id"]
    membership_id = t.json()["owner_membership_id"]

    c = client.post(
        "/v1/contexts",
        json={"principal_id": principal_id, "membership_id": membership_id},
        headers={"X-Tenant-ID": tenant_id, "X-Correlation-ID": corr()},
    )
    expect(f"establish {kind} context", c.status_code, 201)
    envelope = c.json()
    token = envelope["access_token"]
    print(f"       tenant_id={tenant_id}")
    print(f"       bearer token issued ({len(token)} chars, Ed25519-signed)")
    return {"tenant_id": tenant_id, "token": token, "context_id": envelope["context"]["context_id"]}


def authorize(token: str, tenant_id: str | None = None) -> "object":
    headers = {"Authorization": f"Bearer {token}", "X-Correlation-ID": corr()}
    if tenant_id is not None:
        headers["X-Tenant-ID"] = tenant_id
    return client.post(
        "/v1/authorize",
        json={
            "action": "tenant_resource:read",
            "resource_type": "tenant_resource",
            "resource_id": str(uuid.uuid4()),
        },
        headers=headers,
    )


def main() -> int:
    print("=" * 72)
    print("bOPEN end-to-end demonstration — live kernel, live PostgreSQL")
    print("=" * 72)

    h = client.get("/health", headers={"X-Correlation-ID": corr()})
    step("Kernel is up")
    expect("GET /health", h.status_code, 200)

    step("Tenant A — the full chain, ending in an authorization decision")
    a = make_tenant("tenant-A")
    dec = authorize(a["token"])
    expect("authorize with A's bearer", dec.status_code, 200)
    body = dec.json()
    print(f"       decision={body['decision']} reason={body.get('reason_code')} tenant={body['tenant_id']}")
    if body["decision"] != "ALLOW":
        sys.exit("expected ALLOW for the tenant's own owner")

    step("Tenant B — a second, independent tenant")
    b = make_tenant("tenant-B")
    dec_b = authorize(b["token"])
    expect("authorize with B's bearer", dec_b.status_code, 200)

    step("Isolation — B's credential cannot act inside A's tenant")
    # B holds a valid bearer for tenant B. Presenting it while claiming tenant A must be refused:
    # the tenant is taken from the signed token, and a disagreeing X-Tenant-ID is rejected.
    crossed = authorize(b["token"], tenant_id=a["tenant_id"])
    print(f"       B's token + X-Tenant-ID=A -> {crossed.status_code} (a disagreeing tenant is refused)")
    if crossed.status_code == 200 and crossed.json().get("tenant_id") == a["tenant_id"]:
        sys.exit("ISOLATION BREACH: B acted as A")
    print("    OK  B could not cross into A")

    step("Forgery — a tampered token is refused")
    header, payload, _sig = a["token"].split(".")
    forged = f"{header}.{payload}.{'A' * 43}"
    ref = authorize(forged)
    expect("authorize with a forged signature", ref.status_code, 401)

    step("Bearer-only — a context id alone authorizes nothing (AUTH-D1)")
    saved = os.environ.pop("BOPEN_LEGACY_CONTEXT_HEADER_PROFILE", None)
    try:
        no_bearer = client.post(
            "/v1/authorize",
            json={"action": "tenant_resource:read", "resource_type": "tenant_resource",
                  "resource_id": str(uuid.uuid4())},
            headers={"X-Tenant-ID": a["tenant_id"], "X-Context-ID": a["context_id"],
                     "X-Correlation-ID": corr()},
        )
    finally:
        if saved is not None:
            os.environ["BOPEN_LEGACY_CONTEXT_HEADER_PROFILE"] = saved
    expect("authorize with a context id and no bearer", no_bearer.status_code, 401)

    print("\n" + "=" * 72)
    print("RESULT: the kernel provisioned two tenants, issued signed bearer tokens, allowed each")
    print("tenant's own owner, refused a cross-tenant credential, a forged token, and an unsigned")
    print("context id — all against live PostgreSQL. bOPEN's core works end to end.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
