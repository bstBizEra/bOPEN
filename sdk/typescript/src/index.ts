/**
 * bOPEN TypeScript Client SDK v1.0
 * Governed by bOPEN Standard Client HTTP Header Specification
 */

export {
  CONTEXT_SWITCH_PATH,
  ERROR_CODES,
  BopenError,
  ContextClient,
  switchTenantContext,
} from './context';
export type {
  BopenErrorCode,
  ContextClientOptions,
  SwitchContextRequest,
  TenantContext,
  Transport,
  TransportResponse,
} from './context';

export interface BopenClientOptions {
  baseUrl: string;
  authToken: string;
  tenantId: string;
  contextId?: string;
}

export interface BopenRequestHeaders {
  'Authorization': string;
  'X-Tenant-ID': string;
  'X-Context-ID'?: string;
  'X-Correlation-ID': string;
}

export class BopenClient {
  private baseUrl: string;
  private authToken: string;
  private tenantId: string;
  private contextId?: string;

  constructor(options: BopenClientOptions) {
    this.baseUrl = options.baseUrl;
    this.authToken = options.authToken;
    this.tenantId = options.tenantId;
    this.contextId = options.contextId;
  }

  public getHeaders(correlationId?: string): BopenRequestHeaders {
    return {
      'Authorization': `Bearer ${this.authToken}`,
      'X-Tenant-ID': this.tenantId,
      'X-Context-ID': this.contextId,
      'X-Correlation-ID': correlationId || crypto.randomUUID()
    };
  }
}
