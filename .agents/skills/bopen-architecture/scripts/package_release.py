#!/usr/bin/env python3
"""Build a deterministic ZIP release with inventory, provenance, and checksums."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

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


def deterministic_zip(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "bopen-architecture-0.1.0.zip")
    args = parser.parse_args()
    args.output = args.output.resolve()
    allowed_output = (ROOT / "dist").resolve()
    try:
        args.output.relative_to(allowed_output)
    except ValueError:
        parser.error(f"Output must remain inside {allowed_output}")
    digest_file = args.output.with_suffix(args.output.suffix + ".sha256")
    if args.output.exists() or digest_file.exists():
        parser.error(f"Refusing to overwrite release output: {args.output} or {digest_file}")

    initial = subprocess.run([sys.executable, str(ROOT / "scripts/validate_package.py")], cwd=ROOT)
    if initial.returncode != 0:
        return initial.returncode

    deterministic_zip(args.output)
    digest = sha256(args.output)
    digest_file.write_text(f"{digest}  {args.output.name}\n", encoding="utf-8")
    print(args.output.resolve())
    print(digest_file.resolve())
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
