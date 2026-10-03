from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

VERDICT_RANK = {
    "SAFE": 0,
    "CONDITIONAL": 1,
    "REVIEW_REQUIRED": 2,
    "BREAKING": 3,
    "DESTRUCTIVE": 4,
    "SECURITY_CRITICAL": 5,
    "BLOCKED": 6,
    "UNKNOWN": 2,
}

STATUS_FOR_VERDICT = {
    "SAFE": "PASS",
    "CONDITIONAL": "REVIEW",
    "REVIEW_REQUIRED": "REVIEW",
    "BREAKING": "REVIEW",
    "DESTRUCTIVE": "BLOCK",
    "SECURITY_CRITICAL": "BLOCK",
    "BLOCKED": "BLOCK",
    "UNKNOWN": "REVIEW",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*[^\s,;]+"),
    re.compile(r"(?i)postgres(?:ql)?://([^:/@]+):([^@]+)@"),
    re.compile(r"(?i)(token|secret|api[_-]?key)\s*[=:]\s*[^\s,;]+"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def redact(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        if "postgres" in pattern.pattern.lower():
            result = pattern.sub("postgresql://<redacted>:<redacted>@", result)
        else:
            result = pattern.sub(lambda m: m.group(0).split('=')[0] + '=<redacted>' if '=' in m.group(0) else '<redacted>', result)
    return result


def max_verdict(verdicts: list[str]) -> str:
    if not verdicts:
        return "SAFE"
    return max(verdicts, key=lambda v: VERDICT_RANK.get(v, VERDICT_RANK["UNKNOWN"]))


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
