#!/bin/bash
# ============================================================
#  后端容器入口脚本
#  确保依赖已安装后启动 uvicorn
# ============================================================
set -e

# 检查是否需要安装依赖（首次启动或依赖被 volume 覆盖时）
if ! python -c "import fastapi" 2>/dev/null; then
    echo ">>> 检测到依赖缺失，正在安装..."
    pip install --no-cache-dir -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
fi

# 启动 uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8080 --reload
