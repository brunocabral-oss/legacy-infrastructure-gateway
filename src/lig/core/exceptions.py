"""Domain exceptions for LIG."""


class LIGException(Exception):  # noqa: N818
    """Base exception for all LIG domain errors."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class DeviceNotFoundError(LIGException):
    """Raised when a requested device is not found in the inventory."""

    def __init__(self, device: str) -> None:
        super().__init__(f"Device '{device}' not found in inventory", "DEVICE_NOT_FOUND")
        self.device = device


class DeviceDisabledError(LIGException):
    """Raised when a requested device is disabled."""

    def __init__(self, device: str) -> None:
        super().__init__(f"Device '{device}' is disabled", "DEVICE_DISABLED")
        self.device = device


class CapabilityNotSupportedError(LIGException):
    """Raised when an operation is not supported by the device/driver."""

    def __init__(self, device: str, operation: str, reason: str | None = None) -> None:
        msg = f"Operation '{operation}' is not supported by device '{device}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, "CAPABILITY_NOT_SUPPORTED")
        self.device = device
        self.operation = operation


class PolicyDeniedError(LIGException):
    """Raised when policy engine denies an operation."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Policy violation: {reason}", "POLICY_DENIED")


class DriverNotFoundError(LIGException):
    """Raised when no matching driver is registered for a platform."""

    def __init__(self, platform: str) -> None:
        super().__init__(f"No driver found for platform '{platform}'", "DRIVER_NOT_FOUND")


class DeviceTimeoutError(LIGException):
    """Raised when a device operation times out."""

    def __init__(self, device: str, timeout_seconds: int) -> None:
        super().__init__(
            f"Operation timed out after {timeout_seconds}s on device '{device}'", "TIMEOUT"
        )
        self.device = device


class DeviceConnectionError(LIGException):
    """Raised when failing to establish transport connection with device."""

    def __init__(self, device: str, reason: str) -> None:
        super().__init__(f"Failed to connect to device '{device}': {reason}", "CONNECTION_FAILED")
        self.device = device


class AuthenticationError(LIGException):
    """Raised when device authentication credentials are rejected."""

    def __init__(self, device: str, reason: str = "Invalid credentials") -> None:
        super().__init__(
            f"Authentication failed for device '{device}': {reason}", "AUTHENTICATION_FAILED"
        )
        self.device = device


class ConcurrencyLimitError(LIGException):
    """Raised when too many concurrent operations are targeting the same device."""

    def __init__(self, device: str) -> None:
        super().__init__(
            f"Concurrency limit exceeded for device '{device}'", "CONCURRENCY_LIMIT_EXCEEDED"
        )
        self.device = device
