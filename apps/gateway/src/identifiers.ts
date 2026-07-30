/**
 * Identifier acceptance for gateway headers.
 *
 * This module deliberately does NOT decide the bOPEN identifier format. `D-P35-004` — whether
 * bOPEN identifiers are bare UUIDs with prefixes existing only at a presentation boundary — is
 * recorded as Proposed in `DEC-P35-DOCKET` §4.2 and has not been ratified. A gateway that
 * accepted only one form would resolve that decision by validation default, which
 * `AGENTS.md` §16 and `DEC-P35-RUNTIME` prohibit.
 *
 * So the rule here mirrors `normalise_id` in the kernel (`api.py`) exactly: accept a bare UUID
 * or the `<prefix>_<uuid>` form, reject anything else. The prefix set is the kernel's, not a
 * wider one — a gateway that accepted prefixes the kernel rejects would move the failure from
 * a 400 at the edge to a 400 one hop deeper, which is the opposite of what a gateway is for.
 */

/** Prefixes the kernel accepts. Mirrors `_PREFIXED_ID` in `api.py`. */
export const ACCEPTED_PREFIXES = ['usr', 'tnt', 'mem', 'ctx', 'corr'] as const;

/**
 * UUID shape, with no version or variant enforcement — deliberately.
 *
 * RFC 9562 constrains the version nibble to 1-8 and the variant nibble to 8/9/a/b, and strict
 * validators (Zod 4's `z.uuid()` among them) enforce both. The kernel does not: `_PREFIXED_ID`
 * matches `[0-9a-fA-F]` throughout and Python's `uuid.UUID()` accepts any hex-shaped value.
 *
 * Matching the stricter rule here would make the gateway reject identifiers the kernel accepts,
 * which is the one thing a validating proxy must never do — it would turn a working request
 * into a 400 at the edge, with the kernel's own behaviour as evidence that the rejection is
 * wrong. It would also reject the documented examples in `HTTP_HEADER_SPEC.md`, whose
 * `tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c` carries variant nibble `5` and is not RFC 9562
 * conformant.
 *
 * Whether bOPEN identifiers should be RFC-conformant UUIDs is a real question and an open one.
 * It belongs with `D-P35-004`, not in a regex in the gateway. Recorded in `README.md` §4.
 */
export const UUID_SHAPE =
  '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}';

const UUID = UUID_SHAPE;

const BARE_UUID = new RegExp(`^${UUID}$`);
const PREFIXED_ID = new RegExp(`^(?:${ACCEPTED_PREFIXES.join('|')})_(${UUID})$`);

/**
 * True when `value` is an identifier the kernel would accept.
 *
 * Note what this does not do: it does not strip the prefix, and callers must not. The header is
 * forwarded verbatim. Normalising here would hand the kernel a value the client never sent and
 * would quietly pick a side in `D-P35-004`.
 */
export function isAcceptableIdentifier(value: string): boolean {
  const candidate = value.trim();
  return BARE_UUID.test(candidate) || PREFIXED_ID.test(candidate);
}
