#!/usr/bin/env python3
"""Independent verifier for a human-applied bOPEN program-phase transition.

DESIGN (Verifier + human apply). The authoritative, atomic durable state change is the
human operator's SINGLE git commit that replaces the predecessor schedule-register bytes with
the successor bytes. Git provides the compare-and-swap (the commit's parent is the exact
predecessor tree) and the atomic, crash-safe ref update. This tool does NOT perform that
update and holds no authority. Its job is to PROVE that a proposed successor register is
exactly the transition a signed Stage-1 mandate authorizes -- nothing more, nothing less --
so an independent checker and the operator can rely on the human commit being correct.

It enforces, fail-closed, the controls a signature-safe transition requires:

- RFC 8785 (JCS) CANONICALIZATION for every digest and for the signed payload. Object member
  names are ordered by UTF-16 code units (not Python code points); numbers are restricted to
  the I-JSON safe-integer profile the registers use and non-integers are rejected; duplicate
  keys, NaN and Infinity are rejected. Editor-dependent bytes are never signed or compared.
- DSSE + Ed25519 SIGNATURE verification (RFC 8032) against a trust root that binds each key id
  to an authority identity. The pre-authentication encoding is verified, and the signed payload
  is required to already be in canonical form (no signature/parse ambiguity).
- AUTHORITY / TRUST enforcement against the authority-identity register: the signer identity is
  approved, holds the required authority role and action, is inside its validity window at the
  supplied verification time (no wall clock is read), and is neither key-revoked nor
  mandate-revoked.
- COMPARE-AND-SWAP ANTI-REPLAY: the mandate's bound predecessor digest must equal the canonical
  digest of the supplied predecessor register (expected-old), and the decision id must be
  single-use per a supplied consumed-decisions registry (idempotent for the identical apply).
- DETERMINISTIC RECOMPUTE EQUALITY: the successor is recomputed as a pure function of
  predecessor + mandate transform, and its canonical bytes MUST equal the human-proposed
  successor's canonical bytes. Any smuggled change makes the verdict REJECTED.
- INVARIANT ENFORCEMENT: declared invariants (e.g. PG-P1 stays NOT_READY) must hold.

The tool emits an advisory verification receipt. It signs nothing, consumes nothing, mutates no
register, and merges nothing. Sole maker: Claude (BST-SA Motor worker agent). Standard library
only (a clean-room RFC 8032 Ed25519 implementation is bundled; production may substitute a
vetted library behind verify_ed25519()).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


# ================================================================ verdicts

VERIFIED = "VERIFIED"
REJECTED = "REJECTED"

# Rejection reason codes (stable, machine-readable).
CANONICALIZATION_ERROR = "CANONICALIZATION_ERROR"
SIGNATURE_INVALID = "SIGNATURE_INVALID"
UNTRUSTED_KEY = "UNTRUSTED_KEY"
AUTHORITY_DENIED = "AUTHORITY_DENIED"
VALIDITY_EXPIRED = "VALIDITY_EXPIRED"
REVOKED = "REVOKED"
REPLAY_DENIED = "REPLAY_DENIED"
PREDECESSOR_MISMATCH = "PREDECESSOR_MISMATCH"
SUCCESSOR_MISMATCH = "SUCCESSOR_MISMATCH"
INVARIANT_VIOLATION = "INVARIANT_VIOLATION"
MANDATE_INVALID = "MANDATE_INVALID"
CLOSURE_MANIFEST_MISMATCH = "CLOSURE_MANIFEST_MISMATCH"


class VerifyError(Exception):
    """A fail-closed verification rejection carrying a stable reason code."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(f"{reason}: {message}")
        self.reason = reason
        self.message = message


# ================================================================ RFC 8785 canonicalization

def _reject_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise VerifyError(CANONICALIZATION_ERROR, f"duplicate key rejected: {key!r}")
        seen[key] = value
    return seen


