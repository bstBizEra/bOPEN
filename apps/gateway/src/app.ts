/**
 * bOPEN API gateway — blueprint layer 1 (`BOPEN-ARCH-PLAN-001` §2).
 *
 * `WP-P35-04`, deliverable D-09. The gateway validates the header contract at the edge and
 * forwards to the platform kernel. It is a validating proxy, not a policy point:
 * `AGENTS.md` §9 requires authorization decisions to be made through the approved decision
 * interface, and a gateway that decided anything about tenancy or permission would be a second
 * place where those questions get answered.
 *
 * What it therefore does not do, each for a stated reason:
 *
 *   - It does not rewrite, inject or normalise `X-Tenant-ID`. On the bearer path the kernel
 *     takes the tenant from the token's signed `tid` claim and refuses a header that disagrees
 *     with it (`api.py`, "tenant claim conflict"). A gateway that supplied or corrected the
 *     header would be forging agreement with a claim it cannot verify.
 *   - It does not truncate `X-Correlation-ID`. See `headers.ts`.
 *   - It does not strip identifier prefixes. See `identifiers.ts`.
 *   - It does not mint, refresh or inspect tokens. Verification needs the kernel's key material
 *     and `BOPEN-IDP-001` §12.4 keeps signing asymmetric precisely so that a verifier cannot
 *     also be an issuer.
 */

import { Hono } from 'hono';
import { validateHeaders } from './headers.ts';

export interface GatewayOptions {
  /** Base URL of the platform kernel, e.g. `http://127.0.0.1:8000`. */
  kernelBaseUrl: string;
  /** Injectable for tests. Defaults to global `fetch`. */
  fetchImpl?: typeof fetch;
}

/** Headers the gateway never forwards upstream, because a hop-by-hop header is not the client's. */
const HOP_BY_HOP = new Set([
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
  'host',
]);

export function createGateway(options: GatewayOptions): Hono {
  const app = new Hono();
  const fetchImpl = options.fetchImpl ?? fetch;
  const kernelBaseUrl = options.kernelBaseUrl.replace(/\/+$/, '');

  /**
   * Gateway liveness only.
   *
   * Deliberately not a kernel health probe. If this reported the kernel's health, a green
   * gateway would mean "something answered", and an operator would learn nothing about which
   * component is down from the signal designed to tell them.
   */
  app.get('/gateway/health', (c) => c.json({ status: 'ok', component: 'bopen-gateway' }));

  app.all('/*', async (c) => {
    const validation = validateHeaders(c.req.raw.headers);
    if (!validation.ok) {
      // 400 names the offending header and its rule, and never echoes the value. An error that
      // reflects input is a way to probe what the boundary accepts.
      return c.json(
        {
          detail: 'header contract violation (sdk/headers/HTTP_HEADER_SPEC.md)',
          violations: validation.violations,
        },
        400,
      );
    }

    const upstreamUrl = new URL(c.req.path + (new URL(c.req.url).search ?? ''), kernelBaseUrl);

    const forwarded = new Headers();
    c.req.raw.headers.forEach((value, name) => {
      if (!HOP_BY_HOP.has(name.toLowerCase())) forwarded.set(name, value);
    });

    const method = c.req.method;
    const body =
      method === 'GET' || method === 'HEAD' ? undefined : await c.req.raw.arrayBuffer();

    try {
      const upstream = await fetchImpl(upstreamUrl.toString(), {
        method,
        headers: forwarded,
        body,
      });

      const responseHeaders = new Headers();
      upstream.headers.forEach((value, name) => {
        if (!HOP_BY_HOP.has(name.toLowerCase())) responseHeaders.set(name, value);
      });

      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: responseHeaders,
      });
    } catch {
      // The upstream failure reason is not returned. It would describe the kernel's network
      // position to a caller that is meant to see only the gateway.
      return c.json({ detail: 'platform kernel is unreachable' }, 502);
    }
  });

  return app;
}
