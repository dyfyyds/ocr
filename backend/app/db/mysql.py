# ============================================================
#  数据库连接管理 - SQLAlchemy async engine + sessionmaker
# ============================================================
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# 异步 Session 工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """ORM 基类。"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话。"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """启动时初始化数据库连接池。"""
    # 测试连接是否可用
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)


async def close_db():
    """关闭时释放数据库连接池。"""
    await engine.dispose()