def parse_strict(text):
    """Parse JSON rejecting duplicate object keys (RFC 8785 / I-JSON requirement)."""
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def _canonical_string(value):
    # Python's compact JSON string escaping (ensure_ascii=False) matches RFC 8785 for strings:
    # it emits the short escapes \" \\ \b \f \n \r \t and \uXXXX for other control characters,
    # escapes nothing above U+001F, and leaves non-ASCII literal. Reuse it for exactly one
    # string so no separators/whitespace leak in.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _canonical_number(value):
    # I-JSON safe-integer profile: the registers carry only integers. Anything else (float,
    # bool-as-number is handled earlier, NaN/Infinity) is out of profile and rejected rather
    # than serialized with a non-RFC-8785 float formatting.
    if isinstance(value, bool):  # defensive; handled before this call
        raise VerifyError(CANONICALIZATION_ERROR, "bool is not a number")
    if isinstance(value, int):
        return str(value)
    raise VerifyError(
        CANONICALIZATION_ERROR,
        f"non-integer number {value!r} is out of the I-JSON safe-integer profile",
    )


def rfc8785_canonical(value):
    """Return the RFC 8785 (JCS) canonical UTF-8 bytes for a JSON value, for the profile the
    bOPEN registers use (objects, arrays, strings, integers, booleans, null). Member names are
    ordered by UTF-16 code units."""
    return _canonical(value).encode("utf-8")


def _canonical(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _canonical_string(value)
    if isinstance(value, int):
        return _canonical_number(value)
    if isinstance(value, float):
        raise VerifyError(
            CANONICALIZATION_ERROR,
            "floating-point numbers are rejected (I-JSON safe-integer profile only)",
        )
    if isinstance(value, list):
        return "[" + ",".join(_canonical(item) for item in value) + "]"
    if isinstance(value, dict):
        members = []
        for key in _sorted_member_names(value):
            members.append(_canonical_string(key) + ":" + _canonical(value[key]))
        return "{" + ",".join(members) + "}"
    raise VerifyError(CANONICALIZATION_ERROR, f"unserializable value of type {type(value).__name__}")


def _sorted_member_names(obj):
    for key in obj:
        if not isinstance(key, str):
            raise VerifyError(CANONICALIZATION_ERROR, f"non-string object member name: {key!r}")
    # RFC 8785 sorts member names by their UTF-16 code units. Encoding each name to UTF-16
    # big-endian and comparing the resulting byte sequences yields exactly that ordering,
    # including correct handling of supplementary characters via surrogate pairs.
    return sorted(obj.keys(), key=lambda name: name.encode("utf-16-be"))


def digest(value):
    return hashlib.sha256(rfc8785_canonical(value)).hexdigest()


# ================================================================ Ed25519 (RFC 8032, clean-room)
#
# Verify-only is used in production; sign() exists so tests can build fixtures and so the
# implementation can be validated against the RFC 8032 section 7.1 published test vectors.
# This is a from-the-spec reimplementation (no third-party code); a deployment may replace
# verify_ed25519() with a vetted library behind the same signature.

_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _sha512(data):
    return hashlib.sha512(data).digest()


def _sha512_int(data):
    return int.from_bytes(_sha512(data), "little")


def _inv(x):
    return pow(x, _P - 2, _P)


def _recover_x(y, sign):
    if y >= _P:
        return None
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx % _P, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if (x * x - xx) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


_By = (4 * _inv(5)) % _P
_Bx = _recover_x(_By, 0)
_B = (_Bx % _P, _By % _P, 1, (_Bx * _By) % _P)


def _point_add(pt1, pt2):
    x1, y1, z1, t1 = pt1
    x2, y2, z2, t2 = pt2
    a = ((y1 - x1) * (y2 - x2)) % _P
    b = ((y1 + x1) * (y2 + x2)) % _P
    c = (2 * t1 * t2 * _D) % _P
    dd = (2 * z1 * z2) % _P
    e = b - a
    f = dd - c
    g = dd + c
    h = b + a
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _point_mul(scalar, point):
    result = (0, 1, 1, 0)  # neutral element
    while scalar > 0:
        if scalar & 1:
            result = _point_add(result, point)
        point = _point_add(point, point)
        scalar >>= 1
    return result


def _point_equal(pt1, pt2):
    x1, y1, z1, _ = pt1
    x2, y2, z2, _ = pt2
    if (x1 * z2 - x2 * z1) % _P != 0:
        return False
    if (y1 * z2 - y2 * z1) % _P != 0:
        return False
    return True


def _point_compress(point):
    x, y, z, _ = point
    zinv = _inv(z)
    x = (x * zinv) % _P
    y = (y * zinv) % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _point_decompress(data):
    if len(data) != 32:
        return None
    value = int.from_bytes(data, "little")
    sign = (value >> 255) & 1
    y = value & ((1 << 255) - 1)
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, (x * y) % _P)


