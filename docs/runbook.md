# Operational Runbook: Legacy Infrastructure Gateway (LIG)

This runbook covers routine operations, incident troubleshooting, and security maintenance.

---

## 1. Routine Verification & Health Checks

### Check Service Health
```bash
# Check if API process is alive
curl -s http://localhost:8000/health/live

# Check if inventory and drivers are ready
curl -s http://localhost:8000/health/ready
```

### Inspect Audit Logs
All operations emit structured JSON logs tagged with `AUDIT_EVENT`.
To view audit events in real time:
```bash
docker logs -f lig-api | grep "AUDIT_EVENT"
```

Sample event:
```json
{
  "event_id": "evt_1a2b3c4d5e6f",
  "request_id": "req_01H...",
  "timestamp": "2026-10-22T15:40:00Z",
  "actor": "engineer_lab",
  "consumer": "rest-api",
  "source_ip": "192.168.10.50",
  "device": "VDORTD-A",
  "operation": "routes.read",
  "parameters": {"vrf": "lab"},
  "decision": "allowed",
  "driver": "CiscoIOSDriver",
  "transport": "ssh",
  "result": "success",
  "duration_ms": 420
}
```

---

## 2. Troubleshooting Incidents

### Scenario A: HTTP 504 (Device Timeout)
- **Symptom**: API returns `504 Gateway Timeout` with message `Operation timed out after 30s on device '...'`.
- **Root Cause**: Device management interface unresponsive, SSH dropped by firewall, or device CPU overloaded.
- **Action**:
  1. Verify TCP 22 connectivity from the Gateway VM to the target device:
     ```bash
     nc -zv -w 3 192.168.199.45 22
     ```
  2. Check if the device technical user session limit is reached (check active VTY lines on router).
  3. Verify whether Prometheus metric `lig_device_operation_duration_seconds` shows spikes.

### Scenario B: HTTP 401 / 403 (Authentication or Policy Denied)
- **Symptom**: Caller receives 401 Unauthorized or 403 Forbidden.
- **Action**:
  1. Check if caller is sending `X-API-Key: <token>` or `Authorization: Bearer <token>`.
  2. If 403 Forbidden: check if the operation attempted to modify device configuration or run an unapproved command. Remember: the gateway is strictly **Read-Only**.

### Scenario C: HTTP 429 (Rate Limit Exceeded)
- **Symptom**: Caller receives `429 Too Many Requests`.
- **Action**:
  1. Inspect `Retry-After` header.
  2. If legitimate bulk querying is required, tune `max_requests` in `src/lig/security/rate_limit.py`.

---

## 3. Credential & Token Rotation

1. **Rotate Device Credentials**:
   - Update `LIG_CRED_<PROFILE>_PASSWORD` in `/opt/legacy-infrastructure-gateway/.env`.
   - Zero restart is required if using dynamic secret providers; otherwise reload: `docker-compose restart api`.

2. **Rotate API Token**:
   - Add the new token to `LIG_API_TOKEN_READER` / `LIG_API_TOKEN_ADMIN` in `.env`.
   - Perform rolling reload.
