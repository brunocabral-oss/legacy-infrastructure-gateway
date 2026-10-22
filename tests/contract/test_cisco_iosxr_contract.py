"""Contract tests verifying CiscoIOSXRDriver."""

from typing import Any

import pytest

from lig.drivers.base import InfrastructureDriver
from lig.drivers.cisco_iosxr.driver import CiscoIOSXRDriver
from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile, CapabilityStatus
from lig.models.device import Device, DevicePlatform, DeviceTransport
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.route import Route, RouteQuery
from lig.transports.base import Transport


class SimulatedXRTransport(Transport):
    """Simulated transport for Cisco IOS-XR."""

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        if "show version" in command:
            return [
                {
                    "version": "6.5.3",
                    "hardware": "ASR9K",
                    "serial": "FOX12345678",
                    "hostname": "ASR-LAB",
                }
            ]
        elif "show ipv4 interface brief" in command:
            return [
                {
                    "interface": "GigabitEthernet0/0/0/0",
                    "ip_address": "192.168.100.10",
                    "status": "Up",
                    "proto": "Up",
                }
            ]
        elif "show route" in command:
            return [
                {
                    "vrf": "default",
                    "protocol": "S",
                    "network": "192.168.100.0",
                    "prefix_length": "24",
                    "distance": "1",
                    "metric": "0",
                    "nexthop_ip": "192.168.100.1",
                    "nexthop_if": "GigabitEthernet0/0/0/0",
                }
            ]
        elif "show arp" in command:
            return [
                {
                    "address": "192.168.100.1",
                    "age": "2",
                    "mac": "0050.5688.1101",
                    "interface": "GigabitEthernet0/0/0/0",
                }
            ]
        elif "show running-config" in command:
            return "hostname ASR-LAB\nend\n"
        elif "ping" in command:
            return "Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/3 ms\n"
        elif "traceroute" in command:
            return " 1 192.168.100.1 1.0 msec\n"
        return ""


@pytest.fixture
def xr_device() -> Device:
    return Device(
        name="ASR-LAB",
        host="192.168.100.10",
        platform=DevicePlatform.CISCO_IOSXR,
        transport=DeviceTransport.SSH,
    )


@pytest.mark.asyncio
async def test_cisco_iosxr_contract(xr_device: Device) -> None:
    transport = SimulatedXRTransport()
    driver: InfrastructureDriver = CiscoIOSXRDriver(device=xr_device, transport=transport)

    # Capabilities: MAC table should be declared UNSUPPORTED
    caps = driver.capabilities()
    assert isinstance(caps, CapabilityProfile)
    assert caps.driver == "cisco_iosxr"
    assert caps.is_supported("facts.read")
    assert caps.is_supported("routes.read")
    assert caps.capabilities["mac.read"].status == CapabilityStatus.UNSUPPORTED
    assert not caps.is_supported("mac.read")

    # Facts
    facts = await driver.get_facts()
    assert isinstance(facts, DeviceFacts)
    assert facts.hostname == "ASR-LAB"
    assert facts.vendor == "Cisco"
    assert facts.model == "ASR9K"

    # Interfaces
    interfaces = await driver.get_interfaces()
    assert len(interfaces) == 1
    assert isinstance(interfaces[0], Interface)

    # Routes
    routes = await driver.get_routes(RouteQuery())
    assert len(routes) == 1
    assert isinstance(routes[0], Route)

    # ARP
    arp = await driver.get_arp_table()
    assert len(arp) == 1
    assert isinstance(arp[0], ArpEntry)

    # MAC returns empty on unsupported platform
    mac = await driver.get_mac_table()
    assert mac == []

    # Diagnostics
    ping_res = await driver.ping(PingRequest(destination="192.168.100.1"))
    assert isinstance(ping_res, PingResult)
    assert ping_res.packets_received == 5

    trace_res = await driver.traceroute(TracerouteRequest(destination="192.168.100.1"))
    assert isinstance(trace_res, TracerouteResult)
