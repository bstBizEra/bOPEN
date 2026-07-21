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
MANIFEST_DIRECTORY = Path("docs/manifests")
VERSIONED_MANIFEST_NAME = re.compile(r"^[A-Z0-9][A-Z0-9._-]*-MANIFEST\.json$")
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
    excluded = set(exclusions) | {output_rel, DEFAULT_INDEX.as_posix()}
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


def load_manifest_index_bytes(
    raw: bytes,
    *,
    root: Path = ROOT,
    label: str = "MANIFEST INDEX",
) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    try:
        text = raw.decode("utf-8")
    except Exception as exc:
        return [], [f"{label} INVALID: {exc}"]
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        errors.append(f"{label} MUST USE UTF-8 WITHOUT BOM AND LF")
    if raw and not raw.endswith(b"\n"):
        errors.append(f"{label} MUST END WITH LF")
    entries: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            errors.append(f"{label} LINE {number} MUST NOT BE BLANK")
            continue
        try:
            entry = json.loads(line)
        except Exception as exc:
            errors.append(f"{label} LINE {number} INVALID: {exc}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{label} LINE {number} MUST BE OBJECT")
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


def load_manifest_index(index_path: Path, root: Path = ROOT) -> tuple[list[dict], list[str]]:
    path = index_path if index_path.is_absolute() else root / index_path
    try:
        raw = path.read_bytes()
    except Exception as exc:
        return [], [f"MANIFEST INDEX INVALID: {exc}"]
    return load_manifest_index_bytes(raw, root=root)


def _validate_index_successor(prior: bytes, successor: bytes, label: str, root: Path) -> list[str]:
    errors: list[str] = []
    if len(successor) <= len(prior):
        errors.append(f"MANIFEST INDEX HISTORY TRUNCATED OR NOT APPENDED: {label}")
    elif not successor.startswith(prior):
        errors.append(f"MANIFEST INDEX HISTORY PREFIX MUTATED: {label}")
    else:
        appended = successor[len(prior):]
        if not appended or appended.startswith(b"\n"):
            errors.append(f"MANIFEST INDEX HISTORY APPEND MUST START WITH JSON: {label}")
        try:
            appended_text = appended.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"MANIFEST INDEX HISTORY APPEND INVALID UTF-8 {label}: {exc}")
        else:
            if b"\r" in appended or not appended.endswith(b"\n"):
                errors.append(f"MANIFEST INDEX HISTORY APPEND MUST USE LF: {label}")
            for number, line in enumerate(appended_text.splitlines(), start=1):
                try:
                    value = json.loads(line)
                except Exception as exc:
                    errors.append(f"MANIFEST INDEX HISTORY APPEND LINE {number} INVALID {label}: {exc}")
                else:
                    if not isinstance(value, dict):
                        errors.append(f"MANIFEST INDEX HISTORY APPEND LINE {number} MUST BE OBJECT: {label}")
    _, successor_errors = load_manifest_index_bytes(
        successor, root=root, label=f"MANIFEST INDEX HISTORY {label}"
    )
    errors.extend(successor_errors)
    return errors


def validate_manifest_index_history(
    index_path: Path = DEFAULT_INDEX,
    root: Path = ROOT,
) -> list[str]:
    """Require every committed/current index version to be a raw-byte append."""

    try:
        rel = (
            index_path.relative_to(root).as_posix()
            if index_path.is_absolute()
            else index_path.as_posix()
        )
    except ValueError:
        return ["MANIFEST INDEX HISTORY PATH OUTSIDE REPOSITORY"]
    history = git_output(root, "log", "--format=%H", "--reverse", "--", rel)
    if history is None:
        return ["MANIFEST INDEX HISTORY UNAVAILABLE"]
    commits = [line.decode("ascii") for line in history.splitlines() if line]
    if not commits:
        return ["MANIFEST INDEX HISTORY GENESIS MISSING"]
    errors: list[str] = []
    genesis = commits[0]
    if git_output(root, "rev-parse", f"{genesis}^:{rel}") is not None:
        errors.append("MANIFEST INDEX HISTORY GENESIS INVALID")
    blobs: list[tuple[str, bytes]] = []
    for commit in commits:
        blob = git_output(root, "cat-file", "blob", f"{commit}:{rel}")
        if blob is None:
            errors.append(f"MANIFEST INDEX HISTORY BLOB MISSING: {commit}")
            continue
        _, blob_errors = load_manifest_index_bytes(
            blob, root=root, label=f"MANIFEST INDEX HISTORY {commit}"
        )
        errors.extend(blob_errors)
        blobs.append((commit, blob))
    for (prior_commit, prior), (commit, successor) in zip(blobs, blobs[1:]):
        errors.extend(_validate_index_successor(prior, successor, f"{prior_commit}..{commit}", root))
    try:
        current = (root / rel).read_bytes()
    except OSError as exc:
        errors.append(f"MANIFEST INDEX HISTORY CURRENT FILE UNAVAILABLE: {exc}")
    else:
        if blobs and current != blobs[-1][1]:
            errors.extend(_validate_index_successor(blobs[-1][1], current, "HEAD..WORKTREE", root))
    return sorted(set(errors))


