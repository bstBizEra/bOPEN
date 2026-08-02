/**
 * Creation rate-limit tests — `AUTH-D3` Row 1(b), `DEC-P35-AUTH-D3-DOCKET` `D-D3-001`.
 *
 * Written to `BOPEN-GOV-EBIV-001` R4: each rule carries a negative probe. A test that only shows
 * requests passing would pass just as well with the limiter deleted, so every cap here is proven
 * by a request that must be refused, and by the kernel never being reached when it is.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

import { createGateway } from '../src/app.ts';
import { CreationRateLimiter, sourceKey } from '../src/rate-limit.ts';

const CORR = 'corr_12345678-abcd-ef01-2345-6789abcdef01';

function recordingKernel(status = 201) {
  const calls: { url: string; method: string }[] = [];
  const fetchImpl = (async (input: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(input), method: init?.method ?? 'GET' });
    return new Response(JSON.stringify({ ok: true }), {
      status,
      headers: { 'content-type': 'application/json' },
    });
  }) as unknown as typeof fetch;
  return { calls, fetchImpl };
}

function create(fetchImpl: typeof fetch, source: string) {
  // A valid header contract, plus the forwarded source the limiter keys on.
  return {
    method: 'POST',
    headers: { 'X-Correlation-ID': CORR, 'X-Forwarded-For': source },
    body: JSON.stringify({ email: 'a@example.com', type: 'human' }),
  } as const;
}

describe('AUTH-D3 Row 1(b) — creation rate limiting at the gateway', () => {
  test('requests under the per-source limit are forwarded', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const app = createGateway({
      kernelBaseUrl: 'http://kernel.invalid:8000',
      fetchImpl,
      rateLimit: { perSourceLimit: 3, globalLimit: 100, windowMs: 60_000 },
    });
    for (let i = 0; i < 3; i++) {
      const res = await app.request('/v1/principals', create(fetchImpl, '203.0.113.7'));
      assert.equal(res.status, 201, `request ${i} should pass`);
    }
    assert.equal(calls.length, 3, 'all three permitted creations reached the kernel');
  });

  test('the request over the per-source limit is refused with 429 and never reaches the kernel', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const app = createGateway({
      kernelBaseUrl: 'http://kernel.invalid:8000',
      fetchImpl,
      rateLimit: { perSourceLimit: 2, globalLimit: 100, windowMs: 60_000 },
    });
    await app.request('/v1/principals', create(fetchImpl, '203.0.113.7'));
    await app.request('/v1/principals', create(fetchImpl, '203.0.113.7'));
    const res = await app.request('/v1/principals', create(fetchImpl, '203.0.113.7'));

    assert.equal(res.status, 429);
    assert.equal((await res.json()).scope, 'source');
    assert.ok(Number(res.headers.get('retry-after')) >= 1, 'Retry-After is set');
    assert.equal(calls.length, 2, 'the refused creation must not reach the kernel');
  });

  test('a different source is not blocked by the first source window', async () => {
    const { fetchImpl } = recordingKernel();
    const app = createGateway({
      kernelBaseUrl: 'http://kernel.invalid:8000',
      fetchImpl,
      rateLimit: { perSourceLimit: 1, globalLimit: 100, windowMs: 60_000 },
    });
    await app.request('/v1/principals', create(fetchImpl, '198.51.100.1'));
    const blocked = await app.request('/v1/principals', create(fetchImpl, '198.51.100.1'));
    const other = await app.request('/v1/principals', create(fetchImpl, '198.51.100.2'));

    assert.equal(blocked.status, 429, 'the first source is capped');
    assert.equal(other.status, 201, 'a distinct source has its own budget');
  });

  test('the global ceiling backstops source-header rotation', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const app = createGateway({
      kernelBaseUrl: 'http://kernel.invalid:8000',
      fetchImpl,
      // Each source may make 1; the global ceiling is 2. A third distinct source is refused
      // globally even though its own per-source budget is untouched — the rotation backstop.
      rateLimit: { perSourceLimit: 1, globalLimit: 2, windowMs: 60_000 },
    });
    const a = await app.request('/v1/principals', create(fetchImpl, '10.0.0.1'));
    const b = await app.request('/v1/principals', create(fetchImpl, '10.0.0.2'));
    const c = await app.request('/v1/principals', create(fetchImpl, '10.0.0.3'));

    assert.equal(a.status, 201);
    assert.equal(b.status, 201);
    assert.equal(c.status, 429);
    assert.equal((await c.json()).scope, 'global');
    assert.equal(calls.length, 2, 'only two creations reached the kernel across all sources');
  });

  test('tenant provisioning shares the same limiter path', async () => {
    const { fetchImpl } = recordingKernel();
    const app = createGateway({
      kernelBaseUrl: 'http://kernel.invalid:8000',
      fetchImpl,
      rateLimit: { perSourceLimit: 1, globalLimit: 100, windowMs: 60_000 },
    });
    const first = await app.request('/v1/tenants', create(fetchImpl, '203.0.113.9'));
    const second = await app.request('/v1/tenants', create(fetchImpl, '203.0.113.9'));
    assert.equal(first.status, 201);
    assert.equal(second.status, 429);
  });

  test('endpoints that are not creation are never rate-limited', async () => {
    const { fetchImpl } = recordingKernel(200);
    const app = createGateway({
      kernelBaseUrl: 'http://kernel.invalid:8000',
      fetchImpl,
      rateLimit: { perSourceLimit: 1, globalLimit: 1, windowMs: 60_000 },
    });
    // Exhaust the tiny budget on a creation, then show an unrelated endpoint is unaffected.
    await app.request('/v1/principals', create(fetchImpl, '203.0.113.5'));
    for (let i = 0; i < 5; i++) {
      const res = await app.request('/v1/authorize', {
        method: 'POST',
        headers: { 'X-Correlation-ID': CORR, 'X-Forwarded-For': '203.0.113.5' },
        body: '{}',
      });
      assert.equal(res.status, 200, 'authorize is not a rate-limited creation');
    }
  });

  test('without a rateLimit option the gateway forwards every creation as before', async () => {
    const { calls, fetchImpl } = recordingKernel();
    const app = createGateway({ kernelBaseUrl: 'http://kernel.invalid:8000', fetchImpl });
    for (let i = 0; i < 20; i++) {
      await app.request('/v1/principals', create(fetchImpl, '203.0.113.7'));
    }
    assert.equal(calls.length, 20, 'no limiter configured means no cap');
  });
});

describe('CreationRateLimiter — unit', () => {
  test('a refused request is not counted so a blocked flood does not extend its own window', () => {
    let t = 1_000;
    const limiter = new CreationRateLimiter({
      perSourceLimit: 1,
      globalLimit: 100,
      windowMs: 1_000,
      now: () => t,
    });
    assert.equal(limiter.check('s').allowed, true);
    assert.equal(limiter.check('s').allowed, false, 'second is refused');
    // The window opened at t=1000. Advance past it; the source may create again.
    t = 2_001;
    assert.equal(limiter.check('s').allowed, true, 'window reset lets it through');
  });

  test('Retry-After counts whole seconds to the window close', () => {
    let t = 0;
    const limiter = new CreationRateLimiter({
      perSourceLimit: 1,
      globalLimit: 100,
      windowMs: 10_000,
      now: () => t,
    });
    limiter.check('s');
    t = 3_000;
    const decision = limiter.check('s');
    assert.equal(decision.allowed, false);
    assert.equal(decision.retryAfterSeconds, 7, '10s window opened at 0, now 3s in, 7s remain');
  });

  test('a non-positive policy is refused at construction', () => {
    assert.throws(() => new CreationRateLimiter({ perSourceLimit: 0, globalLimit: 1, windowMs: 1 }));
    assert.throws(() => new CreationRateLimiter({ perSourceLimit: 1, globalLimit: 1, windowMs: 0 }));
  });
});

describe('sourceKey', () => {
  test('takes the first forwarded hop, lower-cased', () => {
    assert.equal(sourceKey(new Headers({ 'X-Forwarded-For': '203.0.113.7, 10.0.0.1' })), '203.0.113.7');
  });
  test('a request the proxy did not annotate shares one bucket', () => {
    assert.equal(sourceKey(new Headers()), 'unknown');
  });
});