def _secret_expand(secret):
    if len(secret) != 32:
        raise VerifyError(SIGNATURE_INVALID, "ed25519 secret seed must be 32 bytes")
    h = _sha512(secret)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def ed25519_public_key(secret):
    a, _ = _secret_expand(secret)
    return _point_compress(_point_mul(a, _B))


def sign_ed25519(secret, message):
    a, prefix = _secret_expand(secret)
    public = _point_compress(_point_mul(a, _B))
    r = _sha512_int(prefix + message) % _L
    big_r = _point_compress(_point_mul(r, _B))
    k = _sha512_int(big_r + public + message) % _L
    s = (r + k * a) % _L
    return big_r + s.to_bytes(32, "little")


def verify_ed25519(public_key, message, signature):
    """Return True iff `signature` is a valid Ed25519 signature of `message` by `public_key`."""
    if len(public_key) != 32 or len(signature) != 64:
        return False
    point_a = _point_decompress(public_key)
    if point_a is None:
        return False
    big_r = signature[:32]
    point_r = _point_decompress(big_r)
    if point_r is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= _L:
        return False
    k = _sha512_int(big_r + public_key + message) % _L
    left = _point_mul(s, _B)
    right = _point_add(point_r, _point_mul(k, point_a))
    return _point_equal(left, right)


# ================================================================ DSSE envelope

DSSE_PAYLOAD_TYPE = "application/vnd.bopen.phase-completion-mandate+json"


def _pae(payload_type, payload):
    # DSSE pre-authentication encoding: "DSSEv1 SP len(type) SP type SP len(payload) SP payload".
    return b"DSSEv1 %d %s %d %s" % (
        len(payload_type.encode("utf-8")),
        payload_type.encode("utf-8"),
        len(payload),
        payload,
    )


def _b64decode(text, field):
    try:
        return base64.b64decode(text, validate=True)
    except (ValueError, TypeError) as exc:
        raise VerifyError(MANDATE_INVALID, f"invalid base64 in {field}: {exc}")


def open_signed_mandate(envelope, trust_root):
    """Verify a DSSE envelope against the trust root and return (mandate, signer_keyid).

    Requires the signed payload bytes to already be RFC 8785 canonical, so the bytes that were
    signed are exactly the bytes that yield the parsed mandate (no re-serialization ambiguity)."""
    if not isinstance(envelope, dict):
        raise VerifyError(MANDATE_INVALID, "DSSE envelope must be a JSON object")
    if envelope.get("payloadType") != DSSE_PAYLOAD_TYPE:
        raise VerifyError(MANDATE_INVALID, f"unexpected payloadType: {envelope.get('payloadType')!r}")
    signatures = envelope.get("signatures")
    if not isinstance(signatures, list) or not signatures:
        raise VerifyError(SIGNATURE_INVALID, "envelope has no signatures")
    payload_bytes = _b64decode(envelope.get("payload", ""), "payload")
    pae = _pae(DSSE_PAYLOAD_TYPE, payload_bytes)

    keys = _trust_keys(trust_root)
    accepted_keyid = None
    for entry in signatures:
        if not isinstance(entry, dict):
            continue
        keyid = entry.get("keyid")
        key = keys.get(keyid)
        if key is None:
            continue  # untrusted key id; try the next signature
        sig = _b64decode(entry.get("sig", ""), "sig")
        if verify_ed25519(key["public_key_bytes"], pae, sig):
            accepted_keyid = keyid
            break
    if accepted_keyid is None:
        # Distinguish "no trusted key referenced" from "trusted key but bad signature".
        referenced = {e.get("keyid") for e in signatures if isinstance(e, dict)}
        if not (referenced & set(keys)):
            raise VerifyError(UNTRUSTED_KEY, "no signature references a trusted key id")
        raise VerifyError(SIGNATURE_INVALID, "no valid signature from a trusted key")

    mandate = parse_strict(payload_bytes.decode("utf-8"))
    if rfc8785_canonical(mandate) != payload_bytes:
        raise VerifyError(CANONICALIZATION_ERROR, "signed payload is not RFC 8785 canonical")
    return mandate, accepted_keyid


