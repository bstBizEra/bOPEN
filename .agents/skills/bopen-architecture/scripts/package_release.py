#!/usr/bin/env python3
"""Build a deterministic ZIP release with inventory, provenance, and checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE_PARTS = {".git", ".venv", "__pycache__"}
EXCLUDE_PREFIXES = ("evals/results/",)
EXCLUDE_SUFFIXES = {".pyc", ".zip"}
DYNAMIC_FILES = {"SHA256SUMS", "supply-chain/release-manifest.json", "supply-chain/provenance.intoto.jsonl"}


def included_files(include_dynamic: bool = True) -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in EXCLUDE_PARTS for part in path.relative_to(ROOT).parts):
            continue
        if rel.startswith(EXCLUDE_PREFIXES):
            continue
        if path.suffix in EXCLUDE_SUFFIXES or path.name == ".DS_Store":
            continue
        if not include_dynamic and rel in DYNAMIC_FILES:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(files: list[Path]) -> str:
    h = hashlib.sha256()
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def write_supply_chain() -> None:
    manifest = yaml.safe_load((ROOT / "bopen.skill.yaml").read_text(encoding="utf-8"))
    base_files = included_files(include_dynamic=False)
    digest = tree_digest(base_files)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "bopen-architecture-source-tree", "digest": {"sha256": digest}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://schemas.bopen.io/buildtypes/skill-package/v1",
                "externalParameters": {"version": manifest["metadata"]["version"]},
                "internalParameters": {"deterministicZip": True},
                "resolvedDependencies": [
                    {"uri": "artifact:BOPEN-SYS-001"},
                    {"uri": "artifact:BOPEN-P0-001"},
                    {"uri": "https://agentskills.io/specification"}
                ]
            },
            "runDetails": {
                "builder": {"id": "io.bizera.bopen.skill-packager/0.1.0"},
                "metadata": {"invocationId": digest[:24], "startedOn": now, "finishedOn": now}
            }
        }
    }
    (ROOT / "supply-chain/provenance.intoto.jsonl").write_text(json.dumps(provenance, separators=(",", ":")) + "\n", encoding="utf-8")

    inventory = []
    for path in included_files(include_dynamic=False):
        inventory.append({
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "size": path.stat().st_size,
        })
    release_manifest = {
        "schemaVersion": "1.0",
        "packageId": manifest["metadata"]["id"],
        "name": manifest["metadata"]["name"],
        "version": manifest["metadata"]["version"],
        "lifecycleStage": manifest["spec"]["lifecycle"]["stage"],
        "generatedAt": now,
        "sourceTreeDigest": digest,
        "signatureStatus": "unsigned",
        "independentApprovalStatus": "not-recorded",
        "inventoryExclusions": sorted(DYNAMIC_FILES),
        "files": inventory,
    }
    (ROOT / "supply-chain/release-manifest.json").write_text(json.dumps(release_manifest, indent=2) + "\n", encoding="utf-8")


def write_checksums() -> None:
    lines = []
    for path in included_files(include_dynamic=True):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "SHA256SUMS":
            continue
        lines.append(f"{sha256(path)}  {rel}")
    (ROOT / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def deterministic_zip(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in included_files(include_dynamic=True):
            rel = f"{ROOT.name}/{path.relative_to(ROOT).as_posix()}"
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if path.stat().st_mode & 0o111 else 0o644) << 16
            zf.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "bopen-architecture-0.1.0.zip")
    args = parser.parse_args()

    initial = subprocess.run([sys.executable, str(ROOT / "scripts/validate_package.py")], cwd=ROOT)
    if initial.returncode != 0:
        return initial.returncode

    write_supply_chain()
    write_checksums()

    final = subprocess.run([sys.executable, str(ROOT / "scripts/validate_package.py")], cwd=ROOT)
    if final.returncode != 0:
        return final.returncode

    deterministic_zip(args.output)
    digest = sha256(args.output)
    digest_file = args.output.with_suffix(args.output.suffix + ".sha256")
    digest_file.write_text(f"{digest}  {args.output.name}\n", encoding="utf-8")
    print(args.output.resolve())
    print(digest_file.resolve())
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
