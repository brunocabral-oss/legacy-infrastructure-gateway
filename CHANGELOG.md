# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-22

### Added
- **Phase 0 (Foundation)**:
  - Open source governance, MIT license, and third-party dependency notice (`NOTICE`).
  - Strict security policy (`SECURITY.md`), contribution guidelines (`CONTRIBUTING.md`), and code of conduct (`CODE_OF_CONDUCT.md`).
  - Architecture Decision Records (ADRs 0001 through 0005) establishing API-First design, Read-Only MVP, MCP as upstream consumer, Driver contract, and Raw Access policy.
- **Phase 1 (Core Domain & Mock Driver)**:
  - Normalized Pydantic v2 domain models for `DeviceFacts`, `Interface`, `Route`, `ArpEntry`, `MacEntry`, `Neighbor`, `PingResult`, and `TracerouteResult`.
  - Deterministic `CapabilityService` enforcing fail-closed status (`501 Not Implemented`) for unsupported platform actions.
  - Fail-closed `PolicyEngine` enforcing read-only operation and denying raw command executions.
  - In-memory `AuditService` recording immutable events with automated credential and token redaction.
  - Unified REST API with `/health/live`, `/health/ready`, `/metrics`, and `/api/v1/devices/...`.
  - Self-contained `MockDriver` with comprehensive fixtures for deterministic offline development and testing.
- **Phase 2 (Cisco IOS & Netmiko Transport)**:
  - Non-blocking `NetmikoTransport` running synchronous Netmiko CLI commands in Python thread workers (`asyncio.to_thread`).
  - Secure `EnvironmentCredentialProvider` resolving technical user credentials from environment variables without database persistence.
  - `CiscoIOSDriver` utilizing NTC Templates and resilient regex fallbacks for facts, interfaces, routes, ARP, MAC, CDP/LLDP neighbors, ping, and traceroute.
  - Rigorous contract test suite asserting Cisco IOS compliance.
- **Phase 3 (Multivendor Support: Cisco IOS-XR & Fortinet FortiOS)**:
  - `CiscoIOSXRDriver` implementing semantic operations with explicit capability flags (e.g. `mac.read` marked unsupported with 501 response).
  - `FortiOSDriver` supporting Fortinet FortiOS (FortiOS v5.x / v6.x) with custom regex parsing for system status, physical interfaces, routing tables, and ARP tables.
  - Cross-vendor contract test suite (`test_multivendor_semantics.py`) validating unified Pydantic schema across Cisco IOS, IOS-XR, and FortiGate.
- **Phase 4 (Hardening, Security & Operational Runbooks)**:
  - API Token authentication supporting both `X-API-Key` and `Authorization: Bearer <token>`.
  - Role-Based Access Control (RBAC) with `read_only`, `network_operator`, and `admin` roles.
  - Sliding-window in-memory rate limiter returning `429 Too Many Requests` with `Retry-After` headers.
  - Prometheus metrics instrumentation for security telemetry (`lig_auth_failures_total`, `lig_rate_limit_exceeded_total`).
  - Hardened Dockerfile with non-root user (`liguser`, UID 1000) and multi-stage container optimization.
  - Comprehensive operational deployment guide (`docs/deployment.md`) and incident runbook (`docs/runbook.md`).
