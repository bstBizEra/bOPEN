/**
 * Gateway server entry point.
 *
 * Binds to 127.0.0.1 by default rather than 0.0.0.0. The kernel currently accepts
 * `BOPEN_ALLOW_UNAUTHENTICATED_IDENTITY_ASSERTION`, under which `POST /v1/contexts` mints an
 * owner token for anyone holding three identifiers, so a gateway listening on every interface
 * would publish that. Widening the bind is a deployment decision and must be explicit.
 */

import { serve } from '@hono/node-server';
import { createGateway } from './app.ts';

const kernelBaseUrl = process.env.BOPEN_KERNEL_BASE_URL;
if (!kernelBaseUrl) {
  console.error(
    'BOPEN_KERNEL_BASE_URL is not set. The gateway refuses to start rather than default to a\n' +
      'kernel address, because a wrong default would proxy tenant traffic somewhere unintended.\n' +
      'Set it, e.g. BOPEN_KERNEL_BASE_URL=http://127.0.0.1:8000',
  );
  process.exit(1);
}

const port = Number(process.env.BOPEN_GATEWAY_PORT ?? 8787);
const hostname = process.env.BOPEN_GATEWAY_HOST ?? '127.0.0.1';

serve({ fetch: createGateway({ kernelBaseUrl }).fetch, port, hostname }, (info) => {
  console.log(`bopen-gateway listening on http://${hostname}:${info.port} -> ${kernelBaseUrl}`);
});
