#!/bin/bash


# 设置颜色变量，让输出更清晰
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 定义服务名称
SERVICE_NAME="Neo4J"

# 定义配置文件名
COMPOSE_FILE="docker-compose-neo4j.yml"
ENV_FILE="neo4j.env"

# --- 插件配置 ---
# 设置为 "true" 来启用插件检查功能
USE_PLUGIN="true"
# 定义插件文件的预期路径 (请确保与你的实际路径一致)
PLUGIN_FILE_PATH="./data/neo4j_plugins/apoc-5.26.10-core.jar"

# --- 步骤 1: 检查所需文件是否存在 ---
echo "▶️  检查所需文件..."
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ 错误: Compose 文件 '$COMPOSE_FILE' 不存在！请确保该文件在当前目录下。${NC}"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ 错误: 环境变量文件 '$ENV_FILE' 不存在！请确保该文件在当前目录下。${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 所需文件检查通过。${NC}"
echo ""

if [[ "$USE_PLUGIN" == "true" ]]; then
    echo "▶️  步骤 2: 检查插件文件 (已启用)..."
    # 检查插件文件本身是否存在
    if [ -f "$PLUGIN_FILE_PATH" ]; then
        echo -e "${GREEN}✅ 插件文件 '$PLUGIN_FILE_PATH' 已找到。${NC}\n"
    else
        echo -e "${RED}❌ 错误: 插件功能已启用，但插件文件 '$PLUGIN_FILE_PATH' 未找到！${NC}"
        echo -e "${YELLOW}👉 请下载对应的插件 .jar 文件并放置在正确的路径下，或者在脚本顶部将 USE_PLUGIN 设置为 'false' 以禁用此检查。${NC}"
        exit 1
    fi
else
    echo -e "ℹ️  步骤 2: 插件功能未启用，跳过检查。\n"
fi

# --- 步骤 2: 执行 Docker Compose 命令 ---
echo "▶️  正在尝试以后台模式启动 $SERVICE_NAME 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# --- 步骤 3: 检查命令是否执行成功 ---
# $? 会获取上一个命令的退出状态码。0 代表成功，非 0 代表失败。
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ $SERVICE_NAME 服务启动成功或已在运行中！${NC}"
    echo "----------------------------------------"
    echo "当前容器状态:"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    echo "----------------------------------------"
else
    echo -e "\n${RED}❌ $SERVICE_NAME 服务启动失败！${NC}"
    echo "请检查 Docker 是否正在运行，或者查看容器日志以获取详细错误信息。"
    echo "你可以使用以下命令查看日志:"
    echo "  docker compose -f $COMPOSE_FILE logs"
    exit 1
fi

exit 0