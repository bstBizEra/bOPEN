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

/** Headers the gateway never forwards, because a hop-by-hop header is not the client's. */
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

/**
 * Response headers that describe the *upstream* body encoding and must not be copied.
 *
 * `fetch` decompresses the body before we see it. Copying `content-encoding: gzip` labels a
 * plaintext body as compressed, and copying the compressed `content-length` declares a byte
 * count that does not match what we write — which desynchronises a keep-alive connection, so
 * the client reads the start of the next response as the tail of this one.
 */
const BODY_FRAMING = new Set(['content-encoding', 'content-length']);

/**
 * Names listed in a `Connection` header are hop-by-hop for that message (RFC 9110 §7.6.1).
 *
 * The fixed set above catches the standard names. It does not catch `Connection: X-Internal`,
 * which makes `X-Internal` hop-by-hop for this message only. Without this, a header a peer
 * marked as not-for-forwarding gets forwarded.
 */
function hopByHopFor(headers: Headers): Set<string> {
  const dynamic = new Set(HOP_BY_HOP);
  const connection = headers.get('connection');
  if (connection) {
    for (const name of connection.split(',')) {
      const trimmed = name.trim().toLowerCase();
      if (trimmed) dynamic.add(trimmed);
    }
  }
  return dynamic;
}

/**
 * Build the upstream URL so that the caller cannot choose the host.
 *
 * **This is the security-critical function in this file.** The first implementation resolved the
 * request path as a *relative reference* against the kernel base:
 *
 * ```ts
 * new URL(c.req.path + search, kernelBaseUrl)   // DO NOT
 * ```
 *
 * A path beginning `//` is a scheme-relative URL, so `new URL('//evil/x', 'http://kernel:8000')`
 * resolves to `http://evil/x` — the base's authority is discarded entirely. `///evil/x` and
 * `/\evil/x` do the same, the last because WHATWG folds `\` to `/` for special schemes. The base
 * was a default, not a constraint.
 *
 * That made the gateway an unauthenticated open proxy: any caller could select the upstream host,
 * have the client's `Authorization` bearer token forwarded to it, and receive its response body.
 * Header validation did not help, because it checks the *format* of values any anonymous caller
 * can generate. Found by adversarial sweep 2026-07-31 and reproduced against real sockets.
 *
 * The fix is structural rather than a filter: the URL is built **from the base object**, and only
 * `pathname` and `search` are assigned. Assigning `pathname` cannot alter the origin, so no input
 * to this function can move the request off `kernelBaseUrl`. A denylist of dangerous prefixes
 * would have needed to anticipate every encoding; this needs to anticipate none.
 */
export class UpstreamPathEscape extends Error {}

export function buildUpstreamUrl(kernelBaseUrl: string, path: string, search: string): URL {
  const upstream = new URL(kernelBaseUrl);
  const basePath = upstream.pathname.replace(/\/+$/, '');
  upstream.pathname = `${basePath}${path.startsWith('/') ? '' : '/'}${path}`;
  upstream.search = search;

  // Containment check, added after ballot `P35-04R-16` (gemini, REFUTED, 2026-08-01).
  //
  // Assigning `pathname` cannot change the origin, but WHATWG resolves dot segments during the
  // assignment, so `/base` + `/../../admin` yields `/admin` — the configured prefix is escaped.
  //
  // No *request* can reach here with dot segments: the URL parser normalises them before any
  // handler runs, so `createGateway` only ever passes an already-normalised path. The escape is
  // therefore reachable only by calling this exported function directly. That makes it a latent
  // API hazard rather than a live request-path defect — and a latent hazard in an exported
  // function is still worth closing, because the next caller has no way to know.
  if (basePath && !(upstream.pathname === basePath || upstream.pathname.startsWith(`${basePath}/`))) {
    throw new UpstreamPathEscape(
      `resolved path ${upstream.pathname} escapes the configured base path ${basePath}`,
    );
  }
  return upstream;
}

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

    // `new URL(c.req.url).pathname`, not `c.req.path`.
    //
    // Ballot `P35-04R-15` (gemini, REFUTED, 2026-08-01) established that the request target was
    // being transformed before it reached the kernel. Two transformations were conflated in that
    // finding, and only one is ours:
    //
    //   percent-decoding   `c.req.path` runs `decodeURI`, so `/v1/a%2Fb` reached the kernel as
    //                      `/v1/a/b` — a different path, with a segment boundary invented. Fixed
    //                      here: `URL.pathname` preserves the encoding as sent.
    //
    //   dot segments       `/v1/../admin` arrives as `/admin`. This is NOT fixable at this layer:
    //                      the WHATWG URL parser resolves dot segments when the `Request` is
    //                      constructed, before any handler runs. By the time Hono or this code
    //                      sees the target, the original is gone and cannot be recovered.
    //
    // So `P35-04R-15` as worded — "without percent-decoding **or** dot-segment normalisation" —
    // is half fixed and half unachievable here. The proposition must be re-scoped rather than
    // re-asserted; see `EVD-P35-04-MAKER-R2` §6A.5.
    const upstreamUrl = buildUpstreamUrl(
      kernelBaseUrl,
      new URL(c.req.url).pathname,
      new URL(c.req.url).search,
    );

    const requestHopByHop = hopByHopFor(c.req.raw.headers);
    const forwarded = new Headers();
    c.req.raw.headers.forEach((value, name) => {
      if (!requestHopByHop.has(name.toLowerCase())) forwarded.set(name, value);
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

      const responseHopByHop = hopByHopFor(upstream.headers);
      const responseHeaders = new Headers();
      upstream.headers.forEach((value, name) => {
        const lower = name.toLowerCase();
        if (responseHopByHop.has(lower) || BODY_FRAMING.has(lower) || lower === 'set-cookie') {
          return;
        }
        responseHeaders.set(name, value);
      });

      // `Set-Cookie` is the one response header that legitimately repeats, and `Headers.set`
      // would keep only the last. `getSetCookie` returns them all; append preserves each.
      for (const cookie of upstream.headers.getSetCookie?.() ?? []) {
        responseHeaders.append('set-cookie', cookie);
      }

      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: responseHeaders,
      });
    } catch {
      // The failure reason is not returned: it would describe the kernel's network position to a
      // caller meant to see only the gateway.
      //
      // The wording is "could not be reached" rather than "is unreachable" because this catch
      // cannot tell a network failure from a gateway-side fault — a request method `fetch`
      // refuses, for instance, throws here without a socket ever being opened. Asserting a
      // network diagnosis this code has not established would cost an operator time during an
      // incident.
      return c.json({ detail: 'platform kernel could not be reached' }, 502);
    }
  });

  return app;
}
