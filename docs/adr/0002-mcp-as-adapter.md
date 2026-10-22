# ADR 0002: Model Context Protocol (MCP) as an Upstream Consumer Adapter

## Status
Accepted

## Context
There is increasing demand to integrate network telemetry with AI systems and autonomous LLM agents. However, connecting LLMs directly to network devices or giving agents direct SSH access creates catastrophic security, prompt injection, and operational risks.

## Decision
LIG is designed to function 100% deterministically without artificial intelligence. MCP is treated strictly as an **optional upstream consumer adapter** that consumes the public LIG REST API via standard HTTP. The core gateway and drivers will NEVER import MCP libraries, invoke LLM inference, or grant AI agents direct device access.

## Consequences
- **Positive**: Strict boundary enforcement; LLMs can only invoke pre-approved semantic operations.
- **Positive**: All AI interactions are logged, validated by policy engines, and audited identically to human or CI/CD API calls.
- **Positive**: Zero bloat in the core engine.
