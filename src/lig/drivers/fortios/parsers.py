"""Parsers transforming Fortinet FortiOS CLI / NTC data into normalized models."""

import re
from typing import Any

from lig.models.arp import ArpEntry
from lig.models.diagnostics import PingResult, TracerouteHop, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface, InterfaceAdminStatus, InterfaceIP, InterfaceOperStatus
from lig.models.route import Route, RouteProtocol, RouteQuery

# Map FortiOS routing protocol codes to normalized RouteProtocol enum
FORTIOS_PROTOCOL_MAP: dict[str, RouteProtocol] = {
    "C": RouteProtocol.CONNECTED,
    "S": RouteProtocol.STATIC,
    "S*": RouteProtocol.STATIC,
    "O": RouteProtocol.OSPF,
    "O_IA": RouteProtocol.OSPF,
    "O_E1": RouteProtocol.OSPF,
    "O_E2": RouteProtocol.OSPF,
    "B": RouteProtocol.BGP,
    "R": RouteProtocol.RIP,
    "I": RouteProtocol.ISIS,
    "K": RouteProtocol.STATIC,
}


def parse_system_status(raw_output: Any, fallback_hostname: str = "unknown") -> DeviceFacts:
    """Parse 'get system status' text or NTC dictionary into DeviceFacts."""
    text = str(raw_output)

    # Version and Model: "Version: FortiGate-60D v5.4.10,build1670,180709 (GA)"
    ver_match = re.search(r"Version:\s*([^\s]+)\s+([^\s,]+)", text)
    model = ver_match.group(1) if ver_match else "FortiGate"
    version = ver_match.group(2) if ver_match else "unknown"

    serial_match = re.search(r"Serial-Number:\s*([^\s]+)", text)
    serial_number = serial_match.group(1) if serial_match else None

    host_match = re.search(r"Hostname:\s*([^\s]+)", text)
    hostname = host_match.group(1) if host_match else fallback_hostname

    return DeviceFacts(
        hostname=hostname,
        vendor="Fortinet",
        model=model,
        os_version=version,
        serial_number=serial_number,
    )


def parse_interfaces(raw_output: Any) -> list[Interface]:
    """Parse 'get system interface' output into list of Interface."""
    interfaces: list[Interface] = []
    text = str(raw_output)

    # Blocks separated by ==[ name ] or interface patterns
    # Example pattern in FortiOS:
    # ==[ port1 ]
    #         name: port1   mode: static   ip: 192.168.1.1 255.255.255.0   status: up
    int_pattern = re.compile(
        r"==\[\s*([^\s\]]+)\s*\][\s\S]*?(?=^==\[|\Z)",
        re.MULTILINE,
    )

    matches = list(int_pattern.finditer(text))
    if matches:
        for match in matches:
            block = match.group(0)
            name = match.group(1)

            status_match = re.search(r"status:\s*([^\s]+)", block)
            oper_str = status_match.group(1).lower() if status_match else "up"

            ip_match = re.search(r"ip:\s*([\d.]+)\s+([\d.]+)", block)
            ip_addresses: list[InterfaceIP] = []
            if ip_match and ip_match.group(1) != "0.0.0.0":
                ip_addresses.append(
                    InterfaceIP(address=ip_match.group(1), prefix_length=24, is_primary=True)
                )

            admin_status = InterfaceAdminStatus.UP
            oper_status = InterfaceOperStatus.UP if oper_str == "up" else InterfaceOperStatus.DOWN

            interfaces.append(
                Interface(
                    name=name,
                    enabled=admin_status == InterfaceAdminStatus.UP,
                    admin_status=admin_status,
                    oper_status=oper_status,
                    ip_addresses=ip_addresses,
                )
            )
    else:
        # Fallback table parser (e.g. physical interfaces)
        line_pattern = re.compile(
            r"^\s*([a-zA-Z0-9_\-\.]+)\s+([\d.]+)\s+([\d.]+)\s+([0-9a-fA-F:]+)\s+([a-zA-Z]+)",
            re.MULTILINE,
        )
        for line_match in line_pattern.finditer(text):
            name = line_match.group(1)
            ip = line_match.group(2)
            mac = line_match.group(4)
            status = line_match.group(5).lower()

            ip_addresses = []
            if ip != "0.0.0.0":
                ip_addresses.append(InterfaceIP(address=ip, prefix_length=24, is_primary=True))

            interfaces.append(
                Interface(
                    name=name,
                    enabled=status == "up",
                    admin_status=InterfaceAdminStatus.UP,
                    oper_status=InterfaceOperStatus.UP
                    if status == "up"
                    else InterfaceOperStatus.DOWN,
                    mac_address=mac,
                    ip_addresses=ip_addresses,
                )
            )
    return interfaces


