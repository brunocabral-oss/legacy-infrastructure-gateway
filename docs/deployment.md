# Deployment Guide: Legacy Infrastructure Gateway (LIG)

## 1. LAB Infrastructure Overview

The Gateway is designed to run in a dedicated Linux Virtual Machine (or bare metal server) deployed in the LAB environment.

### Target Specifications:
- **Hostname**: `legacy-gateway-lab`
- **OS**: Ubuntu Server 22.04/24.04 LTS or Rocky Linux 9
- **CPU / RAM / Disk**: 4 vCPU / 8 GB RAM / 40 GB SSD
- **Network Interface**: Dedicated interface connected to the Management VLAN (`VLAN_MGMT`)

---

## 2. Network Boundary and Security Choke Point

```
[Consumers: Systems / NOC / MCP]
              │
              ▼ HTTPS (TCP 443)
┌──────────────────────────────────────────────┐
│           LIG Gateway Choke Point            │
│         API Container: 192.168.10.20         │
└──────────────────────┬───────────────────────┘
                       │
                       ▼ SSH Read-Only (TCP 22)
┌──────────────────────────────────────────────┐
│        Management Network (VLAN MGMT)        │
│  - VDORTD-A  (192.168.199.45)                │
│  - ASR-LAB   (192.168.100.10)                │
│  - CAGE      (192.168.200.138)               │
└──────────────────────────────────────────────┘
```

### Firewall Rules (Fail-Closed Matrix):
| Source | Destination | Protocol / Port | Purpose |
|---|---|---|---|
| Consumer Networks | Gateway VM | TCP 443 (HTTPS) | REST API & Documentation |
| Prometheus Server | Gateway VM | TCP 8000 (/metrics) | Telemetry scraping |
| Gateway VM | Network Devices | TCP 22 (SSH) | Read-only CLI collection |
| Gateway VM | NTP Server | UDP 123 | Clock synchronization |
| Gateway VM | DNS Server | UDP/TCP 53 | Hostname resolution |

---

## 3. Production Deployment with Docker Compose

### Step 1: Environment Variables Setup
On the server, clone the repository and configure `.env`:
```bash
git clone <repo-url> /opt/legacy-infrastructure-gateway
cd /opt/legacy-infrastructure-gateway
cp .env.example .env
```

Ensure production credentials and tokens are set in `.env` (permissions `chmod 600 .env`):
```ini
LIG_ENVIRONMENT=production
LIG_LOG_LEVEL=INFO
LIG_READ_ONLY_MODE=true
LIG_RAW_COMMANDS_ENABLED=false
LIG_DEFAULT_POLICY=deny

# Credentials for devices (never stored in DB or repository)
LIG_CRED_LAB_READER_USERNAME=lig_reader_lab
LIG_CRED_LAB_READER_PASSWORD=StrongTechnicalUserPassword123!

# Gateway API Tokens
LIG_API_TOKEN_READER=lig_tok_prod_reader_9872134
LIG_API_TOKEN_ADMIN=lig_tok_prod_admin_12893712
```

### Step 2: Launch Containers
```bash
docker-compose -f deploy/docker-compose.yml up -d --build
```

### Step 3: Verify Probes
```bash
curl -f http://localhost:8000/health/live
curl -f http://localhost:8000/health/ready
```
