# ============================================================
#  数据字典接口
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.dict_type import DictType
from app.models.dict_item import DictItem
from app.schemas.dict import DictTypeCreate, DictTypeOut, DictItemCreate, DictItemOut
from app.dependencies import require_admin, get_current_user
from app.models.user import User
from app.exceptions import NotFoundError, ValidationError

router = APIRouter()


# ==================== 字典类型 ====================

@router.get("/types")
async def list_dict_types(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有字典类型。"""
    result = await db.execute(select(DictType).order_by(DictType.id))
    types = result.scalars().all()
    return {"items": [DictTypeOut.model_validate(t) for t in types]}


@router.post("/types", response_model=DictTypeOut)
async def create_dict_type(
    body: DictTypeCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """新增字典类型。"""
    exists = (await db.execute(
        select(DictType).where(DictType.type_code == body.type_code)
    )).scalar_one_or_none()
    if exists:
        raise ValidationError("字典类型编码已存在")

    dict_type = DictType(type_code=body.type_code, type_name=body.type_name, remark=body.remark)
    db.add(dict_type)
    await db.flush()
    await db.refresh(dict_type)
    return DictTypeOut.model_validate(dict_type)


@router.delete("/types/{type_id}")
async def delete_dict_type(
    type_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除字典类型（级联删除字典项）。"""
    result = await db.execute(select(DictType).where(DictType.id == type_id))
    dict_type = result.scalar_one_or_none()
    if not dict_type:
        raise NotFoundError("字典类型不存在")
    await db.delete(dict_type)
    return {"message": "删除成功"}


# ==================== 字典项 ====================

@router.get("/types/{type_code}/items")
async def list_dict_items(
    type_code: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按类型编码获取字典项列表。"""
    type_result = await db.execute(select(DictType).where(DictType.type_code == type_code))
    dict_type = type_result.scalar_one_or_none()
    if not dict_type:
        raise NotFoundError("字典类型不存在")

    result = await db.execute(
        select(DictItem).where(DictItem.type_id == dict_type.id).order_by(DictItem.sort_order)
    )
    items = result.scalars().all()
    return {"items": [DictItemOut.model_validate(i) for i in items]}


@router.post("/types/{type_id}/items", response_model=DictItemOut)
async def create_dict_item(
    type_id: int,
    body: DictItemCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """新增字典项。"""
    type_result = await db.execute(select(DictType).where(DictType.id == type_id))
    if not type_result.scalar_one_or_none():
        raise NotFoundError("字典类型不存在")

    item = DictItem(
        type_id=type_id,
        item_label=body.item_label,
        item_value=body.item_value,
        sort_order=body.sort_order,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return DictItemOut.model_validate(item)


@router.delete("/items/{item_id}")
async def delete_dict_item(
    item_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除字典项。"""
    result = await db.execute(select(DictItem).where(DictItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundError("字典项不存在")
    await db.delete(item)
    return {"message": "删除成功"}