def _trust_keys(trust_root):
    if not isinstance(trust_root, dict) or not isinstance(trust_root.get("keys"), list):
        raise VerifyError(UNTRUSTED_KEY, "trust root must contain a keys list")
    keys = {}
    for entry in trust_root["keys"]:
        if not isinstance(entry, dict) or "keyid" not in entry or "public_key" not in entry:
            raise VerifyError(UNTRUSTED_KEY, "trust key needs keyid and public_key")
        if entry.get("algorithm", "ed25519") != "ed25519":
            raise VerifyError(UNTRUSTED_KEY, f"unsupported key algorithm: {entry.get('algorithm')!r}")
        try:
            public_bytes = bytes.fromhex(entry["public_key"])
        except ValueError as exc:
            raise VerifyError(UNTRUSTED_KEY, f"public_key must be hex: {exc}")
        keys[entry["keyid"]] = {"public_key_bytes": public_bytes, "identity_id": entry.get("identity_id")}
    return keys


# ================================================================ mandate model + transform

MANDATE_REQUIRED = {"schema_id", "decision_id", "phase_id", "operation", "predecessor", "transform", "invariants", "authority"}
# `closure_manifest_digest` is OPTIONAL and forward-looking: it lets a mandate cryptographically
# bind the raw-bytes SHA-256 of its pre-execution closure manifest (evidence layer 1, including
# permitted_effects_at_execution_C8) inside the signed PAE. It is additive to MANDATE_REQUIRED, not
# a member of it, so an already-signed mandate that predates this field remains valid unchanged
# (adding it to MANDATE_REQUIRED would retroactively invalidate a signed-and-verified mandate,
# which the DSSE-verification stop conditions forbid: "a mandate is edited after signing, in any
# byte"). The binding for a mandate that omits the field is instead carried out-of-band via
# --closure-manifest (see verify_transition), which independently recomputes and reports the exact
# manifest digest so it is never hand-transcribed (see EVD-CLOSURE-017).
MANDATE_ALLOWED = MANDATE_REQUIRED | {
    "schema_version", "program_id", "accepted_work_item", "integration", "segregation_of_duties",
    "closure_manifest_digest",
}
MUTATION_ALLOWED_KEYS = {"path", "from", "to", "rule", "value"}


def validate_mandate(mandate):
    if not isinstance(mandate, dict):
        raise VerifyError(MANDATE_INVALID, "mandate must be a JSON object")
    unknown = set(mandate) - MANDATE_ALLOWED
    if unknown:
        raise VerifyError(MANDATE_INVALID, f"unknown mandate fields: {sorted(unknown)}")
    missing = MANDATE_REQUIRED - set(mandate)
    if missing:
        raise VerifyError(MANDATE_INVALID, f"missing mandate fields: {sorted(missing)}")
    if mandate.get("schema_id") != "bopen.phase-completion-mandate":
        raise VerifyError(MANDATE_INVALID, "unexpected schema_id")
    predecessor = mandate["predecessor"]
    if not isinstance(predecessor, dict) or "schedule_digest" not in predecessor:
        raise VerifyError(MANDATE_INVALID, "predecessor.schedule_digest required")
    transform = mandate["transform"]
    if not isinstance(transform, dict) or not isinstance(transform.get("permitted_mutations"), list):
        raise VerifyError(MANDATE_INVALID, "transform.permitted_mutations must be a list")
    if not transform["permitted_mutations"]:
        raise VerifyError(MANDATE_INVALID, "transform has no permitted mutations")
    for mutation in transform["permitted_mutations"]:
        if not isinstance(mutation, dict) or "path" not in mutation:
            raise VerifyError(MANDATE_INVALID, "each mutation needs a path")
        extra = set(mutation) - MUTATION_ALLOWED_KEYS
        if extra:
            raise VerifyError(MANDATE_INVALID, f"unknown mutation keys: {sorted(extra)}")
    if not isinstance(mandate["invariants"], dict):
        raise VerifyError(MANDATE_INVALID, "invariants must be an object")
    authority = mandate["authority"]
    if not isinstance(authority, dict):
        raise VerifyError(MANDATE_INVALID, "authority must be an object")
    for field in ("required_role", "required_action", "effective_at"):
        if field not in authority:
            raise VerifyError(MANDATE_INVALID, f"authority.{field} required")
    return mandate


