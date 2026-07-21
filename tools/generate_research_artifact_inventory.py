#!/usr/bin/env python3
"""Deterministically regenerate the BOPEN-RES-001 artifact inventory."""
from __future__ import annotations

import json

from validate_research_g3_design import ARTIFACT_INVENTORY, DEFAULT_CONTRACT, build_research_inventory, load_contract


def main() -> int:
    data = load_contract(DEFAULT_CONTRACT)
    inventory = build_research_inventory(data)
    ARTIFACT_INVENTORY.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(inventory['files'])} research artifact records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
