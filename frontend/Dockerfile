# ============================================================
#  前端 Dockerfile - 开发模式 (Vite HMR 热加载)
# ============================================================
FROM node:20-alpine

WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存层
COPY package.json package-lock.json* ./
RUN npm install --registry=https://registry.npmmirror.com

# 源码通过 volume 挂载，此处仅复制用于首次构建
COPY . .

EXPOSE 5173

# Vite 开发服务器，host 0.0.0.0 供容器外访问
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]
