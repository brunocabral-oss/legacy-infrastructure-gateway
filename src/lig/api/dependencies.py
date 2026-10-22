"""Dependency injection containers for FastAPI endpoints."""

from functools import lru_cache

from lig.core.audit_service import AuditService
from lig.core.capability_service import CapabilityService
from lig.core.driver_manager import DriverManager
from lig.core.operation_service import OperationService
from lig.core.policy_engine import PolicyEngine
from lig.drivers.registry import DriverRegistry
from lig.inventory.base import InventoryProvider
from lig.inventory.memory import InMemoryInventory
from lig.settings.config import settings


@lru_cache
def get_inventory_provider() -> InventoryProvider:
    """Return configured inventory provider singleton."""
    return InMemoryInventory()


@lru_cache
def get_driver_registry() -> DriverRegistry:
    """Return driver registry singleton."""
    return DriverRegistry()


@lru_cache
def get_audit_service() -> AuditService:
    """Return audit service singleton."""
    return AuditService()


@lru_cache
def get_policy_engine() -> PolicyEngine:
    """Return policy engine singleton."""
    return PolicyEngine(
        read_only_mode=settings.read_only_mode,
        raw_commands_enabled=settings.raw_commands_enabled,
    )


@lru_cache
def get_capability_service() -> CapabilityService:
    """Return capability service singleton."""
    return CapabilityService()


@lru_cache
def get_driver_manager() -> DriverManager:
    """Return driver manager singleton."""
    return DriverManager(
        inventory=get_inventory_provider(),
        registry=get_driver_registry(),
        concurrency_limit=settings.device_concurrency_limit,
        timeout_seconds=settings.global_timeout_seconds,
    )


def get_operation_service() -> OperationService:
    """Return operation service orchestrator."""
    return OperationService(
        driver_manager=get_driver_manager(),
        policy_engine=get_policy_engine(),
        capability_service=get_capability_service(),
        audit_service=get_audit_service(),
    )
