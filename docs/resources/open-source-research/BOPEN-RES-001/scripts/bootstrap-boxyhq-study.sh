#!/usr/bin/env bash
set -euo pipefail
[ "${BASH_VERSINFO[0]}" -ge 4 ] || { echo "Bash 4 or newer is required" >&2; exit 2; }
command -v sha256sum >/dev/null || { echo "sha256sum is required" >&2; exit 2; }

WORKSPACE_ROOT="${1:?Provide an approved external workspace root}"
OPERATOR_ID="${2:?Provide an operator ID}"
APPROVED_ROOT="${BOPEN_RESEARCH_APPROVED_ROOT:?Linux workflow disabled: set an approved absolute BOPEN_RESEARCH_APPROVED_ROOT}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
PIN_CONTRACT="$REPO_ROOT/research/sources/boxyhq-upstream-pin.json"

APPROVED_ROOT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$APPROVED_ROOT")"
WORKSPACE_ROOT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$WORKSPACE_ROOT")"
TARGET="$WORKSPACE_ROOT/01-boxyhq/upstream"
EVIDENCE="$WORKSPACE_ROOT/evidence"
case "$WORKSPACE_ROOT" in
  "$APPROVED_ROOT"|"$APPROVED_ROOT"/*) ;;
  *) echo "Workspace escapes BOPEN_RESEARCH_APPROVED_ROOT" >&2; exit 2 ;;
esac
case "$WORKSPACE_ROOT" in
  "$REPO_ROOT"/*) echo "Physical upstream clones must remain outside the bOPEN worktree" >&2; exit 2 ;;
esac
[ ! -e "$TARGET" ] || { echo "Target already exists: $TARGET" >&2; exit 2; }

readarray -t CONTRACT < <(python3 - "$PIN_CONTRACT" <<'PY'
import json, sys
d=json.load(open(sys.argv[1], encoding='utf-8'))
for key in ('source_id','repository_url','commit','default_branch','reference_release','license_observed','license_sha256','lockfile','lock_sha256','archived_observed'):
    print(d[key])
PY
)
SOURCE_ID="${CONTRACT[0]}"; REPO_URL="${CONTRACT[1]}"; PIN="${CONTRACT[2]}"
DEFAULT_BRANCH="${CONTRACT[3]}"; RELEASE="${CONTRACT[4]}"; LICENSE_NAME="${CONTRACT[5]}"
EXPECTED_LICENSE="${CONTRACT[6]}"; LOCKFILE="${CONTRACT[7]}"; EXPECTED_LOCK="${CONTRACT[8]}"
ARCHIVED_OBSERVED="${CONTRACT[9]}"

export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never
mkdir -p "$TARGET" "$EVIDENCE"
git -C "$TARGET" init
git -C "$TARGET" remote add origin "$REPO_URL"
git -C "$TARGET" -c credential.helper= fetch --depth 1 origin "$PIN"
git -C "$TARGET" checkout --detach FETCH_HEAD

ACTUAL="$(git -C "$TARGET" rev-parse HEAD)"
[ "$ACTUAL" = "$PIN" ] || { echo "Pin mismatch" >&2; exit 3; }
[ "$(git -C "$TARGET" remote get-url origin)" = "$REPO_URL" ] || { echo "Origin mismatch" >&2; exit 3; }
[ -z "$(git -C "$TARGET" status --porcelain)" ] || { echo "Dirty checkout" >&2; exit 3; }
LICENSE_HASH="$(sha256sum "$TARGET/LICENSE" | awk '{print $1}')"
[ "$LICENSE_HASH" = "$EXPECTED_LICENSE" ] || { echo "License checksum mismatch" >&2; exit 3; }
[ -f "$TARGET/$LOCKFILE" ] || { echo "Required lockfile missing" >&2; exit 3; }
LOCK_HASH="$(sha256sum "$TARGET/$LOCKFILE" | awk '{print $1}')"
[ "$LOCK_HASH" = "$EXPECTED_LOCK" ] || { echo "Lockfile checksum mismatch" >&2; exit 3; }

SOURCE_ID="$SOURCE_ID" REPO_URL="$REPO_URL" PIN="$PIN" DEFAULT_BRANCH="$DEFAULT_BRANCH" \
RELEASE="$RELEASE" LICENSE_NAME="$LICENSE_NAME" LICENSE_HASH="$LICENSE_HASH" LOCKFILE="$LOCKFILE" \
LOCK_HASH="$LOCK_HASH" OPERATOR_ID="$OPERATOR_ID" TARGET="$TARGET" ARCHIVED_OBSERVED="$ARCHIVED_OBSERVED" python3 - "$EVIDENCE/clone-metadata.json" <<'PY'
import json, os, platform, subprocess, sys
d={
  'schema_version':'1.0','source_id':os.environ['SOURCE_ID'],'repository':os.environ['REPO_URL'],
  'upstream_owner':'boxyhq','default_branch':os.environ['DEFAULT_BRANCH'],'pinned_commit':os.environ['PIN'],
  'actual_commit':os.environ['PIN'],'reference_release':os.environ['RELEASE'],
  'archived_observed':os.environ['ARCHIVED_OBSERVED'].lower() == 'true',
  'license':os.environ['LICENSE_NAME'],'license_sha256':os.environ['LICENSE_HASH'],'lockfile':os.environ['LOCKFILE'],
  'lock_sha256':os.environ['LOCK_HASH'],'local_patches':[],'operator_id':os.environ['OPERATOR_ID'],
  'captured_at_utc':subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'], text=True).strip(),
  'workstation':platform.node(),
  'os':platform.platform(),'git':subprocess.check_output(['git','--version'], text=True).strip(),
  'credential_prompting':'disabled','target':os.environ['TARGET']}
json.dump(d, open(sys.argv[1],'w',encoding='utf-8'), indent=2); open(sys.argv[1],'a').write('\n')
PY
echo "Pinned study clone created at $TARGET"
