#!/usr/bin/env bash
# Start interviewphodo backend with Python 3.12 + Pipecat
set -e
cd "$(dirname "$0")"
lsof -i :8000 -t 2>/dev/null | xargs kill 2>/dev/null || true
sleep 1
exec .venv312/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000
