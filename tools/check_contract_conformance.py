#!/usr/bin/env python3
"""
bOPEN contract conformance coverage check.

Enforces BOPEN-GOV-EBIV-001 R2 and R4 for frozen contracts.

Phase 3 shipped a `RateLimitDecision` that violated its own frozen schema on five fields while
the suite reported 169 of 169 green. The contract suite loaded the schema *document* and asserted
properties of it; nothing ever validated an object the code produces. A schema that no instance
is checked against is a document, not a contract, and the difference is invisible in a pass count.

This tool measures which schemas are actually exercised. It does not guess.

--------------------------------------------------------------------------------------------
How it measures
--------------------------------------------------------------------------------------------
Static analysis cannot answer this reliably: `jsonschema.validate(schema=self.decision_schema)`
gives no syntactic clue which file `self.decision_schema` came from, and a heuristic that assumes
"this test file opened that schema, so it must validate against it" would credit exactly the
pattern that failed in Phase 3 — opening a schema and never using it.

So the tool observes instead. It wraps `jsonschema.validate`, runs the canonical suite in
process, and records the content fingerprint of every schema actually passed to it. A schema on
disk is covered if and only if its fingerprint appears. Comparison is on canonical content rather
than on `$id`, so it works for schemas that declare no `$id` and cannot be fooled by a filename.

--------------------------------------------------------------------------------------------
Why a baseline rather than a hard failure
--------------------------------------------------------------------------------------------
Thirteen of sixteen schemas are uncovered today. Failing the build on all of them would
immediately be silenced, which is the fate of every check that starts out red.

`contract-conformance-baseline.json` records the currently uncovered set with a reason for each.
The tool fails when coverage *regresses* — a schema that was covered stops being covered, or a
new schema appears with no entry. Removing an entry from the baseline is how a debt is paid, and
the file is a standing, reviewable statement of what is not yet contract-tested.

Usage:
    python tools/check_contract_conformance.py
    python tools/check_contract_conformance.py --report      # coverage table, exit 0 regardless
    python tools/check_contract_conformance.py --update-baseline

Exit codes:
    0  no regression against the baseline
    1  a schema lost coverage, or a schema has neither coverage nor a baseline entry
    2  the check could not run
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "schemas"
BASELINE = ROOT / "contracts" / "contract-conformance-baseline.json"

# The governance category is deliberately excluded, and the reason is structural rather than a
# preference. `tests/governance/test_governance_validators.py` invokes this tool as a subprocess
# so that the check runs inside the canonical suite. If this tool then discovered that category,
# it would run the governance test, which would invoke this tool, which would discover the
# category again — unbounded recursion, each level spawning a process.
#
# Excluding it is safe for the measurement: governance tests assert repository and validator
# properties, not message shapes, so none of them validates an instance against a contract
# schema. If one ever does, its schema would be reported as uncovered here — a false negative
# that fails toward recording debt rather than toward hiding it, which is the correct direction
# for this check to be wrong in.
TEST_DIRS = ("unit", "integration", "contracts", "isolation")


def fingerprint(schema: object) -> str:
    """Content hash of a schema, insensitive to key order and whitespace."""
    return hashlib.sha256(
        json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


# Keywords that let a schema reject something. A document with none of them at the top level
# accepts every instance, including `42`, `"a string"` and `null`.
CONSTRAINING_KEYWORDS = frozenset({
    "type", "properties", "required", "items", "prefixItems", "enum", "const",
    "$ref", "allOf", "anyOf", "oneOf", "not", "patternProperties",
    "additionalProperties", "minimum", "maximum", "pattern", "format",
    "minItems", "maxItems", "minLength", "maxLength", "uniqueItems",
})


def is_constraining(schema: object) -> bool:
    """Can this document reject anything at all?

    This exists because of a hole a reviewer found in this tool. Coverage was measured purely by
    observing calls to `jsonschema.validate`, so *any* call counted — including one against
    `membership-transition-matrix.json`, which declares no `type` and no `properties` and
    therefore accepts `{}`, `42`, `"a string"` and `null` alike. A test making that call
    reported green while asserting nothing, and this tool then reported the schema as covered
    and invited its debt entry to be struck.

    That is not a hypothetical: it happened while the Phase 1/2 conformance tests were being
    written, and was caught only because the author noticed the coverage number move for the
    wrong reason.

    A metric that can be satisfied by a vacuous call measures compliance with itself. Schemas
    that cannot constrain are now reported in their own category and can be neither covered nor
    counted as debt, because neither word means anything for them.
    """
    return isinstance(schema, dict) and bool(CONSTRAINING_KEYWORDS & set(schema))


def load_schemas() -> dict[str, dict]:
    """Return {filename: parsed schema} for every schema on disk."""
    out: dict[str, dict] = {}
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        try:
            out[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"ERROR: {path.name} is not valid JSON: {exc}", file=sys.stderr)
            raise SystemExit(2)
    return out


def observe_validated_fingerprints() -> tuple[set[str], bool, int]:
    """Run the canonical suite with `jsonschema.validate` wrapped, recording what it sees.

    Returns (fingerprints, suite_was_green, skipped_count).

    The skip count matters more than it looks. Coverage measured by observation is only as
    complete as the run that produced it: a test skipped because BOPEN_DATABASE_URL is unset
    validates nothing, so its schema reads as uncovered. That produced a false regression the
    first time this tool ran in an environment without a database — `tenant-context.json` is
    covered only by a database-gated test, and its coverage vanished with the database.

    A coverage number that changes with the environment is not a measurement, and a check that
    reports regression on that basis would be training its readers to ignore it. The caller
    therefore refuses to judge when anything was skipped, rather than judging on partial data.
    """
    try:
        import jsonschema
    except ImportError:
        print(
            "ERROR: jsonschema is not installed.\n"
            "       python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        raise SystemExit(2)

    seen: set[str] = set()
    original_validate = jsonschema.validate

    def recording_validate(instance, schema, *args, **kwargs):
        try:
            seen.add(fingerprint(schema))
        except (TypeError, ValueError):
            # A schema that is not JSON-serialisable cannot be matched to a file anyway.
            pass
        return original_validate(instance, schema, *args, **kwargs)

    jsonschema.validate = recording_validate

    for sub in ("packages/kernel-core/python", "services/platform-kernel/python", "sdk/python", "."):
        candidate = str(ROOT / sub)
        if candidate not in sys.path:
            sys.path.insert(0, candidate)

    try:
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        for name in TEST_DIRS:
            directory = ROOT / "tests" / name
            if directory.is_dir():
                suite.addTests(loader.discover(start_dir=str(directory)))

        buffer = io.StringIO()
        with redirect_stdout(buffer), redirect_stderr(buffer):
            result = unittest.TextTestRunner(stream=buffer, verbosity=0).run(suite)

        if not result.wasSuccessful():
            # A tool that reports "suite: RED" without saying why sends the reader back to
            # reproduce it by hand. Print enough to act on: the first few failing tests and the
            # last line of each traceback, which is where the assertion lives.
            print("\n  the in-process suite run was not green:")
            for test, traceback_text in (result.failures + result.errors)[:5]:
                last = traceback_text.strip().splitlines()[-1] if traceback_text.strip() else ""
                print(f"    {str(test)[:100]}")
                print(f"      {last[:160]}")
            remaining = len(result.failures) + len(result.errors) - 5
            if remaining > 0:
                print(f"    ... and {remaining} more")

        return seen, result.wasSuccessful(), len(result.skipped)
    finally:
        jsonschema.validate = original_validate


def load_baseline() -> dict:
    if not BASELINE.is_file():
        return {"uncovered": {}}
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true",
                        help="print the coverage table and exit 0 regardless")
    parser.add_argument("--update-baseline", action="store_true",
                        help="rewrite the baseline from observed coverage (review the diff)")
    args = parser.parse_args()

    if not SCHEMA_DIR.is_dir():
        print(f"ERROR: no schema directory at {SCHEMA_DIR}", file=sys.stderr)
        return 2

    schemas = load_schemas()
    if not schemas:
        print(f"ERROR: no schemas found in {SCHEMA_DIR}", file=sys.stderr)
        return 2

    validated, suite_green, skipped = observe_validated_fingerprints()

    non_constraining = {name for name, doc in schemas.items() if not is_constraining(doc)}
    constraining = {name for name in schemas if name not in non_constraining}

    covered = {name for name in constraining if fingerprint(schemas[name]) in validated}
    uncovered = sorted(constraining - covered)

    print("bOPEN contract conformance coverage (EBIV R2/R4)")
    print(f"- schemas on disk:          {len(schemas)}")
    print(f"- constrain nothing:        {len(non_constraining)}")
    print(f"- validated by an instance: {len(covered)} of {len(constraining)} that can constrain")
    print(f"- uncovered:                {len(uncovered)}")
    print(f"- canonical suite:        {'green' if suite_green else 'RED'}")
    if skipped:
        print(f"- tests skipped:          {skipped}")

    if non_constraining:
        print("\n  schemas that cannot reject any instance — neither covered nor debt:")
        for name in sorted(non_constraining):
            print(f"    {name}")
        print("    Validating against these proves nothing, so neither word applies. They are")
        print("    data documents rather than contracts, or contracts never finished.")

    if args.report or args.update_baseline:
        print("\n  schema                                    instance-validated")
        for name in sorted(schemas):
            if name in non_constraining:
                mark = "n/a — constrains nothing"
            else:
                mark = "yes" if name in covered else "NO"
            print(f"  {name:<42} {mark}")

    if args.update_baseline:
        baseline = {
            "purpose": (
                "Schemas with no test validating a real instance against them. This is recorded "
                "debt, not an exemption. tools/check_contract_conformance.py fails when a schema "
                "loses coverage or appears with no entry here; removing an entry is how the debt "
                "is paid."
            ),
            "uncovered": {
                name: load_baseline().get("uncovered", {}).get(
                    name, "no reason recorded — add one"
                )
                for name in uncovered
            },
        }
        BASELINE.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
        print(f"\nbaseline written with {len(uncovered)} uncovered schema(s). Review the diff.")
        return 0

    if skipped and not args.report:
        # Neither pass nor fail: the measurement is incomplete, so any verdict from it would be
        # about the environment rather than about the contracts. Exit 2 is "could not run",
        # which is what BOPEN-GOV-EBIV-001 R5 asks of a check in this position — reporting
        # success here would make an unconfigured environment indistinguishable from a covered
        # one, which is the exact confusion this repository exists to remove.
        print(
            f"\nCANNOT RUN — {skipped} test(s) were skipped, so coverage was measured on a "
            f"partial run.\n"
            "Schemas covered only by skipped tests read as uncovered, which would report a\n"
            "regression that is really a missing environment. Configure it and re-run:\n"
            "    set -a; . ./.env.local; set +a\n"
            "    python tools/db_bootstrap.py --apply\n"
            "Use --report to see the coverage table anyway, without a verdict."
        )
        return 2

    baseline = load_baseline()
    allowed = set(baseline.get("uncovered", {}))

    regressions = sorted(set(uncovered) - allowed)
    paid = sorted(allowed - set(uncovered))
    stale = sorted(allowed - set(schemas))

    if paid:
        print(f"\n  debt paid since the baseline: {', '.join(paid)}")
        print("  Remove these from contract-conformance-baseline.json to lock the gain in.")

    if stale:
        print(f"\n  baseline names schemas that no longer exist: {', '.join(stale)}")

    if args.report:
        return 0

    if regressions:
        print(f"\nFAIL — {len(regressions)} schema(s) with neither coverage nor a baseline entry:\n")
        for name in regressions:
            print(f"  {name}")
        print(
            "\nEither add a test validating a real instance against it, or record it in\n"
            "contracts/contract-conformance-baseline.json with a reason. A frozen schema that\n"
            "no instance is checked against is a document, not a contract."
        )
        return 1

    print("\nPASS — no schema lost coverage and none is unaccounted for.")
    if uncovered:
        print(
            f"        {len(uncovered)} schema(s) remain uncovered and are recorded as debt "
            f"in contracts/contract-conformance-baseline.json."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
