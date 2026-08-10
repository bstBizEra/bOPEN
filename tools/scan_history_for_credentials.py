"""Scan every blob reachable from HEAD for credential material, before any decision to publish.

Reports counts at each stage so a zero can be distinguished from a broken pipeline — an earlier
attempt reported "0 blobs" because `git rev-list --objects` emits "<sha> <path>" and the reader
consumed the whole line as an object name.
"""
import pathlib
import re
import subprocess
import sys
from collections import defaultdict

ROOT = str(pathlib.Path(__file__).resolve().parents[1])


def git(*args, binary=False):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True,
                          check=True).stdout if binary else subprocess.run(
        ["git", "-C", ROOT, *args], capture_output=True, check=True, text=True,
        errors="replace").stdout


# High-signal patterns. Each is a credential SHAPE, not a keyword, so that a repository which
# discusses secrets in prose does not drown the real findings.
PATTERNS = [
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    ("slack_token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("stripe_key", re.compile(r"\b(?:sk|rk)_live_[0-9a-zA-Z]{20,}\b")),
    ("jwt_like", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
    ("url_with_password", re.compile(r"\b[a-z][a-z0-9+.\-]*://[^\s:@/]+:[^\s:@/]{3,}@[^\s/]+")),
    ("assigned_secret", re.compile(
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|client[_-]?secret)\b"
        r"\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']")),
]

# Values that are obviously not live credentials. Kept narrow and explicit; anything not matched
# here is reported for a human to read rather than silently dropped.
PLACEHOLDER = re.compile(
    r"(?i)^(?:\$\{|<|\{\{|x{4,}|\*{4,}|\.{3,}|changeme|placeholder|example|sample|redacted|"
    r"your[_-]|test[_-]?only|dummy|fake|none|null|todo|tbd|insert|replace|set[_-]?me|"
    r"password|secret|api[_-]?key|token)")

objects = git("rev-list", "--objects", "HEAD").splitlines()
paths = {}
for line in objects:
    sha, _, path = line.partition(" ")
    if path:
        paths.setdefault(sha, path)

print(f"objects reachable from HEAD : {len(objects)}")
print(f"of those, named (blob/tree)  : {len(paths)}")

types = subprocess.run(["git", "-C", ROOT, "cat-file", "--batch-check"],
                       input="\n".join(paths), capture_output=True, text=True).stdout
blobs = []
for line in types.splitlines():
    parts = line.split()
    if len(parts) == 3 and parts[1] == "blob":
        blobs.append((parts[0], int(parts[2])))
print(f"blobs                        : {len(blobs)}")
if not blobs:
    sys.exit("ABORT: zero blobs is not a credible result; the reader is broken, not the repository")

total = sum(s for _, s in blobs)
print(f"total blob bytes             : {total:,}")

SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".woff", ".woff2", ".ttf")
scanned = skipped = 0
findings = defaultdict(list)

proc = subprocess.Popen(["git", "-C", ROOT, "cat-file", "--batch"],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE)
for sha, size in blobs:
    path = paths.get(sha, "")
    if path.lower().endswith(SKIP_EXT) or size > 2_000_000:
        skipped += 1
        continue
    proc.stdin.write((sha + "\n").encode())
    proc.stdin.flush()
    header = proc.stdout.readline().decode(errors="replace").split()
    n = int(header[2])
    data = proc.stdout.read(n)
    proc.stdout.read(1)
    scanned += 1
    text = data.decode("utf-8", errors="replace")
    for name, rx in PATTERNS:
        for m in rx.finditer(text):
            value = m.group(1) if m.groups() else m.group(0)
            if name == "assigned_secret" and PLACEHOLDER.match(value):
                continue
            line_no = text.count("\n", 0, m.start()) + 1
            findings[name].append((path, line_no, m.group(0)[:110]))
proc.stdin.close()

print(f"blobs scanned                : {scanned}")
print(f"blobs skipped (binary/large) : {skipped}")
print()
if not findings:
    print("NO CREDENTIAL-SHAPED MATCH IN ANY BLOB REACHABLE FROM HEAD")
for name, hits in sorted(findings.items(), key=lambda kv: -len(kv[1])):
    print(f"### {name} — {len(hits)} match(es)")
    seen = set()
    for path, line_no, snippet in hits:
        key = (path, snippet)
        if key in seen:
            continue
        seen.add(key)
        print(f"    {path}:{line_no}")
        print(f"        {snippet}")
    print()
