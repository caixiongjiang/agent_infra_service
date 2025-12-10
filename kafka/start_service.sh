#!/bin/bash

# ==============================================================================
#  启动 Kafka Docker 容器的脚本
# ==============================================================================

# 设置颜色变量，让输出更清晰
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 定义服务名称
SERVICE_NAME="Kafka"

# 定义配置文件名
COMPOSE_FILE="docker-compose-kafka.yml"
ENV_FILE="kafka.env"
DATA_DIR="data" # 定义数据目录名，方便后续修改

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

# --- 步骤 2: 检查并创建数据目录 ---
echo "▶️  步骤 2: 检查并准备数据目录 '$DATA_DIR'..."

# 检查数据目录是否存在
if [ ! -d "$DATA_DIR" ]; then
    echo "   目录 '$DATA_DIR' 不存在，正在创建..."
    # 如果不存在，则创建目录
    mkdir "$DATA_DIR"
    # 检查 mkdir 命令是否成功
    if [ $? -eq 0 ]; then
        echo "   目录 '$DATA_DIR' 创建成功。"
        # 设置目录权限为 755
        echo "   正在设置目录权限为 755..."
        chmod 755 "$DATA_DIR"
        echo -e "${GREEN}✅ 数据目录准备就绪。${NC}"
    else
        # 如果创建目录失败，则报错并退出
        echo -e "${RED}❌ 错误: 创建目录 '$DATA_DIR' 失败！请检查当前用户的权限。${NC}"
        exit 1
    fi
else
    # 如果目录已存在，则打印信息并跳过
    echo -e "${GREEN}✅ 数据目录 '$DATA_DIR' 已存在，跳过创建。${NC}"
fi
echo ""

# --- 步骤 3: 执行 Docker Compose 命令 ---
echo "▶️  正在尝试以后台模式启动 $SERVICE_NAME 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# --- 步骤 4: 检查命令是否执行成功 ---
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