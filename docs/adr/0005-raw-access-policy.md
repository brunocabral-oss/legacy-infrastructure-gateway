# ADR 0005: Raw Command Execution Policy

## Status
Accepted

## Context
Operators occasionally request arbitrary command execution (e.g. `show vlan brief`) when a standardized semantic operation has not yet been implemented.

## Decision
In the MVP (v0.1.0):
- **Raw command execution is disabled by default** (`raw_commands: disabled`).
- No public raw command endpoint exists for standard consumers.
- Any future administrative raw execution endpoint must enforce:
  1. Administrative role requirement.
  2. Strict command allowlist.
  3. Operator justification parameter.
  4. Explicit `normalized: false` tag in metadata.
  5. Mandatory immutable audit logging.

## Consequences
- **Positive**: Eliminates arbitrary command injection attacks.
- **Positive**: Enforces deliberate extension of normalized models over ad-hoc scraping.
