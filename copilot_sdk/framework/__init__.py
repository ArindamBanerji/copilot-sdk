"""
CopilotFramework — domain-agnostic copilot infrastructure.

This package is designed for future extraction to copilot-sdk.
Discipline rules (enforced for clean extraction):
  - No imports from app.domains.*
  - No imports from app.services.* (except other framework modules)
  - No imports from app.routers.*
  - Allowed: gae.*, standard library, other framework modules

Already in copilot_sdk/framework/.
Replace 'from app.framework' with 'from copilot_sdk.framework' if needed.
Add gae as a dependency in copilot-sdk/pyproject.toml.
"""
