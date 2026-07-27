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
from pathlib import Path, PurePosixPath


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
# Closure-execution binding codes. These exist so that verifying a *closure execution* (as opposed
# to verifying a bare schedule transform) fails closed unless the mandate cryptographically binds
# the exact closure manifest, the exact permitted effects, the exact predecessor commit/tree, the
# exact compare-and-swap target, and the exact external revocation/consumed state.
CLOSURE_BINDING_REQUIRED = "CLOSURE_BINDING_REQUIRED"
CLOSURE_BINDING_MALFORMED = "CLOSURE_BINDING_MALFORMED"
CLOSURE_MANIFEST_MISMATCH = "CLOSURE_MANIFEST_MISMATCH"
PERMITTED_EFFECTS_MISMATCH = "PERMITTED_EFFECTS_MISMATCH"
REVOCATION_STATE_MISMATCH = "REVOCATION_STATE_MISMATCH"
CONSUMED_STATE_MISMATCH = "CONSUMED_STATE_MISMATCH"
# Successor-blob binding codes. A closure execution is only meaningfully authorized if the mandate
# names the exact resulting bytes of every file the closure may write. An unresolved placeholder is
# a hard rejection, never a "pending" state that a verifier waves through.
SUCCESSOR_BLOBS_INCOMPLETE = "SUCCESSOR_BLOBS_INCOMPLETE"
SUCCESSOR_BLOBS_UNRESOLVED = "SUCCESSOR_BLOBS_UNRESOLVED"
SUCCESSOR_BLOB_MISMATCH = "SUCCESSOR_BLOB_MISMATCH"
EXECUTION_ROOT_REQUIRED = "EXECUTION_ROOT_REQUIRED"
EXECUTION_PATH_UNSAFE = "EXECUTION_PATH_UNSAFE"


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
# `closure_binding` is OPTIONAL in the schema but MANDATORY in closure-execution verification mode
# (see require_closure_binding). It is deliberately NOT added to MANDATE_REQUIRED: a mandate that
# authorizes a bare schedule transform is a different, narrower thing than one that authorizes a
# closure execution, and forcing the field on the former would retroactively invalidate already
# signed mandates without making anything safer. Safety comes from the *mode*: a caller verifying a
# closure execution MUST pass require_closure_binding=True, and then absence is a hard rejection.
MANDATE_ALLOWED = MANDATE_REQUIRED | {
    "schema_version", "program_id", "accepted_work_item", "integration", "segregation_of_duties",
    "closure_binding",
}
MUTATION_ALLOWED_KEYS = {"path", "from", "to", "rule", "value"}

# Every field below must be present and well-formed for a closure binding to be usable. The
# allow-list is closed: an unknown key is CLOSURE_BINDING_MALFORMED, so a binding cannot smuggle in
# an unchecked field that a reader might mistake for an enforced control.
CLOSURE_BINDING_REQUIRED_KEYS = {
    "closure_manifest_digest",
    "permitted_effects_digest",
    "predecessor_commit",
    "predecessor_tree",
    "target_ref",
    "expected_old",
    "revocation_state_digest",
    "consumed_state_digest",
    "successor_blobs",
}
CLOSURE_BINDING_ALLOWED_KEYS = CLOSURE_BINDING_REQUIRED_KEYS | {"successor_blobs_status"}
_SHA256_HEX_KEYS = {
    "closure_manifest_digest",
    "permitted_effects_digest",
    "revocation_state_digest",
    "consumed_state_digest",
}
_GIT_OID_KEYS = {"predecessor_commit", "predecessor_tree", "expected_old"}


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


# ================================================================ closure-execution binding
#
# A closure execution is broader than the schedule transform the DSSE payload's `transform` field
# describes: it also rewrites a validator, a test file, a signing record and two derived manifests,
# and it lands as one commit that a compare-and-swap then publishes. The signed payload alone
# therefore cannot answer "were exactly these effects, on exactly this base, toward exactly this
# ref, under exactly this revocation/consumed state, what the human authorized?" -- `closure_binding`
# is what makes that question answerable, and require_closure_binding is what makes it unskippable.

def _is_lower_hex(value, length):
    if not isinstance(value, str) or len(value) != length:
        return False
    return all(character in "0123456789abcdef" for character in value)


