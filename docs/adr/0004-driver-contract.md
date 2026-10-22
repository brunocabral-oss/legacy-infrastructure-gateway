# ADR 0004: Uniform Infrastructure Driver Contract

## Status
Accepted

## Context
Supporting multiple network platforms (Cisco IOS, Cisco IOS-XR, FortiOS, Junos, etc.) across different connection protocols (Netmiko, NAPALM, RESTCONF, NETCONF) can quickly lead to spaghetti code if drivers do not adhere to a single uniform interface.

## Decision
All drivers must implement the abstract `InfrastructureDriver` class. Each method returns strongly typed Pydantic models.
When an underlying platform does not support an operation, the driver declares it via its capability profile, and the Capability Engine yields `501 Not Implemented`.

## Consequences
- **Positive**: Adding a new platform requires only writing a driver adhering to the contract; zero changes to API routes or core services.
- **Positive**: Strict decoupling of protocol libraries from business logic.
