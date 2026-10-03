#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import STATUS_FOR_VERDICT, max_verdict


def main() -> int:
    parser = argparse.ArgumentParser(description="Recalculate final risk from a bOPEN schema report")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    data = json.loads(args.report.read_text(encoding="utf-8"))
    verdict = max_verdict([f.get("verdict", "UNKNOWN") for f in data.get("findings", [])])
    data["verdict"] = verdict
    data["status"] = STATUS_FOR_VERDICT[verdict]
    print(json.dumps(data, indent=2))
    return 2 if data["status"] == "BLOCK" else 1 if data["status"] == "REVIEW" else 0


if __name__ == "__main__":
    sys.exit(main())
