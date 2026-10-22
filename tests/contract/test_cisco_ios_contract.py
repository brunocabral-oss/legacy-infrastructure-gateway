"""Contract tests verifying CiscoIOSDriver adherence to InfrastructureDriver."""

from typing import Any

import pytest

from lig.drivers.base import InfrastructureDriver
from lig.drivers.cisco_ios.driver import CiscoIOSDriver
from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile
from lig.models.device import Device, DevicePlatform, DeviceTransport
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor
from lig.models.route import Route, RouteQuery
from lig.transports.base import Transport


class SimulatedCiscoTransport(Transport):
    """Simulated transport providing canned NTC structured responses for contract testing."""

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        if "show version" in command:
            return [
                {
                    "version": "16.09.05",
                    "hardware": ["Cisco ASR 1001-X"],
                    "serial": ["FXS213000AB"],
                    "hostname": "VDORTD-A",
                }
            ]
        elif "show ip interface brief" in command:
            return [
                {
                    "interface": "GigabitEthernet0/0/0",
                    "ip_address": "192.168.199.45",
                    "status": "up",
                    "proto": "up",
                }
            ]
        elif "show ip route" in command:
            return [
                {
                    "vrf": "lab",
                    "protocol": "S",
                    "network": "192.168.199.48",
                    "prefix_length": "32",
                    "distance": "10",
                    "metric": "0",
                    "nexthop_ip": "192.168.200.140",
                    "nexthop_if": "GigabitEthernet0/0/0",
                }
            ]
        elif "show ip arp" in command:
            return [
                {
                    "protocol": "Internet",
                    "ip_address": "192.168.199.48",
                    "age": "2",
                    "mac_address": "0050.5688.bb02",
                    "type": "ARPA",
                    "interface": "GigabitEthernet0/0/0",
                }
            ]
        elif "show mac address-table" in command:
            return [
                {
                    "mac_address": "0050.5688.bb02",
                    "vlan": "100",
                    "interface": "GigabitEthernet0/0/0",
                    "type": "dynamic",
                }
            ]
        elif "show cdp neighbors detail" in command:
            return [
                {
                    "neighbor_name": "CORE-SW01",
                    "local_interface": "GigabitEthernet0/0/0",
                    "neighbor_interface": "TenGigabitEthernet1/1/1",
                    "platform": "cisco WS-C2960-24TT-L",
                }
            ]
        elif "show running-config" in command:
            return "! Current configuration\nhostname VDORTD-A\nend\n"
        elif "ping" in command:
            return "Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/3 ms\n"
        elif "traceroute" in command:
            return " 1 192.168.199.254 1.0 msec\n 2 192.168.199.48 2.0 msec\n"
        return ""


@pytest.fixture
def cisco_device() -> Device:
    return Device(
        name="VDORTD-A",
        host="192.168.199.45",
        platform=DevicePlatform.CISCO_IOS,
        transport=DeviceTransport.SSH,
    )


@pytest.mark.asyncio
async def test_cisco_ios_driver_contract(cisco_device: Device) -> None:
    transport = SimulatedCiscoTransport()
    driver: InfrastructureDriver = CiscoIOSDriver(device=cisco_device, transport=transport)

    # 1. Capabilities
    caps = driver.capabilities()
    assert isinstance(caps, CapabilityProfile)
    assert caps.driver == "cisco_ios"
    assert caps.is_supported("facts.read")
    assert caps.is_supported("routes.read")
    assert caps.is_supported("interfaces.read")

    # 2. Facts
    facts = await driver.get_facts()
    assert isinstance(facts, DeviceFacts)
    assert facts.hostname == "VDORTD-A"
    assert facts.vendor == "Cisco"
    assert facts.model == "Cisco ASR 1001-X"
    assert facts.os_version == "16.09.05"

    # 3. Interfaces
    interfaces = await driver.get_interfaces()
    assert isinstance(interfaces, list)
    assert len(interfaces) == 1
    assert isinstance(interfaces[0], Interface)
    assert interfaces[0].name == "GigabitEthernet0/0/0"

    # 4. Routes
    routes = await driver.get_routes(RouteQuery(vrf="lab"))
    assert isinstance(routes, list)
    assert len(routes) == 1
    assert isinstance(routes[0], Route)
    assert routes[0].prefix == "192.168.199.48/32"

    # 5. ARP
    arp_entries = await driver.get_arp_table()
    assert isinstance(arp_entries, list)
    assert len(arp_entries) == 1
    assert isinstance(arp_entries[0], ArpEntry)
    assert arp_entries[0].ip_address == "192.168.199.48"

    # 6. MAC Table
    mac_entries = await driver.get_mac_table()
    assert isinstance(mac_entries, list)
    assert len(mac_entries) == 1
    assert isinstance(mac_entries[0], MacEntry)

    # 7. Neighbors
    neighbors = await driver.get_neighbors()
    assert isinstance(neighbors, list)
    assert len(neighbors) == 1
    assert isinstance(neighbors[0], Neighbor)
    assert neighbors[0].remote_hostname == "CORE-SW01"

    # 8. Running Config
    config = await driver.get_running_config()
    assert isinstance(config, str)
    assert "hostname VDORTD-A" in config

    # 9. Ping
    ping_res = await driver.ping(PingRequest(destination="192.168.199.48"))
    assert isinstance(ping_res, PingResult)
    assert ping_res.packets_received == 5

    # 10. Traceroute
    trace_res = await driver.traceroute(TracerouteRequest(destination="192.168.199.48"))
    assert isinstance(trace_res, TracerouteResult)
    assert len(trace_res.hops) == 2
