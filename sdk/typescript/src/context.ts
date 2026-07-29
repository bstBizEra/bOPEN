/**
 * bOPEN TypeScript Client SDK — Tenant Context Switching v1.0
 *
 * Milestone MILE-2.3 (SDK contract).
 *
 * Governing artifacts:
 *   - BOPEN-P2-001 section 11.4 (SDK contract and rules)
 *   - BOPEN-IDP-001 section 13.1 (API contract; headers are untrusted selectors)
 *   - sdk/headers/HTTP_HEADER_SPEC.md
 *   - contracts/schemas/context-switch.json
 *
 * SDK RULES (BOPEN-P2-001 11.4) enforced here:
 *   - set approved headers consistently;
 *   - never decode tokens to make authorization decisions;
 *   - avoid logging tokens;
 *   - surface typed error codes;
 *   - support caller-provided idempotency;
 *   - clear or replace cached context only after a successful response.
 *
 * The SDK is a transport client. It holds no authorization logic: local role or
 * tenant state is never trusted, and the access token is an opaque credential
 * that is never parsed.
 */

export const CONTEXT_SWITCH_PATH = '/v1/session/context:switch';

/** Stable public error codes (BOPEN-P2-001 14.3). */
export type BopenErrorCode =
  | 'INVALID_REQUEST'
  | 'UNAUTHENTICATED'
  | 'FORBIDDEN'
  | 'NOT_FOUND_OR_NOT_ACCESSIBLE'
  | 'CONFLICT'
  | 'STALE_VERSION'
  | 'CONTEXT_DENIED'
  | 'DEPENDENCY_UNAVAILABLE';

export const ERROR_CODES: ReadonlySet<BopenErrorCode> = new Set<BopenErrorCode>([
  'INVALID_REQUEST',
  'UNAUTHENTICATED',
  'FORBIDDEN',
  'NOT_FOUND_OR_NOT_ACCESSIBLE',
  'CONFLICT',
  'STALE_VERSION',
  'CONTEXT_DENIED',
  'DEPENDENCY_UNAVAILABLE',
]);

const STATUS_TO_CODE: Record<number, BopenErrorCode> = {
  400: 'INVALID_REQUEST',
  401: 'UNAUTHENTICATED',
  403: 'CONTEXT_DENIED',
  404: 'NOT_FOUND_OR_NOT_ACCESSIBLE',
  409: 'CONFLICT',
  412: 'STALE_VERSION',
  503: 'DEPENDENCY_UNAVAILABLE',
};

export class BopenError extends Error {
  public readonly code: BopenErrorCode;
  public readonly status?: number;

  constructor(code: BopenErrorCode, message?: string, status?: number) {
    super(message ?? code);
    this.name = 'BopenError';
    this.code = code;
    this.status = status;
  }
}

/** Request shape frozen by BOPEN-P2-001 section 11.4. */
export type SwitchContextRequest = {
  tenantId: string;
  expectedContextId?: string;
  idempotencyKey: string;
};

/** Response shape frozen by BOPEN-P2-001 section 11.4. */
export type TenantContext = {
  contextId: string;
  tenantId: string;
  membershipId: string;
  expiresAt: string;
  /** Opaque credential. Never decoded; never logged. */
  accessToken?: string;
  delegatedGrantId?: string | null;
};

export type TransportResponse = {
  status: number;
  body: Record<string, unknown>;
};

/**
 * Injectable transport so contract tests run with no network access
 * (BOPEN-P2-001 12.6).
 */
export type Transport = (
  method: string,
  url: string,
  headers: Record<string, string>,
  body: Record<string, unknown>,
) => Promise<TransportResponse>;

export interface ContextClientOptions {
  baseUrl: string;
  authToken: string;
  tenantId: string;
  transport: Transport;
  contextId?: string;
  capabilityVersion?: string;
}

export class ContextClient {
  private readonly baseUrl: string;
  private authToken: string;
  private readonly transport: Transport;
  private readonly capabilityVersion?: string;

  public tenantId: string;
  public contextId?: string;

