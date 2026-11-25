"""Unit tests for Cisco IOS output parsers."""

from lig.drivers.cisco_ios import parsers
from lig.models.interface import InterfaceAdminStatus, InterfaceOperStatus
from lig.models.neighbor import NeighborProtocol
from lig.models.route import RouteProtocol, RouteQuery


def test_parse_version_output_structured() -> None:
    data = [
        {
            "version": "15.0(2)SE4",
            "hardware": ["WS-C2960-24TT-L"],
            "serial": ["FOC1234ABCD"],
            "hostname": "SWITCH-01",
        }
    ]
    facts = parsers.parse_version_output(data, fallback_hostname="SWITCH-01")
    assert facts.hostname == "SWITCH-01"
    assert facts.vendor == "Cisco"
    assert facts.model == "WS-C2960-24TT-L"
    assert facts.os_version == "15.0(2)SE4"
    assert facts.serial_number == "FOC1234ABCD"


def test_parse_version_output_regex_fallback() -> None:
    raw_text = (
        "Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), "
        "Version 15.0(2)SE4, RELEASE SOFTWARE (fc1)\n"
        "cisco WS-C2960-24TT-L (PowerPC405) processor (revision B0) with 65536K bytes of memory.\n"
        "System serial number : FOC1234ABCD\n"
    )
    facts = parsers.parse_version_output(raw_text, fallback_hostname="SWITCH-01")
    assert facts.vendor == "Cisco"
    assert facts.os_version == "15.0(2)SE4"
    assert facts.serial_number == "FOC1234ABCD"


def test_parse_ip_interface_brief() -> None:
    data = [
        {
            "interface": "GigabitEthernet0/0/0",
            "ip_address": "192.0.2.45",
            "status": "up",
            "proto": "up",
        },
        {
            "interface": "GigabitEthernet0/0/1",
            "ip_address": "unassigned",
            "status": "administratively down",
            "proto": "down",
        },
    ]
    interfaces = parsers.parse_ip_interface_brief(data)
    assert len(interfaces) == 2

    int0 = interfaces[0]
    assert int0.name == "GigabitEthernet0/0/0"
    assert int0.admin_status == InterfaceAdminStatus.UP
    assert int0.oper_status == InterfaceOperStatus.UP
    assert len(int0.ip_addresses) == 1
    assert int0.ip_addresses[0].address == "192.0.2.45"

    int1 = interfaces[1]
    assert int1.name == "GigabitEthernet0/0/1"
    assert int1.admin_status == InterfaceAdminStatus.DOWN
    assert int1.oper_status == InterfaceOperStatus.DOWN
    assert len(int1.ip_addresses) == 0


def test_parse_routes_output() -> None:
    data = [
        {
            "vrf": "",
            "protocol": "S",
            "network": "0.0.0.0",
            "prefix_length": "0",
            "distance": "1",
            "metric": "0",
            "nexthop_ip": "192.168.1.1",
            "nexthop_if": "GigabitEthernet0/1",
        },
        {
            "vrf": "lab",
            "protocol": "O",
            "network": "10.10.10.0",
            "prefix_length": "24",
            "distance": "110",
            "metric": "20",
            "nexthop_ip": "192.168.1.254",
            "nexthop_if": "GigabitEthernet0/1",
        },
    ]

    # Query all
    routes = parsers.parse_routes_output(data, query=RouteQuery())
    assert len(routes) == 2
    assert routes[0].protocol == RouteProtocol.STATIC
    assert routes[0].prefix == "0.0.0.0/0"
    assert routes[0].distance == 1

    # Query VRF lab
    lab_routes = parsers.parse_routes_output(data, query=RouteQuery(vrf="lab"))
    assert len(lab_routes) == 1
    assert lab_routes[0].protocol == RouteProtocol.OSPF
    assert lab_routes[0].vrf == "lab"


def test_parse_arp_output() -> None:
    data = [
        {
            "protocol": "Internet",
            "ip_address": "192.168.1.1",
            "age": "-",
            "mac_address": "0000.0c07.ac01",
            "type": "ARPA",
            "interface": "GigabitEthernet0/1",
        },
        {
            "protocol": "Internet",
            "ip_address": "192.168.1.100",
            "age": "15",
            "mac_address": "0050.5688.bb02",
            "type": "ARPA",
            "interface": "GigabitEthernet0/1",
        },
    ]
    entries = parsers.parse_arp_output(data)
    assert len(entries) == 2
    assert entries[0].ip_address == "192.168.1.1"
    assert entries[0].entry_type == "local"
    assert entries[1].ip_address == "192.168.1.100"
    assert entries[1].age_seconds == 900
    assert entries[1].entry_type == "dynamic"


def test_parse_cdp_neighbors_output() -> None:
    data = [
        {
            "neighbor_name": "SW-ACCESS-01.example.net",
            "mgmt_address": "192.168.1.2",
            "platform": "cisco WS-C2960-24TT-L",
            "neighbor_interface": "FastEthernet0/24",
            "local_interface": "GigabitEthernet0/1",
        }
    ]
    neighbors = parsers.parse_cdp_neighbors_output(data)
    assert len(neighbors) == 1
    n = neighbors[0]
    assert n.remote_hostname == "SW-ACCESS-01.example.net"
    assert n.local_interface == "GigabitEthernet0/1"
    assert n.remote_port == "FastEthernet0/24"
    assert n.protocol == NeighborProtocol.CDP


def test_parse_ping_output() -> None:
    sample_ping = """Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 192.168.1.1, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms
"""
    result = parsers.parse_ping_output(sample_ping, destination="192.168.1.1")
    assert result.destination == "192.168.1.1"
    assert result.packets_transmitted == 5
    assert result.packets_received == 5
    assert result.packet_loss_percentage == 0.0
    assert result.rtt_min_ms == 1.0
    assert result.rtt_avg_ms == 2.0
    assert result.rtt_max_ms == 4.0


def test_parse_traceroute_output() -> None:
    sample_trace = """Type escape sequence to abort.
Tracing the route to 192.168.1.1
VRF info: (vrf in name/id, vrf out name/id)
  1 192.168.1.254 1.2 msec 1.0 msec 0.8 msec
  2 192.168.1.1 2.4 msec 2.1 msec 2.3 msec
"""
    result = parsers.parse_traceroute_output(sample_trace, destination="192.168.1.1")
    assert result.destination == "192.168.1.1"
    assert len(result.hops) == 2
    assert result.hops[0].hop_number == 1
    assert result.hops[0].ip_address == "192.168.1.254"
    assert result.hops[0].rtt_ms == 1.2
    assert result.hops[1].hop_number == 2
    assert result.hops[1].ip_address == "192.168.1.1"
