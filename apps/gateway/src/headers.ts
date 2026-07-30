/**
 * Zod header contract, bound to `sdk/headers/HTTP_HEADER_SPEC.md` v1.0.
 *
 * The gateway's job is to refuse malformed requests at the edge with the same verdict the
 * kernel would reach, so that a request which survives the gateway fails for a reason of
 * substance rather than of shape. Where this file and the kernel disagree, the kernel is
 * authoritative and this file is a defect.
 */

import { z } from 'zod';
import { isAcceptableIdentifier } from './identifiers.ts';

/**
 * Maximum accepted `X-Correlation-ID` length.
 *
 * 64 is the width of `audit_events.correlation_id` (migration 003), mirrored from
 * `AUDIT_CORRELATION_ID_MAX` in the kernel. It is a storage limit that became a security limit:
 * `BOPEN-AUTHZ-001` requires every allow and deny outcome to be audited, so a value that cannot
 * be written to the audit column produces a decision that cannot be recorded.
 *
 * The kernel rejects an over-length value rather than truncating it, after a security review on
 * 2026-07-30 found silent truncation. The gateway must reject too. A gateway that truncated
 * would hand the kernel a 64-character value that passes, re-introducing exactly the defect
 * that review closed — and it would do so upstream of the audit record, where nothing would
 * show it had happened.
 */
export const CORRELATION_ID_MAX = 64;

const identifier = (header: string) =>
  z
    .string()
    .trim()
    .min(1, `${header} must not be empty`)
    .refine(isAcceptableIdentifier, {
      message: `${header} must be a UUID, optionally prefixed (e.g. tnt_<uuid>)`,
    });

const correlationId = z
  .string()
  .trim()
  .min(1, 'X-Correlation-ID is mandatory (HTTP_HEADER_SPEC.md)')
  .max(
    CORRELATION_ID_MAX,
    `X-Correlation-ID must be at most ${CORRELATION_ID_MAX} characters; it is stored in the audit record and is not truncated`,
  );

/**
 * Headers the gateway validates.
 *
 * `X-Correlation-ID` is mandatory, matching both the spec and the kernel.
 *
 * `X-Tenant-ID` is optional *here* and mandatory in the spec. This is not an oversight and not a
 * relaxation. `WP-P35-03` made the bearer path authoritative: the tenant is taken from the
 * token's signed `tid` claim and `X-Tenant-ID` is not consulted at all. Requiring it at the
 * gateway would force clients to send a value the kernel ignores, and a header that must be
 * sent but is never read is the kind of thing that later gets trusted. The kernel still
 * requires it on the legacy `X-Context-ID` path, and still enforces that requirement itself.
 *
 * `Authorization` is likewise optional here while the spec calls it mandatory. The kernel
 * accepts the legacy `X-Context-ID` path, which predates the token. Enforcing the spec strictly
 * at the gateway would delete that path by validation default — a behaviour change no ratified
 * decision authorizes. The divergence between spec and implementation is real and is recorded
 * as an open item in `README.md` §4 rather than resolved here.
 */
export const RequestHeaders = z.object({
  'x-correlation-id': correlationId,
  'x-tenant-id': identifier('X-Tenant-ID').optional(),
  'x-context-id': identifier('X-Context-ID').optional(),
  'x-capability-version': z
    .string()
    .trim()
    .regex(/^\d+\.\d+\.\d+$/, 'X-Capability-Version must be semantic version x.y.z')
    .optional(),
  authorization: z
    .string()
    .trim()
    .regex(/^[Bb]earer\s+\S+$/, 'Authorization must be a Bearer token')
    .optional(),
});

export type RequestHeaders = z.infer<typeof RequestHeaders>;

/** A field-level rejection, shaped so the response names what was wrong without echoing it. */
export interface HeaderViolation {
  header: string;
  message: string;
}

/**
 * Validate the headers of an incoming request.
 *
 * Absent optional headers are dropped before parsing rather than passed as `undefined`, so that
 * "not sent" and "sent empty" stay distinguishable: an empty `X-Tenant-ID` is a malformed
 * header and is refused, while an absent one is simply the bearer path.
 */
export function validateHeaders(
  headers: Headers,
): { ok: true; value: RequestHeaders } | { ok: false; violations: HeaderViolation[] } {
  const candidate: Record<string, string> = {};
  for (const name of [
    'x-correlation-id',
    'x-tenant-id',
    'x-context-id',
    'x-capability-version',
    'authorization',
  ]) {
    const raw = headers.get(name);
    if (raw !== null) candidate[name] = raw;
  }

  const result = RequestHeaders.safeParse(candidate);
  if (result.success) return { ok: true, value: result.data };

  const violations = result.error.issues.map((issue) => ({
    header: String(issue.path[0] ?? 'headers'),
    message: issue.message,
  }));
  return { ok: false, violations };
}
