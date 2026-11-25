"""Linux Host driver implementation using OpenSSH transport."""

from typing import Any

from lig.credentials.base import CredentialProvider, DeviceCredential
from lig.credentials.environment import EnvironmentCredentialProvider
from lig.drivers.base import InfrastructureDriver
from lig.drivers.linux_host import commands, parsers
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
from lig.transports.openssh_transport import OpenSSHTransport


class LinuxHostDriver(InfrastructureDriver):
    """Production driver for Linux host nodes (read-only inspection)."""

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
            self._transport = OpenSSHTransport(
                device=device,
                credential=credential,
            )

    def capabilities(self) -> CapabilityProfile:
        return CapabilityProfile(
            driver="linux_host",
            platform="linux",
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
                "mac.read": OperationCapability(supported=True, status=CapabilityStatus.SUPPORTED),
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
        uname_out: Any = await self._transport.send_command(commands.UNAME_ALL, use_textfsm=False)
        os_release_out: Any = await self._transport.send_command(
            commands.OS_RELEASE, use_textfsm=False
        )
        return parsers.parse_facts(
            str(uname_out), str(os_release_out), fallback_hostname=self.device.name
        )

    async def get_interfaces(self) -> list[Interface]:
        output: Any = await self._transport.send_command(commands.IP_ADDR_JSON, use_textfsm=False)
        return parsers.parse_interfaces(output)

    async def get_routes(self, query: RouteQuery) -> list[Route]:
        cmd = commands.format_route_command(destination=query.destination, vrf=query.vrf)
        output: Any = await self._transport.send_command(cmd, use_textfsm=False)
        return parsers.parse_routes(output, query=query)

    async def get_arp_table(self) -> list[ArpEntry]:
        output: Any = await self._transport.send_command(commands.IP_NEIGH_JSON, use_textfsm=False)
        return parsers.parse_arp_table(output)

    async def get_mac_table(self) -> list[MacEntry]:
        try:
            output: Any = await self._transport.send_command(
                commands.BRIDGE_FDB_JSON, use_textfsm=False
            )
            return parsers.parse_mac_table(output)
        except Exception:
            return []

    async def get_neighbors(self) -> list[Neighbor]:
        try:
            output: Any = await self._transport.send_command(
                commands.LLDPCTL_JSON, use_textfsm=False
            )
            neighbors = parsers.parse_neighbors(output)
            if neighbors:
                return neighbors
        except Exception:
            pass
        try:
            output_text: Any = await self._transport.send_command(
                commands.LLDPCTL_TEXT, use_textfsm=False
            )
            return parsers.parse_neighbors(str(output_text))
        except Exception:
            return []

    async def get_running_config(self) -> str:
        output: Any = await self._transport.send_command(
            commands.NETWORKING_CONFIG_FILES, use_textfsm=False
        )
        return str(output)

    async def ping(self, request: PingRequest) -> PingResult:
        cmd = commands.format_ping_command(
            destination=request.destination,
            count=request.count,
            source=request.source,
            vrf=request.vrf,
            timeout_seconds=request.timeout_seconds,
        )
        output: Any = await self._transport.send_command(cmd, use_textfsm=False)
        return parsers.parse_ping_output(str(output), destination=request.destination)

    async def traceroute(self, request: TracerouteRequest) -> TracerouteResult:
        cmd = commands.format_traceroute_command(
            destination=request.destination,
            source=request.source,
            vrf=request.vrf,
            max_hops=request.max_hops,
            timeout_seconds=request.timeout_seconds,
        )
        output: Any = await self._transport.send_command(cmd, use_textfsm=False)
        return parsers.parse_traceroute_output(str(output), destination=request.destination)
