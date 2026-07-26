"""Adversarial tests for the human-applied phase-transition verifier
(tools/verify_phase_transition.py).

Proves, fail-closed: RFC 8785 canonicalization (UTF-16 member ordering, surrogate pairs,
duplicate-key and float rejection), Ed25519 verification anchored to the RFC 8032 section 7.1
published test vector, DSSE signature/trust enforcement, authority-role/action/validity/
revocation checks, compare-and-swap predecessor binding, single-use replay, the crux
recompute-equals-proposed-successor equality, and invariant enforcement.
"""
import base64
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "verify_phase_transition", ROOT / "tools" / "verify_phase_transition.py"
)
v = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v)


# Deterministic test authority key (seed derived, never a committed high-entropy literal).
SEED = hashlib.sha256(b"bopen-verifier-test-authority-key").digest()
PUBLIC_HEX = v.ed25519_public_key(SEED).hex()
KEYID = "test-authority-key-1"
IDENTITY_ID = "HUMAN-OPERATOR-001"
VTIME = "2026-07-25T00:00:00+07:00"


def _predecessor():
    return {
        "register_id": "PG-REG-SCHEDULE-001",
        "entries": [
            {"schedule_id": "PG-P0", "status": "ACTIVE", "planned_end": None, "rebaseline_decision_ref": None},
            {"schedule_id": "PG-P1", "status": "NOT_READY"},
        ],
    }


def _trust_root(public_hex=PUBLIC_HEX, keyid=KEYID, identity_id=IDENTITY_ID):
    return {"keys": [{"keyid": keyid, "algorithm": "ed25519", "public_key": public_hex, "identity_id": identity_id}]}


def _identity_register(roles=None, actions=None, valid_from="2026-01-01T00:00:00+07:00",
                       expires_at="2027-01-01T00:00:00+07:00", revoked_at=None, status="approved"):
    return {
        "register_id": "PG-REG-IDENTITY-001",
        "entries": [{
            "identity_id": IDENTITY_ID,
            "status": status,
            "authority_roles": roles if roles is not None else ["Architecture Authority", "Engineering Authority"],
            "action_ids": actions if actions is not None else ["COMPLETE_PHASE", "ACCEPT_WORK_ITEM"],
            "valid_from": valid_from,
            "expires_at": expires_at,
            "revoked_at": revoked_at,
        }],
    }


def _mandate(predecessor, decision_id="PG-P0-COMPLETE-001"):
    return {
        "schema_id": "bopen.phase-completion-mandate",
        "decision_id": decision_id,
        "phase_id": "PG-P0",
        "operation": "COMPLETE_PHASE",
        "predecessor": {"schedule_digest": v.digest(predecessor)},
        "transform": {
            "specification_digest": "spec-digest-placeholder",
            "permitted_mutations": [
                {"path": "phases.PG-P0.status", "from": "ACTIVE", "to": "COMPLETE"},
                {"path": "phases.PG-P0.planned_end", "rule": "COPY_MANDATE_EFFECTIVE_TIME"},
                {"path": "phases.PG-P0.rebaseline_decision_ref", "value": "PG-P0-COMPLETE-001"},
            ],
        },
        "invariants": {"phases.PG-P1.status": "NOT_READY"},
        "authority": {
            "required_role": "Architecture Authority",
            "required_action": "COMPLETE_PHASE",
            "effective_at": VTIME,
        },
    }


def _envelope(mandate, seed=SEED, keyid=KEYID, payload_bytes=None):
    payload = payload_bytes if payload_bytes is not None else v.rfc8785_canonical(mandate)
    pae = v._pae(v.DSSE_PAYLOAD_TYPE, payload)
    sig = v.sign_ed25519(seed, pae)
    return {
        "payloadType": v.DSSE_PAYLOAD_TYPE,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [{"keyid": keyid, "sig": base64.b64encode(sig).decode("ascii")}],
    }


def _verify(predecessor=None, successor=None, mandate=None, envelope=None, trust_root=None,
            identity_register=None, verification_time=VTIME, consumed=None, revocations=None):
    predecessor = predecessor if predecessor is not None else _predecessor()
    mandate = mandate if mandate is not None else _mandate(predecessor)
    successor = successor if successor is not None else v.recompute_successor(predecessor, mandate)
    envelope = envelope if envelope is not None else _envelope(mandate)
    return v.verify_transition(
        predecessor, successor, envelope,
        trust_root if trust_root is not None else _trust_root(),
        identity_register if identity_register is not None else _identity_register(),
        verification_time, consumed or {}, revocations or {},
    )