def _entry(schedule, schedule_id):
    for item in schedule.get("entries", []):
        if isinstance(item, dict) and item.get("schedule_id") == schedule_id:
            return item
    raise VerifyError(MANDATE_INVALID, f"schedule entry not found: {schedule_id}")


def _resolve_phase_field(path):
    parts = path.split(".")
    if len(parts) != 3 or parts[0] != "phases":
        raise VerifyError(MANDATE_INVALID, f"unsupported mutation path: {path}")
    return parts[1], parts[2]


def recompute_successor(predecessor, mandate):
    """Pure function: successor = transform(predecessor). No I/O, no clock."""
    validate_mandate(mandate)
    successor = json.loads(json.dumps(predecessor))  # structural deep copy
    effective_at = mandate["authority"]["effective_at"]
    for mutation in mandate["transform"]["permitted_mutations"]:
        schedule_id, field = _resolve_phase_field(mutation["path"])
        entry = _entry(successor, schedule_id)
        if "to" in mutation:
            if "from" in mutation and entry.get(field) != mutation["from"]:
                raise VerifyError(
                    SUCCESSOR_MISMATCH,
                    f"{schedule_id}.{field} is {entry.get(field)!r}, mandate expects {mutation['from']!r}",
                )
            entry[field] = mutation["to"]
        elif mutation.get("rule") == "COPY_MANDATE_EFFECTIVE_TIME":
            entry[field] = effective_at
        elif "value" in mutation:
            entry[field] = mutation["value"]
        else:
            raise VerifyError(MANDATE_INVALID, f"mutation has neither to/rule/value: {mutation['path']}")
    _enforce_invariants(successor, mandate)
    return successor


def _enforce_invariants(successor, mandate):
    for key, expected in mandate["invariants"].items():
        if not key.startswith("phases."):
            continue
        schedule_id, field = _resolve_phase_field(key)
        actual = _entry(successor, schedule_id).get(field)
        if actual != expected:
            raise VerifyError(INVARIANT_VIOLATION, f"invariant {key} expected {expected!r}, got {actual!r}")


# ================================================================ authority / trust resolution

def _authority_identity(mandate, signer_keyid, trust_root, identity_register, verification_time, revocations):
    keys = _trust_keys(trust_root)
    identity_id = keys[signer_keyid].get("identity_id")
    if identity_id is None:
        raise VerifyError(UNTRUSTED_KEY, f"trust key {signer_keyid!r} is not bound to an identity")

    revocations = revocations or {}
    if signer_keyid in set(revocations.get("revoked_keyids", [])):
        raise VerifyError(REVOKED, f"key {signer_keyid!r} is revoked")
    if mandate["decision_id"] in set(revocations.get("revoked_decision_ids", [])):
        raise VerifyError(REVOKED, f"decision {mandate['decision_id']!r} is revoked")

    identity = _lookup_identity(identity_register, identity_id)
    if identity.get("status") != "approved":
        raise VerifyError(AUTHORITY_DENIED, f"identity {identity_id!r} is not approved")
    required_role = mandate["authority"]["required_role"]
    required_action = mandate["authority"]["required_action"]
    if required_role not in identity.get("authority_roles", []):
        raise VerifyError(AUTHORITY_DENIED, f"identity lacks required role {required_role!r}")
    if required_action not in identity.get("action_ids", []):
        raise VerifyError(AUTHORITY_DENIED, f"identity lacks required action {required_action!r}")

    # Validity window and revocation timestamp are compared as ISO-8601 strings supplied by the
    # caller; no wall clock is consulted so verification is reproducible. Lexical string order
    # equals chronological order only when the timestamps are normalized to a single offset
    # (e.g. UTC 'Z' or a shared offset). Callers MUST supply normalized timestamps; the register
    # and mandate in this program use a single fixed offset, satisfying that requirement.
    valid_from = identity.get("valid_from")
    expires_at = identity.get("expires_at")
    if valid_from is not None and verification_time < valid_from:
        raise VerifyError(VALIDITY_EXPIRED, f"verification time {verification_time} precedes valid_from {valid_from}")
    if expires_at is not None and verification_time >= expires_at:
        raise VerifyError(VALIDITY_EXPIRED, f"verification time {verification_time} is at/after expires_at {expires_at}")
    revoked_at = identity.get("revoked_at")
    if revoked_at is not None and verification_time >= revoked_at:
        raise VerifyError(REVOKED, f"identity revoked at {revoked_at}")
    return identity_id


