#!/bin/bash


# 设置颜色变量，让输出更清晰
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m' # 用于提示信息
NC='\033[0m' # No Color

# 定义服务名称
SERVICE_NAME="Milvus"

# 定义配置文件和目录名
COMPOSE_FILE="docker-compose-milvus-cpu-standalone.yml"
ENV_FILE="milvus.env"
DATA_DIR="./data" # Milvus 数据存储目录

# --- 步骤 1: 检查所需文件是否存在 ---
echo "▶️  步骤 1: 检查所需文件..."
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

# --- 步骤 2: 准备数据目录 (新增的关键步骤) ---
echo "▶️  步骤 2: 检查并准备数据目录 '$DATA_DIR'..."
# 检查数据目录是否存在
if [ ! -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}ℹ️  数据目录 '$DATA_DIR' 不存在，正在创建...${NC}"
    mkdir -p "$DATA_DIR"

    echo -e "${YELLOW}ℹ️  正在为数据目录设置权限 (owner/group 1001)，这对于容器内非 root 用户写入至关重要...${NC}"
    # 使用 sudo 更改目录所有者。容器内 Milvus/etcd 通常以非 root 用户 (如 UID 1001) 运行。
    sudo chown -R 1001:1001 "$DATA_DIR"

    # 检查 chown 命令是否成功
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 数据目录权限设置成功。${NC}"
    else
        echo -e "${RED}❌ 错误: 设置数据目录权限失败！${NC}"
        echo "请检查您是否有 sudo 权限，或者手动执行 'sudo chown -R 1001:1001 $DATA_DIR'。"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 数据目录 '$DATA_DIR' 已存在，跳过创建和权限设置。${NC}"
fi
echo ""

# --- 步骤 3: 执行 Docker Compose 命令 ---
echo "▶️  步骤 3: 正在尝试以后台模式启动 $SERVICE_NAME 服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# --- 步骤 4: 检查命令是否执行成功 ---
# $? 会获取上一个命令的退出状态码。0 代表成功，非 0 代表失败。
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ $SERVICE_NAME 服务启动命令已成功发送！${NC}"
    echo "----------------------------------------"
    echo "正在检查当前容器状态:"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
    echo "----------------------------------------"
    echo "服务可能需要 1-2 分钟完成初始化。您可以使用以下命令持续监控日志:"
    echo "  docker compose -f $COMPOSE_FILE logs -f standalone"
else
    echo -e "\n${RED}❌ $SERVICE_NAME 服务启动失败！${NC}"
    echo "请检查 Docker 是否正在运行，或者查看容器日志以获取详细错误信息。"
    echo "你可以使用以下命令查看日志:"
    echo "  docker compose -f $COMPOSE_FILE logs"
    exit 1
fi

exit 0