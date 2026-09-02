"""Opt-in SAML/JWT authentication routes for copilot backends."""
from __future__ import annotations
import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from copilot_sdk.auth import create_jwt, derive_role, load_auth_config

log = logging.getLogger(__name__)

def create_auth_router(prefix: str = "/saml", tag: str = "auth") -> APIRouter:
    router = APIRouter(prefix=prefix, tags=[tag])

    def service() -> tuple[Any, Any]:
        from ci_platform.auth.saml import SAMLConfig, SAMLService
        config = load_auth_config()
        return SAMLService(SAMLConfig(sp_entity_id=config.sp_entity_id, sp_acs_url=config.sp_acs_url, idp_entity_id=config.idp_entity_id, idp_sso_url=config.idp_sso_url, idp_x509_cert=config.idp_x509_cert)), config

    @router.get("/metadata")
    async def metadata() -> Response:
        svc, _ = service()
        return Response(content=svc.get_sp_metadata(), media_type="application/xml")

    @router.get("/login")
    async def login() -> RedirectResponse:
        svc, _ = service()
        if not svc.is_configured():
            raise HTTPException(status_code=503, detail="SAML IdP not configured")
        return RedirectResponse(url=svc.create_authn_request()["redirect_url"], status_code=302)

    @router.post("/acs")
    async def acs(request: Request) -> RedirectResponse:
        form_data = await request.form()
        saml_response = form_data.get("SAMLResponse", "")
        if not isinstance(saml_response, str) or not saml_response:
            raise HTTPException(status_code=400, detail="Missing SAMLResponse")
        svc, config = service()
        result = svc.validate_response(saml_response, request_data={"http_host": request.headers.get("host", "localhost:8001"), "script_name": f"{prefix}/acs", "https": "on" if request.url.scheme == "https" else "off", "post_data": {"SAMLResponse": saml_response}})
        if not result.get("valid"):
            raise HTTPException(status_code=401, detail=result.get("error", "SAML validation failed"))
        user_email = result.get("user_email", "")
        if not user_email or user_email == "unknown":
            raise HTTPException(status_code=401, detail="SAML response missing user identity")
        attributes = result.get("attributes", {})
        groups = attributes.get("groups", []) or attributes.get("memberOf", []) or attributes.get("http://schemas.xmlsoap.org/claims/Group", []) or []
        groups = [groups] if isinstance(groups, str) else [group for group in groups if isinstance(group, str)]
        token = create_jwt(user_email, derive_role(groups, config.admin_groups), groups, config)
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="soc_auth_token", value=token, httponly=True, secure=request.url.scheme == "https", samesite="lax", max_age=config.jwt_lifetime_hours * 3600)
        return response

    @router.get("/logout")
    async def logout() -> RedirectResponse:
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie(key="soc_auth_token")
        return response

    @router.get("/status")
    async def status() -> dict[str, Any]:
        svc, config = service()
        return {"saml_enabled": config.saml_enabled, "idp_configured": svc.is_configured(), "sp_entity_id": config.sp_entity_id, "sp_acs_url": config.sp_acs_url}

    return router
