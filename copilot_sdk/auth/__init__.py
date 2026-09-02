"""Opt-in authentication primitives for copilot backends."""
from .config import AuthConfig, load_auth_config
from .dependencies import EXEMPT_PREFIXES, require_auth
from .jwt_utils import create_jwt, derive_role, verify_jwt
from .middleware import AuthMiddleware
from copilot_sdk.backend.auth_router import create_auth_router
__all__ = ["AuthConfig", "AuthMiddleware", "EXEMPT_PREFIXES", "create_auth_router", "create_jwt", "derive_role", "load_auth_config", "require_auth", "verify_jwt"]