def _lookup_identity(identity_register, identity_id):
    if not isinstance(identity_register, dict):
        raise VerifyError(AUTHORITY_DENIED, "identity register must be a JSON object")
    for entry in identity_register.get("entries", []):
        if isinstance(entry, dict) and entry.get("identity_id") == identity_id:
            return entry
    raise VerifyError(AUTHORITY_DENIED, f"identity {identity_id!r} not found in register")


# ================================================================ closure-manifest binding
#
# The closure manifest (evidence layer 1) is NOT the signed DSSE payload -- it is a broader
# governance artifact (predecessor/successor digests, trust root, permitted_effects_at_execution_C8,
# prohibited_effects) that the mandate's signed subject only partially covers (the schedule-register
# transform). Binding it here is deliberately layered outside the PAE rather than retrofitted into
# it: see MANDATE_ALLOWED's closure_manifest_digest for the forward-looking in-PAE option. This
# gives every mandate -- signed before or after that field existed -- a tool-computed, never
# hand-transcribed manifest digest, closing the exact gap that produced the truncated 63-hex-char
# digest in EVD-CLOSURE-014 (see EVD-CLOSURE-017).

def closure_manifest_sha256(raw_bytes):
    """Raw-bytes SHA-256 of the closure manifest file (not RFC 8785 canonical -- the manifest is a
    plain committed JSON file, not a signed payload, so its binding digest is over its exact
    on-disk bytes, matching how every closure-manifest reference elsewhere in the repo is computed)."""
    return hashlib.sha256(raw_bytes).hexdigest()


def permitted_effects_digest(closure_manifest_obj):
    """RFC 8785 canonical digest of the closure manifest's permitted_effects_at_execution_C8 list,
    so the exact permitted-effects set can be independently and cryptographically re-verified
    without re-hashing the whole manifest (whose free-text _status/_encoding fields are allowed to
    grow footnotes across revisions -- see the manifest's own additive revision-note history)."""
    effects = closure_manifest_obj.get("permitted_effects_at_execution_C8")
    if effects is None:
        return None
    return digest(effects)


def verify_closure_manifest_binding(mandate, closure_manifest_bytes):
    """Independently recompute and report the closure-manifest binding. Returns a dict with
    closure_manifest_sha256 and permitted_effects_digest. Raises CLOSURE_MANIFEST_MISMATCH only
    when the mandate itself declares closure_manifest_digest (the optional in-PAE field) and the
    supplied manifest bytes do not match it -- a mandate that omits the field is not contradicted,
    it simply has no in-PAE claim to check (the binding is then advisory/reporting only)."""
    actual = closure_manifest_sha256(closure_manifest_bytes)
    declared = mandate.get("closure_manifest_digest")
    if declared is not None and declared != actual:
        raise VerifyError(
            CLOSURE_MANIFEST_MISMATCH,
            f"mandate binds closure_manifest_digest {declared}, supplied manifest is {actual}",
        )
    try:
        manifest_obj = parse_strict(closure_manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, VerifyError) as exc:
        raise VerifyError(CLOSURE_MANIFEST_MISMATCH, f"closure manifest is not valid JSON: {exc}")
    return {
        "closure_manifest_sha256": actual,
        "permitted_effects_digest": permitted_effects_digest(manifest_obj),
    }


# ================================================================ verify (core)

