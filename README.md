# Legacy Infrastructure Gateway (LIG)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Legacy Infrastructure Gateway (LIG)** is a vendor-agnostic, open-source integration platform that transforms legacy network infrastructure into programmable resources via a modern, normalized, auditable, and secure REST API.

---

## 🎯 Architectural Principles

1. **Vendor & Consumer Agnostic**: Callers request semantic operations (`routes.read`), not vendor CLI commands (`show ip route`).
2. **AI-Optional**: The platform operates 100% deterministically without artificial intelligence. MCP (Model Context Protocol) is strictly an upstream consumer adapter and never accesses devices directly.
3. **Read-Only First**: Fail-closed, deny-by-default security posture. No configuration mutations or raw CLI executions in the core gateway.
4. **Immutable Audit Engine**: Every request (allowed, denied, or failed) is recorded with full telemetry, duration, source IP, actor, and timing.
5. **No Credentials in Logs**: Rigorous redaction ensures secrets, tokens, passwords, and private keys never touch audit logs or API payloads.

---

## 🏗️ Architecture

```
CONSUMERS (curl / Python / PowerShell / MCP / Systems)
  │
  ▼ HTTPS / JSON (TCP 443)
┌───────────────────────────────────────────────┐
│              Legacy Gateway API               │
│        FastAPI · Pydantic · OpenAPI           │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│                 Gateway Core                  │
│   Operation Router · Policy · Capability      │
│                 Audit Engine                  │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│                Driver Manager                 │
└───────┬───────────────────────┬───────────────┘
        │                       │
┌───────▼────────┐      ┌───────▼────────┐      ┌───────────────┐
│ NAPALM Adapter │      │ Netmiko + NTC  │      │  Mock Driver  │
│ (Uniform APIs) │      │ (CLI fallback) │      │  (TDD/Dev)    │
└───────┬────────┘      └───────┬────────┘      └───────────────┘
        │                       │
        ▼ SSH Read-Only (TCP 22)▼
┌───────────────────────────────────────────────┐
│     Management Network (Cisco, Fortinet)      │
└───────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Development with Docker)

### 1. Clone & Configure
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
```bash
docker-compose -f deploy/docker-compose.yml up --build -d
```

### 3. Verify Health Probes
```bash
curl -s http://localhost:8000/health/live
# {"status":"alive","version":"0.1.0"}

curl -s http://localhost:8000/health/ready
# {"status":"ready","database":"connected","driver_registry":"initialized"}
```

### 4. Query Semantic Endpoints (Mock Device)
```bash
# Retrieve Device Facts
curl -s http://localhost:8000/api/v1/devices/mock-router/facts

# Retrieve Normalized Routing Table
curl -s "http://localhost:8000/api/v1/devices/mock-router/routes?vrf=lab"

# Retrieve Capabilities
curl -s http://localhost:8000/api/v1/devices/mock-router/capabilities
```

### 5. Interactive OpenAPI Documentation
Visit `http://localhost:8000/docs` in your browser.

---

## 🧪 Testing

To run the full unit and contract test suite locally:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
Third-party notices and licenses are cataloged in [NOTICE](NOTICE).
