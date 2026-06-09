# ============================================================
#  智能项目管理系统 - FastAPI 应用入口
# ============================================================
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.db.mysql import init_db, close_db, async_session
from app.models.user import User
from app.utils.security import bcrypt_hash
from app.api import auth, users, projects, invoices, payments, close, dashboard, dict_api, expenses, config_api, uploads, ocr
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.response_envelope import ResponseEnvelopeMiddleware

logger = logging.getLogger(__name__)

# 演示账号（用户名, 姓名, 角色），统一密码见 DEMO_PASSWORD
DEMO_USERS = [
    ("admin", "系统管理员", "admin"),
    ("business", "张三（商务经理）", "business"),
    ("finance", "李四（财务总监）", "finance"),
    ("pm", "王五（项目经理）", "pm"),
]
DEMO_PASSWORD = "123456"


async def seed_demo_users():
    """幂等地补齐 / 规范化演示账号。

    mysql/init.sql 只在 MySQL 数据卷首次初始化时执行；当 ./mysql-data 已存在
    时不会重跑，导致演示账号缺失或密码与文档不一致（历史上 admin 曾用
    admin123），按文档凭据无法登录。此处在应用启动时确保 4 个演示账号都存在，
    且密码统一为 DEMO_PASSWORD、状态为启用，使登录始终与文档一致。
    """
    async with async_session() as session:
        for username, real_name, role in DEMO_USERS:
            user = (
                await session.execute(select(User).where(User.username == username))
            ).scalar_one_or_none()
            if user is None:
                session.add(User(
                    username=username,
                    password_hash=bcrypt_hash(DEMO_PASSWORD),
                    real_name=real_name,
                    role=role,
                    status=1,
                ))
                logger.info("已补齐演示账号: %s", username)
            else:
                # 规范化：重置为文档约定的演示密码并确保启用
                user.password_hash = bcrypt_hash(DEMO_PASSWORD)
                user.status = 1
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库连接并补齐演示账号，关闭时释放资源。"""
    await init_db()
    try:
        await seed_demo_users()
    except Exception as e:  # 补齐失败不应阻断服务启动
        logger.warning("演示账号补齐失败（忽略）: %s", e)
    yield
    await close_db()


app = FastAPI(
    title="智能项目管理系统",
    description="项目全生命周期管理 API，支持合同 OCR、立项审核、开票回款、结项归档。",
    version="1.0.0",
    lifespan=lifespan,
)

# 响应信封中间件：统一成功响应为 {code,message,data}。
# 先于 CORS 注册 → CORS 为最外层，信封重建响应后 CORS 头仍正确附加。
app.add_middleware(ResponseEnvelopeMiddleware)

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
