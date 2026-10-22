"""Parsers transforming Cisco IOS-XR CLI / NTC structured data into normalized models."""

import re
from typing import Any

from lig.models.arp import ArpEntry
from lig.models.diagnostics import PingResult, TracerouteHop, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface, InterfaceAdminStatus, InterfaceIP, InterfaceOperStatus
from lig.models.neighbor import Neighbor, NeighborProtocol
from lig.models.route import Route, RouteProtocol, RouteQuery

# Mapping Cisco XR route protocol codes
XR_PROTOCOL_MAP: dict[str, RouteProtocol] = {
    "C": RouteProtocol.CONNECTED,
    "L": RouteProtocol.CONNECTED,
    "S": RouteProtocol.STATIC,
    "R": RouteProtocol.RIP,
    "B": RouteProtocol.BGP,
    "D": RouteProtocol.EIGRP,
    "O": RouteProtocol.OSPF,
    "IA": RouteProtocol.OSPF,
    "I": RouteProtocol.ISIS,
    "i": RouteProtocol.ISIS,
}


def parse_version_output(parsed_data: Any, fallback_hostname: str = "unknown") -> DeviceFacts:
    """Transform show version output into DeviceFacts."""
    if isinstance(parsed_data, list) and len(parsed_data) > 0 and isinstance(parsed_data[0], dict):
        row = parsed_data[0]
        version = row.get("version") or "unknown"
        hardware = row.get("hardware") or "Cisco IOS-XR"
        serial = row.get("serial") or None
        hostname = row.get("hostname") or fallback_hostname
        return DeviceFacts(
            hostname=hostname,
            vendor="Cisco",
            model=str(hardware),
            os_version=str(version),
            serial_number=str(serial) if serial else None,
        )

    # Fallback regex
    raw_str = str(parsed_data)
    ver_match = re.search(r"Version\s+([^\s\[,]+)", raw_str, re.IGNORECASE)
    version = ver_match.group(1) if ver_match else "unknown"

    model_match = re.search(r"cisco\s+([^\s()]+)\s*\(\)", raw_str, re.IGNORECASE)
    model = model_match.group(1) if model_match else "Cisco IOS-XR"

    return DeviceFacts(
        hostname=fallback_hostname,
        vendor="Cisco",
        model=model,
        os_version=version,
        serial_number=None,
    )


def parse_interfaces_brief(parsed_data: Any) -> list[Interface]:
    """Transform show ipv4 interface brief into list of Interface."""
    interfaces: list[Interface] = []
    if not isinstance(parsed_data, list):
        return interfaces

    for row in parsed_data:
        if not isinstance(row, dict):
            continue
        name = row.get("interface", "")
        if not name:
            continue

        raw_admin = str(row.get("status", "")).lower()
        raw_oper = str(row.get("proto", "") or row.get("line_protocol", "")).lower()

        admin_status = (
            InterfaceAdminStatus.DOWN
            if "down" in raw_admin or "shutdown" in raw_admin
            else InterfaceAdminStatus.UP
        )
        oper_status = InterfaceOperStatus.UP if "up" in raw_oper else InterfaceOperStatus.DOWN

        ip_addresses: list[InterfaceIP] = []
        ip = row.get("ip_address")
        if ip and ip.lower() not in {"unassigned", "unset"}:
            ip_addresses.append(InterfaceIP(address=ip, prefix_length=32, is_primary=True))

        interfaces.append(
            Interface(
                name=name,
                enabled=admin_status == InterfaceAdminStatus.UP,
                admin_status=admin_status,
                oper_status=oper_status,
                ip_addresses=ip_addresses,
            )
        )
    return interfaces


def parse_routes_output(parsed_data: Any, query: RouteQuery) -> list[Route]:
    """Transform show route output into list of Route."""
    routes: list[Route] = []
    if not isinstance(parsed_data, list):
        return routes

    for row in parsed_data:
        if not isinstance(row, dict):
            continue
        network = row.get("network")
        if not network:
            continue

        prefix_len = row.get("prefix_length") or row.get("mask") or "32"
        prefix = f"{network}/{prefix_len}" if "/" not in network else network

        raw_proto = str(row.get("protocol", "")).strip()
        protocol = XR_PROTOCOL_MAP.get(raw_proto, RouteProtocol.OTHER)

        next_hop = row.get("nexthop_ip") or None
        outgoing_if = row.get("nexthop_if") or None
        row_vrf = row.get("vrf") or query.vrf or "default"

        distance_val = row.get("distance")
        distance = int(distance_val) if distance_val and str(distance_val).isdigit() else None

        metric_val = row.get("metric")
        metric = int(metric_val) if metric_val and str(metric_val).isdigit() else None

        # Filter
        if query.destination and query.destination not in prefix:
            continue
        if query.vrf and query.vrf.lower() != row_vrf.lower():
            continue
        if query.protocol and query.protocol != protocol:
            continue

        routes.append(
            Route(
                prefix=prefix,
                protocol=protocol,
                next_hop=next_hop,
                outgoing_interface=outgoing_if,
                vrf=row_vrf,
                distance=distance,
                metric=metric,
                active=True,
            )
        )
    return routes


