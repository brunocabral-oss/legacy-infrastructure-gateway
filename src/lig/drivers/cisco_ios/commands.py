"""Cisco IOS standard read-only commands."""

SHOW_VERSION = "show version"
SHOW_INTERFACES = "show interfaces"
SHOW_IP_INTERFACE_BRIEF = "show ip interface brief"
SHOW_IP_ROUTE = "show ip route"
SHOW_IP_ARP = "show ip arp"
SHOW_MAC_ADDRESS_TABLE = "show mac address-table"
SHOW_CDP_NEIGHBORS_DETAIL = "show cdp neighbors detail"
SHOW_LLDP_NEIGHBORS_DETAIL = "show lldp neighbors detail"
SHOW_RUNNING_CONFIG = "show running-config"


def format_route_command(destination: str | None = None, vrf: str | None = None) -> str:
    """Format the show ip route command with optional VRF and destination."""
    cmd = "show ip route"
    if vrf and vrf.lower() != "default":
        cmd += f" vrf {vrf}"
    if destination:
        cmd += f" {destination}"
    return cmd


def format_ping_command(
    destination: str,
    count: int = 5,
    source: str | None = None,
    vrf: str | None = None,
) -> str:
    """Format Cisco IOS ping command."""
    cmd = "ping"
    if vrf and vrf.lower() != "default":
        cmd += f" vrf {vrf}"
    cmd += f" {destination} repeat {count}"
    if source:
        cmd += f" source {source}"
    return cmd


def format_traceroute_command(
    destination: str,
    source: str | None = None,
    vrf: str | None = None,
) -> str:
    """Format Cisco IOS traceroute command."""
    cmd = "traceroute"
    if vrf and vrf.lower() != "default":
        cmd += f" vrf {vrf}"
    cmd += f" {destination}"
    if source:
        cmd += f" source {source}"
    return cmd
