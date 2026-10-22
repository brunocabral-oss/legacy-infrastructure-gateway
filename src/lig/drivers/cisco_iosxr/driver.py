"""Cisco IOS-XR driver implementation."""

from typing import Any

from lig.credentials.base import CredentialProvider, DeviceCredential
from lig.credentials.environment import EnvironmentCredentialProvider
from lig.drivers.base import InfrastructureDriver
from lig.drivers.cisco_iosxr import commands, parsers
from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile, CapabilityStatus, OperationCapability
from lig.models.device import Device
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor
from lig.models.route import Route, RouteQuery
from lig.transports.base import Transport
from lig.transports.netmiko_transport import NetmikoTransport


class CiscoIOSXRDriver(InfrastructureDriver):
    """Driver for Cisco IOS-XR platforms (e.g. ASR9000, NCS)."""

    def __init__(
        self,
        device: Device,
        transport: Transport | None = None,
        credential_provider: CredentialProvider | None = None,
    ) -> None:
        super().__init__(device)
        self._cred_provider = credential_provider or EnvironmentCredentialProvider()
        if transport is not None:
            self._transport = transport
        else:
            credential: DeviceCredential = self._cred_provider.get_credential(
                device.credential_profile
            )
            self._transport = NetmikoTransport(
                device=device,
                credential=credential,
                device_type="cisco_xr",
            )

    def capabilities(self) -> CapabilityProfile:
        return CapabilityProfile(
            driver="cisco_iosxr",
            platform="cisco_iosxr",
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
                    description="MAC table is not supported on L3 routed IOS-XR platforms",
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
        output: Any = await self._transport.send_command(commands.SHOW_VERSION, use_textfsm=True)
        return parsers.parse_version_output(output, fallback_hostname=self.device.name)

    async def get_interfaces(self) -> list[Interface]:
        output: Any = await self._transport.send_command(
            commands.SHOW_IPV4_INTERFACE_BRIEF, use_textfsm=True
        )
        return parsers.parse_interfaces_brief(output)

    async def get_routes(self, query: RouteQuery) -> list[Route]:
        cmd = commands.format_route_command(destination=query.destination, vrf=query.vrf)
        output: Any = await self._transport.send_command(cmd, use_textfsm=True)
        return parsers.parse_routes_output(output, query=query)

    async def get_arp_table(self) -> list[ArpEntry]:
        output: Any = await self._transport.send_command(commands.SHOW_ARP, use_textfsm=True)
        return parsers.parse_arp_output(output)

    async def get_mac_table(self) -> list[MacEntry]:
        # Declaratively unsupported on IOS-XR L3
        return []

    async def get_neighbors(self) -> list[Neighbor]:
        output: Any = await self._transport.send_command(
            commands.SHOW_LLDP_NEIGHBORS_DETAIL, use_textfsm=True
        )
        return parsers.parse_neighbors_output(output)

    async def get_running_config(self) -> str:
        output: Any = await self._transport.send_command(
            commands.SHOW_RUNNING_CONFIG, use_textfsm=False
        )
        return str(output)

    async def ping(self, request: PingRequest) -> PingResult:
        cmd = commands.format_ping_command(
            destination=request.destination,
            count=request.count,
            source=request.source,
            vrf=request.vrf,
        )
        output: Any = await self._transport.send_command(cmd, use_textfsm=False)
        return parsers.parse_ping_output(str(output), destination=request.destination)

    async def traceroute(self, request: TracerouteRequest) -> TracerouteResult:
        cmd = commands.format_traceroute_command(
            destination=request.destination,
            source=request.source,
            vrf=request.vrf,
        )
        output: Any = await self._transport.send_command(cmd, use_textfsm=False)
        return parsers.parse_traceroute_output(str(output), destination=request.destination)
