"""Cisco IOS-XR read-only CLI commands."""

SHOW_VERSION = "show version"
SHOW_IPV4_INTERFACE_BRIEF = "show ipv4 interface brief"
SHOW_ROUTE = "show route"
SHOW_ARP = "show arp"
SHOW_CDP_NEIGHBORS_DETAIL = "show cdp neighbors detail"
SHOW_LLDP_NEIGHBORS_DETAIL = "show lldp neighbors detail"
SHOW_RUNNING_CONFIG = "show running-config"


def format_route_command(destination: str | None = None, vrf: str | None = None) -> str:
    """Format Cisco IOS-XR show route command."""
    cmd = "show route"
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
    """Format Cisco IOS-XR ping command."""
    cmd = f"ping {destination} count {count}"
    if vrf and vrf.lower() != "default":
        cmd += f" vrf {vrf}"
    if source:
        cmd += f" source {source}"
    return cmd


def format_traceroute_command(
    destination: str,
    source: str | None = None,
    vrf: str | None = None,
) -> str:
    """Format Cisco IOS-XR traceroute command."""
    cmd = f"traceroute {destination}"
    if vrf and vrf.lower() != "default":
        cmd += f" vrf {vrf}"
    if source:
        cmd += f" source {source}"
    return cmd
