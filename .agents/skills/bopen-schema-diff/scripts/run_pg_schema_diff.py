#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from common import redact, sha256_bytes

ALLOWED_EXECUTABLES = ("pg-schema-diff", "pgschemadiff")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe pg-schema-diff wrapper; captures a plan only")
    parser.add_argument("--dsn", required=True, help="Read-only DSN or runtime reference")
    parser.add_argument("--schema-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--meta", type=Path)
    parser.add_argument("--executable", choices=ALLOWED_EXECUTABLES, default="pg-schema-diff")
    args, extra = parser.parse_known_args()
    exe = shutil.which(args.executable)
    if not exe:
        print(f"{args.executable} executable not found", file=sys.stderr)
        return 127
    # The upstream CLI surface can change. Extra arguments must be supplied explicitly by an authorized caller.
    command = [exe, "plan", "--dsn", args.dsn, "--schema-dir", str(args.schema_dir)] + extra
    version = subprocess.run([exe, "--version"], capture_output=True, text=True, check=False)
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(proc.stdout, encoding="utf-8")
    meta = {
        "tool": "pg-schema-diff",
        "version": redact((version.stdout or version.stderr).strip()),
        "command": redact(" ".join(command)),
        "exit_code": proc.returncode,
        "stdout_sha256": sha256_bytes(proc.stdout.encode()),
        "stderr": redact(proc.stderr)[:4000],
    }
    if args.meta:
        args.meta.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(meta, indent=2))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
