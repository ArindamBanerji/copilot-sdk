"""
copilot-sdk — Build compounding intelligence copilots.

The engine is open. The framework is open. The protocols are open.
The domain expertise, calibrated values, and accumulated geometry
are the product.

Quick start:
  from copilot_sdk.protocols import DomainConfig, FactorComputer
  from copilot_sdk.framework.iks_base import compute_iks
  See examples/hello_world/ for a minimal working copilot.

Validated domains: SOC (security operations), S2P (procurement).
Platform claim: +40-55pp Day-1 accuracy lift, domain-agnostic.
"""
from copilot_sdk.scoring.iks_service import IKSService
from copilot_sdk.protocols import (
    DomainConfig, FactorComputer, SourceConnector, ReferralRule
)
__version__ = "0.1.0"
__all__ = ["DomainConfig", "FactorComputer",
           "SourceConnector", "ReferralRule", "IKSService"]