def parse_routing_table(parsed_data: Any, query: RouteQuery) -> list[Route]:
    """Parse 'get router info routing-table all' into list of Route."""
    routes: list[Route] = []

    # If NTC template succeeded
    if isinstance(parsed_data, list):
        for row in parsed_data:
            if not isinstance(row, dict):
                continue
            dest = row.get("destination")
            if not dest:
                continue

            raw_type = str(row.get("type", "")).strip()
            proto_key = raw_type.replace("*", "").strip()
            protocol = FORTIOS_PROTOCOL_MAP.get(
                raw_type, FORTIOS_PROTOCOL_MAP.get(proto_key, RouteProtocol.OTHER)
            )

            gateway = row.get("gateway")
            next_hop = gateway if gateway and "connected" not in gateway else None
            outgoing_if = row.get("interface")

            dist_val = row.get("distance")
            distance = int(dist_val) if dist_val and str(dist_val).isdigit() else None

            metric_val = row.get("metric")
            metric = int(metric_val) if metric_val and str(metric_val).isdigit() else None

            # Filters
            if query.destination and query.destination not in dest:
                continue
            if query.protocol and query.protocol != protocol:
                continue

            routes.append(
                Route(
                    prefix=dest,
                    protocol=protocol,
                    next_hop=next_hop,
                    outgoing_interface=outgoing_if,
                    vrf=query.vrf or "default",
                    distance=distance,
                    metric=metric,
                    active=True,
                )
            )
        return routes

    # Fallback regex for FortiOS routing table
    text = str(parsed_data)
    route_regex = re.compile(
        r"^([A-Z\*]+)\s+([\d\.\/]+)\s+(?:\[(\d+)\/(\d+)\]\s+via\s+([\d\.]+),\s+([^\s,]+)|"
        r"is directly connected,\s+([^\s,]+))",
        re.MULTILINE,
    )
    for match in route_regex.finditer(text):
        raw_code = match.group(1).strip()
        prefix = match.group(2)
        distance = int(match.group(3)) if match.group(3) else None
        metric = int(match.group(4)) if match.group(4) else None
        next_hop = match.group(5)
        outgoing_if = match.group(6) or match.group(7)

        clean_code = raw_code.replace("*", "").strip()
        protocol = FORTIOS_PROTOCOL_MAP.get(
            raw_code, FORTIOS_PROTOCOL_MAP.get(clean_code, RouteProtocol.OTHER)
        )

        if query.destination and query.destination not in prefix:
            continue
        if query.protocol and query.protocol != protocol:
            continue

        routes.append(
            Route(
                prefix=prefix,
                protocol=protocol,
                next_hop=next_hop,
                outgoing_interface=outgoing_if,
                vrf=query.vrf or "default",
                distance=distance,
                metric=metric,
                active=True,
            )
        )
    return routes


def parse_arp_table(parsed_data: Any) -> list[ArpEntry]:
    """Parse 'get system arp' output into list of ArpEntry."""
    entries: list[ArpEntry] = []

    if isinstance(parsed_data, list):
        for row in parsed_data:
            if not isinstance(row, dict):
                continue
            ip = row.get("ip_address") or row.get("address")
            mac = row.get("mac_address") or row.get("hardware_addr")
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
                    entry_type="dynamic",
                )
            )
        return entries

    # Fallback regex
    text = str(parsed_data)
    arp_regex = re.compile(
        r"^\s*([\d.]+)\s+(\d+|-)\s+([0-9a-fA-F:]+)\s+([^\s]+)",
        re.MULTILINE,
    )
    for match in arp_regex.finditer(text):
        ip = match.group(1)
        age_str = match.group(2)
        mac = match.group(3)
        interface = match.group(4)

        age_seconds = int(age_str) * 60 if age_str.isdigit() else None
        entries.append(
            ArpEntry(
                ip_address=ip,
                mac_address=mac,
                interface=interface,
                age_seconds=age_seconds,
                entry_type="dynamic",
            )
        )
    return entries


def parse_ping_output(raw_output: str, destination: str) -> PingResult:
    """Parse FortiOS execute ping output into PingResult."""
    text = str(raw_output)
    stat_match = re.search(
        r"(\d+)\s+packets transmitted,\s+(\d+)\s+packets received,\s+([\d.]+)%\s+packet loss",
        text,
    )
    rtt_match = re.search(
        r"round-trip min/avg/max\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)\s*ms",
        text,
    )

    if stat_match:
        transmitted = int(stat_match.group(1))
        received = int(stat_match.group(2))
        loss = float(stat_match.group(3))
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
    """Parse FortiOS execute traceroute output into TracerouteResult."""
    hops: list[TracerouteHop] = []
    text = str(raw_output)

    hop_pattern = re.compile(
        r"^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s*ms",
        re.MULTILINE,
    )
    for match in hop_pattern.finditer(text):
        hop_num = int(match.group(1))
        ip = match.group(2)
        rtt = float(match.group(3))

        hops.append(
            TracerouteHop(
                hop_number=hop_num,
                ip_address=ip,
                rtt_ms=rtt,
            )
        )
    return TracerouteResult(destination=destination, hops=hops)
