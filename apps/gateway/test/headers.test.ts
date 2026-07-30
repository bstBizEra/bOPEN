/**
 * Header contract tests for `WP-P35-04`.
 *
 * Written to `BOPEN-GOV-EBIV-001` R4: each security-relevant rule carries a negative probe
 * asserting that the violating request is refused. A test that only shows the happy path
 * passes just as well when the mechanism is deleted.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

import { createGateway } from '../src/app.ts';
import { CORRELATION_ID_MAX, validateHeaders } from '../src/headers.ts';
import { isAcceptableIdentifier } from '../src/identifiers.ts';

const TENANT = 'tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c';
const BARE = '88a11b22-44c3-55d6-77e8-99f00a11b22c';
const CORR = 'corr_12345678-abcd-ef01-2345-6789abcdef01';

/** Records what the gateway forwarded, so the tests can assert on it rather than on intent. */
function recordingKernel(status = 200) {
  const calls: { url: string; headers: Record<string, string>; method: string }[] = [];
  const fetchImpl = (async (input: string | URL | Request, init?: RequestInit) => {
    const headers: Record<string, string> = {};
    new Headers(init?.headers).forEach((v, k) => (headers[k] = v));
    calls.push({ url: String(input), headers, method: init?.method ?? 'GET' });
    return new Response(JSON.stringify({ ok: true }), {
      status,
      headers: { 'content-type': 'application/json' },
    });
  }) as unknown as typeof fetch;
  return { calls, fetchImpl };
}

function gateway(fetchImpl?: typeof fetch) {
  return createGateway({ kernelBaseUrl: 'http://kernel.invalid:8000', fetchImpl });
}

describe('X-Correlation-ID', () => {
  test('a request without it is refused at the gateway', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Tenant-ID': TENANT },
    });

    assert.equal(res.status, 400);
    assert.equal(calls.length, 0, 'an invalid request must not reach the kernel');
  });

  test(`a value longer than ${CORRELATION_ID_MAX} is refused, not truncated`, async () => {
    const { calls, fetchImpl } = recordingKernel();
    const overLength = 'c'.repeat(CORRELATION_ID_MAX + 1);

    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': overLength, 'X-Tenant-ID': TENANT },
    });

    assert.equal(res.status, 400);
    assert.equal(calls.length, 0);

    // The specific failure this guards: a gateway that truncated would forward a 64-character
    // value that the kernel accepts, silently undoing the 2026-07-30 security fix upstream of
    // the audit record.
    const body = (await res.json()) as { violations: { header: string; message: string }[] };
    assert.ok(
      body.violations.some((v) => v.header === 'x-correlation-id'),
      'the response must name the offending header',
    );
  });

  test('a value of exactly the maximum is accepted', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const atLimit = 'c'.repeat(CORRELATION_ID_MAX);

    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': atLimit, 'X-Tenant-ID': TENANT },
    });

    assert.equal(res.status, 200);
    assert.equal(calls[0]?.headers['x-correlation-id'], atLimit);
  });

  test('a whitespace-only value is refused', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': '   ', 'X-Tenant-ID': TENANT },
    });

    assert.equal(res.status, 400);
    assert.equal(calls.length, 0);
  });
});

describe('X-Tenant-ID is forwarded verbatim', () => {
  test('the prefixed form reaches the kernel unchanged', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': TENANT },
    });

    // Stripping the prefix here would decide D-P35-004, which is unratified. The kernel must
    // receive exactly what the client sent.
    assert.equal(calls[0]?.headers['x-tenant-id'], TENANT);
  });

  test('the bare UUID form also reaches the kernel unchanged', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': BARE },
    });

    assert.equal(calls[0]?.headers['x-tenant-id'], BARE);
  });

  test('the gateway does not invent the header when it is absent', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, Authorization: 'Bearer abc.def.ghi' },
    });

    // On the bearer path the kernel takes the tenant from the signed `tid` claim and refuses a
    // header that disagrees. A gateway that supplied one would be asserting a tenant it cannot
    // verify.
    assert.equal(calls.length, 1);
    assert.equal(calls[0]?.headers['x-tenant-id'], undefined);
  });

  test('a malformed value is refused before it reaches the kernel', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': 'not-a-uuid' },
    });

    assert.equal(res.status, 400);
    assert.equal(calls.length, 0);
  });

  test('an empty value is refused rather than treated as absent', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': '' },
    });

    assert.equal(res.status, 400, 'sent-but-empty is malformed, not the bearer path');
    assert.equal(calls.length, 0);
  });
});

