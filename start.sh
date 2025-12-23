#!/bin/bash
set -e

# Use Railway's PORT environment variable if set, otherwise default to 8000
# Ensure PORT is a valid integer
if [ -z "$PORT" ] || ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    PORT=8000
fi

echo "Starting server on port $PORT"

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

