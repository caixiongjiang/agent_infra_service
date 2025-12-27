# MinerU Tianshu Dockerfile
# 基于 NVIDIA CUDA 镜像构建,支持 GPU 加速

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai \
    PYTHON_VERSION=3.13

# 配置 Ubuntu 清华源
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list && \
    sed -i 's@//.*security.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list

# 安装系统依赖和添加 deadsnakes PPA (用于安装新版 Python)
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y \
    python3.13 \
    python3.13-dev \
    python3.13-venv \
    git \
    wget \
    curl \
    vim \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 3.13 为默认 python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1 && \
    update-alternatives --set python3 /usr/bin/python3.13

# 升级 pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.13

# 配置 pip 清华源
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 创建工作目录
WORKDIR /app

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .

# 升级基础工具
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# 安装项目依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY api_server.py .
COPY litserve_worker.py .
COPY task_scheduler.py .
COPY task_db.py .
COPY start_all.py .
COPY client_example.py .
COPY download_models.py .

# 创建必要的目录
RUN mkdir -p /app/data \
    && mkdir -p /app/output \
    && mkdir -p /app/models

# 暴露端口
# 8000: API Server
# 9000: LitServe Worker
EXPOSE 8000 9000

# 设置启动命令
CMD ["python3", "start_all.py"]
