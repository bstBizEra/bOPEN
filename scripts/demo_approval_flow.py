#!/usr/bin/env python3
"""bOPEN composition demonstration — three foundations doing one business job.

Party, Money and the Workflow state engine were each built and verified on their own. This is them
**working together** as something a business actually does: a customer invoice that is priced in one
currency, converted to another at the tenant's own rate, and driven through an approval workflow
from draft to approved — all over real HTTP through the gateway to the kernel to PostgreSQL, and all
private to the tenant that owns it.

    curl -> Hono gateway (:8791) -> FastAPI kernel (:8004) -> PostgreSQL

Nothing here is new kernel code. Every call uses an endpoint already verified and disposed
(MILE-4.1 Party, MILE-4.2 Money, MILE-4.2 Workflow). The point is the composition, and the proof at
the end that a second tenant cannot see or move one step of the first tenant's process.

Run:  python scripts/demo_approval_flow.py

Self-contained: starts both servers, runs the scenario, tears them down in a finally block.
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
KERNEL_PORT = 8004
GATEWAY_PORT = 8791
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


def money_str(minor: int, currency: str) -> str:
    """Render integer minor units as a human amount, for display only."""
    frac = {"USD": 2, "THB": 2, "JPY": 0}.get(currency, 2)
    if frac == 0:
        return f"{minor:,} {currency}"
    whole, part = divmod(minor, 10 ** frac)
    return f"{whole:,}.{part:0{frac}d} {currency}"


def main() -> int:
    env = load_env_local()
    env["PYTHONPATH"] = os.pathsep.join(
        str(ROOT / p) for p in (
            "services/platform-kernel/python", "packages/kernel-core/python", "sdk/python", ".",
        )
    )
    # The console on Windows defaults to cp1252, which cannot encode the arrows/dashes below.
    # Force UTF-8 so the demo reads the same on every platform rather than crashing on a glyph.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("=" * 74)
    print("bOPEN composition — a customer invoice, priced, converted and approved")
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

        print("\n[3] PARTY — Northwind records the customer being billed")
        s, cust = request("POST", f"{GATEWAY}/v1/parties", headers=hdr(north["token"]),
                          body={"party_type": "organization", "display_name": "Acme Manufacturing"})
        assert s == 201, (s, cust)
        customer = cust["party_id"]
        print(f"    OK  customer party: Acme Manufacturing ({customer[:8]}…)")

        print("\n[4] MONEY — the invoice is priced in USD and converted to THB at Northwind's rate")
        s, _ = request("PUT", f"{GATEWAY}/v1/exchange-rates", headers=hdr(north["token"]),
                       body={"from_currency": "USD", "to_currency": "THB", "rate": "34.50"})
        assert s == 200, (s, _)
        invoice_usd = 1_250_000  # $12,500.00 in integer minor units — never a float
        s, conv = request("POST", f"{GATEWAY}/v1/money/convert", headers=hdr(north["token"]),
                          body={"amount_minor": invoice_usd, "from_currency": "USD", "to_currency": "THB"})
        assert s == 200, (s, conv)
        invoice_thb = conv["amount_minor"]
        print(f"    OK  invoice {money_str(invoice_usd, 'USD')}  ->  {money_str(invoice_thb, 'THB')}  "
              f"(exact, rate 34.50, integer minor units)")

        print("\n[5] WORKFLOW — Northwind defines its invoice-approval process and runs this invoice")
        s, defn = request("POST", f"{GATEWAY}/v1/workflow-definitions", headers=hdr(north["token"]),
                          body={"name": "Invoice Approval", "initial_state": "draft",
                                "states": ["draft", "submitted", "approved", "rejected"],
                                "transitions": [["draft", "submitted"], ["submitted", "approved"],
                                                ["submitted", "rejected"]]})
        assert s == 201, (s, defn)
        subject = f"invoice:{customer}:{invoice_thb}THB"
        s, inst = request("POST", f"{GATEWAY}/v1/workflow-instances", headers=hdr(north["token"]),
                          body={"definition_id": defn["definition_id"], "subject_ref": subject})
        assert s == 201, (s, inst)
        instance = inst["instance_id"]
        print(f"    OK  approval started for {subject[:40]}…  state={inst['current_state']}")

        for target in ("submitted", "approved"):
            s, moved = request("POST", f"{GATEWAY}/v1/workflow-instances/{instance}/transitions",
                               headers=hdr(north["token"]), body={"to_state": target})
            assert s == 200, (s, moved)
            print(f"    OK  transition -> {moved['current_state']}")

        s, hist = request("GET", f"{GATEWAY}/v1/workflow-instances/{instance}/history",
                          headers=hdr(north["token"]))
        assert s == 200, (s, hist)
        trail = " , ".join(f"{h['from_state']}→{h['to_state']}" for h in hist)
        print(f"    OK  immutable approval trail:  {trail}")

        print("\n[6] The state machine refuses an illegal jump (what makes it more than a field)")
        s, inst2 = request("POST", f"{GATEWAY}/v1/workflow-instances", headers=hdr(north["token"]),
                           body={"definition_id": defn["definition_id"], "subject_ref": "invoice:draft-only"})
        assert s == 201, (s, inst2)
        s, refused = request("POST", f"{GATEWAY}/v1/workflow-instances/{inst2['instance_id']}/transitions",
                             headers=hdr(north["token"]), body={"to_state": "approved"})  # skip submitted
        print(f"    draft -> approved (skipping submitted)   -> {s} (must be 422)")
        assert s == 422, "a draft was approved without being submitted"
        s, still = request("GET", f"{GATEWAY}/v1/workflow-instances/{inst2['instance_id']}",
                           headers=hdr(north["token"]))
        assert still["current_state"] == "draft", "state moved on a refused transition"
        print(f"    OK  it stayed at '{still['current_state']}' — no illegal shortcut to approval")

        print("\n[7] PRIVACY — Globex cannot see or move one step of Northwind's process")
        s, _ = request("GET", f"{GATEWAY}/v1/parties/{customer}", headers=hdr(globex["token"]))
        print(f"    Globex reads Northwind's customer         -> {s} (must be 404)")
        assert s == 404, "ISOLATION BREACH: Globex read Northwind's customer"
        s, _ = request("GET", f"{GATEWAY}/v1/workflow-instances/{instance}", headers=hdr(globex["token"]))
        print(f"    Globex reads Northwind's approval         -> {s} (must be 404)")
        assert s == 404, "ISOLATION BREACH: Globex read Northwind's approval"
        s, _ = request("POST", f"{GATEWAY}/v1/workflow-instances/{instance}/transitions",
                       headers=hdr(globex["token"]), body={"to_state": "rejected"})
        print(f"    Globex tries to reject it                 -> {s} (must be 404)")
        assert s == 404, "ISOLATION BREACH: Globex transitioned Northwind's approval"
        s, rate = request("GET", f"{GATEWAY}/v1/exchange-rates/USD/THB", headers=hdr(globex["token"]))
        print(f"    Globex reads Northwind's USD/THB rate     -> {s} (must be 404)")
        assert s == 404, "ISOLATION BREACH: Globex read Northwind's private rate"
        print("    OK  every cross-tenant read and write was refused by the database")

        print("\n" + "=" * 74)
        print("RESULT: one tenant billed a customer (Party), priced the invoice and converted it")
        print("exactly to another currency (Money), and drove it through an approval workflow to")
        print("'approved' with an immutable trail (Workflow) — three foundations composed into one")
        print("business process, end to end over the gateway, and wholly invisible to another")
        print("tenant. bOPEN does real business, privately.")
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
