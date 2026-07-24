"""Regression for MANIFEST-P0-01: GOV-P0-02 document-manifest --check must be
date-invariant (reproducible across UTC days) yet still content-sensitive.

Before the fix, `generated` was stamped from wall-clock UTC, so a byte-frozen
candidate went stale at every UTC-midnight rollover with zero content change,
breaking exact-SHA reproducibility.
"""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("gen_dm", ROOT / "tools" / "generate_document_manifest.py")
gen_dm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_dm)


def _run_check(output: Path) -> int:
    saved = sys.argv
    sys.argv = ["generate_document_manifest.py", "--output", str(output), "--check"]
    try:
        return gen_dm.main()
    finally:
        sys.argv = saved


class DocumentManifestReproducibilityTests(unittest.TestCase):
    def test_check_is_date_invariant(self):
        """A stale `generated` date alone must NOT fail --check."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"  # absolute path -> excluded from its own scan
            manifest = gen_dm.build_manifest(out)
            manifest["generated"] = "1970-01-01"  # deliberately far-past date
            out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
            self.assertEqual(_run_check(out), 0, "manifest check must be date-invariant")

    def test_check_still_fails_on_content_drift(self):
        """Genuine content drift must still fail --check even with a stale date."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            manifest = gen_dm.build_manifest(out)
            manifest["generated"] = "1970-01-01"
            manifest["count"] = manifest["count"] + 1  # tamper
            out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
            self.assertEqual(_run_check(out), 1, "content drift must still fail the check")


if __name__ == "__main__":
    unittest.main()
