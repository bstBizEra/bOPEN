#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = [p for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.name != "SHA256SUMS"]
    sums = "".join(f"{sha(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
    (ROOT / "SHA256SUMS").write_text(sums, encoding="utf-8")
    files.append(ROOT / "SHA256SUMS")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(files):
            info = zipfile.ZipInfo((Path(ROOT.name) / p.relative_to(ROOT)).as_posix(), date_time=(2026, 7, 22, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if p.suffix == ".py" else 0o644) << 16
            zf.writestr(info, p.read_bytes())
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output), "files": len(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
