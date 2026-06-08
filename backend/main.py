# ============================================================
#  智能项目管理系统 - FastAPI 应用入口
# ============================================================
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mysql import init_db, close_db
from app.api import auth, users, projects, invoices, payments, close, dashboard, dict_api, expenses, config_api, uploads, ocr
from app.middleware.exception_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库连接，关闭时释放资源。"""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="智能项目管理系统",
    description="项目全生命周期管理 API，支持合同 OCR、立项审核、开票回款、结项归档。",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册全局异常处理器
register_exception_handlers(app)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"])
app.include_router(invoices.router, prefix="/api/projects", tags=["开票管理"])
app.include_router(payments.router, prefix="/api/projects", tags=["回款管理"])
app.include_router(close.router, prefix="/api/projects", tags=["结项管理"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["工作台"])
app.include_router(dict_api.router, prefix="/api/dict", tags=["数据字典"])
app.include_router(expenses.router, prefix="/api/projects", tags=["支出管理"])
app.include_router(config_api.router, prefix="/api/config", tags=["系统配置"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["文件管理"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR 识别"])


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """健康检查端点，供 Docker 和 Nginx 探测使用。"""
    return {"status": "ok", "service": "智能项目管理系统"}
