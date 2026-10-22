"""Contract tests ensuring drivers fulfill the InfrastructureDriver interface."""

import pytest

from lig.drivers.base import InfrastructureDriver
from lig.drivers.mock.driver import MockDriver
from lig.models.arp import ArpEntry
from lig.models.capabilities import CapabilityProfile
from lig.models.device import Device, DevicePlatform, DeviceTransport
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult
from lig.models.facts import DeviceFacts
from lig.models.interface import Interface
from lig.models.mac import MacEntry
from lig.models.neighbor import Neighbor
from lig.models.route import Route, RouteQuery


@pytest.fixture
def test_device() -> Device:
    return Device(
        name="contract-device",
        host="127.0.0.1",
        platform=DevicePlatform.MOCK,
        transport=DeviceTransport.MOCK,
    )


@pytest.mark.asyncio
async def test_mock_driver_satisfies_contract(test_device: Device) -> None:
    driver: InfrastructureDriver = MockDriver(test_device)

    # 1. Capabilities
    capabilities = driver.capabilities()
    assert isinstance(capabilities, CapabilityProfile)
    assert capabilities.driver == "mock_driver"

    # 2. Facts
    facts = await driver.get_facts()
    assert isinstance(facts, DeviceFacts)
    assert facts.hostname != ""
    assert facts.vendor != ""

    # 3. Interfaces
    interfaces = await driver.get_interfaces()
    assert isinstance(interfaces, list)
    assert all(isinstance(i, Interface) for i in interfaces)

    # 4. Routes
    routes = await driver.get_routes(RouteQuery())
    assert isinstance(routes, list)
    assert all(isinstance(r, Route) for r in routes)

    # 5. ARP
    arp_entries = await driver.get_arp_table()
    assert isinstance(arp_entries, list)
    assert all(isinstance(a, ArpEntry) for a in arp_entries)

    # 6. MAC Table
    mac_entries = await driver.get_mac_table()
    assert isinstance(mac_entries, list)
    assert all(isinstance(m, MacEntry) for m in mac_entries)

    # 7. Neighbors
    neighbors = await driver.get_neighbors()
    assert isinstance(neighbors, list)
    assert all(isinstance(n, Neighbor) for n in neighbors)

    # 8. Running Config
    config = await driver.get_running_config()
    assert isinstance(config, str)
    assert len(config) > 0

    # 9. Diagnostics Ping
    ping_res = await driver.ping(PingRequest(destination="192.168.1.1"))
    assert isinstance(ping_res, PingResult)
    assert ping_res.packets_transmitted > 0

    # 10. Diagnostics Traceroute
    trace_res = await driver.traceroute(TracerouteRequest(destination="192.168.1.1"))
    assert isinstance(trace_res, TracerouteResult)
    assert len(trace_res.hops) > 0
