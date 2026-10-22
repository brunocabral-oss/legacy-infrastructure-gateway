"""Fortinet FortiOS read-only CLI commands."""

GET_SYSTEM_STATUS = "get system status"
GET_SYSTEM_INTERFACE = "get system interface"
GET_SYSTEM_INTERFACE_PHYSICAL = "get system interface physical"
GET_ROUTER_INFO_ROUTING_TABLE_ALL = "get router info routing-table all"
GET_SYSTEM_ARP = "get system arp"
SHOW_FULL_CONFIGURATION = "show full-configuration"


def format_route_command(destination: str | None = None, vrf: str | None = None) -> str:
    """Format FortiOS routing table command."""
    # FortiOS uses VDOMs or VRFs
    cmd = "get router info routing-table all"
    if destination:
        cmd = f"get router info routing-table details {destination}"
    return cmd


def format_ping_command(
    destination: str,
    count: int = 5,
    source: str | None = None,
    vrf: str | None = None,
) -> str:
    """Format FortiOS execute ping command."""
    # execute ping <destination>
    return f"execute ping {destination}"


def format_traceroute_command(
    destination: str,
    source: str | None = None,
    vrf: str | None = None,
) -> str:
    """Format FortiOS execute traceroute command."""
    return f"execute traceroute {destination}"
