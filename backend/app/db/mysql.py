# ============================================================
#  数据库连接管理 - SQLAlchemy async engine + sessionmaker
# ============================================================
import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

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


async def init_db(max_retries: int = 30, retry_interval: float = 1.0):
    """启动时初始化数据库连接池。

    MySQL 容器即使 healthcheck 通过，仍可能在 backend 单独 restart / uvicorn --reload
    重跑 lifespan 的瞬间短暂不可用。此处带退避重试，确保后端永不因 MySQL 瞬时不可用
    而 "Application startup failed. Exiting."；仅在多次重试仍失败时才放弃并抛出。
    """
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda _: None)
            if attempt > 1:
                logger.info("MySQL 连接成功（第 %d 次尝试）。", attempt)
            return
        except Exception as e:  # noqa: BLE001 — 启动期需容忍任意连接异常并重试
            last_err = e
            logger.warning(
                "等待 MySQL 就绪… (%d/%d) %s", attempt, max_retries, e.__class__.__name__
            )
            # 连接池里可能缓存了失败的连接，丢弃后重建
            await engine.dispose()
            await asyncio.sleep(retry_interval)
    logger.error("MySQL 在 %d 次重试后仍不可用，启动失败。", max_retries)
    raise last_err  # type: ignore[misc]


async def close_db():
    """关闭时释放数据库连接池。"""
    await engine.dispose()
