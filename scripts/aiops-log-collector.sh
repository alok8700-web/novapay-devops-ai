#!/bin/bash

set -euo pipefail

CONTAINER="novapay"
AIOPS_URL="http://localhost:8000/logs/analyze"
STATE_FILE="/tmp/novapay-aiops-log-count"

LOGS=$(docker logs "$CONTAINER" 2>&1)

CURRENT_COUNT=$(printf '%s\n' "$LOGS" | wc -l)

if [[ -f "$STATE_FILE" ]]; then
    PREVIOUS_COUNT=$(cat "$STATE_FILE")
else
    PREVIOUS_COUNT=0
fi

if (( CURRENT_COUNT < PREVIOUS_COUNT )); then
    PREVIOUS_COUNT=0
fi

NEW_LOGS=$(printf '%s\n' "$LOGS" | tail -n +"$((PREVIOUS_COUNT + 1))")

printf '%s\n' "$CURRENT_COUNT" > "$STATE_FILE"

printf '%s\n' "$NEW_LOGS" |
python3 -c '
import json
import sys

logs = sys.stdin.read()
print(json.dumps({"logs": logs}))
' |
curl -sS \
  -X POST "$AIOPS_URL" \
  -H "Content-Type: application/json" \
  --data-binary @-
