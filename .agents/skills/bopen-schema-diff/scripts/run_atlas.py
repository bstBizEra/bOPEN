#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from common import redact, sha256_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe Atlas schema diff wrapper; never applies migrations")
    parser.add_argument("--from-source", required=True)
    parser.add_argument("--to-source", required=True)
    parser.add_argument("--dev-url")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--meta", type=Path)
    args = parser.parse_args()
    atlas = shutil.which("atlas")
    if not atlas:
        print("Atlas executable not found", file=sys.stderr)
        return 127
    command = [atlas, "schema", "diff", "--from", args.from_source, "--to", args.to_source]
    if args.dev_url:
        command += ["--dev-url", args.dev_url]
    version = subprocess.run([atlas, "version"], capture_output=True, text=True, check=False)
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(proc.stdout, encoding="utf-8")
    meta = {
        "tool": "atlas",
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