def validate_new_snapshot_output(
    output: Path,
    *,
    index_path: Path = DEFAULT_INDEX,
    root: Path = ROOT,
) -> list[str]:
    """Refuse canonical, historical, indexed, existing or unversioned writes."""

    errors: list[str] = []
    try:
        absolute = output if output.is_absolute() else root / output
        rel = absolute.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return ["MANIFEST WRITE TARGET OUTSIDE REPOSITORY"]
    candidate = Path(rel)
    if output.is_absolute() or ".." in output.parts or output.as_posix() != rel:
        errors.append("MANIFEST WRITE TARGET MUST BE NORMALIZED REPOSITORY-RELATIVE PATH")
    if candidate.parent != MANIFEST_DIRECTORY:
        errors.append("MANIFEST WRITE TARGET MUST BE DIRECTLY UNDER docs/manifests")
    if not VERSIONED_MANIFEST_NAME.fullmatch(candidate.name):
        errors.append("MANIFEST WRITE TARGET MUST HAVE VERSIONED *-MANIFEST.json NAME")
    if candidate == DEFAULT_OUTPUT or candidate == DEFAULT_INDEX:
        errors.append("MANIFEST WRITE TARGET IS PROTECTED")
    target = root / candidate
    if target.exists() or target.is_symlink():
        errors.append("MANIFEST WRITE TARGET MUST NOT ALREADY EXIST")
    if target.parent.is_symlink():
        errors.append("MANIFEST WRITE TARGET DIRECTORY MUST NOT BE SYMLINK")
    entries, index_errors = load_manifest_index(index_path, root)
    if index_errors:
        errors.append("MANIFEST WRITE REFUSED BECAUSE INDEX IS INVALID")
    if any(entry.get("path") == rel for entry in entries):
        errors.append("MANIFEST WRITE TARGET IS ALREADY INDEXED")
    return sorted(set(errors))


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
                expected_keys = {
                    "manifest_id", "version", "status", "lifecycle", "generated",
                    "exclusions", "count", "files",
                }
                if not isinstance(actual, dict) or set(actual) != expected_keys:
                    errors.append(f"MANIFEST INDEX AGGREGATE SHAPE INVALID: {rel}")
                else:
                    files = actual.get("files")
                    paths = [record.get("path") for record in files] if isinstance(files, list) else []
                    if actual.get("count") != len(paths) or paths != sorted(set(paths)):
                        errors.append(f"MANIFEST INDEX AGGREGATE FILE ORDER/COUNT INVALID: {rel}")
                    if actual.get("exclusions") != sorted(set(exclusions) | {rel}):
                        errors.append(f"MANIFEST INDEX AGGREGATE EXCLUSIONS MISMATCH: {rel}")
                    for record in files if isinstance(files, list) else []:
                        if set(record) != {"path", "sha256", "bytes"}:
                            errors.append(f"MANIFEST INDEX AGGREGATE RECORD SHAPE INVALID: {rel}")
                            break
                        digest = record.get("sha256")
                        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                            errors.append(f"MANIFEST INDEX AGGREGATE RECORD DIGEST INVALID: {rel}")
                            break
                        if not isinstance(record.get("bytes"), int) or record["bytes"] < 0:
                            errors.append(f"MANIFEST INDEX AGGREGATE RECORD BYTES INVALID: {rel}")
                            break
    elif mode != "current_exact_file":
        errors.append(f"MANIFEST INDEX MODE UNKNOWN: {mode}")
    return errors


def validate_manifest_index(index_path: Path = DEFAULT_INDEX, root: Path = ROOT) -> list[str]:
    entries, errors = load_manifest_index(index_path, root)
    errors.extend(validate_manifest_index_history(index_path, root))
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
        errors = validate_manifest_index(args.index, ROOT)
        if errors:
            print("ERROR: manifest index validation failed")
            for error in errors:
                print(f"- {error}")
            return 1
        entries, _ = load_manifest_index(args.index, ROOT)
        print(f"Manifest index valid: {args.index} ({len(entries)} immutable/current bindings)")
        return 0
    output = args.output if args.output.is_absolute() else ROOT / args.output
    entries, index_errors = load_manifest_index(args.index, ROOT)
    indexed = next((entry for entry in entries if entry.get("path") == args.output.as_posix()), None)
    if args.check and not index_errors and indexed is not None:
        errors = validate_manifest_entry(indexed, ROOT)
        if errors:
            print(f"ERROR: indexed manifest invalid: {output}")
            for error in errors:
                print(f"- {error}")
            return 1
        print(f"Immutable/indexed manifest valid: {output}")
        return 0
    if not args.check:
        if not args.aggregate:
            print("ERROR: manifest writes require explicit --aggregate new-snapshot mode")
            return 1
        write_errors = validate_new_snapshot_output(args.output, index_path=args.index, root=ROOT)
        if write_errors:
            print("ERROR: immutable manifest write refused")
            for error in write_errors:
                print(f"- {error}")
            return 1
    manifest = (
        build_aggregate_manifest(args.output, root=ROOT, exclusions=tuple(args.exclude))
        if args.aggregate
        else build_manifest(args.output, ROOT)
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
