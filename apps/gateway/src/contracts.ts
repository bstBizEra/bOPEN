/**
 * Zod bindings for the frozen contracts in `contracts/schemas/`.
 *
 * A hand-written Zod schema is a second copy of a frozen contract, and a second copy drifts.
 * The mechanism that stops it is not care, it is `test/contracts.test.ts`, which reads the JSON
 * Schema from disk and asserts that this file's required fields, optional fields and
 * additional-property stance still agree with it. Delete that test and the binding is a comment.
 */

import { z } from 'zod';
import { UUID_SHAPE } from './identifiers.ts';

/**
 * `contracts/schemas/tenant-context.json` v1.0.0 — the validated execution context.
 *
 * Field types are mirrored, not tightened. `tenant_id`, `principal_id` and
 * `active_membership_id` are plain strings in the frozen contract while `context_id` carries
 * `format: uuid`; that asymmetry is the contract's, and narrowing the three loose ones here
 * would decide `D-P35-004` in a file that has no authority to.
 *
 * `.strict()` mirrors `additionalProperties: false`. It matters at a gateway: a kernel response
 * carrying a field the contract does not describe is drift, and the boundary is where that
 * should surface rather than in a client that guesses at it.
 */
export const TenantContext = z
  .object({
    // Shape, not RFC 9562. `z.uuid()` would reject values the kernel accepts, including the
    // examples in HTTP_HEADER_SPEC.md. See the note on `UUID_SHAPE` in `identifiers.ts`.
    context_id: z.string().regex(new RegExp(`^${UUID_SHAPE}$`), 'context_id must be a UUID'),
    principal_id: z.string(),
    tenant_id: z.string(),
    organization_id: z.string().nullable().optional(),
    workspace_id: z.string().nullable().optional(),
    active_membership_id: z.string(),
    roles: z.array(z.string()).optional(),
    scopes: z.array(z.string()).optional(),
    issued_at: z.string().datetime({ offset: true }),
    expires_at: z.string().datetime({ offset: true }),
  })
  .strict();

export type TenantContext = z.infer<typeof TenantContext>;

/** Required property names, kept as data so the binding test can compare them to the schema. */
export const TENANT_CONTEXT_REQUIRED = [
  'principal_id',
  'tenant_id',
  'active_membership_id',
  'context_id',
  'issued_at',
  'expires_at',
] as const;
