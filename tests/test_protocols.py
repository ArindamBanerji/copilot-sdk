"""
tests/test_protocols.py — Protocol smoke tests for copilot-sdk.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_domain_config_protocol_importable():
    from copilot_sdk.protocols import DomainConfig
    assert DomainConfig is not None


def test_factor_computer_protocol_importable():
    from copilot_sdk.protocols import FactorComputer
    assert FactorComputer is not None


def test_hello_world_implements_domain_config():
    from copilot_sdk.protocols import DomainConfig
    from examples.hello_world.config import HelloWorldConfig
    cfg = HelloWorldConfig()
    assert isinstance(cfg, DomainConfig)


def test_all_four_protocols_exported():
    import copilot_sdk
    for name in ["DomainConfig", "FactorComputer",
                 "SourceConnector", "ReferralRule"]:
        assert hasattr(copilot_sdk, name), f"copilot_sdk missing: {name}"
