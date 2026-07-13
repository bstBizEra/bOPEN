$ErrorActionPreference = "Stop"
python tools/generate_document_manifest.py
python tools/validate_repository.py
python -m unittest discover -s tests/governance -p "test_*.py"
Write-Host "bOPEN bootstrap checks passed."