def git_blob_oid(data):
    """Git blob object id for exact file bytes: sha1(b"blob <len>\\0" + data).

    SHA-1 is used here because that is what a git object id IS in this repository's object format --
    this is content addressing for cross-checking against `git rev-parse HEAD:<path>`, not a
    security primitive, and it is never used to authenticate anything. The security-bearing digests
    in this module are SHA-256 (raw_sha256 / digest)."""
    header = b"blob %d\0" % len(data)
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - git object id, not a security hash


def resolve_execution_path(execution_root, relative_path):
    """Resolve a permitted-effect path inside a bounded execution root.

    Fails closed on absolute paths, drive-qualified paths, and any traversal that would escape the
    root, so a manifest path can never be used to hash a file outside the tree under review."""
    if not isinstance(relative_path, str) or not relative_path:
        raise VerifyError(EXECUTION_PATH_UNSAFE, f"invalid permitted-effect path: {relative_path!r}")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or relative_path.startswith("\\") or ".." in pure.parts:
        raise VerifyError(EXECUTION_PATH_UNSAFE, f"path escapes the execution root: {relative_path!r}")
    if len(relative_path) > 1 and relative_path[1] == ":":
        raise VerifyError(EXECUTION_PATH_UNSAFE, f"drive-qualified path rejected: {relative_path!r}")
    root = Path(execution_root).resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise VerifyError(EXECUTION_PATH_UNSAFE, f"path escapes the execution root: {relative_path!r}")
    return candidate


def validate_successor_blobs(binding, permitted_effects, execution_root, *, required):
    """Bind the exact resulting bytes of every permitted effect.

    In closure-execution mode the successor_blobs map must name EXACTLY the permitted-effect paths
    (no missing path, no extra path), every value must be a 40-character lowercase git object id
    (an `UNRESOLVED` placeholder is rejected, not tolerated), and every bound id must equal the git
    blob id recomputed from the actual bytes on disk under the bounded execution root."""
    blobs = binding["successor_blobs"]
    expected_paths = []
    for effect in permitted_effects:
        if not isinstance(effect, dict) or "path" not in effect:
            raise VerifyError(PERMITTED_EFFECTS_MISMATCH, "permitted effect entry has no path")
        expected_paths.append(effect["path"])
    expected = set(expected_paths)
    if len(expected) != len(expected_paths):
        raise VerifyError(PERMITTED_EFFECTS_MISMATCH, "permitted effects contain duplicate paths")
    actual = set(blobs)

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise VerifyError(
            SUCCESSOR_BLOBS_INCOMPLETE,
            f"successor_blobs must name exactly the {len(expected)} permitted-effect paths; "
            f"missing={missing} extra={extra}",
        )

    unresolved = sorted(path for path, oid in blobs.items() if not _is_lower_hex(oid, 40))
    if unresolved:
        if not required:
            return {"successor_blobs_verified": False, "unresolved_paths": unresolved}
        raise VerifyError(
            SUCCESSOR_BLOBS_UNRESOLVED,
            "closure-execution verification requires every successor blob to be a resolved "
            f"40-character lowercase git object id; unresolved or malformed: {unresolved}",
        )

    if execution_root is None:
        if not required:
            return {"successor_blobs_verified": False, "unresolved_paths": []}
        raise VerifyError(
            EXECUTION_ROOT_REQUIRED,
            "closure-execution verification requires an execution root so each bound successor blob "
            "id can be recomputed from the actual file bytes",
        )

    verified = {}
    for path in sorted(blobs):
        resolved = resolve_execution_path(execution_root, path)
        if not resolved.is_file():
            raise VerifyError(
                SUCCESSOR_BLOB_MISMATCH,
                f"bound successor blob for {path!r} but no such file under the execution root",
            )
        recomputed = git_blob_oid(resolved.read_bytes())
        if recomputed != blobs[path]:
            raise VerifyError(
                SUCCESSOR_BLOB_MISMATCH,
                f"{path}: mandate binds blob {blobs[path]}, actual execution bytes hash to {recomputed}",
            )
        verified[path] = recomputed
    return {"successor_blobs_verified": True, "unresolved_paths": [], "verified_blobs": verified}


def raw_sha256(data):
    """SHA-256 over exact on-disk bytes (not RFC 8785). Closure manifests, revocation registries
    and consumed registries are plain committed files, not signed payloads, so their binding digest
    is over the bytes a reader can independently hash with any tool."""
    return hashlib.sha256(data).hexdigest()


