from __future__ import annotations
import time
from typing import Any
import jwt
from .config import AuthConfig

def create_jwt(user_email: str, role: str, groups: list[str], config: AuthConfig) -> str:
    now = int(time.time())
    return str(jwt.encode({"sub": user_email, "role": role, "groups": groups, "iat": now, "exp": now + config.jwt_lifetime_hours * 3600}, config.jwt_secret, algorithm=config.jwt_algorithm))

def verify_jwt(token: str, config: AuthConfig) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
    return dict(payload) if payload.get("sub") and "role" in payload else None

def derive_role(groups: list[str] | None, admin_groups: list[str]) -> str:
    admins = {group.lower() for group in admin_groups if isinstance(group, str)}
    return "admin" if groups and any(isinstance(group, str) and group.lower() in admins for group in groups) else "analyst"
