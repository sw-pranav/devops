#!/usr/bin/env bash
# Generate traffic so the Grafana panels have something to show. Ctrl+C to stop.
URL="${1:-http://localhost:5000}"
echo "Sending traffic to $URL ..."
while true; do
  for path in / /api/items /api/items /health /slow /error; do
    curl -s -o /dev/null "$URL$path" &
  done
  wait
  sleep 0.5
done
