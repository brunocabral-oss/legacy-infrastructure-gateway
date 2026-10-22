"""Contract tests verifying FortiOSDriver."""

from typing import Any

import pytest

from lig.drivers.base import InfrastructureDriver
from lig.drivers.fortios.driver import FortiOSDriver
from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile, CapabilityStatus
from lig.models.device import Device, DevicePlatform, DeviceTransport
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.route import Route, RouteQuery
from lig.transports.base import Transport


class SimulatedFortiOSTransport(Transport):
    """Simulated transport for FortiOS."""

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        if "get system status" in command:
            return (
                "Version: FortiGate-60D v5.4.10,build1670,180709 (GA)\n"
                "Serial-Number: FGT60D4614041234\n"
                "Hostname: CAGE-FW\n"
            )
        elif "get system interface" in command:
            return (
                "==[ internal ]\n"
                "        name: internal   mode: static   "
                "ip: 192.168.200.138 255.255.255.0   status: up\n"
            )
        elif "get router info routing-table" in command:
            return [
                {
                    "type": "S*",
                    "destination": "0.0.0.0/0",
                    "distance": "10",
                    "metric": "0",
                    "gateway": "192.168.200.1",
                    "interface": "wan1",
                }
            ]
        elif "get system arp" in command:
            return [
                {
                    "ip_address": "192.168.200.1",
                    "age": "0",
                    "mac_address": "00:50:56:88:fe:01",
                    "interface": "wan1",
                }
            ]
        elif "show full-configuration" in command:
            return "# FortiGate configuration\n"
        elif "ping" in command:
            return (
                "5 packets transmitted, 5 packets received, 0% packet loss\n"
                "round-trip min/avg/max = 1.0/1.1/1.2 ms\n"
            )
        elif "traceroute" in command:
            return " 1  192.168.200.1  1.123 ms\n"
        return ""


@pytest.fixture
def fortios_device() -> Device:
    return Device(
        name="CAGE",
        host="192.168.200.138",
        platform=DevicePlatform.FORTIOS,
        transport=DeviceTransport.SSH,
    )


@pytest.mark.asyncio
async def test_fortios_contract(fortios_device: Device) -> None:
    transport = SimulatedFortiOSTransport()
    driver: InfrastructureDriver = FortiOSDriver(device=fortios_device, transport=transport)

    # Capabilities
    caps = driver.capabilities()
    assert isinstance(caps, CapabilityProfile)
    assert caps.driver == "fortios"
    assert caps.is_supported("facts.read")
    assert caps.is_supported("routes.read")
    assert caps.capabilities["mac.read"].status == CapabilityStatus.UNSUPPORTED
    assert not caps.is_supported("mac.read")

    # Facts
    facts = await driver.get_facts()
    assert isinstance(facts, DeviceFacts)
    assert facts.hostname == "CAGE-FW"
    assert facts.vendor == "Fortinet"
    assert facts.model == "FortiGate-60D"
    assert facts.os_version == "v5.4.10"

    # Interfaces
    interfaces = await driver.get_interfaces()
    assert len(interfaces) == 1
    assert isinstance(interfaces[0], Interface)
    assert interfaces[0].name == "internal"

    # Routes
    routes = await driver.get_routes(RouteQuery())
    assert len(routes) == 1
    assert isinstance(routes[0], Route)
    assert routes[0].prefix == "0.0.0.0/0"
    assert routes[0].next_hop == "192.168.200.1"

    # ARP
    arp = await driver.get_arp_table()
    assert len(arp) == 1
    assert isinstance(arp[0], ArpEntry)
    assert arp[0].ip_address == "192.168.200.1"

    # Ping
    ping_res = await driver.ping(PingRequest(destination="192.168.200.1"))
    assert isinstance(ping_res, PingResult)
    assert ping_res.packets_received == 5

    # Traceroute
    trace_res = await driver.traceroute(TracerouteRequest(destination="192.168.200.1"))
    assert isinstance(trace_res, TracerouteResult)