def parse_arp_output(parsed_data: Any) -> list[ArpEntry]:
    """Transform show arp output into list of ArpEntry."""
    entries: list[ArpEntry] = []
    if not isinstance(parsed_data, list):
        return entries

    for row in parsed_data:
        if not isinstance(row, dict):
            continue
        ip = row.get("address") or row.get("ip_address")
        mac = row.get("mac") or row.get("mac_address") or row.get("hardware_address")
        interface = row.get("interface")
        if not ip or not mac or not interface:
            continue

        age_raw = str(row.get("age", "-"))
        age_seconds = int(age_raw) * 60 if age_raw.isdigit() else None

        entries.append(
            ArpEntry(
                ip_address=ip,
                mac_address=mac,
                interface=interface,
                age_seconds=age_seconds,
                entry_type="dynamic" if age_raw != "-" else "local",
            )
        )
    return entries


def parse_neighbors_output(parsed_data: Any) -> list[Neighbor]:
    """Transform show cdp / lldp neighbors output into list of Neighbor."""
    neighbors: list[Neighbor] = []
    if not isinstance(parsed_data, list):
        return neighbors

    for row in parsed_data:
        if not isinstance(row, dict):
            continue
        hostname = row.get("device_id") or row.get("neighbor_name") or row.get("system_name")
        local_if = row.get("local_interface") or row.get("local_port")
        remote_port = row.get("port_id") or row.get("remote_port")

        if not hostname or not local_if or not remote_port:
            continue

        platform = row.get("platform")

        neighbors.append(
            Neighbor(
                local_interface=local_if,
                remote_hostname=hostname,
                remote_port=remote_port,
                remote_platform=platform,
                protocol=NeighborProtocol.LLDP,
            )
        )
    return neighbors


def parse_ping_output(raw_output: str, destination: str) -> PingResult:
    """Parse Cisco IOS-XR ping output into PingResult."""
    rate_match = re.search(r"Success rate is\s+(\d+)\s+percent\s+\((\d+)/(\d+)\)", raw_output)
    rtt_match = re.search(
        r"round-trip min/avg/max\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)\s*ms", raw_output
    )

    if rate_match:
        percent = float(rate_match.group(1))
        received = int(rate_match.group(2))
        transmitted = int(rate_match.group(3))
        loss = 100.0 - percent
    else:
        transmitted = 5
        received = 0
        loss = 100.0

    min_ms = float(rtt_match.group(1)) if rtt_match else None
    avg_ms = float(rtt_match.group(2)) if rtt_match else None
    max_ms = float(rtt_match.group(3)) if rtt_match else None

    return PingResult(
        destination=destination,
        packets_transmitted=transmitted,
        packets_received=received,
        packet_loss_percentage=loss,
        rtt_min_ms=min_ms,
        rtt_avg_ms=avg_ms,
        rtt_max_ms=max_ms,
    )


def parse_traceroute_output(raw_output: str, destination: str) -> TracerouteResult:
    """Parse Cisco IOS-XR traceroute output into TracerouteResult."""
    hops: list[TracerouteHop] = []
    hop_pattern = re.compile(
        r"^\s*(\d+)\s+(?:([^\s()]+)\s+\(([\d.]+)\)|([\d.]+))\s+([\d.]+)\s*msec",
        re.MULTILINE,
    )

    for match in hop_pattern.finditer(raw_output):
        hop_num = int(match.group(1))
        hostname = match.group(2)
        ip = match.group(3) or match.group(4)
        rtt = float(match.group(5))

        hops.append(
            TracerouteHop(
                hop_number=hop_num,
                ip_address=ip,
                hostname=hostname,
                rtt_ms=rtt,
            )
        )

    return TracerouteResult(destination=destination, hops=hops)
