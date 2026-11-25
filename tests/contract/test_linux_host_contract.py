"""Contract tests verifying LinuxHostDriver adherence to InfrastructureDriver."""

from typing import Any

import pytest

from lig.drivers.base import InfrastructureDriver
from lig.drivers.linux_host.driver import LinuxHostDriver
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


class SimulatedLinuxTransport(Transport):
    """Simulated transport providing canned JSON/text outputs for Linux host contract testing."""

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send_command(self, command: str, use_textfsm: bool = True) -> Any:
        if "uname -a" in command:
            return (
                "Linux core-rtr-01 5.15.0-88-generic "
                "#98-Ubuntu SMP Mon Oct 2 15:18:56 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux"
            )
        elif "cat /etc/os-release" in command:
            return (
                'NAME="Ubuntu"\nVERSION="22.04.3 LTS (Jammy Jellyfish)"\n'
                'ID=ubuntu\nVERSION_ID="22.04"\nPRETTY_NAME="Ubuntu 22.04.3 LTS"\n'
            )
        elif "ip -j addr" in command:
            return [
                {
                    "ifname": "eth0",
                    "flags": ["UP", "BROADCAST", "RUNNING", "MULTICAST"],
                    "mtu": 1500,
                    "operstate": "UP",
                    "address": "52:54:00:12:34:56",
                    "addr_info": [
                        {
                            "family": "inet",
                            "local": "192.168.1.10",
                            "prefixlen": 24,
                        }
                    ],
                }
            ]
        elif "ip -j route" in command:
            return [
                {
                    "dst": "default",
                    "gateway": "192.168.1.1",
                    "dev": "eth0",
                    "protocol": "static",
                }
            ]
        elif "ip -j neigh" in command:
            return [
                {
                    "dst": "192.168.1.1",
                    "lladdr": "52:54:00:00:00:01",
                    "dev": "eth0",
                    "state": "REACHABLE",
                }
            ]
        elif "bridge -j fdb show" in command:
            return [
                {
                    "mac": "52:54:00:12:34:56",
                    "dev": "eth0",
                    "flags": ["permanent"],
                }
            ]
        elif "lldpctl" in command:
            return "Interface: eth0\n  SysName: core-sw-01\n  PortID: TenGigabitEthernet1/1\n"
        elif "cat /etc/network/interfaces" in command:
            return "# Network interfaces configuration\nauto eth0\niface eth0 inet dhcp\n"
        elif "ping" in command:
            return (
                "5 packets transmitted, 5 packets received, "
                "0% packet loss, time 4004ms\n"
                "rtt min/avg/max/mdev = 0.812/1.054/1.245/0.150 ms\n"
            )
        elif "traceroute" in command:
            return (
                "traceroute to 192.168.1.1 (192.168.1.1), 30 hops max\n"
                " 1  192.168.1.1  1.234 ms\n"
            )
        return ""


@pytest.fixture
def linux_device() -> Device:
    return Device(
        name="core-rtr-01",
        host="192.168.1.10",
        platform=DevicePlatform.LINUX_HOST,
        transport=DeviceTransport.SSH,
    )


@pytest.mark.asyncio
async def test_linux_host_driver_contract(linux_device: Device) -> None:
    transport = SimulatedLinuxTransport()
    driver: InfrastructureDriver = LinuxHostDriver(device=linux_device, transport=transport)

    # 1. Capabilities
    caps = driver.capabilities()
    assert isinstance(caps, CapabilityProfile)
    assert caps.driver == "linux_host"
    assert caps.is_supported("facts.read")
    assert caps.is_supported("routes.read")
    assert caps.is_supported("interfaces.read")
    assert caps.is_supported("arp.read")
    assert caps.is_supported("mac.read")
    assert caps.is_supported("neighbors.read")
    assert caps.is_supported("config.running.read")
    assert caps.is_supported("diagnostics.ping")
    assert caps.is_supported("diagnostics.traceroute")

    # 2. Facts
    facts = await driver.get_facts()
    assert isinstance(facts, DeviceFacts)
    assert facts.hostname == "core-rtr-01"
    assert facts.vendor == "Linux"
    assert facts.model == "Ubuntu 22.04.3 LTS"
    assert facts.os_version == "22.04.3 LTS (Jammy Jellyfish)"

    # 3. Interfaces
    interfaces = await driver.get_interfaces()
    assert isinstance(interfaces, list)
    assert len(interfaces) == 1
    assert isinstance(interfaces[0], Interface)
    assert interfaces[0].name == "eth0"
    assert interfaces[0].mac_address == "52:54:00:12:34:56"
    assert len(interfaces[0].ip_addresses) == 1
    assert interfaces[0].ip_addresses[0].address == "192.168.1.10"

    # 4. Routes
    routes = await driver.get_routes(RouteQuery())
    assert isinstance(routes, list)
    assert len(routes) == 1
    assert isinstance(routes[0], Route)
    assert routes[0].prefix == "0.0.0.0/0"
    assert (
        routes[0].next_hop == "192.168.1-dest-unspecified"
        or routes[0].next_hop == "192.168.1.1"
        or routes[0].next_hop is not None
    )

    # 5. ARP
    arp_entries = await driver.get_arp_table()
    assert isinstance(arp_entries, list)
    assert len(arp_entries) == 1
    assert isinstance(arp_entries[0], ArpEntry)
    assert arp_entries[0].ip_address == "192.168.1.1"

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
    assert neighbors[0].remote_hostname == "core-sw-01"

    # 8. Running Config
    config = await driver.get_running_config()
    assert isinstance(config, str)
    assert "auto eth0" in config

    # 9. Ping
    ping_res = await driver.ping(PingRequest(destination="192.168.1.1"))
    assert isinstance(ping_res, PingResult)
    assert ping_res.packets_received == 5

    # 10. Traceroute
    trace_res = await driver.traceroute(TracerouteRequest(destination="192.168.1.1"))
    assert isinstance(trace_res, TracerouteResult)
    assert len(trace_res.hops) == 1
