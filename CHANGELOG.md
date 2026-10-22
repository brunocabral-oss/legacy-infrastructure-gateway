# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 0: Project foundation, governance, MIT license, third-party NOTICE.
- Phase 1: Core domain models (Pydantic v2), InfrastructureDriver contract, and MockDriver with static fixtures.
- Capability Engine with fail-closed checks (`501 Not Implemented` for unsupported capabilities).
- Policy Engine operating in strict read-only and deny-by-default posture.
- Audit Service with immutable event logging and credential redaction.
- REST API endpoints for device health, facts, interfaces, routes, ARP, MAC, neighbors, config, and diagnostics (ping/traceroute).
- Dockerfile, Docker Compose specification and health check probes.
- Phase 2: Asynchronous NetmikoTransport with thread workers (`asyncio.to_thread`) and safe credential provider.
- Cisco IOS driver (`cisco_ios`) with NTC Templates parsers, commands, and contract tests.
- Phase 3: Cisco IOS-XR driver (`cisco_iosxr`) supporting routing, ARP, LLDP, and explicit capability declarations.
- Fortinet FortiOS driver (`fortios`) supporting system status, physical interfaces, routing table, and ARP.
- Cross-vendor semantic contract verification suite guaranteeing identical Pydantic models across multivendor platforms.
