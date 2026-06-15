# ============================================================
#  后端 Dockerfile - FastAPI + Uvicorn (开发模式)
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# 使用国内 apt 镜像加速下载
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# 系统依赖（PaddleOCR 需要 libgl1/libegl1）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    libmagic1 \
    libmagic-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖清单，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 上传文件目录
RUN mkdir -p /app/uploads/contracts /app/uploads/invoices /app/uploads/reports

# 入口脚本（确保依赖完整后启动服务）
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

# 使用入口脚本启动
ENTRYPOINT ["/entrypoint.sh"]
