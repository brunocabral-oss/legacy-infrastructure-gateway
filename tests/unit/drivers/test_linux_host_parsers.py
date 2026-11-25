"""Unit tests for Linux host parsers."""

from lig.drivers.linux_host import parsers
from lig.models.route import RouteProtocol, RouteQuery


def test_parse_linux_facts() -> None:
    uname_out = (
        "Linux server-01 5.15.0-88-generic #98-Ubuntu SMP "
        "Mon Oct 2 15:18:56 UTC 2023 x86_64"
    )
    os_release = (
        'NAME="Ubuntu"\n'
        'VERSION="22.04.3 LTS (Jammy Jellyfish)"\n'
        "ID=ubuntu\n"
        'PRETTY_NAME="Ubuntu 22.04.3 LTS"\n'
    )
    facts = parsers.parse_facts(uname_out, os_release, fallback_hostname="fallback")
    assert facts.hostname == "server-01"
    assert facts.vendor == "Linux"
    assert facts.model == "Ubuntu 22.04.3 LTS"
    assert facts.os_version == "22.04.3 LTS (Jammy Jellyfish)"


def test_parse_linux_interfaces_json() -> None:
    data = [
        {
            "ifname": "eth0",
            "flags": ["UP", "BROADCAST", "RUNNING", "MULTICAST"],
            "mtu": 1500,
            "operstate": "UP",
            "address": "52:54:00:12:34:56",
            "addr_info": [
                {"family": "inet", "local": "192.168.10.50", "prefixlen": 24},
            ],
        }
    ]
    interfaces = parsers.parse_interfaces(data)
    assert len(interfaces) == 1
    assert interfaces[0].name == "eth0"
    assert interfaces[0].mac_address == "52:54:00:12:34:56"
    assert interfaces[0].mtu == 1500
    assert len(interfaces[0].ip_addresses) == 1
    assert interfaces[0].ip_addresses[0].address == "192.168.10.50"
    assert interfaces[0].ip_addresses[0].prefix_length == 24


def test_parse_linux_routes_json() -> None:
    data = [
        {
            "dst": "default",
            "gateway": "192.168.10.1",
            "dev": "eth0",
            "protocol": "static",
            "metric": 100,
        },
        {"dst": "192.168.10.0/24", "dev": "eth0", "protocol": "kernel"},
    ]
    routes = parsers.parse_routes(data, query=RouteQuery())
    assert len(routes) == 2
    assert routes[0].prefix == "0.0.0.0/0"
    assert routes[0].protocol == RouteProtocol.STATIC
    assert routes[0].next_hop == "192.168.10.1"
    assert routes[1].protocol == RouteProtocol.CONNECTED
    assert routes[1].next_hop is None


def test_parse_linux_arp() -> None:
    data = [
        {
            "dst": "192.168.10.1",
            "lladdr": "00:11:22:33:44:55",
            "dev": "eth0",
            "state": ["REACHABLE"],
        }
    ]
    entries = parsers.parse_arp_table(data)
    assert len(entries) == 1
    assert entries[0].ip_address == "192.168.10.1"
    assert entries[0].mac_address == "00:11:22:33:44:55"
    assert entries[0].interface == "eth0"


def test_parse_linux_ping() -> None:
    sample = """PING 192.168.10.1 (192.168.10.1) 56(84) bytes of data.
64 bytes from 192.168.10.1: icmp_seq=1 ttl=64 time=0.456 ms
--- 192.168.10.1 ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4006ms
rtt min/avg/max/mdev = 0.412/0.485/0.540/0.045 ms
"""
    result = parsers.parse_ping_output(sample, destination="192.168.10.1")
    assert result.packets_transmitted == 5
    assert result.packets_received == 5
    assert result.packet_loss_percentage == 0.0
    assert result.rtt_min_ms == 0.412
    assert result.rtt_avg_ms == 0.485
    assert result.rtt_max_ms == 0.540
