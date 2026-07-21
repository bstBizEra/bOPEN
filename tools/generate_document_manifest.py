#!/usr/bin/env python3
"""Generate a deterministic document manifest or an immutable candidate snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("docs/DOCUMENT-MANIFEST.json")
DEFAULT_INDEX = Path("docs/manifests/MANIFEST-INDEX.jsonl")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml"}
INDEX_COMMON_KEYS = {
    "id", "sequence", "previous_entry_sha256", "mode", "path", "bytes", "sha256"
}
INDEX_MODE_KEYS = {
    "immutable_source_blob": {
        "source_commit", "source_tree", "source_path", "git_blob"
    },
    "current_aggregate": {"exclusions"},
    "current_exact_file": set(),
}


def canonical_document_bytes(path: Path) -> tuple[bytes, str]:
    """Return platform-independent bytes for governed UTF-8 text documents."""
    data = path.read_bytes()
    if path.suffix not in TEXT_SUFFIXES:
        return data, ""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data, ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.encode("utf-8"), normalized


def build_manifest(output: Path, root: Path = ROOT) -> dict:
    records = []
    resolved_output = output if output.is_absolute() else root / output
    document_paths = sorted(
        (root / "docs").rglob("*"),
        key=lambda candidate: candidate.relative_to(root).as_posix(),
    )
    for path in document_paths:
        if not path.is_file() or path.name == "DOCUMENT-MANIFEST.json" or path.resolve() == resolved_output.resolve():
            continue
        data, text = canonical_document_bytes(path)
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), "")
        match = re.search(r"\*\*Status:\*\*\s*([^\n]+)", text)
        records.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "title": title,
                "status": match.group(1).strip() if match else "",
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return {
        "generated": datetime.now(timezone.utc).date().isoformat(),
        "count": len(records),
        "documents": records,
    }


def git_output(root: Path, *args: str) -> bytes | None:
    result = subprocess.run(
        ["git", *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    return result.stdout if result.returncode == 0 else None


def repository_paths(root: Path = ROOT) -> list[Path]:
    tracked = git_output(root, "ls-files", "-z")
    untracked = git_output(root, "ls-files", "--others", "--exclude-standard", "-z")
    if tracked is None or untracked is None:
        raise RuntimeError("Git worktree is required for aggregate manifests")
    names = {
        item.decode("utf-8")
        for payload in (tracked, untracked)
        for item in payload.split(b"\0")
        if item
    }
    return [root / name for name in sorted(names) if (root / name).is_file()]


def build_aggregate_manifest(
    output: Path,
    *,
    root: Path = ROOT,
    exclusions: tuple[str, ...] = (),
) -> dict:
    output_rel = output.as_posix() if not output.is_absolute() else output.relative_to(root).as_posix()
    excluded = set(exclusions) | {output_rel}
    records = []
    for path in repository_paths(root):
        rel = path.relative_to(root).as_posix()
        if rel in excluded:
            continue
        data = path.read_bytes()
        records.append(
            {
                "path": rel,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return {
        "manifest_id": "QUAL-INTEG-001-AGGREGATE",
        "version": "0.1",
        "status": "draft",
        "lifecycle": "inactive",
        "generated": "2026-07-22",
        "exclusions": sorted(excluded),
        "count": len(records),
        "files": records,
    }


def load_manifest_index(index_path: Path, root: Path = ROOT) -> tuple[list[dict], list[str]]:
    path = index_path if index_path.is_absolute() else root / index_path
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except Exception as exc:
        return [], [f"MANIFEST INDEX INVALID: {exc}"]
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        errors.append("MANIFEST INDEX MUST USE UTF-8 WITHOUT BOM AND LF")
    entries: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception as exc:
            errors.append(f"MANIFEST INDEX LINE {number} INVALID: {exc}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"MANIFEST INDEX LINE {number} MUST BE OBJECT")
            continue
        entries.append(entry)
    ids = [entry.get("id") for entry in entries]
    paths = [entry.get("path") for entry in entries]
    if not all(isinstance(item, str) and item for item in ids) or len(ids) != len(set(ids)):
        errors.append("MANIFEST INDEX IDS MUST BE UNIQUE STRINGS")
    if not all(isinstance(item, str) and item for item in paths) or len(paths) != len(set(paths)):
        errors.append("MANIFEST INDEX PATHS MUST BE UNIQUE STRINGS")
    previous_digest = None
    for sequence, entry in enumerate(entries, start=1):
        mode = entry.get("mode")
        expected_keys = INDEX_COMMON_KEYS | INDEX_MODE_KEYS.get(mode, set())
        if mode not in INDEX_MODE_KEYS:
            errors.append(f"MANIFEST INDEX MODE UNKNOWN AT SEQUENCE {sequence}: {mode}")
        elif set(entry) != expected_keys:
            errors.append(f"MANIFEST INDEX KEYS INVALID AT SEQUENCE {sequence}")
        if entry.get("sequence") != sequence:
            errors.append(f"MANIFEST INDEX SEQUENCE INVALID AT LINE {sequence}")
        if entry.get("previous_entry_sha256") != previous_digest:
            errors.append(f"MANIFEST INDEX PREFIX CHAIN INVALID AT SEQUENCE {sequence}")
        rel = entry.get("path")
        if isinstance(rel, str):
            candidate = Path(rel)
            normalized = candidate.as_posix()
            if candidate.is_absolute() or "\\" in rel or normalized != rel or ".." in candidate.parts:
                errors.append(f"MANIFEST INDEX PATH NOT NORMALIZED: {rel}")
            else:
                target = root / candidate
                if target.is_symlink():
                    errors.append(f"MANIFEST INDEX PATH MUST NOT BE SYMLINK: {rel}")
                try:
                    target.resolve().relative_to(root.resolve())
                except ValueError:
                    errors.append(f"MANIFEST INDEX PATH ESCAPES ROOT: {rel}")
        canonical = json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        previous_digest = hashlib.sha256(canonical).hexdigest()
    return entries, errors


def validate_manifest_entry(entry: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    rel = entry.get("path")
    mode = entry.get("mode")
    if not isinstance(rel, str) or not isinstance(mode, str):
        return ["MANIFEST INDEX ENTRY PATH/MODE INVALID"]
    path = root / rel
    try:
        current = path.read_bytes()
    except FileNotFoundError:
        return [f"MANIFEST INDEX FILE MISSING: {rel}"]
    if len(current) != entry.get("bytes"):
        errors.append(f"MANIFEST INDEX BYTE COUNT MISMATCH: {rel}")
    if hashlib.sha256(current).hexdigest() != entry.get("sha256"):
        errors.append(f"MANIFEST INDEX SHA256 MISMATCH: {rel}")

    if mode == "immutable_source_blob":
        commit = entry.get("source_commit")
        source_path = entry.get("source_path")
        if not isinstance(commit, str) or not isinstance(source_path, str):
            return errors + [f"MANIFEST INDEX SOURCE BINDING INVALID: {rel}"]
        if not all(isinstance(entry.get(key), str) and entry.get(key) for key in (
            "source_commit", "source_tree", "source_path", "git_blob", "sha256"
        )) or not isinstance(entry.get("bytes"), int):
            return errors + [f"MANIFEST INDEX SOURCE RECORD INVALID: {rel}"]
        tree = git_output(root, "show", "-s", "--format=%T", commit)
        if tree is None or tree.decode("ascii").strip() != entry.get("source_tree"):
            errors.append(f"MANIFEST INDEX SOURCE TREE MISMATCH: {rel}")
        blob_oid = git_output(root, "rev-parse", f"{commit}:{source_path}")
        if blob_oid is None or blob_oid.decode("ascii").strip() != entry.get("git_blob"):
            errors.append(f"MANIFEST INDEX SOURCE BLOB OID MISMATCH: {rel}")
        source = git_output(root, "cat-file", "blob", f"{commit}:{source_path}")
        if source is None or source != current:
            errors.append(f"MANIFEST INDEX IMMUTABLE BLOB MISMATCH: {rel}")
    elif mode == "current_aggregate":
        exclusions = entry.get("exclusions", [])
        if not isinstance(exclusions, list) or not all(isinstance(item, str) for item in exclusions):
            errors.append(f"MANIFEST INDEX AGGREGATE EXCLUSIONS INVALID: {rel}")
        else:
            try:
                actual = json.loads(current.decode("utf-8"))
            except Exception as exc:
                errors.append(f"MANIFEST INDEX AGGREGATE JSON INVALID {rel}: {exc}")
            else:
                expected = build_aggregate_manifest(Path(rel), root=root, exclusions=tuple(exclusions))
                if actual != expected:
                    errors.append(f"MANIFEST INDEX AGGREGATE STALE: {rel}")
    elif mode != "current_exact_file":
        errors.append(f"MANIFEST INDEX MODE UNKNOWN: {mode}")
    return errors


def validate_manifest_index(index_path: Path = DEFAULT_INDEX, root: Path = ROOT) -> list[str]:
    entries, errors = load_manifest_index(index_path, root)
    for entry in entries:
        errors.extend(validate_manifest_entry(entry, root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Verify output without rewriting it.")
    parser.add_argument("--check-index", action="store_true", help="Verify immutable and current indexed manifests.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--aggregate", action="store_true", help="Write a separately named raw-byte aggregate manifest.")
    parser.add_argument("--exclude", action="append", default=[], help="Repository-relative aggregate exclusion.")
    args = parser.parse_args()
    if args.check_index:
        errors = validate_manifest_index(args.index)
        if errors:
            print("ERROR: manifest index validation failed")
            for error in errors:
                print(f"- {error}")
            return 1
        entries, _ = load_manifest_index(args.index)
        print(f"Manifest index valid: {args.index} ({len(entries)} immutable/current bindings)")
        return 0
    output = args.output if args.output.is_absolute() else ROOT / args.output
    entries, index_errors = load_manifest_index(args.index)
    indexed = next((entry for entry in entries if entry.get("path") == args.output.as_posix()), None)
    if args.check and not index_errors and indexed is not None:
        errors = validate_manifest_entry(indexed)
        if errors:
            print(f"ERROR: indexed manifest invalid: {output}")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"Immutable/indexed manifest valid: {output}")
        return 0
    manifest = (
        build_aggregate_manifest(args.output, exclusions=tuple(args.exclude))
        if args.aggregate
        else build_manifest(args.output)
    )
    rendered = json.dumps(manifest, indent=2) + "\n"
    if args.check:
        try:
            actual = output.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"ERROR: manifest snapshot missing: {output}")
            return 1
        if actual != rendered:
            print(f"ERROR: manifest snapshot stale: {output}")
            return 1
        print(f"Manifest snapshot current: {output} ({manifest['count']} records)")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {manifest['count']} records to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
