#!/usr/bin/env python3
"""Portable, tiered linter for bOPEN agent skill packages.

Pure standard library. No third-party imports. Discovers every skill under
`.agents/skills/*/`, assigns a maturity tier (L0..L3), and validates the
package contents against the portable manifest schema in
`.agents/schemas/skill-manifest.schema.json`.

Exit code 0 when there are no errors, 1 otherwise.

Usage:
    python validate_skill_package.py
    python validate_skill_package.py --tier-report
    python validate_skill_package.py --json report.json
    python validate_skill_package.py --skills-root <dir> --repo-root <dir>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOOLS_DIR = Path(__file__).resolve().parent
AGENTS_DIR = TOOLS_DIR.parent
DEFAULT_SKILLS_ROOT = AGENTS_DIR / "skills"
DEFAULT_SCHEMA = AGENTS_DIR / "schemas" / "skill-manifest.schema.json"
DEFAULT_REPO_ROOT = AGENTS_DIR.parent

MANIFEST_NAME = "bopen.skill.yaml"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DESCRIPTION_MAX = 1024
DESCRIPTION_MIN = 40
SKILL_MD_MAX_LINES = 500

# A `bopen-foo` token that is NOT part of a filesystem path or dotted id.
SKILL_REF_RE = re.compile(
    r"(?<![A-Za-z0-9_./\\-])(bopen-[a-z0-9]+(?:-[a-z0-9]+)*)(?![A-Za-z0-9_.-])"
)
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
PATH_TOKEN_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.<>*-]+)+$")
PLACEHOLDER_MARKERS = ("<", ">", "*", "...")

# Phrases that make a description state WHEN the skill applies.
TRIGGER_MARKERS = (
    "use when",
    "use for",
    "use this",
    "do not use",
    "use after",
    "use before",
    " when ",
    " before ",
    " after ",
    " during ",
    "triggers on",
    "trigger when",
)

# ---------------------------------------------------------------------------
# Tier model
# ---------------------------------------------------------------------------

TIER_DESCRIPTIONS = {
    "L0": "Prompt-only: SKILL.md alone.",
    "L1": "Declared: L0 + bopen.skill.yaml manifest + README + LICENSE.",
    "L2": "Contracted: L1 + schemas/ contracts + evals/ (cases + trigger sets).",
    "L3": "Governed: L2 + policies/ + ci/ + tests/ + bundled validator + release surface.",
}

L1_REQUIRED = [MANIFEST_NAME, "README.md"]
L1_ANY_OF = [["LICENSE.txt", "LICENSE.md", "LICENSE"]]
L2_REQUIRED = [
    "schemas/input.schema.json",
    "schemas/output.schema.json",
    "evals/cases.yaml",
    "evals/trigger-positive.yaml",
    "evals/trigger-negative.yaml",
]
L3_REQUIRED = [
    "policies/execution-policy.yaml",
    "scripts/validate_package.py",
]
L3_ANY_OF = [
    ["ci/validate-skill.yml", "ci/validate-skill.yaml"],
    ["SHA256SUMS", "supply-chain/release-manifest.json"],
]


# ---------------------------------------------------------------------------
# Minimal safe YAML subset parser (stdlib only)
# ---------------------------------------------------------------------------


class MiniYamlError(ValueError):
    """Raised when the document uses YAML beyond the supported subset."""


def _strip_comment(text: str) -> str:
    out = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            break
        else:
            out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _scalar(raw: str) -> Any:
    text = _strip_comment(raw).strip()
    if text == "" or text in ("~", "null", "Null", "NULL"):
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        inner = text[1:-1]
        if text[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")
        else:
            inner = inner.replace("''", "'")
        return inner
    if text in ("true", "True", "TRUE"):
        return True
    if text in ("false", "False", "FALSE"):
        return False
    if text == "[]":
        return []
    if text == "{}":
        return {}
    if re.fullmatch(r"[-+]?[0-9]+", text):
        return int(text)
    if re.fullmatch(r"[-+]?[0-9]*\.[0-9]+(?:[eE][-+]?[0-9]+)?", text):
        return float(text)
    return text


def _tokenize(text: str) -> list[tuple[int, str, int]]:
    lines: list[tuple[int, str, int]] = []
    for number, raw in enumerate(text.split("\n"), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise MiniYamlError(f"line {number}: tab indentation is not supported")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in ("---", "..."):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip(), number))
    return lines


def _parse_block(lines: list[tuple[int, str, int]], start: int, indent: int) -> tuple[Any, int]:
    if start >= len(lines):
        return None, start
    if lines[start][1].startswith("- ") or lines[start][1] == "-":
        return _parse_sequence(lines, start, indent)
    return _parse_mapping(lines, start, indent)


def _parse_sequence(lines: list[tuple[int, str, int]], start: int, indent: int) -> tuple[list, int]:
    items: list[Any] = []
    i = start
    while i < len(lines):
        line_indent, text, number = lines[i]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise MiniYamlError(f"line {number}: unexpected indentation in sequence")
        if not (text.startswith("- ") or text == "-"):
            break
        rest = text[2:].strip() if text.startswith("- ") else ""
        if not rest:
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                value, i = _parse_block(lines, i, lines[i][0])
                items.append(value)
            else:
                items.append(None)
            continue
        key_match = re.match(r"^([A-Za-z0-9_.$-]+):(?:\s+(.*))?$", rest)
        if key_match:
            inner_indent = indent + 2
            synthetic: list[tuple[int, str, int]] = [(inner_indent, rest, number)]
            j = i + 1
            while j < len(lines) and lines[j][0] > indent:
                synthetic.append((lines[j][0], lines[j][1], lines[j][2]))
                j += 1
            value, _ = _parse_mapping(synthetic, 0, inner_indent)
            items.append(value)
            i = j
            continue
        items.append(_scalar(rest))
        i += 1
    return items, i


def _parse_mapping(lines: list[tuple[int, str, int]], start: int, indent: int) -> tuple[dict, int]:
    mapping: dict[str, Any] = {}
    i = start
    while i < len(lines):
        line_indent, text, number = lines[i]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise MiniYamlError(f"line {number}: unexpected indentation in mapping")
        if text.startswith("- "):
            break
        match = re.match(r"^([A-Za-z0-9_.$/-]+|\"[^\"]+\"|'[^']+'):(?:\s+(.*))?$", text)
        if not match:
            raise MiniYamlError(f"line {number}: unsupported YAML construct: {text!r}")
        key = match.group(1).strip("\"'")
        raw_value = match.group(2)
        if key in mapping:
            raise MiniYamlError(f"line {number}: duplicate key {key!r}")
        if raw_value is not None and _strip_comment(raw_value).strip() != "":
            mapping[key] = _scalar(raw_value)
            i += 1
            continue
        i += 1
        if i < len(lines) and lines[i][0] > indent:
            mapping[key], i = _parse_block(lines, i, lines[i][0])
        elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
            mapping[key], i = _parse_sequence(lines, i, indent)
        else:
            mapping[key] = None
    return mapping, i


def mini_yaml_load(text: str) -> Any:
    lines = _tokenize(text)
    if not lines:
        return None
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise MiniYamlError(f"line {lines[index][2]}: trailing content not parsed")
    return value


# ---------------------------------------------------------------------------
# Minimal JSON Schema (draft 2020-12 subset) validator
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def schema_errors(instance: Any, schema: dict, where: str = "<root>") -> list[str]:
    out: list[str] = []
    if "const" in schema and instance != schema["const"]:
        out.append(f"{where}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        out.append(f"{where}: {instance!r} is not one of {schema['enum']}")

    expected = schema.get("type")
    if expected:
        if not _type_ok(instance, expected):
            out.append(f"{where}: expected type {expected}, got {type(instance).__name__}")
            return out

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append(f"{where}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            out.append(f"{where}: longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            out.append(f"{where}: {instance!r} does not match pattern {schema['pattern']}")
        if schema.get("format") == "date" and not DATE_RE.fullmatch(instance):
            out.append(f"{where}: {instance!r} is not a YYYY-MM-DD date")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            out.append(f"{where}: below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            out.append(f"{where}: above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            out.append(f"{where}: fewer than minItems {schema['minItems']}")
        if schema.get("uniqueItems"):
            seen = [json.dumps(v, sort_keys=True, default=str) for v in instance]
            if len(seen) != len(set(seen)):
                out.append(f"{where}: items are not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                out.extend(schema_errors(item, item_schema, f"{where}[{index}]"))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                out.append(f"{where}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    out.append(f"{where}: additional property {key!r} is not allowed")
        for key, sub_schema in properties.items():
            if key in instance:
                out.extend(schema_errors(instance[key], sub_schema, f"{where}.{key}"))
    return out


def _type_ok(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    return True


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Findings:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def add(self, severity: str, skill: str, code: str, message: str, location: str = "") -> None:
        self.items.append(
            {
                "severity": severity,
                "skill": skill,
                "code": code,
                "message": message,
                "location": location,
            }
        )

    def error(self, skill: str, code: str, message: str, location: str = "") -> None:
        self.add("error", skill, code, message, location)

    def warning(self, skill: str, code: str, message: str, location: str = "") -> None:
        self.add("warning", skill, code, message, location)

    @property
    def errors(self) -> list[dict[str, Any]]:
        return [i for i in self.items if i["severity"] == "error"]

    @property
    def warnings(self) -> list[dict[str, Any]]:
        return [i for i in self.items if i["severity"] == "warning"]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with a '---' YAML frontmatter delimiter")
    end = text.find("\n---\n", 3)
    if end == -1:
        raise ValueError("SKILL.md frontmatter closing '---' delimiter not found")
    front = mini_yaml_load(text[4:end])
    if not isinstance(front, dict):
        raise ValueError("SKILL.md frontmatter must be a mapping")
    return front, text[end + 5 :]


def assign_tier(skill_dir: Path) -> tuple[str, list[str]]:
    """Return (tier, missing_for_next_tier)."""

    def have(rel: str) -> bool:
        return (skill_dir / rel).exists()

    def missing(required: list[str], any_of: list[list[str]]) -> list[str]:
        gaps = [r for r in required if not have(r)]
        for group in any_of:
            if not any(have(g) for g in group):
                gaps.append(" | ".join(group))
        return gaps

    if not (skill_dir / "SKILL.md").is_file():
        return "INVALID", ["SKILL.md"]

    gap1 = missing(L1_REQUIRED, L1_ANY_OF)
    if gap1:
        return "L0", gap1
    gap2 = missing(L2_REQUIRED, [])
    if gap2:
        return "L1", gap2
    gap3 = missing(L3_REQUIRED, L3_ANY_OF)
    if gap3:
        return "L2", gap3
    return "L3", []


def check_hygiene(findings: Findings, skill: str, path: Path, rel: str) -> None:
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    if crlf:
        findings.error(skill, "HYGIENE_CRLF", f"{crlf} CRLF line ending(s); files must be LF only", rel)
    if b"\x97" in raw:
        line = raw[: raw.index(b"\x97")].count(b"\n") + 1
        findings.error(
            skill,
            "HYGIENE_CP1252",
            "byte 0x97 present (cp1252 em dash); indicates encoding corruption",
            f"{rel}:{line}",
        )
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        findings.error(skill, "HYGIENE_UTF8", f"not valid UTF-8: {exc}", rel)
        return
    non_ascii = sorted({b for b in raw if b > 0x7F})
    if non_ascii:
        findings.warning(
            skill,
            "HYGIENE_NON_ASCII",
            "non-ASCII bytes present: " + ", ".join(hex(b) for b in non_ascii[:8]),
            rel,
        )
    if raw and not raw.endswith(b"\n"):
        findings.warning(skill, "HYGIENE_EOF_NEWLINE", "file does not end with a newline", rel)


def check_skill_md(findings: Findings, skill_dir: Path, tier: str, strict_triggers: bool) -> tuple[dict, str]:
    skill = skill_dir.name
    path = skill_dir / "SKILL.md"
    rel = f"{skill}/SKILL.md"
    check_hygiene(findings, skill, path, rel)
    text = path.read_text(encoding="utf-8", errors="replace")

    try:
        front, body = split_frontmatter(text)
    except (ValueError, MiniYamlError) as exc:
        findings.error(skill, "FRONTMATTER", str(exc), rel)
        return {}, ""

    name = front.get("name")
    if not isinstance(name, str) or not name.strip():
        findings.error(skill, "NAME_MISSING", "frontmatter 'name' is missing or empty", rel)
    elif not NAME_RE.fullmatch(name):
        findings.error(skill, "NAME_FORMAT", f"name {name!r} is not lowercase-kebab-case", rel)
    elif len(name) > 64:
        findings.error(skill, "NAME_LENGTH", "name exceeds 64 characters", rel)
    elif name != skill:
        findings.error(skill, "NAME_DIR_MISMATCH", f"name {name!r} does not match directory {skill!r}", rel)

    desc = front.get("description")
    if not isinstance(desc, str) or not desc.strip():
        findings.error(skill, "DESC_MISSING", "frontmatter 'description' is missing or empty", rel)
    else:
        if len(desc) > DESCRIPTION_MAX:
            findings.error(
                skill, "DESC_TOO_LONG", f"description is {len(desc)} chars (max {DESCRIPTION_MAX})", rel
            )
        if len(desc) < DESCRIPTION_MIN:
            findings.warning(
                skill, "DESC_TOO_SHORT", f"description is {len(desc)} chars (min useful {DESCRIPTION_MIN})", rel
            )
        lowered = " " + desc.lower() + " "
        if not any(marker in lowered for marker in TRIGGER_MARKERS):
            severity = "error" if (strict_triggers or tier in ("L2", "L3")) else "warning"
            findings.add(
                severity,
                skill,
                "DESC_NO_TRIGGER",
                "description does not state WHEN to use the skill (no 'Use when/Use for/before/after' clause)",
                rel,
            )

    if not body.strip():
        findings.error(skill, "BODY_EMPTY", "SKILL.md body after frontmatter is empty", rel)

    line_count = len(text.splitlines())
    if line_count > SKILL_MD_MAX_LINES:
        findings.warning(skill, "BODY_TOO_LONG", f"SKILL.md is {line_count} lines (recommend < {SKILL_MD_MAX_LINES})", rel)

    allowed_tools = front.get("allowed-tools")
    if allowed_tools is not None and not isinstance(allowed_tools, str):
        findings.error(skill, "ALLOWED_TOOLS_TYPE", "allowed-tools must be a space-separated string", rel)

    metadata = front.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        findings.error(skill, "METADATA_TYPE", "frontmatter 'metadata' must be a mapping", rel)

    return front, body


def check_cross_references(
    findings: Findings, skill_dir: Path, known_skills: set[str], repo_root: Path, repo_paths_warn: bool
) -> None:
    skill = skill_dir.name
    path = skill_dir / "SKILL.md"
    rel = f"{skill}/SKILL.md"
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for match in SKILL_REF_RE.finditer(line):
            token = match.group(1)
            if token == skill or token in known_skills:
                continue
            findings.error(
                skill,
                "XREF_SKILL_DANGLING",
                f"references skill {token!r} but no such directory exists",
                f"{rel}:{number}",
            )
        for match in BACKTICK_RE.finditer(line):
            token = match.group(1).strip()
            if not PATH_TOKEN_RE.fullmatch(token):
                continue
            if any(marker in token for marker in PLACEHOLDER_MARKERS):
                continue
            if token.startswith(("http:", "https:", "//")):
                continue
            if (repo_root / token).exists() or (skill_dir / token).exists():
                continue
            add = findings.warning if repo_paths_warn else findings.error
            add(
                skill,
                "XREF_PATH_MISSING",
                f"repo path {token!r} does not exist under {repo_root}",
                f"{rel}:{number}",
            )


def check_manifest(findings: Findings, skill_dir: Path, schema: dict) -> None:
    skill = skill_dir.name
    path = skill_dir / MANIFEST_NAME
    rel = f"{skill}/{MANIFEST_NAME}"
    if not path.is_file():
        return
    check_hygiene(findings, skill, path, rel)
    try:
        manifest = mini_yaml_load(path.read_text(encoding="utf-8"))
    except (MiniYamlError, ValueError) as exc:
        findings.error(skill, "MANIFEST_PARSE", f"cannot parse manifest: {exc}", rel)
        return
    if not isinstance(manifest, dict):
        findings.error(skill, "MANIFEST_TYPE", "manifest root must be a mapping", rel)
        return

    for message in schema_errors(manifest, schema, "manifest"):
        findings.error(skill, "MANIFEST_SCHEMA", message, rel)

    metadata = manifest.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("name") != skill:
        findings.error(
            skill,
            "MANIFEST_NAME_DIR_MISMATCH",
            f"metadata.name {metadata.get('name')!r} does not match directory {skill!r}",
            rel,
        )

    spec = manifest.get("spec") or {}
    if isinstance(spec, dict):
        referenced: dict[str, Any] = {}
        referenced.update(spec.get("contracts") or {})
        lifecycle = spec.get("lifecycle") or {}
        evaluation = spec.get("evaluation") or {}
        if isinstance(lifecycle, dict):
            referenced["lifecycle.deprecationPolicy"] = lifecycle.get("deprecationPolicy")
            referenced["lifecycle.revocationPolicy"] = lifecycle.get("revocationPolicy")
        if isinstance(evaluation, dict):
            referenced["evaluation.suite"] = evaluation.get("suite")
        for key, target in referenced.items():
            if isinstance(target, str) and not (skill_dir / target).exists():
                findings.error(
                    skill, "MANIFEST_PATH_MISSING", f"{key} points at missing file {target!r}", rel
                )


def check_trigger_fixtures(findings: Findings, skill_dir: Path) -> None:
    skill = skill_dir.name
    for rel_name in ("evals/trigger-positive.yaml", "evals/trigger-negative.yaml"):
        path = skill_dir / rel_name
        if not path.is_file():
            continue
        rel = f"{skill}/{rel_name}"
        check_hygiene(findings, skill, path, rel)
        try:
            items = mini_yaml_load(path.read_text(encoding="utf-8"))
        except (MiniYamlError, ValueError) as exc:
            findings.error(skill, "EVAL_PARSE", f"cannot parse {rel_name}: {exc}", rel)
            continue
        if not isinstance(items, list) or not items or any(not isinstance(v, str) or not v.strip() for v in items):
            findings.error(skill, "EVAL_TRIGGER_SHAPE", f"{rel_name} must be a non-empty list of prompt strings", rel)
        elif len(items) != len(set(items)):
            findings.error(skill, "EVAL_TRIGGER_DUPLICATE", f"{rel_name} contains duplicate prompts", rel)


TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".toml", ".csv"}


def iter_text_files(skill_dir: Path):
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in ("Makefile", "SHA256SUMS", "LICENSE", "NOTICE"):
            yield path


def check_package_hygiene(findings: Findings, skill_dir: Path, already_checked: set[Path]) -> None:
    """Sweep every text file in the package for CRLF / 0x97 / non-ASCII."""
    for path in iter_text_files(skill_dir):
        if path in already_checked:
            continue
        rel = str(path.relative_to(skill_dir.parent)).replace("\\", "/")
        check_hygiene(findings, skill_dir.name, path, rel)


def check_secrets(findings: Findings, skill_dir: Path) -> None:
    patterns = {
        "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "openai-like-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
        "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    }
    suffixes = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".toml", ".csv"}
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in patterns.items():
            if pattern.search(text):
                findings.error(
                    skill_dir.name,
                    "SECRET_SUSPECTED",
                    f"possible embedded secret ({label})",
                    str(path.relative_to(skill_dir.parent)).replace("\\", "/"),
                )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def validate(
    skills_root: Path, repo_root: Path, schema_path: Path, strict_triggers: bool, repo_paths_warn: bool
) -> dict[str, Any]:
    findings = Findings()
    schema: dict = {}
    if schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    else:
        findings.warning("<global>", "SCHEMA_MISSING", f"manifest schema not found at {schema_path}")

    skill_dirs = sorted(d for d in skills_root.iterdir() if d.is_dir() and not d.name.startswith("."))
    known = {d.name for d in skill_dirs}
    rows: list[dict[str, Any]] = []

    for skill_dir in skill_dirs:
        skill = skill_dir.name
        if not NAME_RE.fullmatch(skill):
            findings.error(skill, "DIR_NAME_FORMAT", "skill directory name is not lowercase-kebab-case", skill)
        if not (skill_dir / "SKILL.md").is_file():
            findings.error(skill, "SKILL_MD_MISSING", "SKILL.md is missing", f"{skill}/SKILL.md")
            rows.append({"skill": skill, "tier": "INVALID", "files": 0, "gaps": ["SKILL.md"]})
            continue

        tier, gaps = assign_tier(skill_dir)
        check_skill_md(findings, skill_dir, tier, strict_triggers)
        check_cross_references(findings, skill_dir, known, repo_root, repo_paths_warn)
        if schema:
            check_manifest(findings, skill_dir, schema)
        check_trigger_fixtures(findings, skill_dir)
        check_package_hygiene(
            findings,
            skill_dir,
            {
                skill_dir / "SKILL.md",
                skill_dir / MANIFEST_NAME,
                skill_dir / "evals/trigger-positive.yaml",
                skill_dir / "evals/trigger-negative.yaml",
            },
        )
        check_secrets(findings, skill_dir)

        file_count = sum(1 for p in skill_dir.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        rows.append({"skill": skill, "tier": tier, "files": file_count, "gaps": gaps})

    return {
        "status": "fail" if findings.errors else "pass",
        "skillsRoot": str(skills_root),
        "repoRoot": str(repo_root),
        "tierDefinitions": TIER_DESCRIPTIONS,
        "skills": rows,
        "errorCount": len(findings.errors),
        "warningCount": len(findings.warnings),
        "findings": findings.items,
    }


def print_tier_report(report: dict[str, Any]) -> None:
    print("Tier  Files  Skill                            Gap to next tier")
    print("-" * 100)
    for row in sorted(report["skills"], key=lambda r: (r["tier"], r["skill"])):
        gaps = ", ".join(row["gaps"]) if row["gaps"] else "-"
        if len(gaps) > 46:
            gaps = gaps[:43] + "..."
        print(f"{row['tier']:<5} {row['files']:>5}  {row['skill']:<32} {gaps}")
    print()
    for tier in ("L0", "L1", "L2", "L3"):
        count = sum(1 for r in report["skills"] if r["tier"] == tier)
        print(f"  {tier}: {count:>2} skill(s)  - {TIER_DESCRIPTIONS[tier]}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint bOPEN agent skill packages.")
    parser.add_argument("--skills-root", type=Path, default=DEFAULT_SKILLS_ROOT)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--json", type=Path, default=None, help="write the machine-readable report to this path")
    parser.add_argument("--tier-report", action="store_true", help="print the maturity tier table")
    parser.add_argument("--strict-triggers", action="store_true", help="treat weak descriptions as errors at every tier")
    parser.add_argument("--repo-paths-warn", action="store_true", help="downgrade missing repo paths to warnings")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    skills_root = args.skills_root.resolve()
    if not skills_root.is_dir():
        print(f"FAIL: skills root not found: {skills_root}", file=sys.stderr)
        return 1

    report = validate(
        skills_root, args.repo_root.resolve(), args.schema.resolve(), args.strict_triggers, args.repo_paths_warn
    )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

    if not args.quiet:
        if args.tier_report:
            print_tier_report(report)
        for item in report["findings"]:
            label = "FAIL" if item["severity"] == "error" else "WARN"
            location = item["location"] or item["skill"]
            print(f"{label}: [{item['code']}] {location}: {item['message']}")
        print(
            f"\nResult: {report['status'].upper()} - {len(report['skills'])} skill(s), "
            f"{report['errorCount']} error(s), {report['warningCount']} warning(s)"
        )
    return 1 if report["errorCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
