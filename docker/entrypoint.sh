#!/usr/bin/env bash
set -euo pipefail

echo "[LIG] Starting Legacy Infrastructure Gateway container..."

# Execute command passed from Docker
exec "$@"