class Ed25519Rfc8032Tests(unittest.TestCase):
    # RFC 8032 section 7.1, Test 1 (empty message). Public key + signature only (no secret).
    PUB = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
    SIG = bytes.fromhex(
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
        "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )

    def test_official_vector_accepts(self):
        self.assertTrue(v.verify_ed25519(self.PUB, b"", self.SIG))

    def test_official_vector_bitflip_rejects(self):
        bad = bytearray(self.SIG)
        bad[0] ^= 0x01
        self.assertFalse(v.verify_ed25519(self.PUB, b"", bytes(bad)))

    def test_roundtrip_sign_verify(self):
        msg = b"phase-completion-mandate"
        sig = v.sign_ed25519(SEED, msg)
        self.assertTrue(v.verify_ed25519(bytes.fromhex(PUBLIC_HEX), msg, sig))
        self.assertFalse(v.verify_ed25519(bytes.fromhex(PUBLIC_HEX), msg + b"!", sig))


class Rfc8785CanonicalTests(unittest.TestCase):
    def test_member_names_sorted_by_utf16(self):
        self.assertEqual(v.rfc8785_canonical({"b": 1, "a": 2}), b'{"a":2,"b":1}')

    def test_supplementary_char_orders_by_utf16_code_units(self):
        # RFC 8785 orders member names by UTF-16 code units, NOT Unicode code points.
        # U+10000 -> surrogate pair D800 DC00; its first code unit 0xD800 < 0xFFFF, so U+10000
        # sorts BEFORE U+FFFF -- the reverse of a naive code-point sort. This is the exact
        # subtlety a JCS-aligned-but-unproven canonicalizer gets wrong.
        canon = v.rfc8785_canonical({"\U00010000": 1, "￿": 2})
        self.assertEqual(canon, '{"\U00010000":1,"￿":2}'.encode("utf-8"))

    def test_duplicate_key_rejected(self):
        with self.assertRaises(v.VerifyError) as cm:
            v.parse_strict('{"a":1,"a":2}')
        self.assertEqual(cm.exception.reason, v.CANONICALIZATION_ERROR)

    def test_float_rejected(self):
        with self.assertRaises(v.VerifyError) as cm:
            v.rfc8785_canonical({"x": 1.5})
        self.assertEqual(cm.exception.reason, v.CANONICALIZATION_ERROR)

    def test_integer_and_key_order_independent(self):
        self.assertEqual(v.digest({"a": 1, "b": 2}), v.digest({"b": 2, "a": 1}))


class VerifierHappyPathTests(unittest.TestCase):
    def test_verified_exact(self):
        result = _verify()
        self.assertEqual(result["verdict"], v.VERIFIED)
        self.assertEqual(result["outcome"], "VERIFIED_EXACT")
        r = result["receipt"]
        self.assertEqual(r["signer_identity"], IDENTITY_ID)
        self.assertEqual(r["authorized_successor_schedule_digest"], r["proposed_successor_schedule_digest"])
        self.assertEqual(r["phase_id"], "PG-P0")

    def test_receipt_binds_pg_p1_still_not_ready(self):
        pred = _predecessor()
        succ = v.recompute_successor(pred, _mandate(pred))
        self.assertEqual(v._entry(succ, "PG-P0")["status"], "COMPLETE")
        self.assertEqual(v._entry(succ, "PG-P1")["status"], "NOT_READY")

    def test_idempotent_already_verified_exact(self):
        first = _verify()
        again = _verify(consumed=first["consumed"])
        self.assertEqual(again["outcome"], "ALREADY_VERIFIED_EXACT")


class VerifierRejectionTests(unittest.TestCase):
    def _assert_reason(self, reason, **kwargs):
        with self.assertRaises(v.VerifyError) as cm:
            _verify(**kwargs)
        self.assertEqual(cm.exception.reason, reason)

    def test_tampered_signature(self):
        env = _envelope(_mandate(_predecessor()))
        raw = bytearray(base64.b64decode(env["signatures"][0]["sig"]))
        raw[0] ^= 0x01
        env["signatures"][0]["sig"] = base64.b64encode(bytes(raw)).decode("ascii")
        self._assert_reason(v.SIGNATURE_INVALID, envelope=env)

    def test_untrusted_key_id(self):
        env = _envelope(_mandate(_predecessor()), keyid="stranger")
        self._assert_reason(v.UNTRUSTED_KEY, envelope=env)

    def test_wrong_signing_key_same_keyid(self):
        other = hashlib.sha256(b"attacker").digest()
        env = _envelope(_mandate(_predecessor()), seed=other)  # keyid trusted, key wrong
        self._assert_reason(v.SIGNATURE_INVALID, envelope=env)

    def test_non_canonical_signed_payload(self):
        mandate = _mandate(_predecessor())
        non_canonical = json.dumps(mandate, indent=2).encode("utf-8")  # valid but not JCS
        env = _envelope(mandate, payload_bytes=non_canonical)
        self._assert_reason(v.CANONICALIZATION_ERROR, envelope=env)

    def test_authority_missing_role(self):
        self._assert_reason(v.AUTHORITY_DENIED, identity_register=_identity_register(roles=["Engineering Authority"]))

    def test_authority_missing_action(self):
        self._assert_reason(v.AUTHORITY_DENIED, identity_register=_identity_register(actions=["ACCEPT_WORK_ITEM"]))

    def test_before_valid_from(self):
        self._assert_reason(v.VALIDITY_EXPIRED, verification_time="2025-01-01T00:00:00+07:00")

    def test_after_expires_at(self):
        self._assert_reason(v.VALIDITY_EXPIRED, verification_time="2027-06-01T00:00:00+07:00")

    def test_identity_revoked(self):
        reg = _identity_register(revoked_at="2026-06-01T00:00:00+07:00")
        self._assert_reason(v.REVOKED, identity_register=reg)

    def test_key_revoked(self):
        self._assert_reason(v.REVOKED, revocations={"revoked_keyids": [KEYID]})

    def test_decision_revoked(self):
        self._assert_reason(v.REVOKED, revocations={"revoked_decision_ids": ["PG-P0-COMPLETE-001"]})

    def test_predecessor_mismatch_cas(self):
        pred = _predecessor()
        mandate = _mandate(pred)
        drifted = _predecessor()
        drifted["entries"][0]["planned_start"] = "2026-07-01T00:00:00+07:00"  # register moved on
        succ = v.recompute_successor(pred, mandate)
        self._assert_reason(v.PREDECESSOR_MISMATCH, predecessor=drifted, mandate=mandate, successor=succ,
                            envelope=_envelope(mandate))

    def test_successor_mismatch_smuggled_change(self):
        pred = _predecessor()
        mandate = _mandate(pred)
        succ = v.recompute_successor(pred, mandate)
        succ["entries"][1]["status"] = "READY"  # human tries to also nudge PG-P1
        self._assert_reason(v.SUCCESSOR_MISMATCH, predecessor=pred, mandate=mandate, successor=succ,
                            envelope=_envelope(mandate))

    def test_invariant_violation_opening_p1(self):
        pred = _predecessor()
        mandate = _mandate(pred)
        mandate["transform"]["permitted_mutations"].append(
            {"path": "phases.PG-P1.status", "from": "NOT_READY", "to": "ACTIVE"}
        )
        env = _envelope(mandate)
        # recompute itself raises INVARIANT_VIOLATION; verify surfaces the same reason
        with self.assertRaises(v.VerifyError) as cm:
            succ = v.recompute_successor(pred, mandate)
            _verify(predecessor=pred, mandate=mandate, successor=succ, envelope=env)
        self.assertEqual(cm.exception.reason, v.INVARIANT_VIOLATION)

    def test_unknown_mandate_field_rejected(self):
        pred = _predecessor()
        mandate = _mandate(pred)
        mandate["evil"] = "x"
        env = _envelope(mandate)  # signed over the tampered (still-canonical) mandate
        self._assert_reason(v.MANDATE_INVALID, predecessor=pred, mandate=mandate,
                            successor=_predecessor(), envelope=env)

    def test_replay_different_transition_denied(self):
        first = _verify()
        # same decision id, but a different predecessor/successor pairing
        pred2 = _predecessor()
        pred2["entries"][0]["title"] = "changed"
        mandate2 = _mandate(pred2)  # same decision_id default
        succ2 = v.recompute_successor(pred2, mandate2)
        with self.assertRaises(v.VerifyError) as cm:
            _verify(predecessor=pred2, mandate=mandate2, successor=succ2,
                    envelope=_envelope(mandate2), consumed=first["consumed"])
        self.assertEqual(cm.exception.reason, v.REPLAY_DENIED)


if __name__ == "__main__":
    unittest.main()
