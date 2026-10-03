#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md", "README.md", "bopen.skill.yaml", "LICENSE.txt", "NOTICE.md",
    "schemas/input.schema.json", "schemas/output.schema.json", "schemas/canonical-change.schema.json",
    "policies/execution-policy.yaml", "references/operating-procedure.md",
    "evals/cases.yaml", "scripts/analyze_sql.py", "tests/test_analyze_sql.py",
]
SECRET_PATTERNS = [
    re.compile(r"(?i)postgres(?:ql)?://[^\s:/]+:[^\s@]+@"),
    re.compile(r"(?i)(password|passwd|api[_-]?key|secret)\s*[=:]\s*['\"]?[A-Za-z0-9+/=_-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
]


def main() -> int:
    errors = []
    warnings = []
    passed = 0
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            errors.append(f"Missing required file: {rel}")
        else:
            passed += 1

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n([\s\S]*?)\n---\n", skill)
    if not m:
        errors.append("SKILL.md YAML frontmatter missing")
    else:
        meta = yaml.safe_load(m.group(1))
        if meta.get("name") != ROOT.name:
            errors.append("SKILL.md name must match parent directory")
        else:
            passed += 1
        if not meta.get("description") or len(meta["description"]) < 80:
            errors.append("SKILL.md description is too short for reliable activation")
        else:
            passed += 1
        if len(skill.splitlines()) > 500:
            warnings.append("SKILL.md exceeds 500 lines")
        else:
            passed += 1

    manifest = yaml.safe_load((ROOT / "bopen.skill.yaml").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/bopen-skill.schema.json").read_text(encoding="utf-8"))
    manifest_errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda e: list(e.path))
    errors.extend([f"Manifest schema: {e.message}" for e in manifest_errors])
    if not manifest_errors:
        passed += 1

    for path in sorted((ROOT / "schemas").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(data)
            passed += 1
        except Exception as exc:
            errors.append(f"Invalid JSON Schema {path.name}: {exc}")

    for path in sorted(ROOT.rglob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
            passed += 1
        except Exception as exc:
            errors.append(f"Invalid YAML {path.relative_to(ROOT)}: {exc}")

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name in {"SHA256SUMS", "common.py", "validate_package.py"} or ".git" in path.parts:
            continue
        if path.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".py", ".txt", ".sql", ".toml"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    errors.append(f"Possible embedded secret in {path.relative_to(ROOT)}")
                    break
            else:
                passed += 1

    print(json.dumps({"passed": passed, "warnings": warnings, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
