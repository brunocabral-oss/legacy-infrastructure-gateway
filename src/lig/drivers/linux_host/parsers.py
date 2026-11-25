"""Parsers transforming Linux CLI (iproute2, uname, os-release, ping, traceroute)

into normalized models.
"""

import json
import re
from typing import Any

from lig.models.arp import ArpEntry
from lig.models.diagnostics import PingResult, TracerouteHop, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface, InterfaceAdminStatus, InterfaceIP, InterfaceOperStatus
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor, NeighborProtocol
from lig.models.route import Route, RouteProtocol, RouteQuery


def parse_facts(
    uname_output: str, os_release_output: str, fallback_hostname: str = "linux-host"
) -> DeviceFacts:
    """Parse uname and /etc/os-release into DeviceFacts."""
    hostname = fallback_hostname
    uname_parts = uname_output.strip().split()
    if len(uname_parts) >= 2 and uname_parts[0].lower() == "linux":
        hostname = uname_parts[1]

    os_name = "Linux"
    os_version = "unknown"
    for line in os_release_output.splitlines():
        if line.startswith("PRETTY_NAME="):
            os_name = line.split("=", 1)[1].strip('"\'')
        elif line.startswith("VERSION="):
            os_version = line.split("=", 1)[1].strip('"\'')
        elif line.startswith("ID=") and os_name == "Linux":
            os_name = line.split("=", 1)[1].strip('"\'').capitalize()

    if os_version == "unknown":
        if len(uname_parts) >= 3:
            os_version = uname_parts[2]

    return DeviceFacts(
        hostname=hostname,
        vendor="Linux",
        model=os_name,
        os_version=os_version,
        serial_number=None,
    )


def parse_interfaces(raw_output: Any) -> list[Interface]:
    """Parse 'ip -j addr' JSON or text into list of Interface."""
    interfaces: list[Interface] = []
    data: Any = None
    if isinstance(raw_output, list):
        data = raw_output
    elif isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except Exception:
            data = None

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("ifname")
            if not name:
                continue

            mac = item.get("address")
            if mac in {"", None, "00:00:00:00:00:00"}:
                mac = None

            oper_state = str(item.get("operstate", "UP")).upper()
            flags = item.get("flags", [])
            up_flag = "UP" in flags or oper_state == "UP"

            admin_status = InterfaceAdminStatus.UP if up_flag else InterfaceAdminStatus.DOWN
            oper_status = InterfaceOperStatus.UP if oper_state == "UP" else InterfaceOperStatus.DOWN

            mtu = item.get("mtu")

            ip_addresses: list[InterfaceIP] = []
            addr_info = item.get("addr_info", [])
            is_first = True
            for addr_dict in addr_info:
                if not isinstance(addr_dict, dict):
                    continue
                family = addr_dict.get("family")
                if family not in {"inet", "inet6"}:
                    continue
                local_ip = addr_dict.get("local") or addr_dict.get("address")
                prefixlen = addr_dict.get("prefixlen", 24 if family == "inet" else 64)
                if local_ip:
                    ip_addresses.append(
                        InterfaceIP(
                            address=local_ip,
                            prefix_length=int(prefixlen),
                            is_primary=is_first,
                        )
                    )
                    is_first = False

            interfaces.append(
                Interface(
                    name=name,
                    enabled=admin_status == InterfaceAdminStatus.UP,
                    admin_status=admin_status,
                    oper_status=oper_status,
                    mac_address=mac,
                    mtu=int(mtu) if mtu else None,
                    ip_addresses=ip_addresses,
                )
            )
        return interfaces

    text = str(raw_output)
    int_pattern = re.compile(r"^\d+:\s+([^\s:]+)(?:@\S+)?:\s+<([^>]+)>\s+mtu\s+(\d+)", re.MULTILINE)
    for match in int_pattern.finditer(text):
        name = match.group(1)
        flags = match.group(2)
        mtu = int(match.group(3))
        enabled = "UP" in flags

        interfaces.append(
            Interface(
                name=name,
                enabled=enabled,
                admin_status=InterfaceAdminStatus.UP if enabled else InterfaceAdminStatus.DOWN,
                oper_status=InterfaceOperStatus.UP if enabled else InterfaceOperStatus.DOWN,
                mtu=mtu,
            )
        )
    return interfaces


