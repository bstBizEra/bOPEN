#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$HOME/bopen-research}"
REPO_URL="https://github.com/boxyhq/saas-starter-kit.git"
PIN="abc9b686823cbfb4973c79bc36fea37a3244be6c"
TARGET="$ROOT/01-boxyhq/upstream"
META="$ROOT/01-boxyhq/clone-metadata.txt"

mkdir -p "$(dirname "$TARGET")"
if [ -e "$TARGET" ]; then
  echo "Target already exists: $TARGET" >&2
  exit 2
fi

git clone --no-checkout "$REPO_URL" "$TARGET"
cd "$TARGET"
git fetch --depth 1 origin "$PIN"
git checkout --detach "$PIN"
ACTUAL="$(git rev-parse HEAD)"
[ "$ACTUAL" = "$PIN" ] || { echo "Pin mismatch" >&2; exit 3; }

{
  echo "repository=$REPO_URL"
  echo "pinned_commit=$PIN"
  echo "actual_commit=$ACTUAL"
  echo "cloned_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "git_version=$(git --version)"
  if command -v sha256sum >/dev/null; then
    echo "license_sha256=$(sha256sum LICENSE | awk '{print $1}')"
    [ -f package-lock.json ] && echo "lock_sha256=$(sha256sum package-lock.json | awk '{print $1}')"
  fi
} > "$META"

echo "Pinned study clone created at $TARGET"
echo "Metadata written to $META"
