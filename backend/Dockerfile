# ============================================================
#  后端 Dockerfile - FastAPI + Uvicorn (开发模式)
# ============================================================
FROM python:3.12-slim

WORKDIR /app

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

EXPOSE 8080

# 开发模式：--reload 热重载
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
