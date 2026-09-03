"""Opt-in tenant context for shared copilot graphs."""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from collections.abc import Iterator, Mapping


_TENANT_ID = ContextVar("copilot_sdk_tenant_id", default="default")
_TENANT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True)
class TenantConfig:
    """Tenant isolation settings.

    Isolation is disabled by default so existing single-tenant deployments
    retain their historical behavior.  The context still resolves to the
    stable ``default`` tenant in that mode.
    """

    enabled: bool = False
    header_name: str = "X-Tenant-Id"
    default_tenant: str = "default"

    @classmethod
    def load(cls, env: Mapping[str, str] | None = None) -> "TenantConfig":
        source = os.environ if env is None else env
        enabled = str(source.get("TENANT_ISOLATION_ENABLED", "false")).lower() == "true"
        header_name = str(source.get("TENANT_HEADER", "X-Tenant-Id")).strip() or "X-Tenant-Id"
        default_tenant = str(source.get("DEFAULT_TENANT_ID", "default")).strip() or "default"
        return cls(enabled=enabled, header_name=header_name, default_tenant=validate_tenant_id(default_tenant))

    def tenant_from_headers(self, headers: Mapping[str, str]) -> str:
        raw = headers.get(self.header_name) if self.enabled else None
        return validate_tenant_id(raw.strip()) if raw and raw.strip() else self.default_tenant


def validate_tenant_id(tenant_id: str) -> str:
    value = str(tenant_id).strip()
    if not _TENANT_PATTERN.fullmatch(value):
        raise ValueError("tenant_id must be 1-128 characters: letters, digits, '.', '_', ':', or '-'")
    return value


def current_tenant_id() -> str:
    return _TENANT_ID.get()


def set_tenant_id(tenant_id: str) -> Token[str]:
    return _TENANT_ID.set(validate_tenant_id(tenant_id))


def reset_tenant_id(token: Token[str]) -> None:
    _TENANT_ID.reset(token)


@contextmanager
def tenant_context(tenant_id: str) -> Iterator[str]:
    token = set_tenant_id(tenant_id)
    try:
        yield current_tenant_id()
    finally:
        reset_tenant_id(token)
