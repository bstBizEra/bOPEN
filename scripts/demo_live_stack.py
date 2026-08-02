#!/usr/bin/env python3
"""bOPEN live-stack demonstration — the real gateway and kernel, over real sockets.

Where `demo_end_to_end.py` drives the kernel in-process (ASGI TestClient), this starts the two
services as actual processes and sends HTTP over the loopback:

    curl -> Hono gateway (:8788) -> FastAPI kernel (:8001) -> PostgreSQL

It proves the full stack end to end: the gateway validates at the edge and forwards, the kernel
provisions tenants and issues Ed25519 bearer tokens, and the multi-tenant guarantees hold across
the wire. It also shows two things only the gateway does — reject a header-contract violation before
the kernel is touched, and cap creation with the AUTH-D3 Row 1(b) rate limit.

Run:  python scripts/demo_live_stack.py

Self-contained: starts both servers, runs the flow, and tears them down in a finally block. Binds
loopback only. Safe, non-destructive, re-runnable. Retained utility (Rule 13): demonstration.
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
KERNEL_PORT = 8001
GATEWAY_PORT = 8788
KERNEL = f"http://127.0.0.1:{KERNEL_PORT}"
GATEWAY = f"http://127.0.0.1:{GATEWAY_PORT}"


def load_env_local() -> dict:
    env = dict(os.environ)
    f = ROOT / ".env.local"
    if not f.is_file():
        sys.exit(".env.local not found — needs BOPEN_DATABASE_URL")
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
            status, _ = request("GET", url, headers={"X-Correlation-ID": f"corr_{uuid.uuid4()}"})
            if status == 200:
                print(f"    OK  {label} healthy ({url})")
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise SystemExit(f"{label} did not become healthy at {url}")


def corr() -> str:
    return f"corr_{uuid.uuid4()}"


def hdr(extra=None) -> dict:
    h = {"X-Correlation-ID": corr(), "X-Forwarded-For": "203.0.113.10"}
    if extra:
        h.update(extra)
    return h


def main() -> int:
    env = load_env_local()
    pythonpath = os.pathsep.join(
        str(ROOT / p) for p in (
            "services/platform-kernel/python", "packages/kernel-core/python", "sdk/python", ".",
        )
    )
    env["PYTHONPATH"] = pythonpath

    print("=" * 72)
    print("bOPEN live-stack demonstration — real gateway + kernel over sockets")
    print("=" * 72)

    procs = []
    try:
        print("\n[1] Starting the kernel (uvicorn)")
        kernel = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "platform_kernel.api:app",
             "--host", "127.0.0.1", "--port", str(KERNEL_PORT), "--log-level", "warning"],
            cwd=str(ROOT), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(kernel)
        wait_healthy(f"{KERNEL}/health", "kernel")

        print("\n[2] Starting the gateway (node, pointing at the kernel)")
        genv = dict(env)
        genv["BOPEN_KERNEL_BASE_URL"] = KERNEL
        genv["BOPEN_GATEWAY_PORT"] = str(GATEWAY_PORT)
        genv["BOPEN_GATEWAY_HOST"] = "127.0.0.1"
        gateway = subprocess.Popen(
            ["node", "src/index.ts"],
            cwd=str(ROOT / "apps" / "gateway"), env=genv,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(gateway)
        wait_healthy(f"{GATEWAY}/gateway/health", "gateway")

        print("\n[3] Full chain THROUGH THE GATEWAY: principal -> tenant -> context -> authorize")
        s, p = request("POST", f"{GATEWAY}/v1/principals",
                       headers=hdr(), body={"email": f"live-{uuid.uuid4().hex[:10]}@example.com", "type": "human"})
        assert s == 201, (s, p)
        principal_id = p["principal_id"]
        s, t = request("POST", f"{GATEWAY}/v1/tenants",
                       headers=hdr(), body={"name": f"live-{uuid.uuid4().hex[:8]}", "owner_principal_id": principal_id})
        assert s == 201, (s, t)
        tenant_id, membership_id = t["tenant_id"], t["owner_membership_id"]
        s, c = request("POST", f"{GATEWAY}/v1/contexts",
                       headers=hdr({"X-Tenant-ID": tenant_id}),
                       body={"principal_id": principal_id, "membership_id": membership_id})
        assert s == 201, (s, c)
        token = c["access_token"]
        print(f"    OK  provisioned tenant {tenant_id} and minted a bearer token, all via the gateway")

        s, d = request("POST", f"{GATEWAY}/v1/authorize",
                       headers=hdr({"Authorization": f"Bearer {token}"}),
                       body={"action": "tenant_resource:read", "resource_type": "tenant_resource",
                             "resource_id": str(uuid.uuid4())})
        print(f"    OK  authorize through the gateway -> {s} {d.get('decision')} ({d.get('reason_code')})")
        assert s == 200 and d["decision"] == "ALLOW", (s, d)

        print("\n[4] The gateway rejects a header-contract violation before the kernel is touched")
        s, v = request("POST", f"{GATEWAY}/v1/principals",
                       headers={"X-Forwarded-For": "203.0.113.10"},  # no X-Correlation-ID
                       body={"email": "x@example.com", "type": "human"})
        print(f"    OK  missing X-Correlation-ID -> {s} (gateway 400, never forwarded)")
        assert s == 400, (s, v)

        print("\n[5] AUTH-D3 Row 1(b): the gateway caps creation from one source")
        codes = []
        for _ in range(14):  # default per-source limit is 10/min
            s, _ = request("POST", f"{GATEWAY}/v1/principals",
                           headers=hdr(), body={"email": f"flood-{uuid.uuid4().hex[:8]}@example.com", "type": "human"})
            codes.append(s)
        limited = sum(1 for x in codes if x == 429)
        print(f"    OK  14 rapid creations from one source -> {codes.count(201)} allowed, {limited} rate-limited (429)")
        assert limited > 0, f"expected some 429s, got {codes}"

        print("\n" + "=" * 72)
        print("RESULT: real HTTP traversed gateway -> kernel -> PostgreSQL. The edge validated and")
        print("forwarded, the kernel provisioned a tenant and authorized its owner, and the gateway")
        print("refused a malformed request and capped a creation flood. Full stack works.")
        print("=" * 72)
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
