#!/usr/bin/env python3
"""Collect a read-only local Git provenance audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

OID_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")
PROFILES = (
    "local-integrity",
    "forge-provenance",
    "release-provenance",
    "incident-timeline",
    "migration-chain-of-custody",
    "policy-drift",
    "full",
)
VERDICTS = {
    "PASS",
    "PASS_WITH_GAPS",
    "FAIL",
    "INDETERMINATE",
    "BLOCKED_ACCESS",
    "NOT_APPLICABLE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_observed_at(value: str) -> str:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("--observed-at must include a UTC offset")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def redact(text: str) -> str:
    text = re.sub(r"(https?://)[^/@\s]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"(?i)(authorization:\s*)(\S+)", r"\1[REDACTED]", text)
    return text


def normalize_remote(value: str) -> str:
    value = value.strip()
    if not value:
        return "NOT_CONFIGURED"
    scp = re.match(r"^(?:[^@]+@)?([^:]+):(.+)$", value)
    if scp and "://" not in value and not re.match(r"^[A-Za-z]:[\\/]", value):
        return f"ssh://{scp.group(1)}/{scp.group(2).lstrip('/')}"
    parts = urlsplit(value)
    if parts.scheme and parts.netloc:
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        return urlunsplit((parts.scheme.lower(), host.lower(), parts.path, "", ""))
    return str(Path(value).expanduser().resolve()) if not value.startswith("file:") else value


class Collector:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.commands: list[dict[str, object]] = []

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ["git", "-C", str(self.repo), *args]
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        result = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=env,
            check=False,
        )
        self.commands.append(
            {
                "argv": ["git", "-C", "<REPOSITORY>", *args],
                "returncode": result.returncode,
                "stdout": redact(result.stdout),
                "stderr": redact(result.stderr),
            }
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {redact(result.stderr.strip())}")
        return result


def finding(
    finding_id: str,
    control_id: str,
    claim: str,
    verdict: str,
    mandatory: bool,
    evidence: list[str],
    basis: str,
    limitations: list[str] | None = None,
    remediation: list[str] | None = None,
    authorization_status: str = "OUT_OF_SCOPE",
) -> dict[str, object]:
    if verdict not in VERDICTS:
        raise ValueError(f"unsupported verdict: {verdict}")
    return {
        "finding_id": finding_id,
        "control_id": control_id,
        "claim": claim,
        "verdict": verdict,
        "mandatory": mandatory,
        "evidence": evidence,
        "basis": basis,
        "limitations": limitations or [],
        "remediation": remediation or [],
        "authorization_status": authorization_status,
    }


def overall_verdict(findings: list[dict[str, object]]) -> str:
    mandatory = [item["verdict"] for item in findings if item["mandatory"]]
    if "FAIL" in mandatory:
        return "FAIL"
    if "BLOCKED_ACCESS" in mandatory:
        return "BLOCKED_ACCESS"
    if "INDETERMINATE" in mandatory:
        return "INDETERMINATE"
    if any(item["verdict"] not in {"PASS", "NOT_APPLICABLE"} for item in findings):
        return "PASS_WITH_GAPS"
    return "PASS"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target-ref", required=True)
    parser.add_argument("--profile", choices=PROFILES, default="local-integrity")
    parser.add_argument("--expected-commit")
    parser.add_argument("--observed-at")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    output = args.output.expanduser().resolve()
    observed_at = validate_observed_at(args.observed_at) if args.observed_at else utc_now()
    if args.expected_commit and not OID_RE.fullmatch(args.expected_commit):
        parser.error("--expected-commit must be a full 40- or 64-hex object ID")

    collector = Collector(repo)
    try:
        git_dir = Path(collector.git("rev-parse", "--absolute-git-dir").stdout.strip())
        is_bare = collector.git("rev-parse", "--is-bare-repository").stdout.strip() == "true"
        root = repo if is_bare else Path(collector.git("rev-parse", "--show-toplevel").stdout.strip())
        object_format = collector.git("rev-parse", "--show-object-format").stdout.strip()
        observed_ref = collector.git("rev-parse", "--verify", args.target_ref).stdout.strip()
        if not OID_RE.fullmatch(observed_ref):
            raise RuntimeError("target ref did not resolve to a full object ID")
        if collector.git("cat-file", "-t", observed_ref).stdout.strip() != "commit":
            raise RuntimeError("target ref does not resolve to a commit")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 4

    remote_result = collector.git("remote", "get-url", "origin", check=False)
    remote = normalize_remote(remote_result.stdout) if remote_result.returncode == 0 else "NOT_CONFIGURED"
    repository_identity = hashlib.sha256(f"{root}|{remote}|{object_format}".encode()).hexdigest()

    fields = collector.git(
        "show",
        "-s",
        "--format=%H%x00%T%x00%P%x00%an%x00%ae%x00%cn%x00%ce%x00%aI%x00%cI%x00%G?%x00%GK%x00%GS",
        observed_ref,
    ).stdout.rstrip("\n").split("\x00")
    if len(fields) != 12:
        print("unexpected git show field count", file=sys.stderr)
        return 4
    (
        commit_oid,
        tree_oid,
        parents,
        author_name,
        author_email,
        committer_name,
        committer_email,
        authored_at,
        committed_at,
        signature_status,
        signature_key,
        signature_signer,
    ) = fields

    limitations: list[str] = []
    shallow = (git_dir / "shallow").exists()
    if shallow:
        limitations.append("repository is shallow")
    alternates_path = git_dir / "objects" / "info" / "alternates"
    alternates = []
    if alternates_path.exists():
        alternates = [redact(line) for line in alternates_path.read_text(encoding="utf-8").splitlines()]
        limitations.append("repository uses object alternates")
    replace_refs = collector.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/replace").stdout.splitlines()
    if replace_refs:
        limitations.append("replace refs are configured")
    promisor = collector.git("config", "--get", "remote.origin.promisor", check=False).stdout.strip()
    partial_filter = collector.git("config", "--get", "remote.origin.partialclonefilter", check=False).stdout.strip()
    if promisor == "true" or partial_filter:
        limitations.append("repository is a partial clone")

    status = "NOT_APPLICABLE"
    if not is_bare:
        status = collector.git("status", "--porcelain=v1", "--untracked-files=all").stdout

    findings: list[dict[str, object]] = []
    expected_matches = args.expected_commit is None or args.expected_commit.lower() == observed_ref.lower()
    findings.append(
        finding(
            "F-REF-001",
            "GIT-REF-001",
            "Observed target ref equals the supplied expected commit",
            "NOT_APPLICABLE" if args.expected_commit is None else ("PASS" if expected_matches else "FAIL"),
            args.expected_commit is not None,
            ["audit.json#/baseline/observed_ref_oid"],
            "No expected commit was supplied."
            if args.expected_commit is None
            else f"expected={args.expected_commit.lower()} observed={observed_ref.lower()}",
            remediation=[] if expected_matches else ["Stop promotion and reconcile the expected target out of band."],
        )
    )

    fsck = collector.git("fsck", "--connectivity-only", "--no-dangling", observed_ref, check=False)
    findings.append(
        finding(
            "F-OBJ-001",
            "GIT-OBJ-001",
            "Commit, tree, parent and reachable object connectivity is intact",
            "PASS" if fsck.returncode == 0 else "FAIL",
            True,
            ["raw/commands.json"],
            f"git fsck returncode={fsck.returncode}",
            remediation=[] if fsck.returncode == 0 else ["Quarantine the repository and obtain a trusted object source."],
        )
    )

    signature_map = {
        "G": ("PASS", "good signature with trusted validity"),
        "U": ("PASS_WITH_GAPS", "good signature with unknown trust"),
        "N": ("INDETERMINATE", "no signature"),
        "B": ("FAIL", "bad signature"),
        "E": ("INDETERMINATE", "signature verification error"),
        "X": ("INDETERMINATE", "good signature made with expired signature"),
        "Y": ("INDETERMINATE", "good signature made with expired key"),
        "R": ("FAIL", "good signature made with revoked key"),
    }
    sig_verdict, sig_basis = signature_map.get(signature_status, ("INDETERMINATE", "unknown signature status"))
    findings.append(
        finding(
            "F-SIG-001",
            "GIT-SIG-001",
            "Commit signature is cryptographically verified",
            sig_verdict,
            False,
            ["audit.json#/revision/signature"],
            sig_basis,
            limitations=["Signature validity does not prove accepted identity or authorization."],
            authorization_status="NOT_PROVEN",
        )
    )

    reflog = collector.git("reflog", "show", args.target_ref, "--format=%H%x00%gn%x00%ge%x00%gs", check=False)
    reflog_entries: list[dict[str, str]] = []
    non_fast_forward: list[dict[str, str]] = []
    if reflog.returncode == 0:
        for line in reflog.stdout.splitlines():
            parts = line.split("\x00")
            if len(parts) == 4:
                reflog_entries.append(
                    {"new_oid": parts[0], "actor_name": parts[1], "actor_email": parts[2], "message": parts[3]}
                )
        for index in range(len(reflog_entries) - 1):
            new_oid = reflog_entries[index]["new_oid"]
            old_oid = reflog_entries[index + 1]["new_oid"]
            ancestry = collector.git("merge-base", "--is-ancestor", old_oid, new_oid, check=False)
            if ancestry.returncode != 0:
                non_fast_forward.append({"old_oid": old_oid, "new_oid": new_oid})
    else:
        limitations.append("target ref reflog unavailable")

    rewrite_mandatory = args.profile in {"incident-timeline", "migration-chain-of-custody", "policy-drift", "full"}
    rewrite_verdict = "PASS" if not non_fast_forward else "INDETERMINATE"
    if reflog.returncode != 0:
        rewrite_verdict = "BLOCKED_ACCESS" if rewrite_mandatory else "INDETERMINATE"
    findings.append(
        finding(
            "F-REF-002",
            "GIT-REF-002",
            "Observed target-ref movements satisfy the requested policy",
            rewrite_verdict,
            rewrite_mandatory,
            ["audit.json#/ref_history"],
            f"reflog_entries={len(reflog_entries)} non_fast_forward_observations={len(non_fast_forward)}",
            limitations=["Git reflog actor fields are self-asserted and local unless externally bound."],
            remediation=[]
            if not non_fast_forward
            else ["Obtain forge audit events and attributable authorization for each rewrite."],
            authorization_status="NOT_PROVEN",
        )
    )

    external_required = args.profile != "local-integrity"
    findings.append(
        finding(
            "F-FORGE-001",
            "FORGE-POL-001",
            "Forge repository identity and protected-ref policy are proven",
            "INDETERMINATE" if external_required else "NOT_APPLICABLE",
            external_required,
            [],
            "The local collector does not call forge APIs.",
            limitations=["Collect official read-only forge evidence separately."],
            authorization_status="OUT_OF_SCOPE",
        )
    )
    findings.append(
        finding(
            "F-AUTH-001",
            "AUTH-001",
            "Organizational authorization for the observed revision is proven",
            "INDETERMINATE",
            False,
            [],
            "Git objects and local actor fields cannot create organizational authority.",
            limitations=["Requires an external mandate and accepted identity binding."],
            authorization_status="NOT_PROVEN",
        )
    )

    audit = {
        "schema_version": "1.0.0",
        "profile": args.profile,
        "observed_at_utc": observed_at,
        "repository_identity": repository_identity,
        "normalized_remote_url": remote,
        "forge_repository_id": "NOT_APPLICABLE" if args.profile == "local-integrity" else "INDETERMINATE",
        "object_format": object_format,
        "baseline": {
            "repository_path": str(root),
            "git_dir": str(git_dir),
            "target_ref": args.target_ref,
            "observed_ref_oid": observed_ref,
            "expected_commit_oid": args.expected_commit,
            "is_bare": is_bare,
            "worktree_status": status,
        },
        "revision": {
            "commit_oid": commit_oid,
            "tree_oid": tree_oid,
            "parent_oids": parents.split() if parents else [],
            "author": {"name": author_name, "email": author_email, "asserted_only": True},
            "committer": {"name": committer_name, "email": committer_email, "asserted_only": True},
            "authored_at": authored_at,
            "committed_at": committed_at,
            "signature": {
                "status": signature_status,
                "key": signature_key,
                "signer": signature_signer,
            },
        },
        "repository_boundaries": {
            "shallow": shallow,
            "alternates": alternates,
            "replace_refs": replace_refs,
            "promisor_remote": promisor or None,
            "partial_clone_filter": partial_filter or None,
        },
        "ref_history": {
            "entries": reflog_entries,
            "non_fast_forward_observations": non_fast_forward,
        },
        "limitations": sorted(set(limitations)),
        "overall_verdict": overall_verdict(findings),
        "authorization_status": "NOT_PROVEN",
    }

    write_json(output / "audit.json", audit)
    write_json(output / "findings.json", findings)
    write_json(output / "raw" / "commands.json", collector.commands)
    print(json.dumps({"output": str(output), "overall_verdict": audit["overall_verdict"]}, sort_keys=True))

    if audit["overall_verdict"] == "FAIL":
        return 2
    if audit["overall_verdict"] in {"BLOCKED_ACCESS", "INDETERMINATE"}:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
