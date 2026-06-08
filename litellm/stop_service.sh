#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SERVICE_NAME="LiteLLM"
COMPOSE_FILE="docker-compose-litellm.yml"
ENV_FILE="litellm.env"

echo "▶️  正在尝试停止并移除由 '$COMPOSE_FILE' 定义的服务..."

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ $SERVICE_NAME 所有相关服务已成功停止并移除。${NC}"
else
    echo -e "\n${RED}❌ 操作失败。请检查 Docker 是否在运行。${NC}"
    exit 1
fi

exit 0
