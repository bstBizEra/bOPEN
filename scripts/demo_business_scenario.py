#!/usr/bin/env python3
"""bOPEN business-scenario demonstration — the success target (BOPEN-NEXT-SUCCESS-TARGET.md).

This is bOPEN doing the thing a business actually uses: two tenants each keep their own **parties**
(customers, vendors, organizations) and the **relationships** between them, all over real HTTP
through the gateway to the kernel to PostgreSQL — and then the proof, that tenant B cannot see or
touch a single one of tenant A's parties or relationships, because the database refuses it.

    curl -> Hono gateway (:8790) -> FastAPI kernel (:8003) -> PostgreSQL

Every write goes through a signed Ed25519 bearer token. Isolation is PostgreSQL row-level security,
not this script. Placement routing (WP-P35-06) resolves each tenant fail-closed on the way in.

Run:  python scripts/demo_business_scenario.py

Self-contained: starts both servers, runs the scenario, and tears them down in a finally block.
Loopback only. Safe, non-destructive, re-runnable. Retained utility (Rule 13): demonstration.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_PORT = 8003
GATEWAY_PORT = 8790
KERNEL = f"http://127.0.0.1:{KERNEL_PORT}"
GATEWAY = f"http://127.0.0.1:{GATEWAY_PORT}"


def load_env_local() -> dict:
    env = dict(os.environ)
    f = ROOT / ".env.local"
    if not f.is_file():
        sys.exit(".env.local not found — needs BOPEN_DATABASE_URL and BOPEN_CONTEXT_TOKEN_KEY")
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def request(method: str, url: str, *, headers=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or b"null")
        except Exception:
            return e.code, raw.decode(errors="replace")


def wait_healthy(url: str, label: str, tries=40) -> None:
    for _ in range(tries):
        try:
            s, _ = request("GET", url, headers={"X-Correlation-ID": f"corr_{uuid.uuid4()}"})
            if s == 200:
                print(f"    OK  {label} up ({url})")
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit(f"{label} did not become healthy at {url}")


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


def hdr(token: str | None = None) -> dict:
    h = {"X-Correlation-ID": corr(), "X-Forwarded-For": "203.0.113.10"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def onboard_tenant(label: str) -> dict:
    """principal -> tenant -> context -> bearer token, all through the gateway."""
    s, p = request("POST", f"{GATEWAY}/v1/principals",
                   headers=hdr(), body={"email": f"{label}-{uuid.uuid4().hex[:8]}@example.com", "type": "human"})
    assert s == 201, (s, p)
    s, t = request("POST", f"{GATEWAY}/v1/tenants",
                   headers=hdr(), body={"name": label, "owner_principal_id": p["principal_id"]})
    assert s == 201, (s, t)
    s, c = request("POST", f"{GATEWAY}/v1/contexts",
                   headers=hdr() | {"X-Tenant-ID": t["tenant_id"]},
                   body={"principal_id": p["principal_id"], "membership_id": t["owner_membership_id"]})
    assert s == 201, (s, c)
    print(f"    OK  onboarded {label}: tenant {t['tenant_id'][:8]}…, bearer issued")
    return {"tenant_id": t["tenant_id"], "token": c["access_token"]}


def make_party(token: str, name: str, kind: str = "organization") -> str:
    s, p = request("POST", f"{GATEWAY}/v1/parties",
                   headers=hdr(token), body={"party_type": kind, "display_name": name})
    assert s == 201, (s, p)
    return p["party_id"]


def main() -> int:
    env = load_env_local()
    env["PYTHONPATH"] = os.pathsep.join(
        str(ROOT / p) for p in (
            "services/platform-kernel/python", "packages/kernel-core/python", "sdk/python", ".",
        )
    )
    print("=" * 74)
    print("bOPEN business scenario — two tenants, their parties, their privacy")
    print("=" * 74)

    procs = []
    try:
        print("\n[1] Bring up the stack (kernel + gateway)")
        procs.append(subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "platform_kernel.api:app",
             "--host", "127.0.0.1", "--port", str(KERNEL_PORT), "--log-level", "warning"],
            cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        wait_healthy(f"{KERNEL}/health", "kernel")
        genv = dict(env, BOPEN_KERNEL_BASE_URL=KERNEL,
                    BOPEN_GATEWAY_PORT=str(GATEWAY_PORT), BOPEN_GATEWAY_HOST="127.0.0.1")
        procs.append(subprocess.Popen(
            ["node", "src/index.ts"], cwd=str(ROOT / "apps" / "gateway"), env=genv,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        wait_healthy(f"{GATEWAY}/gateway/health", "gateway")

        print("\n[2] Onboard two independent tenants — Northwind and Globex")
        north = onboard_tenant("Northwind")
        globex = onboard_tenant("Globex")

        print("\n[3] Northwind builds its own book of business (parties + a relationship)")
        acme = make_party(north["token"], "Acme Manufacturing", "organization")
        jane = make_party(north["token"], "Jane the Buyer", "person")
        s, rel = request("POST", f"{GATEWAY}/v1/party-relationships",
                         headers=hdr(north["token"]),
                         body={"from_party_id": acme, "to_party_id": jane, "relationship_type": "supplies"})
        assert s == 201, (s, rel)
        print(f"    OK  Acme Manufacturing --supplies--> Jane the Buyer  (in Northwind only)")

        print("\n[4] Globex builds its own, separately")
        make_party(globex["token"], "Globex Logistics", "organization")
        s, mine = request("GET", f"{GATEWAY}/v1/parties", headers=hdr(globex["token"]))
        print(f"    OK  Globex sees {len(mine)} party of its own")

        print("\n[5] Privacy — Globex cannot reach into Northwind (the whole point)")
        s, _ = request("GET", f"{GATEWAY}/v1/parties/{acme}", headers=hdr(globex["token"]))
        print(f"    Globex reads Northwind's Acme party      -> {s} (must be 404)")
        assert s == 404, "ISOLATION BREACH: Globex read Northwind's party"
        globex_party = make_party(globex["token"], "Globex smuggling attempt")
        s, _ = request("POST", f"{GATEWAY}/v1/party-relationships", headers=hdr(globex["token"]),
                       body={"from_party_id": globex_party, "to_party_id": acme, "relationship_type": "owns"})
        print(f"    Globex links its party to Northwind's    -> {s} (must be 422)")
        assert s == 422, "ISOLATION BREACH: Globex formed a cross-tenant relationship"
        s, _ = request("POST", f"{GATEWAY}/v1/parties", headers=hdr(),  # no bearer
                       body={"party_type": "person", "display_name": "anon"})
        print(f"    Anyone creates a party with no bearer    -> {s} (must be 401)")
        assert s == 401, "a party was created without authentication"
        print("    OK  every cross-tenant and unauthenticated attempt was refused")

        print("\n" + "=" * 74)
        print("RESULT: two tenants ran their own business data end to end through the gateway,")
        print("each isolated from the other by PostgreSQL — a private customer graph one tenant")
        print("cannot see, cannot link to, and cannot touch without its own signed token.")
        print("bOPEN works.")
        print("=" * 74)
        return 0
    finally:
        for pr in reversed(procs):
            try:
                pr.terminate()
                pr.wait(timeout=5)
            except Exception:
                try:
                    pr.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
