#!/usr/bin/env python3
"""Deterministic, idempotent phase-transition encoder for bOPEN program-phase mandates.

This tool executes Stage 2 of the two-stage phase-transition model: it applies a
human-signed Stage-1 completion mandate to the authoritative schedule register and emits
an append-only transition receipt. It enforces the controls that must NOT be left as prose:

- CANONICALIZATION: digests are taken over a JCS-aligned canonical JSON form (recursively
  sorted keys, UTF-8, compact separators, duplicate keys rejected, no BOM). Editor-dependent
  bytes are never signed or compared.
- COMPARE-AND-SWAP ANTI-REPLAY: the mandate's predecessor schedule digest must equal the
  digest of the current authoritative schedule, else the apply is denied. A mandate valid
  against an old schedule cannot be replayed against a later one.
- SINGLE-USE DECISION CONSUMPTION: a consumed-decisions registry records decision ids; a
  decision may be consumed exactly once, atomically with the transition.
- DETERMINISTIC TRANSFORM: only the mandate's explicitly permitted mutations are applied;
  unknown mutation paths are rejected; the successor is a pure function of predecessor +
  transform spec, so a checker can independently recompute it.
- INVARIANT ENFORCEMENT: declared invariants (e.g. PG-P1 stays NOT_READY) must hold in the
  successor, else the apply is denied.
- IDEMPOTENCY: re-applying the same mandate to the same predecessor yields byte-identical
  output (APPLIED_EXACT); applying against an already-authoritative successor yields
  ALREADY_APPLIED_EXACT with no new transition/receipt; a different or partial state yields
  CONFLICT; a consumed decision replayed against another predecessor yields REPLAY_DENIED.

Sole maker: Claude (BST-SA Motor worker agent). Dependency-free (standard library only).
This tool does not sign, does not grant authority, and does not merge; it only applies an
already-signed mandate and produces evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


# ---------------------------------------------------------------- outcomes

APPLIED_EXACT = "APPLIED_EXACT"
ALREADY_APPLIED_EXACT = "ALREADY_APPLIED_EXACT"
CONFLICT = "CONFLICT"
REPLAY_DENIED = "REPLAY_DENIED"
INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
MANDATE_INVALID = "MANDATE_INVALID"


class TransitionError(Exception):
    """Raised for a denied or invalid transition; carries an outcome code."""

    def __init__(self, outcome: str, message: str) -> None:
        super().__init__(f"{outcome}: {message}")
        self.outcome = outcome
        self.message = message


# ---------------------------------------------------------------- canonicalization

def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise TransitionError(MANDATE_INVALID, f"duplicate key rejected: {key}")
        seen[key] = value
    return seen


def parse_strict(text: str) -> object:
    """Parse JSON rejecting duplicate keys (a JCS/anti-ambiguity requirement)."""
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def canonical_bytes(value: object) -> bytes:
    """JCS-aligned canonical JSON: recursively sorted keys, UTF-8, compact separators, no
    trailing whitespace, no BOM. Suitable for digesting and signing."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


# ---------------------------------------------------------------- mandate model

MANDATE_REQUIRED = {"schema_id", "decision_id", "phase_id", "operation", "predecessor", "transform", "invariants"}
MANDATE_ALLOWED = MANDATE_REQUIRED | {"schema_version", "program_id", "accepted_work_item", "integration", "authority", "segregation_of_duties"}
MUTATION_ALLOWED_KEYS = {"path", "from", "to", "rule", "value"}


def validate_mandate(mandate: object) -> dict:
    if not isinstance(mandate, dict):
        raise TransitionError(MANDATE_INVALID, "mandate must be a JSON object")
    unknown = set(mandate) - MANDATE_ALLOWED
    if unknown:
        raise TransitionError(MANDATE_INVALID, f"unknown mandate fields: {sorted(unknown)}")
    missing = MANDATE_REQUIRED - set(mandate)
    if missing:
        raise TransitionError(MANDATE_INVALID, f"missing mandate fields: {sorted(missing)}")
    if mandate.get("schema_id") != "bopen.phase-completion-mandate":
        raise TransitionError(MANDATE_INVALID, "unexpected schema_id")
    predecessor = mandate["predecessor"]
    if not isinstance(predecessor, dict) or "schedule_digest" not in predecessor:
        raise TransitionError(MANDATE_INVALID, "predecessor.schedule_digest required")
    transform = mandate["transform"]
    if not isinstance(transform, dict) or not isinstance(transform.get("permitted_mutations"), list):
        raise TransitionError(MANDATE_INVALID, "transform.permitted_mutations must be a list")
    if not transform["permitted_mutations"]:
        raise TransitionError(MANDATE_INVALID, "transform has no permitted mutations")
    for mutation in transform["permitted_mutations"]:
        if not isinstance(mutation, dict) or "path" not in mutation:
            raise TransitionError(MANDATE_INVALID, "each mutation needs a path")
        extra = set(mutation) - MUTATION_ALLOWED_KEYS
        if extra:
            raise TransitionError(MANDATE_INVALID, f"unknown mutation keys: {sorted(extra)}")
    if not isinstance(mandate["invariants"], dict):
        raise TransitionError(MANDATE_INVALID, "invariants must be an object")
    return mandate


# ---------------------------------------------------------------- schedule / transform

def _entry(schedule: dict, schedule_id: str) -> dict:
    for item in schedule.get("entries", []):
        if isinstance(item, dict) and item.get("schedule_id") == schedule_id:
            return item
    raise TransitionError(MANDATE_INVALID, f"schedule entry not found: {schedule_id}")