describe('identifier acceptance mirrors the kernel', () => {
  test('accepts every prefix the kernel accepts', () => {
    for (const prefix of ['usr', 'tnt', 'mem', 'ctx', 'corr']) {
      assert.ok(isAcceptableIdentifier(`${prefix}_${BARE}`), `${prefix}_ must be accepted`);
    }
  });

  test('rejects a prefix the kernel does not accept', () => {
    // A gateway accepting a wider set than the kernel would move the 400 one hop deeper
    // instead of catching it at the edge.
    assert.equal(isAcceptableIdentifier(`org_${BARE}`), false);
  });

  test('rejects a prefixed value whose body is not a UUID', () => {
    assert.equal(isAcceptableIdentifier('tnt_not-a-uuid'), false);
  });

  test('rejects a UUID with trailing content', () => {
    assert.equal(isAcceptableIdentifier(`${BARE}extra`), false);
  });

  test('accepts the documented examples from HTTP_HEADER_SPEC.md verbatim', () => {
    // These are not RFC 9562 conformant: `55d6` and `55d6` carry variant nibble 5, and a strict
    // UUID validator rejects them. The kernel accepts them, so the gateway must. This test
    // exists because Zod 4's z.uuid() enforces the RFC and silently made the gateway stricter
    // than the kernel it fronts — a 400 at the edge for a request the kernel would have served.
    for (const example of [
      'tnt_88a11b22-44c3-55d6-77e8-99f00a11b22c',
      'ctx_99f11a22-33b4-44c5-55d6-66e77f88a99b',
      'corr_12345678-abcd-ef01-2345-6789abcdef01',
    ]) {
      assert.ok(
        isAcceptableIdentifier(example),
        `HTTP_HEADER_SPEC.md documents ${example}; the gateway must not reject its own spec`,
      );
    }
  });
});

describe('other headers', () => {
  test('a non-Bearer Authorization scheme is refused', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, Authorization: 'Basic dXNlcjpwYXNz' },
    });

    assert.equal(res.status, 400);
    assert.equal(calls.length, 0);
  });

  test('a malformed X-Capability-Version is refused', async () => {
    const { fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': TENANT, 'X-Capability-Version': 'v1' },
    });

    assert.equal(res.status, 400);
  });

  test('the violation response does not echo the offending value', async () => {
    const { fetchImpl } = recordingKernel();
    const secret = `tnt_${'S'.repeat(40)}`;
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': secret },
    });

    const text = await res.text();
    assert.equal(res.status, 400);
    assert.ok(!text.includes(secret), 'an error that reflects input is a probe of the boundary');
  });
});

describe('proxy behaviour', () => {
  test('gateway health does not consult the kernel', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const res = await gateway(fetchImpl).request('/gateway/health');

    assert.equal(res.status, 200);
    assert.equal(calls.length, 0, 'a green gateway must not mean "something answered"');
  });

  test('an unreachable kernel is a 502 that does not describe the kernel', async () => {
    const failing = (async () => {
      throw new Error('connect ECONNREFUSED 10.0.0.5:8000');
    }) as unknown as typeof fetch;

    const res = await gateway(failing).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': TENANT },
    });

    assert.equal(res.status, 502);
    const text = await res.text();
    assert.ok(!text.includes('10.0.0.5'), 'the kernel network position must not leak');
  });

  test('the upstream status is passed through rather than reinterpreted', async () => {
    const { fetchImpl } = recordingKernel(403);
    const res = await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': TENANT },
    });

    // A gateway that mapped kernel denials onto its own vocabulary would make a deny
    // indistinguishable from a gateway fault in the audit trail.
    assert.equal(res.status, 403);
  });

  test('the request path and method reach the kernel unchanged', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('/v1/resources/abc', {
      method: 'GET',
      headers: { 'X-Correlation-ID': CORR, 'X-Tenant-ID': TENANT },
    });

    assert.equal(calls[0]?.method, 'GET');
    assert.ok(calls[0]?.url.endsWith('/v1/resources/abc'), `unexpected url ${calls[0]?.url}`);
  });

  test('a hop-by-hop header is not forwarded', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('/v1/authorize', {
      method: 'POST',
      headers: {
        'X-Correlation-ID': CORR,
        'X-Tenant-ID': TENANT,
        Connection: 'keep-alive',
      },
    });

    assert.equal(calls[0]?.headers['connection'], undefined);
  });
});

describe('validateHeaders reports every violation, not the first', () => {
  test('two bad headers produce two violations', () => {
    const result = validateHeaders(
      new Headers({ 'X-Correlation-ID': 'x'.repeat(100), 'X-Tenant-ID': 'nope' }),
    );

    assert.equal(result.ok, false);
    if (result.ok) return;
    assert.equal(result.violations.length, 2, 'a client fixing one at a time is a slow client');
  });
});
