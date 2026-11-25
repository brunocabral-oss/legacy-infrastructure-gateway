"""Linux host read-only inspection commands."""

UNAME_ALL = "uname -a"
OS_RELEASE = "cat /etc/os-release"
IP_ADDR_JSON = "ip -j addr"
IP_ROUTE_JSON = "ip -j route"
IP_NEIGH_JSON = "ip -j neigh"
BRIDGE_FDB_JSON = "bridge -j fdb show"
LLDPCTL_JSON = "lldpctl -f json"
LLDPCTL_TEXT = "lldpctl"
SYSCTL_ALL = "sysctl -a 2>/dev/null"
NETWORKING_CONFIG_FILES = "cat /etc/network/interfaces /etc/sysctl.conf 2>/dev/null || true"


def format_route_command(destination: str | None = None, vrf: str | None = None) -> str:
    """Format ip route command with optional destination and VRF (ip vrf exec)."""
    cmd = "ip"
    if vrf and vrf.lower() != "default":
        cmd += f" vrf exec {vrf}"
    cmd += " -j route show"
    if destination:
        cmd += f" {destination}"
    return cmd


def format_ping_command(
    destination: str,
    count: int = 5,
    source: str | None = None,
    vrf: str | None = None,
    timeout_seconds: int = 2,
) -> str:
    """Format Linux ping command."""
    cmd = "ping"
    if vrf and vrf.lower() != "default":
        cmd = f"ip vrf exec {vrf} ping"
    cmd += f" -c {count} -W {timeout_seconds}"
    if source:
        cmd += f" -I {source}"
    cmd += f" {destination}"
    return cmd


def format_traceroute_command(
    destination: str,
    source: str | None = None,
    vrf: str | None = None,
    max_hops: int = 30,
    timeout_seconds: int = 3,
) -> str:
    """Format Linux traceroute command."""
    cmd = "traceroute"
    if vrf and vrf.lower() != "default":
        cmd = f"ip vrf exec {vrf} traceroute"
    cmd += f" -n -m {max_hops} -w {timeout_seconds}"
    if source:
        cmd += f" -s {source}"
    cmd += f" {destination}"
    return cmd