def validate_closure_binding(binding):
    """Structurally validate a mandate's closure_binding. Fails closed on absence of any required
    field, any unknown field, and any malformed digest -- including the near-miss shapes that a
    hand-transcribed value produces (a 63-character digest, an uppercase digest, a truncated OID)."""
    if not isinstance(binding, dict):
        raise VerifyError(CLOSURE_BINDING_MALFORMED, "closure_binding must be a JSON object")
    unknown = set(binding) - CLOSURE_BINDING_ALLOWED_KEYS
    if unknown:
        raise VerifyError(CLOSURE_BINDING_MALFORMED, f"unknown closure_binding fields: {sorted(unknown)}")
    missing = CLOSURE_BINDING_REQUIRED_KEYS - set(binding)
    if missing:
        raise VerifyError(CLOSURE_BINDING_MALFORMED, f"missing closure_binding fields: {sorted(missing)}")
    for key in sorted(_SHA256_HEX_KEYS):
        if not _is_lower_hex(binding[key], 64):
            raise VerifyError(
                CLOSURE_BINDING_MALFORMED,
                f"closure_binding.{key} must be 64 lowercase hex characters, got {binding[key]!r}",
            )
    for key in sorted(_GIT_OID_KEYS):
        if not _is_lower_hex(binding[key], 40):
            raise VerifyError(
                CLOSURE_BINDING_MALFORMED,
                f"closure_binding.{key} must be a 40-character lowercase git object id, got {binding[key]!r}",
            )
    target_ref = binding["target_ref"]
    if not isinstance(target_ref, str) or not target_ref.startswith("refs/"):
        raise VerifyError(
            CLOSURE_BINDING_MALFORMED,
            f"closure_binding.target_ref must be a fully-qualified ref, got {target_ref!r}",
        )
    if not isinstance(binding["successor_blobs"], dict) or not binding["successor_blobs"]:
        raise VerifyError(
            CLOSURE_BINDING_MALFORMED, "closure_binding.successor_blobs must be a non-empty object"
        )
    return binding