def verify_transition(
    predecessor,
    proposed_successor,
    envelope,
    trust_root,
    identity_register,
    verification_time,
    consumed=None,
    revocations=None,
    closure_manifest_bytes=None,
):
    """Verify that `proposed_successor` is exactly the transition authorized by the signed
    mandate `envelope` applied to `predecessor`. Returns a result dict with a VERIFIED verdict
    and a receipt, or raises VerifyError(reason) with a stable rejection code."""
    consumed = consumed or {}

    mandate, signer_keyid = open_signed_mandate(envelope, trust_root)
    validate_mandate(mandate)
    signer_identity = _authority_identity(
        mandate, signer_keyid, trust_root, identity_register, verification_time, revocations
    )

    current_digest = digest(predecessor)
    if mandate["predecessor"]["schedule_digest"] != current_digest:
        raise VerifyError(
            PREDECESSOR_MISMATCH,
            f"mandate binds predecessor {mandate['predecessor']['schedule_digest']}, supplied is {current_digest}",
        )

    decision_id = mandate["decision_id"]
    recomputed = recompute_successor(predecessor, mandate)
    recomputed_digest = digest(recomputed)
    proposed_digest = digest(proposed_successor)
    if recomputed_digest != proposed_digest:
        raise VerifyError(
            SUCCESSOR_MISMATCH,
            f"proposed successor {proposed_digest} != authorized recomputation {recomputed_digest}",
        )

    closure_manifest_binding = None
    if closure_manifest_bytes is not None:
        closure_manifest_binding = verify_closure_manifest_binding(mandate, closure_manifest_bytes)

    prior = consumed.get(decision_id)
    if prior is not None:
        # Single-use: the only acceptable re-verification is the byte-identical transition.
        if prior.get("predecessor_digest") == current_digest and prior.get("successor_digest") == recomputed_digest:
            outcome = "ALREADY_VERIFIED_EXACT"
        else:
            raise VerifyError(REPLAY_DENIED, f"decision {decision_id} already consumed for a different transition")
    else:
        outcome = "VERIFIED_EXACT"

    receipt = {
        "schema_id": "bopen.phase-transition-verification-receipt",
        "verdict": VERIFIED,
        "outcome": outcome,
        "decision_id": decision_id,
        "operation": mandate["operation"],
        "phase_id": mandate["phase_id"],
        "signer_identity": signer_identity,
        "signer_keyid": signer_keyid,
        "verification_time": verification_time,
        "mandate_digest": digest(mandate),
        "transform_specification_digest": mandate["transform"].get("specification_digest"),
        "predecessor_schedule_digest": current_digest,
        "authorized_successor_schedule_digest": recomputed_digest,
        "proposed_successor_schedule_digest": proposed_digest,
        "closure_manifest_sha256": closure_manifest_binding["closure_manifest_sha256"] if closure_manifest_binding else None,
        "permitted_effects_digest": closure_manifest_binding["permitted_effects_digest"] if closure_manifest_binding else None,
        "note": "advisory verification only; no register mutated, nothing signed or consumed",
    }
    consumed_next = dict(consumed)
    consumed_next.setdefault(
        decision_id, {"predecessor_digest": current_digest, "successor_digest": recomputed_digest}
    )
    return {"verdict": VERIFIED, "outcome": outcome, "receipt": receipt, "consumed": consumed_next}


def _load(path):
    return parse_strict(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Independently verify a human-applied phase transition.")
    parser.add_argument("--predecessor", required=True, help="predecessor schedule register JSON")
    parser.add_argument("--successor", required=True, help="human-proposed successor schedule register JSON")
    parser.add_argument("--mandate", required=True, help="signed DSSE mandate envelope JSON")
    parser.add_argument("--trust-root", required=True, help="trust root JSON (keyid -> public_key, identity_id)")
    parser.add_argument("--identity-register", required=True, help="authority identity register JSON")
    parser.add_argument("--verification-time", required=True, help="ISO-8601 time to evaluate validity at")
    parser.add_argument("--consumed", help="consumed-decisions registry JSON (optional)")
    parser.add_argument("--revocations", help="revocations JSON (optional)")
    parser.add_argument(
        "--closure-manifest",
        help="pre-execution closure manifest JSON (optional); independently recomputes and reports "
             "its raw-bytes SHA-256 and the permitted_effects_at_execution_C8 digest, and enforces "
             "the mandate's closure_manifest_digest when the mandate declares one",
    )
    args = parser.parse_args()
    consumed = _load(args.consumed) if args.consumed and Path(args.consumed).is_file() else {}
    revocations = _load(args.revocations) if args.revocations and Path(args.revocations).is_file() else {}
    closure_manifest_bytes = (
        Path(args.closure_manifest).read_bytes() if args.closure_manifest else None
    )
    try:
        result = verify_transition(
            _load(args.predecessor),
            _load(args.successor),
            _load(args.mandate),
            _load(args.trust_root),
            _load(args.identity_register),
            args.verification_time,
            consumed,
            revocations,
            closure_manifest_bytes,
        )
    except VerifyError as exc:
        print(f"{REJECTED}: {exc.reason}: {exc.message}")
        return 1
    print(f"{result['verdict']}: {result['outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
