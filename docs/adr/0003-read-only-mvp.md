# ADR 0003: Read-Only MVP and Fail-Closed Security Posture

## Status
Accepted

## Context
Network outages are predominantly caused by unauthorized, untested, or unintended configuration changes. In legacy environments, granting write access through automated gateways requires extensive rollback, atomic commit, and dry-run guarantees.

## Decision
The MVP of LIG is strictly **Read-Only**:
- All operations are limited to state retrieval (`facts.read`, `interfaces.read`, `routes.read`, `arp.read`, `mac.read`, `neighbors.read`, `config.running.read`) and non-destructive diagnostics (`diagnostics.ping`, `diagnostics.traceroute`).
- Technical user accounts provisioned on target devices must be configured with read-only privilege levels.
- All configuration mutation attempts are rejected at the Policy Engine layer.

## Consequences
- **Positive**: Zero risk of inadvertent device reconfigurations or outages.
- **Positive**: High trust adoption by network operations and security teams.
- **Negative**: Write/provisioning use cases are deferred to future major milestones.
