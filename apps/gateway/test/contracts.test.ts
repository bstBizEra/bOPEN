/**
 * Binding tests between the Zod schemas in `src/contracts.ts` and the frozen JSON Schemas.
 *
 * `BOPEN-GOV-EBIV-001` R2 requires a named test per invariant, and the invariant here is that
 * a hand-written second copy of a contract has not drifted from the contract. These tests read
 * the JSON Schema from disk at run time; they cannot pass by agreeing with a stale copy of it.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { TenantContext, TENANT_CONTEXT_REQUIRED } from '../src/contracts.ts';

const schemaPath = fileURLToPath(
  new URL('../../../contracts/schemas/tenant-context.json', import.meta.url),
);
const schema = JSON.parse(readFileSync(schemaPath, 'utf8')) as {
  required: string[];
  properties: Record<string, unknown>;
  additionalProperties: boolean;
};

const BARE_OR_PREFIXED = '88a11b22-44c3-55d6-77e8-99f00a11b22c';

const VALID = {
  context_id: '99f11a22-33b4-44c5-55d6-66e77f88a99b',
  principal_id: 'usr_88a11b22-44c3-55d6-77e8-99f00a11b22c',
  tenant_id: 'tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c',
  active_membership_id: 'mem_88a11b22-44c3-55d6-77e8-99f00a11b22c',
  issued_at: '2026-07-31T02:24:53+07:00',
  expires_at: '2026-07-31T02:29:53+07:00',
};

describe('tenant-context.json binding', () => {
  test('the Zod required set equals the JSON Schema required set', () => {
    assert.deepEqual(
      [...TENANT_CONTEXT_REQUIRED].sort(),
      [...schema.required].sort(),
      'the frozen contract changed its required fields and this binding did not follow',
    );
  });

  test('every JSON Schema property is known to the Zod schema', () => {
    const declared = Object.keys(schema.properties).sort();
    const known = Object.keys(TenantContext.shape).sort();
    assert.deepEqual(known, declared, 'a property exists in one copy and not the other');
  });

  test('a conforming payload is accepted', () => {
    assert.equal(TenantContext.safeParse(VALID).success, true);
  });

  test('each required field is genuinely required', () => {
    // Removal probe: if any of these stopped being required, this test fails. Asserting only
    // that the valid payload passes would not notice.
    for (const field of TENANT_CONTEXT_REQUIRED) {
      const incomplete: Record<string, unknown> = { ...VALID };
      delete incomplete[field];
      assert.equal(
        TenantContext.safeParse(incomplete).success,
        false,
        `${field} is required by the contract but the Zod schema accepted its absence`,
      );
    }
  });

  test('an unknown property is refused, mirroring additionalProperties: false', () => {
    assert.equal(schema.additionalProperties, false, 'the contract stance changed');
    assert.equal(
      TenantContext.safeParse({ ...VALID, injected: 'value' }).success,
      false,
      'drift in a kernel response should surface at the boundary',
    );
  });

  test('a non-UUID context_id is refused', () => {
    assert.equal(TenantContext.safeParse({ ...VALID, context_id: 'ctx_abc' }).success, false);
  });

  test('a loosely typed identifier is accepted, because the contract types it as a string', () => {
    // Not laxity. `tenant_id` is a plain string in the frozen schema while `context_id` carries
    // format: uuid. Tightening it here would decide D-P35-004 from a file with no authority.
    assert.equal(TenantContext.safeParse({ ...VALID, tenant_id: BARE_OR_PREFIXED }).success, true);
  });

  test('a non-timestamp issued_at is refused', () => {
    assert.equal(TenantContext.safeParse({ ...VALID, issued_at: 'yesterday' }).success, false);
  });
});
