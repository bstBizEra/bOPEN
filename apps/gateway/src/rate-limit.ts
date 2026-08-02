/**
 * Creation rate limiting at the gateway edge — `AUTH-D3` Row 1(b).
 *
 * `DEC-P35-AUTH-D3-DOCKET` `D-D3-001` Row 1(b), operator-disposed 2026-08-02 to the **gateway
 * layer**: cap `POST /v1/principals` and `POST /v1/tenants` at the edge so the abuse and
 * cost-inflation vectors the exposure measured (40 principals + 20 tenants in 5.8s, zero 429s) are
 * bounded before they reach PostgreSQL. This is availability hardening, not a confidentiality
 * control — the blast radius was already tenant-bounded.
 *
 * Two fixed windows, both enforced:
 *
 *   - **per-source** — keyed by the first `X-Forwarded-For` hop, which the trusted upstream proxy
 *     sets. It caps a single source. On its own it is evadable by rotating the forwarded value, so
 *     it does not stand alone;
 *   - **global** — a ceiling across all sources in the window, the backstop for exactly that
 *     rotation. One abuser rotating the source header still cannot exceed the global cap.
 *
 * Fixed window rather than a token bucket: it is the least machinery that caps a burst, and the
 * limiter holds only counters, never request content. In-memory and per-instance — sufficient for
 * a single edge; a shared store is a later concern named in the docket, not built here.
 */

export interface RateLimitPolicy {
  /** Max creation requests from one source within a window. */
  readonly perSourceLimit: number;
  /** Max creation requests across all sources within a window — the backstop against source rotation. */
  readonly globalLimit: number;
  /** Window length in milliseconds. */
  readonly windowMs: number;
  /** Injectable clock; defaults to `Date.now`. Tests supply a deterministic one. */
  readonly now?: () => number;
}

export interface RateLimitDecision {
  readonly allowed: boolean;
  /** Which ceiling refused, when refused. */
  readonly scope?: 'source' | 'global';
  /** Seconds until the offending window resets, for `Retry-After`. */
  readonly retryAfterSeconds?: number;
}

interface Window {
  count: number;
  start: number;
}

/**
 * A fixed-window counter over creation requests. `check` both decides and records: a permitted
 * request is counted, a refused one is not (so a blocked flood does not extend its own window).
 */
export class CreationRateLimiter {
  readonly #perSourceLimit: number;
  readonly #globalLimit: number;
  readonly #windowMs: number;
  readonly #now: () => number;
  readonly #perSource = new Map<string, Window>();
  #global: Window = { count: 0, start: 0 };

  constructor(policy: RateLimitPolicy) {
    if (policy.perSourceLimit < 1 || policy.globalLimit < 1 || policy.windowMs < 1) {
      throw new Error('rate-limit policy must have positive limits and window');
    }
    this.#perSourceLimit = policy.perSourceLimit;
    this.#globalLimit = policy.globalLimit;
    this.#windowMs = policy.windowMs;
    this.#now = policy.now ?? Date.now;
  }

  #retryAfter(windowStart: number, at: number): number {
    // Whole seconds, at least 1, until this window closes.
    return Math.max(1, Math.ceil((windowStart + this.#windowMs - at) / 1000));
  }

  check(source: string): RateLimitDecision {
    const at = this.#now();

    // Roll the global window first, but do NOT count yet — a request refused by the per-source
    // ceiling must not consume global budget, or a single noisy source would exhaust it for all.
    if (at - this.#global.start >= this.#windowMs) {
      this.#global = { count: 0, start: at };
    }

    const src = this.#perSource.get(source);
    const srcWindow = src && at - src.start < this.#windowMs ? src : { count: 0, start: at };

    if (srcWindow.count >= this.#perSourceLimit) {
      return {
        allowed: false,
        scope: 'source',
        retryAfterSeconds: this.#retryAfter(srcWindow.start, at),
      };
    }
    if (this.#global.count >= this.#globalLimit) {
      return {
        allowed: false,
        scope: 'global',
        retryAfterSeconds: this.#retryAfter(this.#global.start, at),
      };
    }

    srcWindow.count += 1;
    this.#perSource.set(source, srcWindow);
    this.#global.count += 1;
    return { allowed: true };
  }
}

/** Paths whose creation this limiter guards. Kept explicit rather than pattern-matched. */
export const RATE_LIMITED_CREATIONS: ReadonlySet<string> = new Set([
  '/v1/principals',
  '/v1/tenants',
]);

/**
 * Whether a request path is a creation the limiter guards — checked against the raw path AND its
 * percent-decoded form.
 *
 * The gateway forwards the raw bytes unchanged; it deliberately does not decode the request target
 * (see `app.ts`). But the kernel percent-decodes before routing, so `POST /v1/%70rincipals` reaches
 * `register_principal` and creates a principal all the same. Classifying only the raw path let that
 * encoded equivalent slip the cap entirely — refuted as `P35-D3b-05` (codex, 2026-08-02, a
 * reproducible bypass). Decoding once for the *classification decision only*, never for forwarding,
 * makes the limiter see the route the kernel will actually run. A single decode matches the kernel's
 * single decode: `/v1/%2570rincipals` decodes once to `/v1/%70rincipals`, which the kernel does not
 * route to creation either.
 */
export function isCreationPath(rawPath: string): boolean {
  if (RATE_LIMITED_CREATIONS.has(rawPath)) return true;
  try {
    return RATE_LIMITED_CREATIONS.has(decodeURIComponent(rawPath));
  } catch {
    // A malformed percent-sequence is not a path the kernel will route to a creation handler.
    return false;
  }
}

/**
 * The source key for a request: the first `X-Forwarded-For` hop, lower-cased and trimmed.
 *
 * Absent the header — a direct caller the proxy did not annotate — every such request shares the
 * key `unknown`, which is deliberately one bucket so a direct flood is capped together rather than
 * each treated as its own source.
 */
export function sourceKey(headers: Headers): string {
  const xff = headers.get('x-forwarded-for');
  if (!xff) return 'unknown';
  const first = xff.split(',')[0]?.trim().toLowerCase();
  return first || 'unknown';
}
