"""Static normalized fixtures for MockDriver."""

from lig.models.arp import ArpEntry
from lig.models.diagnostics import PingResult, TracerouteHop, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface, InterfaceAdminStatus, InterfaceIP, InterfaceOperStatus
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor, NeighborProtocol
from lig.models.route import Route, RouteProtocol

MOCK_FACTS = DeviceFacts(
    hostname="VDORTD-A",
    fqdn="vdortd-a.lab.local",
    vendor="Cisco",
    model="Cisco ASR 1001-X",
    os_version="16.09.05",
    serial_number="FXS213000AB",
    uptime_seconds=842100,
    interfaces_count=8,
)

MOCK_INTERFACES = [
    Interface(
        name="GigabitEthernet0/0/0",
        description="Uplink to Core-1",
        enabled=True,
        admin_status=InterfaceAdminStatus.UP,
        oper_status=InterfaceOperStatus.UP,
        mac_address="00:50:56:88:aa:01",
        mtu=1500,
        speed_mbps=1000,
        ip_addresses=[InterfaceIP(address="192.168.199.45", prefix_length=24, is_primary=True)],
    ),
    Interface(
        name="GigabitEthernet0/0/1",
        description="Downlink to LAB-Switches",
        enabled=True,
        admin_status=InterfaceAdminStatus.UP,
        oper_status=InterfaceOperStatus.UP,
        mac_address="00:50:56:88:aa:02",
        mtu=1500,
        speed_mbps=1000,
        ip_addresses=[InterfaceIP(address="10.10.10.1", prefix_length=24, is_primary=True)],
    ),
]

MOCK_ROUTES = [
    Route(
        prefix="192.168.199.48/32",
        protocol=RouteProtocol.STATIC,
        next_hop="192.168.200.140",
        outgoing_interface="GigabitEthernet0/0/0",
        vrf="lab",
        distance=10,
        metric=0,
        active=True,
        age_seconds=3600,
    ),
    Route(
        prefix="10.0.0.0/8",
        protocol=RouteProtocol.OSPF,
        next_hop="192.168.199.1",
        outgoing_interface="GigabitEthernet0/0/0",
        vrf="default",
        distance=110,
        metric=20,
        active=True,
        age_seconds=86400,
    ),
    Route(
        prefix="0.0.0.0/0",
        protocol=RouteProtocol.STATIC,
        next_hop="192.168.199.254",
        outgoing_interface="GigabitEthernet0/0/0",
        vrf="default",
        distance=1,
        metric=0,
        active=True,
        age_seconds=900000,
    ),
]

MOCK_ARP_TABLE = [
    ArpEntry(
        ip_address="192.168.199.48",
        mac_address="00:50:56:88:bb:02",
        interface="GigabitEthernet0/0/0",
        age_seconds=120,
        entry_type="dynamic",
    ),
    ArpEntry(
        ip_address="192.168.199.254",
        mac_address="00:50:56:88:cc:fe",
        interface="GigabitEthernet0/0/0",
        age_seconds=45,
        entry_type="dynamic",
    ),
]

MOCK_MAC_TABLE = [
    MacEntry(
        mac_address="00:50:56:88:bb:02",
        vlan_id=100,
        interface="GigabitEthernet0/0/0",
        entry_type="dynamic",
        is_active=True,
    )
]

MOCK_NEIGHBORS = [
    Neighbor(
        local_interface="GigabitEthernet0/0/0",
        remote_hostname="CORE-SW01",
        remote_port="TenGigabitEthernet1/1/1",
        remote_platform="Cisco Catalyst 9300",
        protocol=NeighborProtocol.LLDP,
    )
]

MOCK_RUNNING_CONFIG = """!
version 16.9
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname VDORTD-A
!
ip routing
!
interface GigabitEthernet0/0/0
 description Uplink to Core-1
 ip address 192.168.199.45 255.255.255.0
!
ip route 192.168.199.48 255.255.255.255 192.168.200.140
!
end
"""

MOCK_PING_RESULT = PingResult(
    destination="192.168.199.48",
    packets_transmitted=5,
    packets_received=5,
    packet_loss_percentage=0.0,
    rtt_min_ms=1.2,
    rtt_avg_ms=1.8,
    rtt_max_ms=2.4,
)

MOCK_TRACEROUTE_RESULT = TracerouteResult(
    destination="192.168.199.48",
    hops=[
        TracerouteHop(
            hop_number=1, ip_address="192.168.199.254", hostname="gw-core.lab.local", rtt_ms=0.8
        ),
        TracerouteHop(
            hop_number=2, ip_address="192.168.200.140", hostname="rtr-edge.lab.local", rtt_ms=1.4
        ),
        TracerouteHop(
            hop_number=3, ip_address="192.168.199.48", hostname="target.lab.local", rtt_ms=1.9
        ),
    ],
)
