#!/usr/bin/env python3
"""Dual-policy evaluation (`BOPEN-WP-GOV-AUTONOMY-001`).

A pull request that changes the classifier or the envelope must not be judged
solely by the logic it proposes — that is a policy ratifying itself
(`AGENTS.md` section 30.2: dual-policy evaluation, adopted from the SecB
Project Framework's `SECB-WP-FWK-012`). This script evaluates the same diff
twice:

    base verdict   the classifier and envelope as they exist on the base ref
    head verdict   the classifier and envelope as this PR would leave them

Auto-merge requires **both** to pass and **agree**. Divergence is not an
error in the change; it is a signal that the change alters judgement, which
belongs in shadow mode and a later governance epoch, never in the same event
that introduces it.

Contract:

    stdin        output of ``git diff --numstat <base>...<head>``
    BASE_REF     git ref for the base logic (CI passes the PR base SHA;
                 local runs must pass the trunk ref explicitly)

Exit codes:

    0  both verdicts pass and agree
    2  escalation required — either verdict escalates, or they diverge
    3  either verdict is REJECTED

Fail-closed: if the base logic cannot be recovered (missing script or
envelope on the base ref), the result escalates. A PR that deletes the base
classifier cannot thereby escape being compared against it.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

CLASSIFIER = "scripts/classify_authority_delta.py"
ENVELOPE = "config/delegation_envelope.json"

EXIT_OK = 0
EXIT_ESCALATE = 2
EXIT_REJECTED = 3


def git_show(ref: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], capture_output=True, timeout=60
    )
    return result.stdout if result.returncode == 0 else None


def run_classifier(script: Path, envelope: Path, numstat: str) -> tuple[int, str]:
    env = dict(os.environ)
    env["ENVELOPE"] = str(envelope)
    result = subprocess.run(
        [sys.executable, str(script)],
        input=numstat,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    output = (result.stdout + result.stderr).strip().splitlines()
    verdict_line = next((ln for ln in output if ln.startswith("VERDICT:")), "VERDICT: <none>")
    return result.returncode, verdict_line


def verdict_name(line: str) -> str:
    body = line.removeprefix("VERDICT:").strip()
    return body.split("—")[0].split(" - ")[0].strip()


def main() -> int:
    numstat = sys.stdin.read()
    base_ref = os.environ.get("BASE_REF", "origin/main")

    head_script = Path(CLASSIFIER)
    head_envelope = Path(ENVELOPE)
    if not head_script.exists() or not head_envelope.exists():
        print(
            "DUAL POLICY: ESCALATE — head classifier or envelope missing; "
            "a change may not remove the logic that judges it",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    base_script_blob = git_show(base_ref, CLASSIFIER)
    base_envelope_blob = git_show(base_ref, ENVELOPE)
    if base_script_blob is None or base_envelope_blob is None:
        print(
            f"DUAL POLICY: ESCALATE — base logic not recoverable at {base_ref} "
            "(first installation, or the base ref is unavailable). "
            "Genesis and bootstrap changes escalate by construction.",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    with tempfile.TemporaryDirectory() as tmp:
        base_script = Path(tmp) / "base_classifier.py"
        base_envelope = Path(tmp) / "base_envelope.json"
        base_script.write_bytes(base_script_blob)
        base_envelope.write_bytes(base_envelope_blob)

        base_code, base_line = run_classifier(base_script, base_envelope, numstat)
        head_code, head_line = run_classifier(head_script, head_envelope, numstat)

    print(f"base ({base_ref}): {base_line}")
    print(f"head (this PR):    {head_line}")

    if EXIT_REJECTED in (base_code, head_code):
        print("DUAL POLICY: REJECTED — a prohibited change under at least one policy",
              file=sys.stderr)
        return EXIT_REJECTED

    if verdict_name(base_line) != verdict_name(head_line):
        print(
            "DUAL POLICY: ESCALATE — base and head policies disagree. The change "
            "alters judgement, so it belongs in shadow mode and a later epoch, "
            "not in the event that introduces it.",
            file=sys.stderr,
        )
        return EXIT_ESCALATE

    if base_code != EXIT_OK or head_code != EXIT_OK:
        print("DUAL POLICY: ESCALATE — both policies agree that this escalates",
              file=sys.stderr)
        return EXIT_ESCALATE

    print("DUAL POLICY: PASS — both policies agree the envelope covers this change")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
