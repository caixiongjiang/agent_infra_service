#!/bin/bash

COMPOSE_FILE="docker-compose-bge-m3.yml"
ENV_FILE="bge-m3.env"

echo "▶️  正在停止 BGE-M3 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down

echo "✅ 服务已停止。"
