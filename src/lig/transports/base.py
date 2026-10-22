"""Base transport interface for device communication."""

from abc import ABC, abstractmethod
from typing import Any


class Transport(ABC):
    """Abstract transport representing a communication channel to a network device."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish transport session."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close transport session cleanly."""
        ...

    @abstractmethod
    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        """Execute a CLI command and return parsed (or raw) output."""
        ...

    async def __aenter__(self) -> "Transport":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect()
