#!/usr/bin/env python3
"""Generate the deterministic G3 design-readiness report; never execute research."""
from __future__ import annotations

from pathlib import Path

from validate_research_g3_design import DEFAULT_CONTRACT, DEFAULT_SCHEMA, load_contract, render_report, validate_all

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/validation/research-g3-design-readiness.md"


def main() -> int:
    data = load_contract(DEFAULT_CONTRACT)
    schema = load_contract(DEFAULT_SCHEMA)
    errors = validate_all(data, schema)
    if errors:
        print("G3 design report not written because validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    content = render_report(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