  constructor(options: ContextClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, '');
    this.authToken = options.authToken;
    this.tenantId = options.tenantId;
    this.contextId = options.contextId;
    this.capabilityVersion = options.capabilityVersion;
    this.transport = options.transport;
  }

  /** Approved headers per sdk/headers/HTTP_HEADER_SPEC.md. */
  public getHeaders(correlationId?: string, idempotencyKey?: string): Record<string, string> {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.authToken}`,
      'X-Tenant-ID': this.tenantId,
      'X-Correlation-ID': correlationId ?? crypto.randomUUID(),
    };
    if (this.contextId) {
      headers['X-Context-ID'] = this.contextId;
    }
    if (this.capabilityVersion) {
      headers['X-Capability-Version'] = this.capabilityVersion;
    }
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return headers;
  }

  /**
   * Switch the active tenant context.
   *
   * The requested tenant is sent in both the header and the body; the server
   * denies any mismatch (BOPEN-P2-001 11.2). Cached context is replaced only
   * after a successful response.
   */
  public async switchTenantContext(input: SwitchContextRequest): Promise<TenantContext> {
    if (!input.tenantId) {
      throw new BopenError('INVALID_REQUEST', 'tenantId is required');
    }
    if (!input.idempotencyKey) {
      throw new BopenError('INVALID_REQUEST', 'idempotencyKey is required');
    }

    const headers = this.getHeaders(undefined, input.idempotencyKey);
    headers['X-Tenant-ID'] = input.tenantId; // untrusted selector; server revalidates
    if (input.expectedContextId) {
      headers['X-Context-ID'] = input.expectedContextId;
    }

    const body = {
      tenant_id: input.tenantId,
      expected_context_id: input.expectedContextId ?? null,
      idempotency_key: input.idempotencyKey,
    };

    const response = await this.transport(
      'POST',
      `${this.baseUrl}${CONTEXT_SWITCH_PATH}`,
      headers,
      body,
    );

    if (response.status !== 200) {
      const payloadCode = response.body?.['code'];
      const code: BopenErrorCode =
        typeof payloadCode === 'string' && ERROR_CODES.has(payloadCode as BopenErrorCode)
          ? (payloadCode as BopenErrorCode)
          : (STATUS_TO_CODE[response.status] ?? 'CONTEXT_DENIED');
      throw new BopenError(code, undefined, response.status);
    }

    const payload = response.body;
    const contextId = payload['context_id'];
    const tenantId = payload['tenant_id'];
    const membershipId = payload['membership_id'];
    const expiresAt = payload['expires_at'];

    if (
      typeof contextId !== 'string' ||
      typeof tenantId !== 'string' ||
      typeof membershipId !== 'string' ||
      typeof expiresAt !== 'string'
    ) {
      throw new BopenError('INVALID_REQUEST', 'Malformed context response');
    }

    const accessToken = payload['access_token'];
    const delegatedGrantId = payload['delegated_grant_id'];

    const context: TenantContext = {
      contextId,
      tenantId,
      membershipId,
      expiresAt,
      accessToken: typeof accessToken === 'string' ? accessToken : undefined,
      delegatedGrantId: typeof delegatedGrantId === 'string' ? delegatedGrantId : null,
    };

    // Replace cached state only after a successful response.
    this.tenantId = context.tenantId;
    this.contextId = context.contextId;
    if (context.accessToken) {
      this.authToken = context.accessToken;
    }
    return context;
  }

  /** Drop cached context. Does not itself revoke server-side state. */
  public clearContext(): void {
    this.contextId = undefined;
  }

  /** Keeps opaque credentials out of logs and stack traces. */
  public toJSON(): Record<string, unknown> {
    return {
      baseUrl: this.baseUrl,
      tenantId: this.tenantId,
      contextId: this.contextId,
      authToken: '<redacted>',
    };
  }
}

/** Module-level form of the frozen SDK signature (BOPEN-P2-001 11.4). */
export function switchTenantContext(
  client: ContextClient,
  input: SwitchContextRequest,
): Promise<TenantContext> {
  return client.switchTenantContext(input);
}
