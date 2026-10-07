#!/bin/bash

set -euo pipefail

CONTAINER="novapay"
AIOPS_URL="http://localhost:8000/logs/analyze"

LOGS=$(docker logs --tail 100 "$CONTAINER" 2>&1)

PAYLOAD=$(python3 -c '
import json
import sys

logs = sys.stdin.read()
print(json.dumps({"logs": logs}))
' <<< "$LOGS")

curl -sS \
  -X POST "$AIOPS_URL" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
