"""
bOPEN Python Client SDK — Tenant Context Switching v1.0

Milestone MILE-2.3 (SDK contract).

Governing artifacts:
  - BOPEN-P2-001 section 11.4 (SDK contract and rules)
  - BOPEN-IDP-001 section 13.1 (API contract; headers are untrusted selectors)
  - sdk/headers/HTTP_HEADER_SPEC.md
  - contracts/schemas/context-switch.json

SDK RULES (BOPEN-P2-001 11.4) enforced here:
  - set approved headers consistently;
  - never decode tokens to make authorization decisions;
  - avoid logging tokens;
  - surface typed error codes;
  - support caller-provided idempotency;
  - clear or replace cached context only after a successful response.

The SDK is a transport client. It holds no authorization logic: local role or
tenant state is never trusted, and the access token is treated as an opaque
credential that is never parsed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

CONTEXT_SWITCH_PATH = "/v1/session/context:switch"


class BopenError(Exception):
    """Typed SDK error carrying a stable machine-readable code."""

    def __init__(self, code: str, message: str = "", status: Optional[int] = None):
        super().__init__(message or code)
        self.code = code
        self.status = status

    def __repr__(self) -> str:  # never interpolate credentials into diagnostics
        return f"BopenError(code={self.code!r}, status={self.status!r})"


# Stable public error codes (BOPEN-P2-001 14.3).
ERROR_CODES = (
    "INVALID_REQUEST",
    "UNAUTHENTICATED",
    "FORBIDDEN",
    "NOT_FOUND_OR_NOT_ACCESSIBLE",
    "CONFLICT",
    "STALE_VERSION",
    "CONTEXT_DENIED",
    "DEPENDENCY_UNAVAILABLE",
)

_STATUS_TO_CODE = {
    400: "INVALID_REQUEST",
    401: "UNAUTHENTICATED",
    403: "CONTEXT_DENIED",
    404: "NOT_FOUND_OR_NOT_ACCESSIBLE",
    409: "CONFLICT",
    412: "STALE_VERSION",
    503: "DEPENDENCY_UNAVAILABLE",
}


@dataclass(frozen=True)
class SwitchContextRequest:
    """Request shape frozen by BOPEN-P2-001 section 11.4."""
    tenant_id: str
    idempotency_key: str
    expected_context_id: str | None = None

    def to_body(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "expected_context_id": self.expected_context_id,
            "idempotency_key": self.idempotency_key,
        }


@dataclass(frozen=True)
class TenantContext:
    """
    Response shape frozen by BOPEN-P2-001 section 11.4.

    `access_token` is opaque. The SDK never decodes it and callers must not derive
    authorization decisions from it.
    """
    context_id: str
    tenant_id: str
    membership_id: str
    expires_at: str
    access_token: str | None = None
    delegated_grant_id: str | None = None

    def __repr__(self) -> str:  # keep tokens out of logs and tracebacks
        return (
            f"TenantContext(context_id={self.context_id!r}, tenant_id={self.tenant_id!r}, "
            f"membership_id={self.membership_id!r}, expires_at={self.expires_at!r}, "
            f"access_token=<redacted>)"
        )


class ContextClient:
    """
    Tenant-context extension for the bOPEN client.

    `transport` is any callable accepting (method, url, headers, json_body) and
    returning (status_code, response_dict). Keeping transport injectable means the
    contract tests run with no network access (BOPEN-P2-001 12.6).
    """

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        tenant_id: str,
        transport: Callable[..., Any],
        context_id: Optional[str] = None,
        capability_version: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._auth_token = auth_token
        self.tenant_id = tenant_id
        self.context_id = context_id
        self.capability_version = capability_version
        self._transport = transport

    # -- headers -----------------------------------------------------------------

    def get_headers(self, correlation_id: Optional[str] = None,
                    idempotency_key: Optional[str] = None) -> Dict[str, str]:
        """Approved headers per sdk/headers/HTTP_HEADER_SPEC.md."""
        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "X-Tenant-ID": self.tenant_id,
            "X-Correlation-ID": correlation_id or str(uuid.uuid4()),
        }
        if self.context_id:
            headers["X-Context-ID"] = self.context_id
        if self.capability_version:
            headers["X-Capability-Version"] = self.capability_version
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    # -- commands ----------------------------------------------------------------

    def switch_tenant_context(
        self, request: SwitchContextRequest, correlation_id: Optional[str] = None
    ) -> TenantContext:
        """
        Switch the active tenant context.

        The requested tenant is sent in both the header and the body; the server
        denies any mismatch (BOPEN-P2-001 11.2). Cached context is replaced only
        after a successful response.
        """
        if not request.tenant_id:
            raise BopenError("INVALID_REQUEST", "tenant_id is required")
        if not request.idempotency_key:
            raise BopenError("INVALID_REQUEST", "idempotency_key is required")

        headers = self.get_headers(correlation_id, idempotency_key=request.idempotency_key)
        headers["X-Tenant-ID"] = request.tenant_id   # untrusted selector; server revalidates
        if request.expected_context_id:
            headers["X-Context-ID"] = request.expected_context_id

        status, body = self._transport(
            "POST", f"{self.base_url}{CONTEXT_SWITCH_PATH}", headers, request.to_body()
        )

        if status != 200:
            code = _STATUS_TO_CODE.get(status, "CONTEXT_DENIED")
            if isinstance(body, dict) and body.get("code") in ERROR_CODES:
                code = body["code"]
            raise BopenError(code, status=status)

        try:
            context = TenantContext(
                context_id=body["context_id"],
                tenant_id=body["tenant_id"],
                membership_id=body["membership_id"],
                expires_at=body["expires_at"],
                access_token=body.get("access_token"),
                delegated_grant_id=body.get("delegated_grant_id"),
            )
        except (KeyError, TypeError) as exc:
            raise BopenError("INVALID_REQUEST", "Malformed context response") from exc

        # Replace cached state only after a successful response.
        self.tenant_id = context.tenant_id
        self.context_id = context.context_id
        if context.access_token:
            self._auth_token = context.access_token
        return context

    def clear_context(self) -> None:
        """Drop cached context. Does not itself revoke server-side state."""
        self.context_id = None


def switch_tenant_context(client: ContextClient, request: SwitchContextRequest) -> TenantContext:
    """Module-level form of the frozen SDK signature (BOPEN-P2-001 11.4)."""
    return client.switch_tenant_context(request)
