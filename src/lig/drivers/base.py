"""Abstract Base Class defining the InfrastructureDriver contract."""

from abc import ABC, abstractmethod

from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile
from lig.models.device import Device
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor
from lig.models.route import Route, RouteQuery


class InfrastructureDriver(ABC):
    """Abstract interface that all platform drivers must implement.

    Drivers normalize vendor CLI/API responses into standard Pydantic models.
    They must never return raw unparsed output.
    """

    def __init__(self, device: Device) -> None:
        self.device = device

    @abstractmethod
    def capabilities(self) -> CapabilityProfile:
        """Return the capability profile declaring what this driver supports."""
        ...

    @abstractmethod
    async def get_facts(self) -> DeviceFacts:
        """Retrieve system facts (hostname, vendor, model, os_version, serial, uptime)."""
        ...

    @abstractmethod
    async def get_interfaces(self) -> list[Interface]:
        """Retrieve all interfaces with administrative and operational state."""
        ...

    @abstractmethod
    async def get_routes(self, query: RouteQuery) -> list[Route]:
        """Retrieve routing table entries matching optional query filters."""
        ...

    @abstractmethod
    async def get_arp_table(self) -> list[ArpEntry]:
        """Retrieve ARP resolution table entries."""
        ...

    @abstractmethod
    async def get_mac_table(self) -> list[MacEntry]:
        """Retrieve MAC forwarding table entries."""
        ...

    @abstractmethod
    async def get_neighbors(self) -> list[Neighbor]:
        """Retrieve LLDP / CDP neighbor discovery entries."""
        ...

    @abstractmethod
    async def get_running_config(self) -> str:
        """Retrieve sanitized running configuration text."""
        ...

    @abstractmethod
    async def ping(self, request: PingRequest) -> PingResult:
        """Execute ping diagnostic."""
        ...

    @abstractmethod
    async def traceroute(self, request: TracerouteRequest) -> TracerouteResult:
        """Execute traceroute diagnostic."""
        ...
