# ============================================================
#  系统配置接口（管理员）
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.system_config import SystemConfig
from app.dependencies import require_admin
from app.models.user import User
from app.exceptions import NotFoundError

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


@router.put("/{config_id}")
async def update_config(
    config_id: int,
    config_value: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新系统配置值。"""
    result = await db.execute(select(SystemConfig).where(SystemConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise NotFoundError("配置项不存在")

    config.config_value = config_value
    await db.flush()
    return {"message": "更新成功", "config_key": config.config_key}
