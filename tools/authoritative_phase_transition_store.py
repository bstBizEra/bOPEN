#!/usr/bin/env python3
"""Authoritative Git-ref adapter for the phase-transition verifier.

This is the bounded incorporation layer: read the protected ref, verify the
signed mandate against the exact current predecessor, build one commit with
all governed state, then perform one expected-old update-ref CAS. It does not
sign, approve, consume human authority, or open PG-P1.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("verify_phase_transition", ROOT / "verify_phase_transition.py")
verify = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(verify)

INCORPORATED = "INCORPORATED_EXACT"
ALREADY_APPLIED = "ALREADY_APPLIED_EXACT"
REPLAY_DENIED = "REPLAY_DENIED"
INCORPORATION_CONFLICT = "INCORPORATION_CONFLICT"


class StoreError(Exception):
    def __init__(self, outcome: str, message: str) -> None:
        super().__init__(message)
        self.outcome = outcome
        self.message = message


def git(repo: Path, *args: str, env: dict[str, str] | None = None, input_bytes: bytes | None = None) -> bytes:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], input=input_bytes, stderr=subprocess.STDOUT, env=merged
        )
    except subprocess.CalledProcessError as exc:
        raise StoreError(INCORPORATION_CONFLICT, exc.output.decode("utf-8", "replace").strip()) from exc


def json_at(repo: Path, ref: str, path: str, default: object = None) -> object:
    try:
        raw = git(repo, "show", f"{ref}:{path}")
    except StoreError:
        if default is not None:
            return default
        raise
    return verify.parse_strict(raw.decode("utf-8"))


def canonical_json(value: object) -> bytes:
    return verify.rfc8785_canonical(value) + b"\n"


def commit_with_files(repo: Path, parent: str, files: dict[str, bytes], message: str, when: str) -> str:
    handle = tempfile.NamedTemporaryFile(prefix="bopen-index-", suffix=".idx", delete=False)
    handle.close()
    index = Path(handle.name)
    env = {"GIT_INDEX_FILE": str(index)}
    try:
        git(repo, "read-tree", parent, env=env)
        for path, data in files.items():
            blob = git(repo, "hash-object", "-w", "--stdin", input_bytes=data).decode().strip()
            git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = git(repo, "write-tree", env=env).decode().strip()
        return git(
            repo, "commit-tree", tree, "-p", parent, "-m", message,
            env={
                **env,
                "GIT_AUTHOR_NAME": "BST Phase Transition Store",
                "GIT_AUTHOR_EMAIL": "bst-phase-transition@bizera-smartthink.local",
                "GIT_COMMITTER_NAME": "BST Phase Transition Store",
                "GIT_COMMITTER_EMAIL": "bst-phase-transition@bizera-smartthink.local",
                "GIT_AUTHOR_DATE": when,
                "GIT_COMMITTER_DATE": when,
            },
        ).decode().strip()
    finally:
        index.unlink(missing_ok=True)


def epoch_time(iso_value: str) -> str:
    value = dt.datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise StoreError(verify.MANDATE_INVALID, "effective_at must include timezone")
    return f"@{int(value.timestamp())} +0000"


def incorporate(
    repo: Path,
    ref: str,
    schedule_path: str,
    consumed_path: str,
    mandate_source: Path,
    mandate_repo_path: str,
    trust_root_source: Path,
    identity_source: Path,
    verification_time: str,
    observed_at: str,
    receipt_path: str,
    revocations_source: Path | None = None,
) -> dict:
    old = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    predecessor = json_at(repo, ref, schedule_path)
    consumed = json_at(repo, ref, consumed_path, {})
    envelope = verify.parse_strict(mandate_source.read_text(encoding="utf-8"))
    trust_root = verify.parse_strict(trust_root_source.read_text(encoding="utf-8"))
    identity_register = verify.parse_strict(identity_source.read_text(encoding="utf-8"))
    revocations = (
        verify.parse_strict(revocations_source.read_text(encoding="utf-8"))
        if revocations_source else {}
    )
    mandate, _ = verify.open_signed_mandate(envelope, trust_root)
    decision_id = mandate["decision_id"]
    prior = consumed.get(decision_id) if isinstance(consumed, dict) else None
    current_digest = verify.digest(predecessor)

    if prior is not None:
        if prior.get("successor_digest") != current_digest:
            raise StoreError(REPLAY_DENIED, "decision was consumed for another successor")
        parent = git(repo, "rev-parse", "--verify", f"{ref}^").decode().strip()
        old_predecessor = json_at(repo, parent, schedule_path)
        result = verify.verify_transition(
            old_predecessor, predecessor, envelope, trust_root, identity_register,
            verification_time, consumed, revocations
        )
        return {"outcome": ALREADY_APPLIED, "commit": old, "verification": result["receipt"]}

    successor = verify.recompute_successor(predecessor, mandate)
    result = verify.verify_transition(
        predecessor, successor, envelope, trust_root, identity_register,
        verification_time, consumed, revocations
    )
    consumed_next = result["consumed"]
    stage2 = {
        "schema_id": "bopen.phase-transition-incorporation-receipt",
        "outcome": INCORPORATED,
        "decision_id": decision_id,
        "mandate_digest": verify.digest(mandate),
        "predecessor_schedule_digest": current_digest,
        "successor_schedule_digest": verify.digest(successor),
        "consumption_record_digest": verify.digest(consumed_next[decision_id]),
        "verification_receipt_digest": verify.digest(result["receipt"]),
        "verification_time": verification_time,
        "observed_at": observed_at,
    }
    commit = commit_with_files(
        repo, old,
        {
            schedule_path: canonical_json(successor),
            consumed_path: canonical_json(consumed_next),
            mandate_repo_path: canonical_json(envelope),
            receipt_path: canonical_json(stage2),
        },
        f"[{decision_id}] Incorporate verified phase transition",
        epoch_time(mandate["authority"]["effective_at"]),
    )
    try:
        git(repo, "update-ref", ref, commit, old)
    except StoreError as exc:
        raise StoreError(INCORPORATION_CONFLICT, f"expected-old CAS lost; ref remains {old}: {exc.message}") from exc
    event = {
        "schema_id": "bopen.phase-transition-incorporation-event",
        "outcome": INCORPORATED,
        "decision_id": decision_id,
        "previous_ref": old,
        "resulting_ref": commit,
        "observed_at": observed_at,
        "stage2_receipt_digest": verify.digest(stage2),
    }
    event_path = Path(repo) / (receipt_path + ".incorporation.json")
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_bytes(canonical_json(event))
    return {"outcome": INCORPORATED, "previous_ref": old, "resulting_ref": commit, "receipt": event}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--schedule-path", default="schedule.json")
    parser.add_argument("--consumed-path", default="governance/consumed-decisions.json")
    parser.add_argument("--mandate", type=Path, required=True)
    parser.add_argument("--mandate-repo-path", default="governance/mandates/phase-completion.dsse.json")
    parser.add_argument("--trust-root", type=Path, required=True)
    parser.add_argument("--identity-register", type=Path, required=True)
    parser.add_argument("--verification-time", required=True)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument("--receipt-path", default="governance/phase-transition-receipt.json")
    parser.add_argument("--revocations", type=Path)
    args = parser.parse_args()
    try:
        result = incorporate(
            args.repo, args.ref, args.schedule_path, args.consumed_path,
            args.mandate, args.mandate_repo_path, args.trust_root,
            args.identity_register, args.verification_time, args.observed_at,
            args.receipt_path, args.revocations,
        )
    except verify.VerifyError as exc:
        print(f"REJECTED: {exc.reason}: {exc.message}")
        return 1
    except StoreError as exc:
        print(f"{exc.outcome}: {exc.message}")
        return 1
    print(f"{result['outcome']}: {result.get('resulting_ref', result.get('commit'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
