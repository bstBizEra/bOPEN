#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:?Provide upstream clone path}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIN_CONTRACT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)/research/sources/boxyhq-upstream-pin.json"
readarray -t CONTRACT < <(python3 - "$PIN_CONTRACT" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding='utf-8'))
for key in ('repository_url','commit','license_sha256','lockfile','lock_sha256'): print(d[key])
PY
)
REPO_URL="${CONTRACT[0]}"; EXPECTED="${CONTRACT[1]}"; EXPECTED_LICENSE="${CONTRACT[2]}"
LOCKFILE="${CONTRACT[3]}"; EXPECTED_LOCK="${CONTRACT[4]}"
[ "$(git -C "$TARGET" rev-parse HEAD)" = "$EXPECTED" ] || { echo "Pin mismatch" >&2; exit 1; }
[ "$(git -C "$TARGET" remote get-url origin)" = "$REPO_URL" ] || { echo "Origin mismatch" >&2; exit 1; }
! git -C "$TARGET" symbolic-ref -q HEAD >/dev/null || { echo "Checkout must be detached" >&2; exit 1; }
[ -z "$(git -C "$TARGET" status --porcelain)" ] || { echo "Working tree modified" >&2; exit 1; }
[ "$(sha256sum "$TARGET/LICENSE" | awk '{print $1}')" = "$EXPECTED_LICENSE" ] || { echo "License checksum mismatch" >&2; exit 1; }
[ -f "$TARGET/$LOCKFILE" ] || { echo "Required lockfile missing" >&2; exit 1; }
[ "$(sha256sum "$TARGET/$LOCKFILE" | awk '{print $1}')" = "$EXPECTED_LOCK" ] || { echo "Lock checksum mismatch" >&2; exit 1; }
echo "PASS: origin, detached pin, clean tree, license, and lockfile verified"
