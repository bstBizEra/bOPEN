/**
 * Header contract tests for `WP-P35-04`.
 *
 * Written to `BOPEN-GOV-EBIV-001` R4: each security-relevant rule carries a negative probe
 * asserting that the violating request is refused. A test that only shows the happy path
 * passes just as well when the mechanism is deleted.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

import { buildUpstreamUrl, createGateway, UpstreamPathEscape } from '../src/app.ts';
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

describe('the caller cannot choose the upstream host', () => {
  // Regression tests for the critical defect found by adversarial sweep on 2026-07-31.
  //
  // The original code did `new URL(path + search, kernelBaseUrl)`, resolving the caller's path as
  // a relative reference. A path starting `//` is scheme-relative, so the base authority was
  // discarded and the caller chose the upstream host — an unauthenticated open proxy that also
  // forwarded the client's bearer token to the attacker's host.
  //
  // Every one of these was reproduced against real sockets before the fix.
  const ESCAPES = [
    '//evil.example/x',
    '///evil.example/x',
    '/\\evil.example/x',
    '//user:pass@evil.example/x',
    '//evil.example:9999/x',
  ];

  for (const path of ESCAPES) {
    test(`${JSON.stringify(path)} cannot move the request off the kernel origin`, () => {
      const url = buildUpstreamUrl('http://kernel.internal:8000', path, '');
      assert.equal(url.origin, 'http://kernel.internal:8000', `escaped to ${url.toString()}`);
      assert.equal(url.hostname, 'kernel.internal');
    });
  }

  test('an ordinary path still reaches the kernel unchanged', () => {
    const url = buildUpstreamUrl('http://kernel.internal:8000', '/v1/authorize', '?a=1');
    assert.equal(url.toString(), 'http://kernel.internal:8000/v1/authorize?a=1');
  });

  test('a base path prefix is preserved rather than discarded', () => {
    // Relative-reference resolution silently dropped a base path. Assigning pathname keeps it.
    const url = buildUpstreamUrl('http://kernel.internal:8000/api', '/v1/authorize', '');
    assert.equal(url.toString(), 'http://kernel.internal:8000/api/v1/authorize');
  });

  test('an escaping path does not reach the kernel as a different host end to end', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('//evil.example/v1/pwn', {
      method: 'GET',
      headers: { 'X-Correlation-ID': CORR, Authorization: 'Bearer secret.token.value' },
    });

    assert.equal(calls.length, 1);
    const target = new URL(calls[0]!.url);
    assert.equal(target.hostname, 'kernel.invalid', `token would have gone to ${target.hostname}`);
  });
});

describe('request target fidelity — after ballots P35-04R-15 and P35-04R-16', () => {
  test('percent-encoding reaches the kernel as sent', async () => {
    // `c.req.path` runs decodeURI, so `/v1/a%2Fb` arrived as `/v1/a/b` — a different path with a
    // segment boundary invented out of an encoded slash. `URL.pathname` preserves it.
    const { calls, fetchImpl } = recordingKernel();
    const gw = gateway(fetchImpl);

    for (const target of ['/v1/a%2Fb', '/v1/caf%C3%A9']) {
      await gw.request(`http://g${target}`, { headers: { 'X-Correlation-ID': CORR } });
    }

    assert.deepEqual(
      calls.map((c) => new URL(c.url).pathname),
      ['/v1/a%2Fb', '/v1/caf%C3%A9'],
    );
  });

  test('KNOWN LIMITATION: dot segments are resolved before this code runs', async () => {
    // Asserts the defective behaviour on purpose. `P35-04R-15` was REFUTED on this and the
    // refutation stands: the WHATWG URL parser resolves dot segments when the Request is
    // constructed, so `/v1/../admin` is already `/admin` before Hono or the gateway sees it. The
    // original target is unrecoverable at this layer.
    //
    // This test exists so the limitation cannot change silently in either direction — if a future
    // runtime stops normalising, this fails and the claim gets revisited rather than drifting.
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('http://g/v1/../admin', {
      headers: { 'X-Correlation-ID': CORR },
    });

    assert.equal(new URL(calls[0]!.url).pathname, '/admin', 'dot-segment behaviour changed');
  });

  test('a path escaping the configured base prefix is refused, not resolved', () => {
    // `P35-04R-16`. Unreachable from a request — the parser normalises first — so this closes a
    // latent hazard in an exported function rather than a live request path.
    assert.throws(
      () => buildUpstreamUrl('http://kernel.internal:8000/base', '/../../admin', ''),
      UpstreamPathEscape,
    );
  });

  test('an ordinary path under a base prefix is still allowed', () => {
    const url = buildUpstreamUrl('http://kernel.internal:8000/base', '/v1/authorize', '');
    assert.equal(url.pathname, '/base/v1/authorize');
  });

  test('the only path normalisation is the URL pathname setter, exactly', async () => {
    // `P35-04R5-17`, replacing `P35-04R4-17` — REFUTED by Codex because `/v1\item` became
    // `/v1/item`, a third transformation the wording had not excluded. It was the sixth
    // proposition in this package to claim more than its test evaluated.
    //
    // Enumerating exclusions cannot close an unbounded negative claim: every round finds one more
    // that WHATWG performs. So the claim is stated positively and bounded by the setter itself —
    // whatever `URL.pathname =` does IS the specification, and this asserts equivalence rather
    // than listing behaviours. A future runtime changing the setter fails this test on both sides
    // at once, which is the point: the claim tracks the mechanism instead of a snapshot of it.
    const BS = String.fromCharCode(92);
    const vectors = [
      '/v1/item', // untouched
      `/v1${BS}item`, // backslash folded — the refutation vector
      `/v1/a${BS}b`,
      '/v1/../admin', // dot segments resolved
      '/v1/%2E%2E/admin', // encoded dot segments resolved
      '/v1/a%2Fb', // encoded slash preserved
      '/v1/caf%C3%A9', // encoded UTF-8 preserved
      '/v1//double', // empty segment preserved
      '/v1/trailing/',
      'v1/no-leading-slash',
    ];

    for (const path of vectors) {
      const reference = new URL('http://kernel.internal:8000');
      reference.pathname = path.startsWith('/') ? path : `/${path}`;

      assert.equal(
        buildUpstreamUrl('http://kernel.internal:8000', path, '').pathname,
        reference.pathname,
        `buildUpstreamUrl transformed ${JSON.stringify(path)} beyond the pathname setter`,
      );
    }
  });

  test('the origin and query survive every path in the normalisation vectors', () => {
    // The other half of `P35-04R5-17`: origin fixed, search verbatim. `P35-04R3-01` claims no
    // request path can move the upstream off the kernel origin; this claims the same for direct
    // calls, which is where the escape hazard lives.
    const BS = String.fromCharCode(92);
    for (const path of ['/v1/item', `/v1${BS}item`, '//evil.example/x', '/v1/../admin']) {
      const url = buildUpstreamUrl('http://kernel.internal:8000', path, '?a=1&b=%20');
      assert.equal(url.origin, 'http://kernel.internal:8000', `origin moved by ${path}`);
      assert.equal(url.search, '?a=1&b=%20', `search altered by ${path}`);
    }
  });
});

describe('response header handling', () => {
  function kernelReturning(headers: Record<string, string>, body = '{"ok":true}') {
    return (async () =>
      new Response(body, { status: 200, headers })) as unknown as typeof fetch;
  }

  test('content-encoding is not copied, because fetch already decompressed the body', async () => {
    const res = await gateway(
      kernelReturning({ 'content-encoding': 'gzip', 'content-type': 'application/json' }),
    ).request('/v1/x', { headers: { 'X-Correlation-ID': CORR } });

    assert.equal(res.headers.get('content-encoding'), null);
  });

  test('the upstream content-length is not copied onto a different body', async () => {
    // Copying it declares a byte count that does not match what we write, which desynchronises
    // a keep-alive connection: the client reads the next response's head as this body's tail.
    const res = await gateway(
      kernelReturning({ 'content-length': '49', 'content-type': 'application/json' }),
    ).request('/v1/x', { headers: { 'X-Correlation-ID': CORR } });

    assert.equal(res.headers.get('content-length'), null);
  });

  test('every Set-Cookie survives, not only the last', async () => {
    const fetchImpl = (async () => {
      const h = new Headers();
      h.append('set-cookie', 'a=1; HttpOnly');
      h.append('set-cookie', 'b=2; Secure');
      return new Response('{}', { status: 200, headers: h });
    }) as unknown as typeof fetch;

    const res = await gateway(fetchImpl).request('/v1/x', {
      headers: { 'X-Correlation-ID': CORR },
    });

    const cookies = res.headers.getSetCookie?.() ?? [];
    assert.equal(cookies.length, 2, `expected both cookies, got ${JSON.stringify(cookies)}`);
  });
});

describe('Connection-named headers are hop-by-hop too', () => {
  test('a header named in Connection is not forwarded', async () => {
    const { calls, fetchImpl } = recordingKernel();
    await gateway(fetchImpl).request('/v1/x', {
      method: 'GET',
      headers: {
        'X-Correlation-ID': CORR,
        Connection: 'close, X-Secret-Hop',
        'X-Secret-Hop': 'leaked',
      },
    });

    // RFC 9110 §7.6.1: names listed in Connection are hop-by-hop for that message. A fixed
    // denylist catches the standard names and misses these.
    assert.equal(calls[0]?.headers['x-secret-hop'], undefined);
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
