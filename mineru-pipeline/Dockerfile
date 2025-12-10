# 使用NVIDIA CUDA基础镜像（Ubuntu 22.04）
FROM nvidia/cuda:12.4.0-base-ubuntu22.04

WORKDIR /app

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1


# 替换为阿里云Ubuntu源
RUN sed -i 's@archive.ubuntu.com@mirrors.aliyun.com@g' /etc/apt/sources.list && \
    sed -i 's@security.ubuntu.com@mirrors.aliyun.com@g' /etc/apt/sources.list

# 配置清华pip源
RUN mkdir -p /root/.pip && \
    echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple\ntrusted-host = pypi.tuna.tsinghua.edu.cn" > /root/.pip/pip.conf

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    vim \
    unzip \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    python-is-python3  \
    libgl1 \
    libglib2.0-0 \
    libgomp1&& \
    apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /root
COPY ./ ./

# 安装Python依赖
RUN pip install -r requirements.txt --index https://mirrors.aliyun.com/pypi/simple

# 复制应用文件
#COPY start_service.sh /app/start_service.sh
COPY magic-pdf.json /root/magic-pdf.json
#COPY app.py /app/app.py
#COPY multi_gpu_app.py /app/multi_gpu_app.py
#RUN chmod +x /app/start_service.sh
#
## 暴露端口并设置启动命令
#EXPOSE 8000
#ENTRYPOINT []
CMD ["python","multi_gpu_app.py"]
