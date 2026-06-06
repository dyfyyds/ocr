# ============================================================
#  用户管理接口（管理员）
# ============================================================
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.mysql import get_db
from app.models.user import User
from app.schemas.users import UserCreate, UserUpdate, UserOut, UserListQuery
from app.dependencies import require_admin
from app.utils.security import bcrypt_hash
from app.utils.pagination import paginate, PageResponse
from app.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.get("", response_model=PageResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    role: str | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """用户列表（分页 + 筛选）。"""
    query = select(User)
    count_query = select(func.count(User.id))

    if keyword:
        query = query.where(User.username.contains(keyword) | User.real_name.contains(keyword))
        count_query = count_query.where(User.username.contains(keyword) | User.real_name.contains(keyword))
    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(User.id.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    return paginate([UserOut.model_validate(u) for u in users], total, page, size)


@router.post("", response_model=UserOut)
async def create_user(
    body: UserCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """新增用户。"""
    # 检查用户名唯一
    exists = (await db.execute(select(User).where(User.username == body.username))).scalar_one_or_none()
    if exists:
        raise ValidationError("用户名已存在")

    user = User(
        username=body.username,
        password_hash=bcrypt_hash(body.password),
        real_name=body.real_name,
        email=body.email,
        phone=body.phone,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """编辑用户。"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户不存在")

    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(user, k, v)

    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.put("/{user_id}/status")
async def toggle_user_status(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用用户。"""
    if user_id == admin.id:
        raise ValidationError("不能禁用自己的账号")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户不存在")

    user.status = 0 if user.status == 1 else 1
    await db.flush()
    return {"id": user.id, "status": user.status}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除用户。"""
    if user_id == admin.id:
        raise ValidationError("不能删除自己的账号")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户不存在")

    await db.delete(user)
    return {"message": "删除成功"}
