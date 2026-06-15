# 智能项目管理系统 - Docker 开发环境

## 快速开始

```bash
# 1. 复制环境变量配置
cp .env.example .env
# 编辑 .env 修改密码等敏感配置

# 2. 启动所有服务
docker compose up -d

# 3. 访问系统
# 前端 (Nginx 入口): http://localhost
# 前端 (Vite 直连):  http://localhost:5173
# 后端 API 文档:     http://localhost:8080/docs
# 数据库:            localhost:3306
```

## 架构说明

| 服务 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| mysql | MySQL 8.0 | 3306 | 关系数据库 |
| backend | FastAPI + Uvicorn | 8080 | 后端 API |
| frontend | Vue 3 + Vite | 5173 | 前端开发服务器 |
| nginx | Nginx Alpine | 80 | 反向代理 |

## 开发模式特性

- **后端热加载**: 源码通过卷挂载，`uvicorn --reload` 自动重载，修改代码后自动生效
- **前端 HMR**: Vite dev server 支持模块热替换，修改代码后浏览器自动刷新
- **数据库持久化**: MySQL 数据存储在 `./mysql-data/` 目录，手动管理
- **文件上传持久化**: 上传文件存储在 `./uploads/` 目录

## 常用命令

```bash
# 启动
docker compose up -d

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启后端（代码改动后）
docker compose restart backend

# 停止（保留数据）
docker compose down

# 停止并清除所有数据（包括数据库）
docker compose down -v

# 重新构建镜像（依赖变更时）
docker compose build --no-cache backend
docker compose up -d
```

## 目录结构

```
OCR-docker/
├── docker-compose.yml      # Docker Compose 编排
├── .env                    # 环境变量（从 .env.example 复制）
├── .env.example            # 环境变量模板
├── mysql/
│   └── init.sql            # MySQL 初始化脚本
├── nginx/
│   └── nginx.conf          # Nginx 反向代理配置
├── backend/                # 后端源码（卷挂载）
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── api/            # 路由层
│       ├── models/         # ORM 模型
│       ├── schemas/        # Pydantic Schema
│       ├── services/       # 业务逻辑层
│       ├── core/           # OCR/NLP 引擎
│       ├── utils/          # 工具函数
│       ├── dependencies.py # 依赖注入
│       ├── exceptions.py   # 异常类
│       └── config.py       # 配置管理
├── frontend/               # 前端源码（卷挂载）
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── api/            # API 请求封装
│       ├── router/         # 路由配置
│       ├── store/          # Pinia 状态管理
│       └── views/          # 页面组件
├── uploads/                # 上传文件存储
│   ├── contracts/          # 合同文件
│   ├── invoices/           # 发票文件
│   └── reports/            # 验收报告
└── mysql-data/             # MySQL 数据文件（自动生成）
```

## 默认账号

> 应用启动时会自动补齐以下演示账号（幂等，不覆盖已存在账号），因此即使
> `mysql-data/` 数据卷已存在、`init.sql` 未重跑，也能正常登录。

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 123456 | 管理员 |
| business | 123456 | 商务经理 |
| finance | 123456 | 财务总监 |
| pm | 123456 | 项目经理 |