def parse_routes(raw_output: Any, query: RouteQuery) -> list[Route]:
    """Parse 'ip -j route' JSON or text into list of Route."""
    routes: list[Route] = []
    data: Any = None
    if isinstance(raw_output, list):
        data = raw_output
    elif isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except Exception:
            data = None

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            dst = item.get("dst") or "default"
            if dst == "default":
                dst = "0.0.0.0/0"

            proto_str = str(item.get("protocol", "boot")).lower()
            if proto_str in {"kernel", "static"}:
                protocol = (
                    RouteProtocol.CONNECTED
                    if proto_str == "kernel"
                    else RouteProtocol.STATIC
                )
            elif proto_str in {"ospf", "bgp", "rip", "isis"}:
                protocol = RouteProtocol(proto_str)
            else:
                protocol = RouteProtocol.OTHER

            gateway = item.get("gateway")
            dev = item.get("dev")
            metric = item.get("metric")

            if query.destination and query.destination not in dst:
                continue
            if query.protocol and query.protocol != protocol:
                continue

            routes.append(
                Route(
                    prefix=dst,
                    protocol=protocol,
                    next_hop=gateway,
                    outgoing_interface=dev,
                    vrf=query.vrf or "default",
                    metric=int(metric) if metric is not None else None,
                    active=True,
                )
            )
        return routes

    text = str(raw_output)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if not parts:
            continue
        dst = parts[0]
        if dst == "default":
            dst = "0.0.0.0/0"

        next_hop = None
        dev = None
        if "via" in parts:
            via_idx = parts.index("via")
            if via_idx + 1 < len(parts):
                next_hop = parts[via_idx + 1]
        if "dev" in parts:
            dev_idx = parts.index("dev")
            if dev_idx + 1 < len(parts):
                dev = parts[dev_idx + 1]

        if query.destination and query.destination not in dst:
            continue

        routes.append(
            Route(
                prefix=dst,
                protocol=RouteProtocol.CONNECTED
                if "dev" in parts and "via" not in parts
                else RouteProtocol.STATIC,
                next_hop=next_hop,
                outgoing_interface=dev,
                vrf=query.vrf or "default",
                active=True,
            )
        )
    return routes


def parse_arp_table(raw_output: Any) -> list[ArpEntry]:
    """Parse 'ip -j neigh' JSON or text into list of ArpEntry."""
    entries: list[ArpEntry] = []
    data: Any = None
    if isinstance(raw_output, list):
        data = raw_output
    elif isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except Exception:
            data = None

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            ip = item.get("dst")
            mac = item.get("lladdr")
            dev = item.get("dev")
            state_list = item.get("state", [])

            if not ip or not mac:
                continue

            entry_type = "dynamic"
            if isinstance(state_list, list) and "PERMANENT" in state_list:
                entry_type = "static"

            entries.append(
                ArpEntry(
                    ip_address=ip,
                    mac_address=mac,
                    interface=dev or "unknown",
                    entry_type=entry_type,
                )
            )
        return entries

    text = str(raw_output)
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 5 and "lladdr" in parts:
            ip = parts[0]
            ll_idx = parts.index("lladdr")
            mac = parts[ll_idx + 1]
            dev = parts[parts.index("dev") + 1] if "dev" in parts else "unknown"
            entries.append(
                ArpEntry(
                    ip_address=ip,
                    mac_address=mac,
                    interface=dev,
                    entry_type="dynamic",
                )
            )
    return entries


def parse_mac_table(raw_output: Any) -> list[MacEntry]:
    """Parse 'bridge -j fdb show' JSON into list of MacEntry."""
    entries: list[MacEntry] = []
    data: Any = None
    if isinstance(raw_output, list):
        data = raw_output
    elif isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except Exception:
            data = None

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            mac = item.get("mac")
            dev = item.get("dev")
            vlan = item.get("vlan")
            if not mac or not dev:
                continue
            entries.append(
                MacEntry(
                    mac_address=mac,
                    interface=dev,
                    vlan_id=int(vlan) if vlan is not None and str(vlan).isdigit() else None,
                    entry_type="dynamic",
                    is_active=True,
                )
            )
    return entries


