#!/usr/bin/env bash
set -euo pipefail
python3 tools/generate_document_manifest.py
python3 tools/validate_repository.py
python3 -m unittest discover -s tests/governance -p 'test_*.py'
echo 'bOPEN bootstrap checks passed.'
