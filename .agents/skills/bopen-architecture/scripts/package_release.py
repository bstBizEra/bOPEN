#!/usr/bin/env python3
"""Build a deterministic ZIP only from internally consistent approved records."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[2].resolve()
OUTPUT_ROOT = (ROOT.parents[1] / "skill-build-output" / ROOT.name).resolve()
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


def deterministic_zip(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing release: {output}")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in included_files(include_dynamic=True):
            rel = f"{ROOT.name}/{path.relative_to(ROOT).as_posix()}"
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if path.stat().st_mode & 0o111 else 0o644) << 16
            zf.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()

    manifest = yaml.safe_load((ROOT / "bopen.skill.yaml").read_text(encoding="utf-8"))
    status = manifest.get("metadata", {}).get("status")
    stage = manifest.get("spec", {}).get("lifecycle", {}).get("stage")
    source_revision = manifest.get("metadata", {}).get("sourceRevision")
    if status not in {"approved", "published"} or stage not in {"approved", "published"}:
        parser.error("Release packaging is disabled until independently approved lifecycle metadata is effective")
    if not isinstance(source_revision, str) or source_revision.upper() in {
        "UNBOUND",
        "UNCOMMITTED-CANDIDATE",
    }:
        parser.error("Release packaging requires an immutable source revision")

    try:
        OUTPUT_ROOT.relative_to(WORKSPACE)
    except ValueError:
        parser.error(f"Release output root must remain inside {WORKSPACE}")
    if OUTPUT_ROOT.exists() and (not OUTPUT_ROOT.is_dir() or OUTPUT_ROOT.is_symlink()):
        parser.error(f"Unsafe release output root: {OUTPUT_ROOT}")

    output = OUTPUT_ROOT / f"{ROOT.name}-{manifest['metadata']['version']}.zip"
    digest_file = output.with_suffix(output.suffix + ".sha256")
    if output.exists() or digest_file.exists():
        parser.error(f"Refusing to overwrite release output: {output} or {digest_file}")

    initial = subprocess.run([sys.executable, str(ROOT / "scripts/validate_package.py")], cwd=ROOT)
    if initial.returncode != 0:
        return initial.returncode

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    deterministic_zip(output)
    digest = sha256(output)
    with digest_file.open("x", encoding="utf-8") as handle:
        handle.write(f"{digest}  {output.name}\n")
    print(output)
    print(digest_file.resolve())
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
