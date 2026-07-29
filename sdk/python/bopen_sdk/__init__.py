"""
bOPEN Python Client SDK v1.0
Governed by bOPEN Standard Client HTTP Header Specification
"""

import uuid
from typing import Dict, Optional

from bopen_sdk.context import (  # noqa: F401  (public SDK surface)
    CONTEXT_SWITCH_PATH,
    ERROR_CODES,
    BopenError,
    ContextClient,
    SwitchContextRequest,
    TenantContext,
    switch_tenant_context,
)

__all__ = [
    "BopenClient",
    "ContextClient",
    "SwitchContextRequest",
    "TenantContext",
    "BopenError",
    "ERROR_CODES",
    "CONTEXT_SWITCH_PATH",
    "switch_tenant_context",
]

class BopenClient:
    def __init__(self, base_url: str, auth_token: str, tenant_id: str, context_id: Optional[str] = None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.tenant_id = tenant_id
        self.context_id = context_id

    def get_headers(self, correlation_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "X-Tenant-ID": self.tenant_id,
            "X-Correlation-ID": correlation_id or str(uuid.uuid4())
        }
        if self.context_id:
            headers["X-Context-ID"] = self.context_id
        return headers
