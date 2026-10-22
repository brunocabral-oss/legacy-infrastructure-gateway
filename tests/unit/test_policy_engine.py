"""Unit tests for the PolicyEngine."""

import pytest

from lig.core.exceptions import PolicyDeniedError
from lig.core.policy_engine import PolicyEngine


def test_allowed_operations() -> None:
    engine = PolicyEngine(read_only_mode=True, raw_commands_enabled=False)
    # These operations must succeed without error
    engine.validate_operation("facts.read")
    engine.validate_operation("interfaces.read")
    engine.validate_operation("routes.read")
    engine.validate_operation("arp.read")
    engine.validate_operation("mac.read")
    engine.validate_operation("neighbors.read")
    engine.validate_operation("config.running.read")
    engine.validate_operation("diagnostics.ping")
    engine.validate_operation("diagnostics.traceroute")


def test_unknown_operation_denied() -> None:
    engine = PolicyEngine()
    with pytest.raises(PolicyDeniedError, match="not an authorized semantic operation"):
        engine.validate_operation("unauthorized.custom_operation")


def test_mutation_denied_in_read_only() -> None:
    engine = PolicyEngine(read_only_mode=True)
    with pytest.raises(PolicyDeniedError):
        engine.validate_operation("config.write")


def test_raw_commands_denied_when_disabled() -> None:
    engine = PolicyEngine(raw_commands_enabled=False)
    with pytest.raises(PolicyDeniedError):
        engine.validate_operation("raw.cli_exec")
