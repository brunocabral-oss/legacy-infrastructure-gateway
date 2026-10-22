# ADR 0001: API-First Architecture

## Status
Accepted

## Context
Legacy network infrastructure is traditionally managed via vendor-specific CLI over SSH or telnet, proprietary GUIs, or disparate APIs. Exposing raw CLI execution or bespoke scripts directly to consumers creates vendor lock-in, elevates security risks, and makes automated orchestration brittle.

## Decision
LIG adopts an **API-First** architectural design. All interactions with network infrastructure must be expressed as standardized RESTful operations using semantic endpoints (e.g., `GET /devices/{device}/routes`). The core application translates semantic requests into vendor-specific operations and normalizes all responses into vendor-neutral Pydantic domain models.

## Consequences
- **Positive**: Consumers do not need to know vendor CLI syntax or parse strings.
- **Positive**: Consistent schema validation and OpenAPI contract specifications.
- **Negative**: Requires maintenance of translation drivers and parsers for each supported platform.
