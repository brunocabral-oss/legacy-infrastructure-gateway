"""Mock driver implementation using static fixtures."""

from lig.drivers.base import InfrastructureDriver
from lig.drivers.mock.fixtures import (
    MOCK_ARP_TABLE,
    MOCK_FACTS,
    MOCK_INTERFACES,
    MOCK_MAC_TABLE,
    MOCK_NEIGHBORS,
    MOCK_PING_RESULT,
    MOCK_ROUTES,
    MOCK_RUNNING_CONFIG,
    MOCK_TRACEROUTE_RESULT,
)
from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile, CapabilityStatus, OperationCapability
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor
from lig.models.route import Route, RouteQuery


class MockDriver(InfrastructureDriver):
    """Driver implementation providing canned normalized fixtures for development and tests."""

    def capabilities(self) -> CapabilityProfile:
        return CapabilityProfile(
            driver="mock_driver",
            platform="mock",
            version="0.1.0",
            capabilities={
                "facts.read": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
                "interfaces.read": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
                "routes.read": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
                "arp.read": OperationCapability(supported=True, status=CapabilityStatus.SUPPORTED),
                "mac.read": OperationCapability(
                    supported=False,
                    status=CapabilityStatus.UNSUPPORTED,
                    description="MAC address table not available on this L3 mock platform",
                ),
                "neighbors.read": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
                "config.running.read": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
                "diagnostics.ping": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
                "diagnostics.traceroute": OperationCapability(
                    supported=True, status=CapabilityStatus.SUPPORTED
                ),
            },
        )

    async def get_facts(self) -> DeviceFacts:
        return MOCK_FACTS

    async def get_interfaces(self) -> list[Interface]:
        return MOCK_INTERFACES

    async def get_routes(self, query: RouteQuery) -> list[Route]:
        routes = list(MOCK_ROUTES)
        if query.vrf:
            routes = [r for r in routes if r.vrf.lower() == query.vrf.lower()]
        if query.destination:
            routes = [r for r in routes if query.destination in r.prefix]
        if query.protocol:
            routes = [r for r in routes if r.protocol == query.protocol]
        return routes

    async def get_arp_table(self) -> list[ArpEntry]:
        return MOCK_ARP_TABLE

    async def get_mac_table(self) -> list[MacEntry]:
        return MOCK_MAC_TABLE

    async def get_neighbors(self) -> list[Neighbor]:
        return MOCK_NEIGHBORS

    async def get_running_config(self) -> str:
        return MOCK_RUNNING_CONFIG

    async def ping(self, request: PingRequest) -> PingResult:
        result = MOCK_PING_RESULT.model_copy()
        result.destination = request.destination
        return result

    async def traceroute(self, request: TracerouteRequest) -> TracerouteResult:
        result = MOCK_TRACEROUTE_RESULT.model_copy()
        result.destination = request.destination
        return result
