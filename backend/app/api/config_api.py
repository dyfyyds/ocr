# ============================================================
#  系统配置接口（管理员）
# ============================================================
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.system_config import SystemConfig
from app.dependencies import require_admin
from app.models.user import User
from app.exceptions import NotFoundError
from app.utils.config_helper import invalidate_config_cache

router = APIRouter()


@router.get("")
async def list_configs(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取所有系统配置。"""
    result = await db.execute(select(SystemConfig).order_by(SystemConfig.id))
    configs = result.scalars().all()
    return {"items": [
        {
            "id": c.id,
            "config_key": c.config_key,
            "config_value": c.config_value,
            "description": c.description,
        }
        for c in configs
    ]}


class ConfigUpdateBody(BaseModel):
    config_value: str


@router.put("/{config_id}")
async def update_config(
    config_id: int,
    body: ConfigUpdateBody,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新系统配置值（JSON body）。"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundError("配置项不存在")

    config.config_value = body.config_value
    await db.flush()

    # 清除该 key 的缓存，使下次读取立即生效
    invalidate_config_cache(config.config_key)

    return {"message": "更新成功", "config_key": config.config_key}


class TestLLMBody(BaseModel):
    llm_api_url: str
    llm_api_key: str
    llm_model: str


@router.post("/test-llm")
async def test_llm_connection(
    body: TestLLMBody,
    admin: User = Depends(require_admin),
):
    """测试 LLM 连通性：用给定配置发一条简单消息。"""
    from app.core.llm_client import LLMClient

    client = LLMClient()
    try:
        reply = await client.chat_with_config(
            config={
                "llm_api_url": body.llm_api_url,
                "llm_api_key": body.llm_api_key,
                "llm_model": body.llm_model,
            },
            messages=[
                {"role": "user", "content": "请回复"连接成功"四个字。"},
            ],
            max_tokens=32,
            timeout=15,
            retries=1,
        )
        return {"success": True, "reply": reply.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}
