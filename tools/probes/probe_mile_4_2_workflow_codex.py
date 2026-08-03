#!/usr/bin/env python3
"""Candidate-bound defensive verifier probe for the MILE-4.2 workflow engine."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = "2ee4612342fbd30f1f122ac4abfd909c62d746c4"
TREE = "8b21e48f8d897cb0f766cbe6888892193598aef9"
EXPECTED_BLOBS = {
    "infrastructure/database/013_workflow_state_engine.sql":
        "f5e58332918dafde84e1cba592d7440301e257b4",
    "infrastructure/database/014_workflow_history_survives_its_instance.sql":
        "7d505ec8ef3200a03958eda10320475a01689759",
    "services/platform-kernel/python/platform_kernel/workflow_repositories.py":
        "d9fff1b0b93e77dbd8c901368d9a39c2e758aa94",
    "services/platform-kernel/python/platform_kernel/api.py":
        "e50569363ccfc64947d414f36a15190f59f196ec",
    "docs/evidence/phase-3.5/invariant-traceability.csv":
        "dd9982011280763dcf39199349965de5448e88b6",
    "tests/isolation/test_workflow_isolation.py":
        "3605168712d4d95efa27ef33ef03535f97601f95",
}
EXPECTED_INVARIANTS = {
    "INV-WF-TENANT-ISOLATION-01",
    "INV-WF-TENANT-ISOLATION-02",
    "INV-WF-TENANT-WRITE-01",
    "INV-WF-INSTANCE-DEF-SAME-TENANT-01",
    "INV-WF-HISTORY-APPEND-ONLY-01",
    "INV-WF-HISTORY-APPEND-ONLY-02",
    "INV-WF-TRANSITION-ALLOWED-01",
    "INV-WF-HTTP-LIFECYCLE-01",
    "INV-WF-HTTP-TRANSITION-01",
    "INV-WF-HTTP-HISTORY-ORDER-01",
    "INV-WF-HTTP-TRANSITION-REFUSED-01",
    "INV-WF-HTTP-DEF-MALFORMED-01",
    "INV-WF-HTTP-ISOLATION-INST-01",
    "INV-WF-HTTP-ISOLATION-DEF-01",
    "INV-WF-HTTP-TRANSITION-CROSS-TENANT-01",
    "INV-WF-HTTP-BEARER-01",
}
REQUIRED_ENV = {
    "BOPEN_DATABASE_URL",
    "BOPEN_ADMIN_DATABASE_URL",
    "BOPEN_CONTEXT_TOKEN_KEY",
    "BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION",
    "BOPEN_LEGACY_CONTEXT_HEADER_PROFILE",
}


def load_required_env() -> None:
    env_path = ROOT / ".env.local"
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name not in REQUIRED_ENV or os.environ.get(name):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[name] = value
    missing = sorted(name for name in REQUIRED_ENV if not os.environ.get(name, "").strip())
    if missing:
        raise RuntimeError(f"required verifier environment is missing: {', '.join(missing)}")


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def bind_candidate() -> None:
    if git("rev-parse", f"{CANDIDATE}^{{commit}}") != CANDIDATE:
        raise RuntimeError("candidate commit does not resolve exactly")
    if git("rev-parse", f"{CANDIDATE}^{{tree}}") != TREE:
        raise RuntimeError("candidate tree does not match the maker submission")
    for path, expected in EXPECTED_BLOBS.items():
        observed = git("rev-parse", f"{CANDIDATE}:{path}")
        if observed != expected:
            raise RuntimeError(f"candidate blob mismatch for {path}: {observed}")

    drift = subprocess.run(
        [
            "git", "diff", "--quiet", CANDIDATE, "--",
            "services", "packages", "contracts", "tests", "infrastructure/database",
        ],
        cwd=ROOT,
        check=False,
    )
    if drift.returncode != 0:
        raise RuntimeError("live executable, schema, contract, or test bytes differ from candidate")

    trace = git("show", f"{CANDIDATE}:docs/evidence/phase-3.5/invariant-traceability.csv")
    present = {line.split(",", 1)[0] for line in trace.splitlines() if line.startswith("INV-WF-")}
    if present != EXPECTED_INVARIANTS:
        raise RuntimeError(
            f"INV-WF traceability mismatch: missing={sorted(EXPECTED_INVARIANTS - present)}, "
            f"extra={sorted(present - EXPECTED_INVARIANTS)}"
        )


def expect_status(response, status: int, label: str) -> None:
    if response.status_code != status:
        raise AssertionError(
            f"{label}: expected HTTP {status}, got {response.status_code}: {response.text}"
        )


def main() -> int:
    load_required_env()
    bind_candidate()

    sys.path.insert(0, str(ROOT / "packages" / "kernel-core" / "python"))
    sys.path.insert(0, str(ROOT / "services" / "platform-kernel" / "python"))
    sys.path.insert(0, str(ROOT / "sdk" / "python"))

    import psycopg
    from fastapi.testclient import TestClient
    from platform_kernel import db
    from platform_kernel.api import app

    client = TestClient(app, raise_server_exceptions=False)
    tenant_ids: list[str] = []
    principal_ids: list[str] = []

    def headers(token: str | None = None) -> dict[str, str]:
        result = {"X-Correlation-ID": f"corr_{uuid.uuid4()}"}
        if token:
            result["Authorization"] = f"Bearer {token}"
        return result

    def make_tenant(label: str) -> tuple[str, str, str]:
        principal_response = client.post(
            "/v1/principals",
            json={"email": f"codex-wf-{uuid.uuid4().hex}@example.com", "type": "human"},
            headers=headers(),
        )
        expect_status(principal_response, 201, f"{label} principal")
        principal_id = principal_response.json()["principal_id"]
        principal_ids.append(principal_id)
        tenant_response = client.post(
            "/v1/tenants",
            json={"name": f"Codex workflow {label} {uuid.uuid4().hex[:8]}",
                  "owner_principal_id": principal_id},
            headers=headers(),
        )
        expect_status(tenant_response, 201, f"{label} tenant")
        tenant_id = tenant_response.json()["tenant_id"]
        tenant_ids.append(tenant_id)
        context_response = client.post(
            "/v1/contexts",
            json={
                "principal_id": principal_id,
                "membership_id": tenant_response.json()["owner_membership_id"],
            },
            headers={"X-Tenant-ID": tenant_id, **headers()},
        )
        expect_status(context_response, 201, f"{label} context")
        return tenant_id, principal_id, context_response.json()["access_token"]

    results: dict[str, object] = {
        "candidate": CANDIDATE,
        "tree": TREE,
        "traceability_rows": len(EXPECTED_INVARIANTS),
    }
    try:
        tenant_a, _, token_a = make_tenant("A")
        tenant_b, _, token_b = make_tenant("B")

        no_bearer = client.post(
            "/v1/workflow-instances",
            json={"definition_id": str(uuid.uuid4()), "subject_ref": "no-bearer"},
            headers=headers(),
        )
        expect_status(no_bearer, 401, "start without bearer")

        malformed = client.post(
            "/v1/workflow-definitions",
            json={
                "name": "Malformed",
                "initial_state": "missing",
                "states": ["draft", "submitted"],
                "transitions": [["draft", "submitted"]],
            },
            headers=headers(token_a),
        )
        expect_status(malformed, 422, "malformed definition")

        definition_response = client.post(
            "/v1/workflow-definitions",
            json={
                "name": "Independent approval probe",
                "initial_state": "draft",
                "states": ["draft", "submitted", "approved"],
                "transitions": [["draft", "submitted"], ["submitted", "approved"]],
            },
            headers=headers(token_a),
        )
        expect_status(definition_response, 201, "create definition")
        definition_id = definition_response.json()["definition_id"]
        expect_status(
            client.get(f"/v1/workflow-definitions/{definition_id}", headers=headers(token_a)),
            200,
            "own definition read",
        )
        expect_status(
            client.get(f"/v1/workflow-definitions/{definition_id}", headers=headers(token_b)),
            404,
            "foreign definition read",
        )
        expect_status(
            client.post(
                "/v1/workflow-instances",
                json={"definition_id": definition_id, "subject_ref": "foreign-definition"},
                headers=headers(token_b),
            ),
            404,
            "foreign definition instance over HTTP",
        )

        instance_response = client.post(
            "/v1/workflow-instances",
            json={"definition_id": definition_id, "subject_ref": "invoice-independent-1"},
            headers=headers(token_a),
        )
        expect_status(instance_response, 201, "start instance")
        instance_id = instance_response.json()["instance_id"]
        if instance_response.json()["current_state"] != "draft":
            raise AssertionError("instance did not start at definition initial state")
        expect_status(
            client.get(f"/v1/workflow-instances/{instance_id}", headers=headers(token_b)),
            404,
            "foreign instance read",
        )
        expect_status(
            client.post(
                f"/v1/workflow-instances/{instance_id}/transitions",
                json={"to_state": "submitted"},
                headers=headers(token_b),
            ),
            404,
            "foreign instance transition",
        )

        refused = client.post(
            f"/v1/workflow-instances/{instance_id}/transitions",
            json={"to_state": "approved"},
            headers=headers(token_a),
        )
        expect_status(refused, 422, "draft to approved")
        unchanged = client.get(
            f"/v1/workflow-instances/{instance_id}", headers=headers(token_a)
        )
        expect_status(unchanged, 200, "read after refused transition")
        if unchanged.json()["current_state"] != "draft":
            raise AssertionError("refused transition changed instance state")
        empty_history = client.get(
            f"/v1/workflow-instances/{instance_id}/history", headers=headers(token_a)
        )
        expect_status(empty_history, 200, "history after refused transition")
        if empty_history.json() != []:
            raise AssertionError("refused transition wrote a history row")

        with db.tenant_session(tenant_b) as cur:
            cur.execute("SELECT count(*) FROM workflow_definitions WHERE id = %s", (definition_id,))
            if cur.fetchone()[0] != 0:
                raise AssertionError("tenant B read tenant A's definition through SQL")
            cur.execute("SELECT count(*) FROM workflow_instances WHERE id = %s", (instance_id,))
            if cur.fetchone()[0] != 0:
                raise AssertionError("tenant B read tenant A's instance through SQL")

        try:
            with db.tenant_session(tenant_b) as cur:
                cur.execute(
                    "INSERT INTO workflow_definitions "
                    "(tenant_id, name, initial_state, states, transitions) "
                    "VALUES (%s, 'cross-write', 'draft', '[\"draft\"]'::jsonb, '[]'::jsonb)",
                    (tenant_a,),
                )
        except psycopg.Error:
            pass
        else:
            raise AssertionError("cross-tenant workflow definition INSERT succeeded")

        try:
            with db.tenant_session(tenant_b) as cur:
                cur.execute(
                    "INSERT INTO workflow_instances "
                    "(tenant_id, definition_id, current_state, subject_ref) "
                    "VALUES (%s, %s, 'draft', 'cross-definition')",
                    (tenant_b, definition_id),
                )
        except psycopg.Error:
            pass
        else:
            raise AssertionError("instance of another tenant's definition succeeded")

        first_move = client.post(
            f"/v1/workflow-instances/{instance_id}/transitions",
            json={"to_state": "submitted"},
            headers=headers(token_a),
        )
        expect_status(first_move, 200, "legal draft to submitted")

        with db.tenant_session(tenant_a) as cur:
            cur.execute(
                "UPDATE workflow_history SET to_state = 'tampered' WHERE instance_id = %s",
                (instance_id,),
            )
            if cur.rowcount != 0:
                raise AssertionError("recorded workflow history row was updated")
            cur.execute("DELETE FROM workflow_history WHERE instance_id = %s", (instance_id,))
            if cur.rowcount != 0:
                raise AssertionError("recorded workflow history row was deleted")
            cur.execute(
                "SELECT from_state, to_state FROM workflow_history WHERE instance_id = %s",
                (instance_id,),
            )
            if cur.fetchall() != [("draft", "submitted")]:
                raise AssertionError("recorded workflow history was not immutable")

        # Replay the exact referential path that refuted a09022d. Migration 014 must make the
        # parent DELETE fail, and both parent and recorded history must remain after that refusal.
        try:
            with db.tenant_session(tenant_a) as cur:
                cur.execute("DELETE FROM workflow_instances WHERE id = %s", (instance_id,))
        except psycopg.Error:
            pass
        else:
            raise AssertionError("instance DELETE succeeded and could erase recorded history")

        with db.tenant_session(tenant_a) as cur:
            cur.execute("SELECT count(*) FROM workflow_instances WHERE id = %s", (instance_id,))
            instance_rows_after_delete = cur.fetchone()[0]
            cur.execute(
                "SELECT from_state, to_state FROM workflow_history WHERE instance_id = %s",
                (instance_id,),
            )
            history_after_instance_delete = cur.fetchall()
        if instance_rows_after_delete != 1:
            raise AssertionError("instance disappeared despite the RESTRICT refusal")
        if history_after_instance_delete != [("draft", "submitted")]:
            raise AssertionError("recorded history was erased through the parent DELETE path")

        second_move = client.post(
            f"/v1/workflow-instances/{instance_id}/transitions",
            json={"to_state": "approved"},
            headers=headers(token_a),
        )
        expect_status(second_move, 200, "legal submitted to approved")
        ordered_history = client.get(
            f"/v1/workflow-instances/{instance_id}/history", headers=headers(token_a)
        )
        expect_status(ordered_history, 200, "ordered history")
        pairs = [(item["from_state"], item["to_state"]) for item in ordered_history.json()]
        if pairs != [("draft", "submitted"), ("submitted", "approved")]:
            raise AssertionError(f"workflow history was not in transition order: {pairs}")

        results.update(
            {
                "no_bearer": no_bearer.status_code,
                "malformed_definition": malformed.status_code,
                "foreign_definition_read": 404,
                "foreign_instance_read": 404,
                "foreign_transition": 404,
                "illegal_transition": refused.status_code,
                "state_after_refusal": unchanged.json()["current_state"],
                "history_after_refusal": len(empty_history.json()),
                "cross_tenant_definition_insert": "refused",
                "cross_tenant_definition_fk": "refused",
                "history_update_rows": 0,
                "history_delete_rows": 0,
                "instance_delete_with_history": "refused",
                "instance_rows_after_delete": instance_rows_after_delete,
                "history_after_instance_delete": history_after_instance_delete,
                "legal_transition_states": [
                    first_move.json()["current_state"], second_move.json()["current_state"]
                ],
                "history_order": pairs,
            }
        )
        print(json.dumps(results, sort_keys=True))
        return 0
    finally:
        # The repository's PostgreSQL evidence tests deliberately leave unique committed rows in
        # the disposable verification database: audit_events is append-only and outlives the
        # context it names, so deleting a tenant would either fail or weaken the invariant under
        # review. This probe follows that established evidence-fixture rule.
        pass


if __name__ == "__main__":
    raise SystemExit(main())
