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
