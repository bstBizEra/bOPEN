# Runbook — Bootstrap Validation

## Procedure

1. Run `python tools/validate_repository.py`.
2. Run `python -m unittest discover -s tests/governance -p 'test_*.py'`.
3. Review generated output and resolve failures.
4. Store CI/run reference in the applicable evidence record.
