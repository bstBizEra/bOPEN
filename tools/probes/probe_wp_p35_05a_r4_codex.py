#!/usr/bin/env python3
"""Candidate-bound independent WP-P35-05a R4 verifier probe."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from probe_wp_p35_05a_r3_codex import main


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = "119f2d8cf678624c055c8d1be48c770b3936de11"
TREE = "210c6f4be07837f01c6e866b490aca730afc529f"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def bind_candidate() -> None:
    if git("rev-parse", f"{CANDIDATE}^{{commit}}") != CANDIDATE:
        raise RuntimeError("R4 candidate commit does not resolve exactly")
    if git("rev-parse", f"{CANDIDATE}^{{tree}}") != TREE:
        raise RuntimeError("R4 candidate tree does not match the maker submission")

    # The shared branch has later governance-only commits. Refuse to execute if any
    # implementation, contract, or test byte differs from the detached candidate.
    result = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            CANDIDATE,
            "--",
            "services",
            "packages",
            "contracts",
            "tests",
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("live executable/test inputs differ from the R4 candidate")


if __name__ == "__main__":
    bind_candidate()
    os.environ["BOPEN_WP_P35_05A_R4"] = "1"
    raise SystemExit(main())
