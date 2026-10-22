"""Operation Service orchestrating policy, capability, execution, and audit."""

import time
from typing import Any, Callable, Coroutine
from uuid import uuid4

from lig.core.audit_service import AuditService
from lig.core.capability_service import CapabilityService
from lig.core.driver_manager import DriverManager
from lig.core.exceptions import LIGException
from lig.core.policy_engine import PolicyEngine
from lig.models.audit import AuditDecision, AuditResult
from lig.models.common import OperationMetadata, ResponseEnvelope


class OperationService:
    """Core orchestrator executing semantic operations across gateway layers."""

    def __init__(
        self,
        driver_manager: DriverManager,
        policy_engine: PolicyEngine,
        capability_service: CapabilityService,
        audit_service: AuditService,
    ) -> None:
        self.driver_manager = driver_manager
        self.policy_engine = policy_engine
        self.capability_service = capability_service
        self.audit_service = audit_service

    async def execute_operation(
        self,
        device_name: str,
        operation: str,
        executor_func: Callable[[Any], Coroutine[Any, Any, Any]],
        source_ip: str = "127.0.0.1",
        actor: str = "anonymous",
        parameters: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> ResponseEnvelope[Any]:
        """Execute a semantic operation through the full gateway pipeline."""
        req_id = request_id or f"req_{uuid4().hex[:12]}"
        start_time = time.perf_counter()
        driver_name = "unknown"
        transport_name = "unknown"

        # 1. Policy validation
        try:
            self.policy_engine.validate_operation(operation)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self.audit_service.record_event(
                request_id=req_id,
                device=device_name,
                operation=operation,
                source_ip=source_ip,
                decision=AuditDecision.DENIED,
                result=AuditResult.ERROR,
                duration_ms=duration_ms,
                actor=actor,
                parameters=parameters,
                error_code="POLICY_DENIED",
                error_message=str(exc),
            )
            raise

        # 2. Driver resolution
        try:
            device, driver = await self.driver_manager.get_driver_for_device(device_name)
            driver_name = driver.__class__.__name__
            transport_name = device.transport.value

            # 3. Capability validation
            self.capability_service.verify_capability(driver, operation)

            # 4. Execution with guardrails (concurrency + timeout)
            data = await self.driver_manager.execute_with_guardrails(
                device_name,
                executor_func(driver),
            )

            duration_ms = int((time.perf_counter() - start_time) * 1000)

            # 5. Audit allowed & success
            self.audit_service.record_event(
                request_id=req_id,
                device=device_name,
                operation=operation,
                source_ip=source_ip,
                decision=AuditDecision.ALLOWED,
                result=AuditResult.SUCCESS,
                duration_ms=duration_ms,
                driver=driver_name,
                transport=transport_name,
                actor=actor,
                parameters=parameters,
            )

            # 6. Response envelope
            metadata = OperationMetadata(
                driver=driver_name,
                transport=transport_name,
                normalized=True,
                duration_ms=duration_ms,
            )

            return ResponseEnvelope[Any](
                request_id=req_id,
                device=device_name,
                operation=operation,
                status="success",
                data=data,
                metadata=metadata,
            )

        except LIGException as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self.audit_service.record_event(
                request_id=req_id,
                device=device_name,
                operation=operation,
                source_ip=source_ip,
                decision=AuditDecision.ALLOWED
                if exc.error_code != "POLICY_DENIED"
                else AuditDecision.DENIED,
                result=AuditResult.ERROR,
                duration_ms=duration_ms,
                driver=driver_name,
                transport=transport_name,
                actor=actor,
                parameters=parameters,
                error_code=exc.error_code,
                error_message=exc.message,
            )
            raise
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            self.audit_service.record_event(
                request_id=req_id,
                device=device_name,
                operation=operation,
                source_ip=source_ip,
                decision=AuditDecision.ALLOWED,
                result=AuditResult.ERROR,
                duration_ms=duration_ms,
                driver=driver_name,
                transport=transport_name,
                actor=actor,
                parameters=parameters,
                error_code="INTERNAL_ERROR",
                error_message=str(exc),
            )
            raise
