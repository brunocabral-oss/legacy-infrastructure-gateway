# Contributing to Legacy Infrastructure Gateway (LIG)

Thank you for contributing to LIG!

## Core Architectural Principles

Before opening a pull request, ensure your contribution respects our core rules:
1. **Semantic over Syntactic**: Consumers request semantic operations (`routes.read`), never arbitrary commands (`show ip route ...`).
2. **Fail-Closed / Deny-by-Default**: Unknown operations, unknown platforms, or unverified capabilities must return proper error codes (`501 Not Implemented`, `403 Forbidden`, `404 Not Found`).
3. **Read-Only**: Write operations, configuration pushes, and raw CLI executions are disabled.
4. **Third-Party Licenses**: Only MIT, BSD, or Apache-2.0 licensed dependencies are permitted. Check and record new dependencies in `NOTICE`.
5. **No AI in Core**: The core gateway must function 100% deterministically without AI or LLM dependencies. MCP is strictly an upstream consumer adapter.
6. **Zero Credentials in Artifacts**: Never log or return passwords, secrets, or keys.

## Development Workflow

1. Fork or branch from `main`.
2. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests and linters:
   ```bash
   pytest
   ruff check .
   mypy src
   ```
4. Submit PR with clear description and contract test verification.
