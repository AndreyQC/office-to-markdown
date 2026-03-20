#!/bin/sh
set -e

# Запускаем MCP HTTP-сервер (FastMCP) в фоне
python mcp_server.py &

# Запускаем основное HTTP API (FastAPI / Uvicorn) на порту 8000
uvicorn main:app --host 0.0.0.0 --port 8000

