#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:?Provide upstream clone path}"
EXPECTED="abc9b686823cbfb4973c79bc36fea37a3244be6c"
cd "$TARGET"
ACTUAL="$(git rev-parse HEAD)"
if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "FAIL: expected $EXPECTED, got $ACTUAL" >&2
  exit 1
fi
git diff --quiet || { echo "FAIL: working tree modified" >&2; exit 2; }
echo "PASS: upstream pin and clean tree verified"
