from __future__ import annotations
import os
from typing import Any
from urllib.parse import unquote
from fastapi import HTTPException, Request
from .config import AuthConfig, load_auth_config
from .jwt_utils import verify_jwt

_auth_config: AuthConfig | None = None
EXEMPT_PREFIXES = ("/health", "/saml/", "/docs", "/openapi.json", "/redoc")
ADMIN_PREFIXES = ("/api/admin", "/api/framework", "/api/audit")
MUTATION_PATHS = ("/api/soc/checkpoint/rollback", "/api/soc/scorer/freeze", "/api/soc/scorer/unfreeze", "/api/soc/interventions/rollback", "/api/soc/interventions/threshold", "/api/soc/reset", "/api/admin/reset")

def get_auth_config() -> AuthConfig:
    global _auth_config
    # Reload from the environment so opt-in hosts can change configuration
    # during controlled startup and tests without sharing stale process state.
    _auth_config = load_auth_config()
    return _auth_config

async def require_auth(request: Request | None) -> dict[str, Any] | None:
    config = get_auth_config()
    path = request.url.path if request is not None else ""
    if any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES):
        return None
    if not config.saml_enabled:
        if os.environ.get("SOC_DEMO_MODE", "false").lower() == "true":
            return None
        raise HTTPException(status_code=403, detail="Authentication required. Set SOC_DEMO_MODE=true only for an explicit local demo.")
    path = unquote(path)
    while "//" in path:
        path = path.replace("//", "/")
    if "/.." in path or "/../" in path:
        path = "/" + path.split("/")[-1]
    token = request.cookies.get("soc_auth_token") if request is not None else None
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    claims = verify_jwt(token, config)
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    for prefixes, detail in ((ADMIN_PREFIXES, "Admin access required"), (MUTATION_PATHS, "Admin access required for mutation")):
        if any(path == prefix or path.startswith(prefix + "/") for prefix in prefixes) and claims.get("role") != "admin":
            raise HTTPException(status_code=403, detail=detail)
    return claims
