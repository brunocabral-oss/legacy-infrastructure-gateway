"""Cross-vendor semantic consistency contract tests.

Validates that Cisco IOS, Cisco IOS-XR, and FortiGate all yield
strictly identical Pydantic model schemas for the same operations.
"""

import pytest

from lig.drivers.base import InfrastructureDriver
from lig.drivers.cisco_ios.driver import CiscoIOSDriver
from lig.drivers.cisco_iosxr.driver import CiscoIOSXRDriver
from lig.drivers.fortios.driver import FortiOSDriver
from lig.models.arp import ArpEntry
from lig.models.device import Device, DevicePlatform, DeviceTransport
from lig.models.diagnostics import PingRequest, PingResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.route import Route, RouteQuery
from tests.contract.test_cisco_ios_contract import SimulatedCiscoTransport
from tests.contract.test_cisco_iosxr_contract import SimulatedXRTransport
from tests.contract.test_fortios_contract import SimulatedFortiOSTransport


@pytest.fixture
def all_drivers() -> list[InfrastructureDriver]:
    dev_ios = Device(
        name="VDORTD-A",
        host="192.168.199.45",
        platform=DevicePlatform.CISCO_IOS,
        transport=DeviceTransport.SSH,
    )
    dev_xr = Device(
        name="ASR-LAB",
        host="192.168.100.10",
        platform=DevicePlatform.CISCO_IOSXR,
        transport=DeviceTransport.SSH,
    )
    dev_forti = Device(
        name="CAGE",
        host="192.168.200.138",
        platform=DevicePlatform.FORTIOS,
        transport=DeviceTransport.SSH,
    )

    return [
        CiscoIOSDriver(dev_ios, transport=SimulatedCiscoTransport()),
        CiscoIOSXRDriver(dev_xr, transport=SimulatedXRTransport()),
        FortiOSDriver(dev_forti, transport=SimulatedFortiOSTransport()),
    ]


@pytest.mark.asyncio
async def test_multivendor_facts_semantic_equality(
    all_drivers: list[InfrastructureDriver],
) -> None:
    for driver in all_drivers:
        facts = await driver.get_facts()
        assert isinstance(facts, DeviceFacts)
        assert bool(facts.hostname)
        assert bool(facts.vendor)
        assert bool(facts.model)
        assert bool(facts.os_version)


@pytest.mark.asyncio
async def test_multivendor_interfaces_semantic_equality(
    all_drivers: list[InfrastructureDriver],
) -> None:
    for driver in all_drivers:
        interfaces = await driver.get_interfaces()
        assert isinstance(interfaces, list)
        assert len(interfaces) >= 1
        for iface in interfaces:
            assert isinstance(iface, Interface)
            assert bool(iface.name)
            assert iface.admin_status in {"up", "down", "unknown"}
            assert iface.oper_status in {"up", "down", "lower_layer_down", "unknown"}


@pytest.mark.asyncio
async def test_multivendor_routes_semantic_equality(
    all_drivers: list[InfrastructureDriver],
) -> None:
    for driver in all_drivers:
        routes = await driver.get_routes(RouteQuery())
        assert isinstance(routes, list)
        assert len(routes) >= 1
        for route in routes:
            assert isinstance(route, Route)
            assert "/" in route.prefix
            assert bool(route.protocol)
            assert route.active is True


@pytest.mark.asyncio
async def test_multivendor_arp_semantic_equality(
    all_drivers: list[InfrastructureDriver],
) -> None:
    for driver in all_drivers:
        arp_entries = await driver.get_arp_table()
        assert isinstance(arp_entries, list)
        assert len(arp_entries) >= 1
        for entry in arp_entries:
            assert isinstance(entry, ArpEntry)
            assert bool(entry.ip_address)
            assert bool(entry.mac_address)
            assert bool(entry.interface)


@pytest.mark.asyncio
async def test_multivendor_ping_semantic_equality(
    all_drivers: list[InfrastructureDriver],
) -> None:
    for driver in all_drivers:
        res = await driver.ping(PingRequest(destination="192.168.1.1"))
        assert isinstance(res, PingResult)
        assert res.packets_transmitted > 0
        assert res.packets_received >= 0
        assert 0.0 <= res.packet_loss_percentage <= 100.0
