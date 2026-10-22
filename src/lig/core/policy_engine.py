"""Policy engine enforcing fail-closed and read-only invariants."""

from lig.core.exceptions import PolicyDeniedError
from lig.settings.config import settings


class PolicyEngine:
    """Enforces organizational and security policies on gateway operations."""

    ALLOWED_OPERATIONS = {
        "facts.read",
        "interfaces.read",
        "routes.read",
        "arp.read",
        "mac.read",
        "neighbors.read",
        "config.running.read",
        "diagnostics.ping",
        "diagnostics.traceroute",
    }

    def __init__(
        self,
        read_only_mode: bool = settings.read_only_mode,
        raw_commands_enabled: bool = settings.raw_commands_enabled,
    ) -> None:
        self.read_only_mode = read_only_mode
        self.raw_commands_enabled = raw_commands_enabled

    def validate_operation(self, operation: str) -> None:
        """Validate whether an operation is permitted.

        Raises PolicyDeniedError if not allowed.
        """
        # Unknown operations are denied by default
        if operation not in self.ALLOWED_OPERATIONS:
            raise PolicyDeniedError(
                f"Operation '{operation}' is not an authorized semantic operation"
            )

        # Check raw command protection
        if "raw" in operation and not self.raw_commands_enabled:
            raise PolicyDeniedError(
                "Raw command execution is strictly disabled in this gateway environment"
            )

        # Check configuration mutation protection
        if ("config.write" in operation or "mutate" in operation) and self.read_only_mode:
            raise PolicyDeniedError(
                "Configuration mutations are prohibited: gateway is in read-only mode"
            )
