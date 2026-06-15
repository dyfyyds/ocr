# ============================================================
#  系统配置读取工具 — 带内存 TTL 缓存，避免每次请求查 DB
# ============================================================
import time
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

# 内存缓存：{config_key: (value, expire_ts)}
_cache: dict[str, tuple[str, float]] = {}
_TTL = 60  # 秒


async def get_config_value(db: AsyncSession, key: str, default: str = "") -> str:
    """
    从 system_config 表读取配置值，带 60s 内存缓存。
    """
    now = time.time()
    cached = _cache.get(key)
    if cached and cached[1] > now:
        return cached[0]

    try:
        result = await db.execute(
            select(SystemConfig.config_value).where(SystemConfig.config_key == key)
        )
        row = result.scalar_one_or_none()
        value = row if row is not None else default
    except Exception as e:
        logger.warning(f"读取配置 {key} 失败，使用默认值: {e}")
        value = default

    _cache[key] = (value, now + _TTL)
    return value


async def get_llm_config(db: AsyncSession) -> dict[str, Any]:
    """
    一次读取全部 LLM 配置项，返回 dict。
    """
    return {
        "llm_enabled": await get_config_value(db, "llm_enabled", "false"),
        "llm_api_url": await get_config_value(db, "llm_api_url", ""),
        "llm_api_key": await get_config_value(db, "llm_api_key", ""),
        "llm_model": await get_config_value(db, "llm_model", "mimo-v2.5-pro"),
    }


def invalidate_config_cache(key: str | None = None):
    """
    清除缓存。key=None 清除全部。
    """
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()
