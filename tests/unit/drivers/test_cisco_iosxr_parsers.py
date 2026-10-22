"""Unit tests for Cisco IOS-XR parsers."""

from lig.drivers.cisco_iosxr import parsers
from lig.models.interface import InterfaceAdminStatus, InterfaceOperStatus
from lig.models.route import RouteProtocol, RouteQuery


def test_parse_iosxr_version_structured() -> None:
    data = [
        {
            "version": "6.5.3",
            "hardware": "ASR9K",
            "serial": "FOX12345678",
            "hostname": "ASR-LAB",
        }
    ]
    facts = parsers.parse_version_output(data, fallback_hostname="ASR-LAB")
    assert facts.hostname == "ASR-LAB"
    assert facts.vendor == "Cisco"
    assert facts.model == "ASR9K"
    assert facts.os_version == "6.5.3"
    assert facts.serial_number == "FOX12345678"


def test_parse_iosxr_interfaces_brief() -> None:
    data = [
        {
            "interface": "GigabitEthernet0/0/0/0",
            "ip_address": "192.168.100.10",
            "status": "Up",
            "proto": "Up",
        },
        {
            "interface": "GigabitEthernet0/0/0/1",
            "ip_address": "unassigned",
            "status": "Shutdown",
            "proto": "Down",
        },
    ]
    interfaces = parsers.parse_interfaces_brief(data)
    assert len(interfaces) == 2
    assert interfaces[0].name == "GigabitEthernet0/0/0/0"
    assert interfaces[0].oper_status == InterfaceOperStatus.UP
    assert interfaces[0].ip_addresses[0].address == "192.168.100.10"
    assert interfaces[1].admin_status == InterfaceAdminStatus.DOWN


def test_parse_iosxr_routes() -> None:
    data = [
        {
            "vrf": "default",
            "protocol": "S",
            "network": "192.168.100.0",
            "prefix_length": "24",
            "distance": "1",
            "metric": "0",
            "nexthop_ip": "192.168.100.1",
            "nexthop_if": "GigabitEthernet0/0/0/0",
        },
        {
            "vrf": "lab_vrf",
            "protocol": "B",
            "network": "10.0.0.0",
            "prefix_length": "8",
            "distance": "20",
            "metric": "0",
            "nexthop_ip": "192.168.100.254",
            "nexthop_if": "GigabitEthernet0/0/0/0",
        },
    ]
    routes = parsers.parse_routes_output(data, query=RouteQuery(vrf="lab_vrf"))
    assert len(routes) == 1
    assert routes[0].prefix == "10.0.0.0/8"
    assert routes[0].protocol == RouteProtocol.BGP
    assert routes[0].vrf == "lab_vrf"


def test_parse_iosxr_arp() -> None:
    data = [
        {
            "address": "192.168.100.1",
            "age": "4",
            "mac": "0050.5688.1101",
            "interface": "GigabitEthernet0/0/0/0",
        }
    ]
    entries = parsers.parse_arp_output(data)
    assert len(entries) == 1
    assert entries[0].ip_address == "192.168.100.1"
    assert entries[0].mac_address == "0050.5688.1101"
    assert entries[0].age_seconds == 240