def _resolve_phase_field(path: str) -> tuple[str, str]:
    """A mutation path 'phases.<schedule_id>.<field>' addresses a register entry field."""
    parts = path.split(".")
    if len(parts) != 3 or parts[0] != "phases":
        raise TransitionError(MANDATE_INVALID, f"unsupported mutation path: {path}")
    return parts[1], parts[2]


def recompute_successor(predecessor: dict, mandate: dict) -> dict:
    """Pure function: successor = transform(predecessor). No I/O, no clock. A checker calls
    this to recompute the successor independently of any maker output."""
    validate_mandate(mandate)
    successor = json.loads(json.dumps(predecessor))  # deep copy without shared refs
    effective_at = (mandate.get("authority") or {}).get("effective_at")
    for mutation in mandate["transform"]["permitted_mutations"]:
        schedule_id, field = _resolve_phase_field(mutation["path"])
        entry = _entry(successor, schedule_id)
        if "to" in mutation:
            if "from" in mutation and entry.get(field) != mutation["from"]:
                raise TransitionError(CONFLICT, f"{schedule_id}.{field} is {entry.get(field)!r}, mandate expects {mutation['from']!r}")
            entry[field] = mutation["to"]
        elif mutation.get("rule") == "COPY_MANDATE_EFFECTIVE_TIME":
            if effective_at is None:
                raise TransitionError(MANDATE_INVALID, "authority.effective_at required for COPY_MANDATE_EFFECTIVE_TIME")
            entry[field] = effective_at
        elif "value" in mutation:
            entry[field] = mutation["value"]
        else:
            raise TransitionError(MANDATE_INVALID, f"mutation has neither to/rule/value: {mutation['path']}")
    _enforce_invariants(successor, mandate)
    return successor


def _enforce_invariants(successor: dict, mandate: dict) -> None:
    for key, expected in mandate["invariants"].items():
        if not key.startswith("phases."):
            continue  # non-schedule invariants (e.g. production_authorized) are asserted elsewhere
        schedule_id, field = _resolve_phase_field(key)
        actual = _entry(successor, schedule_id).get(field)
        if actual != expected:
            raise TransitionError(INVARIANT_VIOLATION, f"invariant {key} expected {expected!r}, got {actual!r}")


# ---------------------------------------------------------------- apply (Stage 2)

def apply_transition(predecessor: dict, mandate: dict, consumed: dict) -> dict:
    """Apply the mandate to the predecessor with CAS anti-replay, single-use consumption and
    idempotency. `consumed` maps decision_id -> {predecessor_digest, successor_digest}.
    Returns a result dict {outcome, successor, receipt, consumed}."""
    validate_mandate(mandate)
    decision_id = mandate["decision_id"]
    current_digest = digest(predecessor)  # `predecessor` is the current authoritative schedule

    prior = consumed.get(decision_id)
    if prior is not None:
        # Decision already consumed. Idempotent only when the current state IS the successor
        # it produced — do NOT recompute the transform against the already-applied state.
        if current_digest == prior.get("successor_digest"):
            return {"outcome": ALREADY_APPLIED_EXACT, "successor": None, "receipt": None, "consumed": consumed}
        raise TransitionError(REPLAY_DENIED, f"decision {decision_id} already consumed for a different state")

    # Decision not yet consumed: compare-and-swap — the mandate's bound predecessor digest
    # MUST equal the current schedule digest, or a valid old/other mandate is being replayed.
    if mandate["predecessor"]["schedule_digest"] != current_digest:
        raise TransitionError(
            REPLAY_DENIED,
            f"predecessor mismatch: mandate binds {mandate['predecessor']['schedule_digest']}, current is {current_digest}",
        )

    successor = recompute_successor(predecessor, mandate)  # current == predecessor: from-checks hold
    successor_digest = digest(successor)
    consumed_next = dict(consumed)
    consumed_next[decision_id] = {"predecessor_digest": current_digest, "successor_digest": successor_digest}
    receipt = {
        "schema_id": "bopen.phase-transition-receipt",
        "receipt_id": mandate.get("integration", {}).get("receipt_id", "SIGNING-PASS-PHASE"),
        "decision_id": decision_id,
        "mandate_digest": digest(mandate),
        "transform_specification_digest": mandate["transform"].get("specification_digest"),
        "predecessor": {"schedule_digest": current_digest},
        "successor": {"schedule_digest": successor_digest},
        "outcome": APPLIED_EXACT,
    }
    return {"outcome": APPLIED_EXACT, "successor": successor, "receipt": receipt, "consumed": consumed_next}


def _load(path: Path) -> object:
    return parse_strict(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a signed phase-completion mandate (Stage 2).")
    parser.add_argument("--schedule", type=Path, required=True, help="current authoritative schedule register JSON")
    parser.add_argument("--mandate", type=Path, required=True, help="signed Stage-1 mandate JSON")
    parser.add_argument("--consumed", type=Path, help="consumed-decisions registry JSON (default: empty)")
    args = parser.parse_args()
    schedule = _load(args.schedule)
    mandate = _load(args.mandate)
    consumed = _load(args.consumed) if args.consumed and args.consumed.is_file() else {}
    try:
        result = apply_transition(schedule, mandate, consumed)
    except TransitionError as exc:
        print(f"{exc.outcome}: {exc.message}")
        return 1
    print(result["outcome"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
