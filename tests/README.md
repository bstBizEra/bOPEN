# tests

Governance, contract, integration, isolation and end-to-end tests.

- `governance/`: repository bootstrap and clean-room invariants.
- `contracts/`: machine-readable contract validation behavior.

Nested test directories include package markers so `python -m unittest discover -s tests -p "test_*.py"` can discover all suites.