def enforce_closure_binding(
    mandate, closure_manifest_bytes, revocation_bytes, consumed_bytes, *, required,
    execution_root=None,
):
    """Enforce the closure binding. When `required` is True (closure-execution verification), a
    missing binding or missing manifest bytes is a hard rejection -- never a silent pass. When it is
    False, a binding that IS present is still fully enforced; only its absence is tolerated."""
    binding = mandate.get("closure_binding")
    if binding is None:
        if required:
            raise VerifyError(
                CLOSURE_BINDING_REQUIRED,
                "closure-execution verification requested but the mandate declares no closure_binding",
            )
        return None
    validate_closure_binding(binding)

    if closure_manifest_bytes is None:
        if required:
            raise VerifyError(
                CLOSURE_BINDING_REQUIRED,
                "closure-execution verification requested but no closure manifest bytes were supplied",
            )
        return {"closure_binding_enforced": False, "reason": "manifest bytes not supplied"}

    actual_manifest_digest = raw_sha256(closure_manifest_bytes)
    if actual_manifest_digest != binding["closure_manifest_digest"]:
        raise VerifyError(
            CLOSURE_MANIFEST_MISMATCH,
            f"mandate binds closure manifest {binding['closure_manifest_digest']}, "
            f"supplied manifest is {actual_manifest_digest}",
        )

    try:
        manifest = parse_strict(closure_manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerifyError(CLOSURE_BINDING_MALFORMED, f"closure manifest is not valid JSON: {exc}")
    effects = manifest.get("permitted_effects_at_execution_C8")
    if effects is None:
        raise VerifyError(
            PERMITTED_EFFECTS_MISMATCH,
            "closure manifest declares no permitted_effects_at_execution_C8",
        )
    # Independent second control. The whole-file digest above already rejects any byte change, but
    # a manifest legitimately accretes free-text revision notes over its life, so the effects list
    # gets its own digest: an attacker who alters WHAT MAY BE WRITTEN is caught by this check even
    # in a future where the whole-file digest is re-issued for an unrelated editorial reason.
    actual_effects_digest = digest(effects)
    if actual_effects_digest != binding["permitted_effects_digest"]:
        raise VerifyError(
            PERMITTED_EFFECTS_MISMATCH,
            f"mandate binds permitted effects {binding['permitted_effects_digest']}, "
            f"supplied manifest's effects are {actual_effects_digest}",
        )

    if revocation_bytes is not None:
        actual = raw_sha256(revocation_bytes)
        if actual != binding["revocation_state_digest"]:
            raise VerifyError(
                REVOCATION_STATE_MISMATCH,
                f"mandate binds revocation state {binding['revocation_state_digest']}, supplied is {actual}",
            )
    elif required:
        raise VerifyError(
            CLOSURE_BINDING_REQUIRED,
            "closure-execution verification requested but no revocation-state bytes were supplied",
        )

    if consumed_bytes is not None:
        actual = raw_sha256(consumed_bytes)
        if actual != binding["consumed_state_digest"]:
            raise VerifyError(
                CONSUMED_STATE_MISMATCH,
                f"mandate binds consumed state {binding['consumed_state_digest']}, supplied is {actual}",
            )
    elif required:
        raise VerifyError(
            CLOSURE_BINDING_REQUIRED,
            "closure-execution verification requested but no consumed-state bytes were supplied",
        )

    successor_blob_result = validate_successor_blobs(
        binding, effects, execution_root, required=required
    )

    return {
        "closure_binding_enforced": True,
        "closure_manifest_digest": actual_manifest_digest,
        "permitted_effects_digest": actual_effects_digest,
        "successor_blobs": successor_blob_result,
        "predecessor_commit": binding["predecessor_commit"],
        "predecessor_tree": binding["predecessor_tree"],
        "target_ref": binding["target_ref"],
        "expected_old": binding["expected_old"],
        "successor_blobs_status": binding.get("successor_blobs_status", "UNSPECIFIED"),
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
    revocation_bytes=None,
    consumed_bytes=None,
    require_closure_binding=False,
    execution_root=None,
):
    """Verify that `proposed_successor` is exactly the transition authorized by the signed
    mandate `envelope` applied to `predecessor`. Returns a result dict with a VERIFIED verdict
    and a receipt, or raises VerifyError(reason) with a stable rejection code."""
    consumed = consumed or {}

    mandate, signer_keyid = open_signed_mandate(envelope, trust_root)
    validate_mandate(mandate)
    # Enforced BEFORE authority resolution and before any digest comparison: if the closure binding
    # is required and absent/malformed/mismatched, no later check should get the chance to produce
    # a VERIFIED-looking verdict.
    closure_binding_result = enforce_closure_binding(
        mandate,
        closure_manifest_bytes,
        revocation_bytes,
        consumed_bytes,
        required=require_closure_binding,
        execution_root=execution_root,
    )
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
        "closure_binding": closure_binding_result,
        "closure_execution_verification": bool(require_closure_binding),
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
        help="pre-execution closure manifest JSON; required with --require-closure-binding",
    )
    parser.add_argument(
        "--execution-root",
        help="directory holding the actual execution bytes; each bound successor blob id is "
             "recomputed from the file at that path (git blob hashing) and must match. Required "
             "with --require-closure-binding. Paths are resolved strictly inside this root.",
    )
    parser.add_argument(
        "--require-closure-binding",
        action="store_true",
        help="closure-execution verification: fail closed unless the mandate's closure_binding is "
             "present, well-formed, and matches the supplied closure manifest, revocation state "
             "and consumed state exactly",
    )
    args = parser.parse_args()
    consumed = _load(args.consumed) if args.consumed and Path(args.consumed).is_file() else {}
    revocations = _load(args.revocations) if args.revocations and Path(args.revocations).is_file() else {}
    closure_manifest_bytes = Path(args.closure_manifest).read_bytes() if args.closure_manifest else None
    # Bound as exact bytes, not as reparsed objects: the digest a human can reproduce with any
    # sha256 tool is the one that must match.
    revocation_bytes = (
        Path(args.revocations).read_bytes()
        if args.revocations and Path(args.revocations).is_file()
        else None
    )
    consumed_bytes = (
        Path(args.consumed).read_bytes()
        if args.consumed and Path(args.consumed).is_file()
        else None
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
            revocation_bytes,
            consumed_bytes,
            args.require_closure_binding,
            args.execution_root,
        )
    except VerifyError as exc:
        print(f"{REJECTED}: {exc.reason}: {exc.message}")
        return 1
    print(f"{result['verdict']}: {result['outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
