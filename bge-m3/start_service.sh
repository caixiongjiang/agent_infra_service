#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SERVICE_NAME="BGE-M3"
COMPOSE_FILE="docker-compose-bge-m3.yml"
ENV_FILE="bge-m3.env"

echo "▶️  检查所需文件..."
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ 错误: Compose 文件 '$COMPOSE_FILE' 不存在！${NC}"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ 错误: 环境变量文件 '$ENV_FILE' 不存在！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 所需文件检查通过。${NC}"

echo "▶️  正在构建并启动 $SERVICE_NAME 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ $SERVICE_NAME 服务启动成功！${NC}"
    echo "端口: 18085"
    echo "接口: /v1/embeddings (Dense + Sparse)"
    echo "文档: http://localhost:18085/docs"
else
    echo -e "\n${RED}❌ $SERVICE_NAME 服务启动失败！${NC}"
    exit 1
fi
