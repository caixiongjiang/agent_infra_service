#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SERVICE_NAME="Logto Auth"
COMPOSE_FILE="docker-compose-logto-pgsql.yml"
ENV_FILE="logto.env"
DATA_DIR="./data/postgres"

echo "▶️  步骤 1: 检查所需文件..."
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ 错误: Compose 文件 '$COMPOSE_FILE' 不存在！请确保该文件在当前目录下。${NC}"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ 错误: 环境变量文件 '$ENV_FILE' 不存在！请确保该文件在当前目录下。${NC}"
    exit 1
fi

set -a
. "./$ENV_FILE"
set +a

echo -e "${GREEN}✅ 所需文件检查通过。${NC}"
echo ""

echo "▶️  步骤 2: 检查并准备数据目录 '$DATA_DIR'..."
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}ℹ️  数据目录 '$DATA_DIR' 不存在，正在创建...${NC}"
    mkdir -p "$DATA_DIR"
else
    echo -e "${GREEN}✅ 数据目录 '$DATA_DIR' 已存在，跳过创建。${NC}"
fi
echo ""

echo "▶️  步骤 3: 正在尝试以后台模式启动 $SERVICE_NAME 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ $SERVICE_NAME 服务启动命令已成功发送！${NC}"
    echo "----------------------------------------"
    echo "正在检查当前容器状态:"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo "----------------------------------------"
    echo "初始化完成后可通过以下地址访问:"
    echo "  用户接口: ${LOGTO_ENDPOINT:-http://localhost:3001}"
    echo "  管理后台: ${LOGTO_ADMIN_ENDPOINT:-http://localhost:3002}"
    echo "如需持续查看日志，可执行:"
    echo "  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs -f"
else
    echo -e "\n${RED}❌ $SERVICE_NAME 服务启动失败！${NC}"
    echo "请检查 Docker 是否正在运行，或者查看容器日志以获取详细错误信息。"
    echo "你可以使用以下命令查看日志:"
    echo "  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE logs"
    exit 1
fi

exit 0
