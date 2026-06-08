#!/bin/bash
# ============================================================
#  后端容器入口脚本
#  等待 MySQL 就绪后启动 uvicorn
# ============================================================
set -e

# 等待 MySQL 可连接（最多等 60 秒）
echo ">>> 等待 MySQL 就绪..."
for i in $(seq 1 60); do
    if python3 -c "
import socket, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((os.environ.get('MYSQL_HOST', 'mysql'), int(os.environ.get('MYSQL_PORT', 3306))))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        echo ">>> MySQL 已就绪"
        break
    fi
    echo ">>> MySQL 未就绪，等待中... ($i/60)"
    sleep 1
done

# 检查是否需要安装依赖
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo ">>> 检测到依赖缺失，正在安装..."
    pip install --no-cache-dir -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
fi

# 启动 uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8080 --reload