def parse_neighbors(raw_output: Any) -> list[Neighbor]:
    """Parse lldpctl output (JSON or text) into list of Neighbor."""
    neighbors: list[Neighbor] = []
    data: Any = None
    if isinstance(raw_output, dict):
        data = raw_output
    elif isinstance(raw_output, str):
        try:
            data = json.loads(raw_output)
        except Exception:
            data = None

    if isinstance(data, dict):
        lldp_root = data.get("lldp", data)
        if isinstance(lldp_root, dict):
            ifaces = lldp_root.get("interface", [])
            if isinstance(ifaces, dict):
                ifaces = [ifaces]
            for iface_entry in ifaces:
                if not isinstance(iface_entry, dict):
                    continue
                local_port = iface_entry.get("name", "unknown")
                chassis = iface_entry.get("chassis", {})
                if isinstance(chassis, dict):
                    sys_name_dict = chassis.get("name", {})
                    remote_host = (
                        sys_name_dict.get("value")
                        if isinstance(sys_name_dict, dict)
                        else str(sys_name_dict)
                    )

                    mgmt_port = iface_entry.get("mgmt-port", {})
                    remote_port = (
                        mgmt_port.get("id", {}) if isinstance(mgmt_port, dict) else "unknown"
                    )
                    if isinstance(remote_port, dict):
                        remote_port = remote_port.get("value", "unknown")

                    desc_dict = chassis.get("descr", {})
                    platform = desc_dict.get("value") if isinstance(desc_dict, dict) else None

                    if remote_host:
                        neighbors.append(
                            Neighbor(
                                local_interface=local_port,
                                remote_hostname=str(remote_host),
                                remote_port=str(remote_port),
                                remote_platform=str(platform) if platform else None,
                                protocol=NeighborProtocol.LLDP,
                            )
                        )
        return neighbors

    text = str(raw_output)
    current_iface = None
    remote_sys = None
    remote_port = None
    for line in text.splitlines():
        if line.startswith("Interface:"):
            current_iface = line.split(":", 1)[1].strip()
        elif "SysName:" in line or "System Name:" in line:
            remote_sys = line.split(":", 1)[1].strip()
        elif "PortID:" in line or "Port Description:" in line:
            remote_port = line.split(":", 1)[1].strip()

        if current_iface and remote_sys:
            neighbors.append(
                Neighbor(
                    local_interface=current_iface,
                    remote_hostname=remote_sys,
                    remote_port=remote_port or "unknown",
                    protocol=NeighborProtocol.LLDP,
                )
            )
            remote_sys = None
            remote_port = None

    return neighbors


def parse_ping_output(raw_output: str, destination: str) -> PingResult:
    """Parse Linux ping output into PingResult."""
    trans_match = re.search(
        r"(\d+)\s+packets transmitted,\s+(\d+)\s+(?:packets\s+)?received", raw_output
    )
    loss_match = re.search(r"([\d.]+)%\s+packet loss", raw_output)
    rtt_match = re.search(
        r"rtt\s+min/avg/max/(?:mdev|stddev)\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)", raw_output
    )

    transmitted = int(trans_match.group(1)) if trans_match else 5
    received = int(trans_match.group(2)) if trans_match else 0

    if loss_match:
        loss = float(loss_match.group(1))
    elif transmitted > 0:
        loss = ((transmitted - received) / transmitted) * 100.0
    else:
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
    """Parse Linux traceroute output into TracerouteResult."""
    hops: list[TracerouteHop] = []
    hop_regex = re.compile(
        r"^\s*(\d+)\s+(?:([^\s()]+)\s+\(([\d.]+)\)|([^\s]+))\s+(?:[\d.]+\s+ms|\*)",
        re.MULTILINE,
    )
    time_regex = re.compile(r"([\d.]+)\s+ms")

    for line in raw_output.splitlines():
        match = hop_regex.search(line)
        if match:
            hop_num = int(match.group(1))
            host_or_ip1 = match.group(2)
            ip_addr = match.group(3) or match.group(4)
            hostname = host_or_ip1 if match.group(3) else None

            rtt_match = time_regex.search(line)
            rtt = float(rtt_match.group(1)) if rtt_match else None

            hops.append(
                TracerouteHop(
                    hop_number=hop_num,
                    ip_address=ip_addr if ip_addr and ip_addr != "*" else None,
                    hostname=hostname,
                    rtt_ms=rtt,
                )
            )

    return TracerouteResult(destination=destination, hops=hops)
