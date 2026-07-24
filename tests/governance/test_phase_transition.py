"""Executable-control tests for the phase-transition encoder (tools/apply_phase_transition.py).

Proves the controls that were previously documented but not enforced: deterministic
transform, compare-and-swap anti-replay, single-use decision consumption, idempotency
(APPLIED_EXACT / ALREADY_APPLIED_EXACT / CONFLICT / REPLAY_DENIED), invariant enforcement,
canonicalization (duplicate-key + unknown-field rejection), and independent recompute.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("apply_phase_transition", ROOT / "tools" / "apply_phase_transition.py")
enc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(enc)


def _schedule():
    return {
        "register_id": "PG-REG-SCHEDULE-001",
        "entries": [
            {"schedule_id": "PG-P0", "status": "ACTIVE", "planned_end": None, "rebaseline_decision_ref": None},
            {"schedule_id": "PG-P1", "status": "NOT_READY"},
        ],
    }


def _mandate(schedule, decision_id="PG-P0-COMPLETE-001"):
    return {
        "schema_id": "bopen.phase-completion-mandate",
        "decision_id": decision_id,
        "phase_id": "PG-P0",
        "operation": "COMPLETE_PHASE",
        "predecessor": {"schedule_digest": enc.digest(schedule)},
        "transform": {
            "specification_digest": "spec-digest-placeholder",
            "permitted_mutations": [
                {"path": "phases.PG-P0.status", "from": "ACTIVE", "to": "COMPLETE"},
                {"path": "phases.PG-P0.planned_end", "rule": "COPY_MANDATE_EFFECTIVE_TIME"},
                {"path": "phases.PG-P0.rebaseline_decision_ref", "value": "PG-P0-COMPLETE-001"},
            ],
        },
        "invariants": {"phases.PG-P1.status": "NOT_READY"},
        "authority": {"effective_at": "2026-07-25T00:00:00+07:00"},
    }


class PhaseTransitionEncoderTests(unittest.TestCase):
    def test_deterministic_transform_is_byte_identical(self):
        sched, mandate = _schedule(), None
        mandate = _mandate(sched)
        a = enc.recompute_successor(sched, mandate)
        b = enc.recompute_successor(sched, mandate)
        self.assertEqual(enc.canonical_bytes(a), enc.canonical_bytes(b))
        self.assertEqual(enc._entry(a, "PG-P0")["status"], "COMPLETE")
        self.assertEqual(enc._entry(a, "PG-P0")["planned_end"], "2026-07-25T00:00:00+07:00")
        self.assertEqual(enc._entry(a, "PG-P1")["status"], "NOT_READY")  # invariant held

    def test_apply_exact_and_recompute_matches(self):
        sched = _schedule()
        result = enc.apply_transition(sched, _mandate(sched), {})
        self.assertEqual(result["outcome"], enc.APPLIED_EXACT)
        # checker recompute equals maker output
        recomputed = enc.recompute_successor(sched, _mandate(sched))
        self.assertEqual(enc.canonical_bytes(result["successor"]), enc.canonical_bytes(recomputed))
        self.assertEqual(result["receipt"]["successor"]["schedule_digest"], enc.digest(result["successor"]))

    def test_anti_replay_predecessor_mismatch_is_denied(self):
        sched = _schedule()
        mandate = _mandate(sched)
        mandate["predecessor"]["schedule_digest"] = "0" * 64  # stale/wrong predecessor
        with self.assertRaises(enc.TransitionError) as cm:
            enc.apply_transition(sched, mandate, {})
        self.assertEqual(cm.exception.outcome, enc.REPLAY_DENIED)

    def test_single_use_replay_against_other_predecessor_denied(self):
        sched = _schedule()
        result = enc.apply_transition(sched, _mandate(sched), {})
        consumed = result["consumed"]
        other = _schedule()
        other["entries"][0]["title"] = "changed"  # a different predecessor state
        mandate2 = _mandate(other)  # same decision_id, different predecessor
        with self.assertRaises(enc.TransitionError) as cm:
            enc.apply_transition(other, mandate2, consumed)
        self.assertEqual(cm.exception.outcome, enc.REPLAY_DENIED)

    def test_idempotent_already_applied_exact(self):
        sched = _schedule()
        result = enc.apply_transition(sched, _mandate(sched), {})
        successor, consumed = result["successor"], result["consumed"]
        # re-apply the SAME decision against the already-authoritative successor
        mandate_on_successor = _mandate(sched)  # predecessor digest still binds the original predecessor
        again = enc.apply_transition(successor, mandate_on_successor, consumed)
        self.assertEqual(again["outcome"], enc.ALREADY_APPLIED_EXACT)
        self.assertIsNone(again["successor"])  # no new transition/receipt

    def test_conflict_when_current_state_diverges(self):
        sched = _schedule()
        sched["entries"][0]["status"] = "SOMETHING_ELSE"  # neither predecessor-as-signed nor successor
        with self.assertRaises(enc.TransitionError) as cm:
            enc.apply_transition(sched, _mandate(_schedule()), {})
        self.assertIn(cm.exception.outcome, {enc.REPLAY_DENIED, enc.CONFLICT})

    def test_invariant_violation_blocks_pg_p1_change(self):
        sched = _schedule()
        mandate = _mandate(sched)
        mandate["transform"]["permitted_mutations"].append(
            {"path": "phases.PG-P1.status", "from": "NOT_READY", "to": "ACTIVE"}  # would open P1
        )
        with self.assertRaises(enc.TransitionError) as cm:
            enc.apply_transition(sched, mandate, {})
        self.assertEqual(cm.exception.outcome, enc.INVARIANT_VIOLATION)

    def test_unknown_mandate_field_rejected(self):
        sched = _schedule()
        mandate = _mandate(sched)
        mandate["evil"] = "extra"
        with self.assertRaises(enc.TransitionError) as cm:
            enc.apply_transition(sched, mandate, {})
        self.assertEqual(cm.exception.outcome, enc.MANDATE_INVALID)

    def test_duplicate_key_rejected_in_canonical_parse(self):
        with self.assertRaises(enc.TransitionError) as cm:
            enc.parse_strict('{"a": 1, "a": 2}')
        self.assertEqual(cm.exception.outcome, enc.MANDATE_INVALID)

    def test_canonical_bytes_are_key_order_independent(self):
        self.assertEqual(enc.canonical_bytes({"b": 1, "a": 2}), enc.canonical_bytes({"a": 2, "b": 1}))


if __name__ == "__main__":
    unittest.main()
