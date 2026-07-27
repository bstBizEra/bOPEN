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
            identity_register=None, verification_time=VTIME, consumed=None, revocations=None,
            closure_manifest_bytes=None, revocation_bytes=None, consumed_bytes=None,
            require_closure_binding=False):
    predecessor = predecessor if predecessor is not None else _predecessor()
    mandate = mandate if mandate is not None else _mandate(predecessor)
    successor = successor if successor is not None else v.recompute_successor(predecessor, mandate)
    envelope = envelope if envelope is not None else _envelope(mandate)
    return v.verify_transition(
        predecessor, successor, envelope,
        trust_root if trust_root is not None else _trust_root(),
        identity_register if identity_register is not None else _identity_register(),
        verification_time, consumed or {}, revocations or {},
        closure_manifest_bytes, revocation_bytes, consumed_bytes, require_closure_binding,
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


class ClosureBindingFailClosedTests(unittest.TestCase):
    """Closure-execution verification must fail closed when the closure binding is absent,
    malformed, or mismatched. There is deliberately NO test asserting that an unbound mandate is
    'not contradicted' in closure mode -- that shape is the vulnerability, not a compatibility
    requirement."""

    MANIFEST_EFFECTS = [
        {"path": "docs/00-governance/registers/SCHEDULE-REGISTER.json", "effect": "apply successor"},
        {"path": "tools/validate_pg_g0_authority_docket.py", "effect": "extend expected state"},
    ]

    def _manifest_bytes(self, effects=None):
        obj = {
            "decision_id": "PG-P0-CLOSURE-001",
            "_status": "frozen pre-execution manifest",
            "permitted_effects_at_execution_C8": effects if effects is not None else self.MANIFEST_EFFECTS,
        }
        return json.dumps(obj, indent=2).encode("utf-8")

    def _revocation_bytes(self):
        return json.dumps({"revoked_keyids": [], "revoked_decision_ids": []}).encode("utf-8")

    def _consumed_bytes(self):
        return json.dumps({}).encode("utf-8")

    def _binding(self, manifest_bytes=None, **overrides):
        manifest_bytes = manifest_bytes if manifest_bytes is not None else self._manifest_bytes()
        effects = json.loads(manifest_bytes.decode("utf-8"))["permitted_effects_at_execution_C8"]
        binding = {
            "closure_manifest_digest": hashlib.sha256(manifest_bytes).hexdigest(),
            "permitted_effects_digest": v.digest(effects),
            "predecessor_commit": "042dda535be70927b73cd1a131b2545349729643",
            "predecessor_tree": "1732e445c0d05b416223443314e73c5b978ce1be",
            "target_ref": "refs/heads/pg-p0-closure-lineage",
            "expected_old": "042dda535be70927b73cd1a131b2545349729643",
            "revocation_state_digest": hashlib.sha256(self._revocation_bytes()).hexdigest(),
            "consumed_state_digest": hashlib.sha256(self._consumed_bytes()).hexdigest(),
            "successor_blobs": {"docs/00-governance/registers/SCHEDULE-REGISTER.json": "UNRESOLVED"},
            "successor_blobs_status": "UNRESOLVED_PENDING_HUMAN_EXECUTION_BYTES",
        }
        binding.update(overrides)
        return binding

    def _bound_mandate(self, manifest_bytes=None, **overrides):
        pred = _predecessor()
        mandate = _mandate(pred)
        mandate["closure_binding"] = self._binding(manifest_bytes, **overrides)
        return pred, mandate

    def _verify_closure(self, pred, mandate, manifest_bytes=None, **kwargs):
        kwargs.setdefault("revocation_bytes", self._revocation_bytes())
        kwargs.setdefault("consumed_bytes", self._consumed_bytes())
        return _verify(
            predecessor=pred, mandate=mandate, envelope=_envelope(mandate),
            closure_manifest_bytes=manifest_bytes if manifest_bytes is not None else self._manifest_bytes(),
            require_closure_binding=True, **kwargs
        )

    def _assert_reason(self, reason, pred, mandate, manifest_bytes=None, **kwargs):
        with self.assertRaises(v.VerifyError) as cm:
            self._verify_closure(pred, mandate, manifest_bytes, **kwargs)
        self.assertEqual(cm.exception.reason, reason)

    # ---- happy path -----------------------------------------------------------------
    def test_complete_valid_binding_accepts(self):
        pred, mandate = self._bound_mandate()
        result = self._verify_closure(pred, mandate)
        self.assertEqual(result["verdict"], v.VERIFIED)
        binding = result["receipt"]["closure_binding"]
        self.assertTrue(binding["closure_binding_enforced"])
        self.assertEqual(binding["target_ref"], "refs/heads/pg-p0-closure-lineage")
        self.assertTrue(result["receipt"]["closure_execution_verification"])

    # ---- absent ---------------------------------------------------------------------
    def test_absent_binding_rejects_in_closure_mode(self):
        pred = _predecessor()
        mandate = _mandate(pred)
        self.assertNotIn("closure_binding", mandate)
        self._assert_reason(v.CLOSURE_BINDING_REQUIRED, pred, mandate)

    def test_absent_manifest_bytes_rejects_in_closure_mode(self):
        pred, mandate = self._bound_mandate()
        with self.assertRaises(v.VerifyError) as cm:
            _verify(predecessor=pred, mandate=mandate, envelope=_envelope(mandate),
                    closure_manifest_bytes=None, revocation_bytes=self._revocation_bytes(),
                    consumed_bytes=self._consumed_bytes(), require_closure_binding=True)
        self.assertEqual(cm.exception.reason, v.CLOSURE_BINDING_REQUIRED)

    def test_absent_revocation_state_rejects_in_closure_mode(self):
        pred, mandate = self._bound_mandate()
        self._assert_reason(v.CLOSURE_BINDING_REQUIRED, pred, mandate, revocation_bytes=None)

    def test_absent_consumed_state_rejects_in_closure_mode(self):
        pred, mandate = self._bound_mandate()
        self._assert_reason(v.CLOSURE_BINDING_REQUIRED, pred, mandate, consumed_bytes=None)

    def test_missing_required_binding_field_rejects(self):
        pred, mandate = self._bound_mandate()
        del mandate["closure_binding"]["expected_old"]
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    # ---- malformed ------------------------------------------------------------------
    def test_truncated_63_char_digest_rejects(self):
        # The exact defect shape that shipped in EVD-CLOSURE-014: a hand-transcribed digest one
        # character short. A near-miss must be a hard rejection, never a near-pass.
        pred, mandate = self._bound_mandate()
        full = mandate["closure_binding"]["closure_manifest_digest"]
        mandate["closure_binding"]["closure_manifest_digest"] = full[:-1]
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_uppercase_digest_rejects(self):
        pred, mandate = self._bound_mandate()
        binding = mandate["closure_binding"]
        binding["closure_manifest_digest"] = binding["closure_manifest_digest"].upper()
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_non_hex_digest_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["permitted_effects_digest"] = "z" * 64
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_short_git_oid_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["expected_old"] = "042dda5"
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_unqualified_target_ref_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["target_ref"] = "main"
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_unknown_binding_field_rejects(self):
        # The binding allow-list is closed, so a field a reader might mistake for an enforced
        # control cannot be smuggled in.
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["also_verified"] = "trust me"
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_empty_successor_blobs_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["successor_blobs"] = {}
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate)

    def test_manifest_not_json_rejects(self):
        raw = b"not json at all"
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["closure_manifest_digest"] = hashlib.sha256(raw).hexdigest()
        self._assert_reason(v.CLOSURE_BINDING_MALFORMED, pred, mandate, raw)

    # ---- mismatched -----------------------------------------------------------------
    def test_mismatched_manifest_digest_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["closure_manifest_digest"] = "0" * 64
        self._assert_reason(v.CLOSURE_MANIFEST_MISMATCH, pred, mandate)

    def test_mismatched_revocation_state_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["revocation_state_digest"] = "1" * 64
        self._assert_reason(v.REVOCATION_STATE_MISMATCH, pred, mandate)

    def test_mismatched_consumed_state_rejects(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["consumed_state_digest"] = "2" * 64
        self._assert_reason(v.CONSUMED_STATE_MISMATCH, pred, mandate)

    def test_manifest_without_permitted_effects_rejects(self):
        raw = json.dumps({"decision_id": "PG-P0-CLOSURE-001"}).encode("utf-8")
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["closure_manifest_digest"] = hashlib.sha256(raw).hexdigest()
        self._assert_reason(v.PERMITTED_EFFECTS_MISMATCH, pred, mandate, raw)

    # ---- semantic attacker ----------------------------------------------------------
    def test_attacker_altered_permitted_effects_rejects(self):
        """SEMANTIC ATTACK: the attacker widens what the closure is allowed to write -- adding a
        write to the authority matrix -- while leaving the schedule transform, the signature, and
        every other input untouched. The transform-level checks are all still perfectly happy;
        only the closure binding catches this."""
        pred, mandate = self._bound_mandate()
        attacker_effects = self.MANIFEST_EFFECTS + [
            {"path": "docs/00-governance/registers/AUTHORITY-MATRIX.json", "effect": "grant self approval"},
        ]
        attacker_manifest = self._manifest_bytes(attacker_effects)
        # Sanity: the transform itself is untouched, so this is purely an effects-scope attack.
        self.assertEqual(mandate["transform"], _mandate(pred)["transform"])
        self._assert_reason(v.CLOSURE_MANIFEST_MISMATCH, pred, mandate, attacker_manifest)

    def test_permitted_effects_digest_is_an_independent_control(self):
        """Defence in depth: even if the whole-file digest were re-issued for a legitimate
        editorial reason (manifests accrete revision notes), an altered effects list is still
        caught by its own digest. Here the mandate binds the ALTERED file's whole-file digest but
        the ORIGINAL effects digest -- the second control is what fires."""
        original_effects_digest = v.digest(self.MANIFEST_EFFECTS)
        attacker_effects = self.MANIFEST_EFFECTS + [
            {"path": "tools/check_secrets.py", "effect": "disable"},
        ]
        attacker_manifest = self._manifest_bytes(attacker_effects)
        pred, mandate = self._bound_mandate(
            attacker_manifest,
            permitted_effects_digest=original_effects_digest,
        )
        # whole-file digest matches the attacker's file, so ONLY the effects digest can catch it
        self.assertEqual(
            mandate["closure_binding"]["closure_manifest_digest"],
            hashlib.sha256(attacker_manifest).hexdigest(),
        )
        self._assert_reason(v.PERMITTED_EFFECTS_MISMATCH, pred, mandate, attacker_manifest)

    # ---- non-closure mode remains usable, but never silently unbound ------------------
    def test_present_binding_is_enforced_even_outside_closure_mode(self):
        pred, mandate = self._bound_mandate()
        mandate["closure_binding"]["closure_manifest_digest"] = "3" * 64
        with self.assertRaises(v.VerifyError) as cm:
            _verify(predecessor=pred, mandate=mandate, envelope=_envelope(mandate),
                    closure_manifest_bytes=self._manifest_bytes(), require_closure_binding=False)
        self.assertEqual(cm.exception.reason, v.CLOSURE_MANIFEST_MISMATCH)

    def test_non_closure_mode_reports_no_binding(self):
        result = _verify()
        self.assertIsNone(result["receipt"]["closure_binding"])
        self.assertFalse(result["receipt"]["closure_execution_verification"])


if __name__ == "__main__":
    unittest.main()
