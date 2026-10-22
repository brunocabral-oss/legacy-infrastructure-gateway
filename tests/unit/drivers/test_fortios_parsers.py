"""Unit tests for Fortinet FortiOS parsers."""

from lig.drivers.fortios import parsers
from lig.models.interface import InterfaceAdminStatus, InterfaceOperStatus
from lig.models.route import RouteProtocol, RouteQuery


def test_parse_fortios_status() -> None:
    sample = """Version: FortiGate-60D v5.4.10,build1670,180709 (GA)
Serial-Number: FGT60D4614041234
Hostname: CAGE-FW
"""
    facts = parsers.parse_system_status(sample, fallback_hostname="CAGE")
    assert facts.hostname == "CAGE-FW"
    assert facts.vendor == "Fortinet"
    assert facts.model == "FortiGate-60D"
    assert facts.os_version == "v5.4.10"
    assert facts.serial_number == "FGT60D4614041234"


def test_parse_fortios_interfaces() -> None:
    sample = """==[ internal ]
        name: internal   mode: static   ip: 192.168.200.138 255.255.255.0   status: up
==[ wan1 ]
        name: wan1   mode: dhcp   ip: 0.0.0.0 0.0.0.0   status: down
"""
    interfaces = parsers.parse_interfaces(sample)
    assert len(interfaces) == 2
    assert interfaces[0].name == "internal"
    assert interfaces[0].admin_status == InterfaceAdminStatus.UP
    assert interfaces[0].oper_status == InterfaceOperStatus.UP
    assert len(interfaces[0].ip_addresses) == 1
    assert interfaces[0].ip_addresses[0].address == "192.168.200.138"

    assert interfaces[1].name == "wan1"
    assert interfaces[1].oper_status == InterfaceOperStatus.DOWN


def test_parse_fortios_routing_table() -> None:
    data = [
        {
            "type": "S*",
            "destination": "0.0.0.0/0",
            "distance": "10",
            "metric": "0",
            "gateway": "192.168.200.1",
            "interface": "wan1",
        },
        {
            "type": "C",
            "destination": "192.168.200.0/24",
            "distance": "",
            "metric": "",
            "gateway": "is directly connected",
            "interface": "internal",
        },
        {
            "type": "O",
            "destination": "10.0.0.0/24",
            "distance": "110",
            "metric": "10",
            "gateway": "192.168.200.254",
            "interface": "internal",
        },
    ]

    routes = parsers.parse_routing_table(data, query=RouteQuery())
    assert len(routes) == 3
    assert routes[0].prefix == "0.0.0.0/0"
    assert routes[0].protocol == RouteProtocol.STATIC
    assert routes[0].next_hop == "192.168.200.1"

    assert routes[1].protocol == RouteProtocol.CONNECTED
    assert routes[1].next_hop is None

    assert routes[2].protocol == RouteProtocol.OSPF
    assert routes[2].distance == 110


def test_parse_fortios_arp() -> None:
    sample = """Address           Age(min)   Hardware Addr      Interface
192.168.200.1            0   00:50:56:88:fe:01  wan1
10.0.0.50               12   00:50:56:88:00:50  internal
"""
    entries = parsers.parse_arp_table(sample)
    assert len(entries) == 2
    assert entries[0].ip_address == "192.168.200.1"
    assert entries[0].mac_address == "00:50:56:88:fe:01"
    assert entries[1].ip_address == "10.0.0.50"
    assert entries[1].age_seconds == 720


def test_parse_fortios_ping() -> None:
    sample = """PING 192.168.200.1 (192.168.200.1): 56 data bytes
56 bytes from 192.168.200.1: icmp_seq=0 ttl=64 time=1.2 ms
--- 192.168.200.1 ping statistics ---
5 packets transmitted, 5 packets received, 0% packet loss
round-trip min/avg/max = 1.0/1.1/1.2 ms
"""
    result = parsers.parse_ping_output(sample, destination="192.168.200.1")
    assert result.destination == "192.168.200.1"
    assert result.packets_transmitted == 5
    assert result.packets_received == 5
    assert result.packet_loss_percentage == 0.0
    assert result.rtt_avg_ms == 1.1
