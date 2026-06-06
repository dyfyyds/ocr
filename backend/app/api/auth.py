# ============================================================
#  认证接口 - 登录/登出/刷新/改密
# ============================================================
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.mysql import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserBrief, RefreshRequest, ChangePasswordRequest
from app.dependencies import get_current_user
from app.exceptions import AuthError
from app.utils.security import verify_password, bcrypt_hash, create_access_token, create_refresh_token, decode_jwt

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录。"""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise AuthError("用户名或密码错误")
    if user.status != 1:
        raise AuthError("账号已被禁用")

    # 更新最后登录时间
    await db.execute(
        update(User).where(User.id == user.id).values(last_login=datetime.now(timezone.utc))
    )

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserBrief(id=user.id, username=user.username, real_name=user.real_name, role=user.role),
    )


@router.get("/me", response_model=UserBrief)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息。"""
    return UserBrief(id=user.id, username=user.username, real_name=user.real_name, role=user.role)


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """刷新 access_token。"""
    try:
        payload = decode_jwt(body.refresh_token)
    except Exception:
        raise AuthError("Refresh Token 无效或已过期")

    if payload.get("type") != "refresh":
        raise AuthError("Token 类型错误")

    user_id = payload.get("user_id")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or user.status != 1:
        raise AuthError("用户不存在或已被禁用")

    new_access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)

    return {"access_token": new_access, "refresh_token": new_refresh}


@router.put("/password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码。"""
    if not verify_password(body.old_password, user.password_hash):
        raise AuthError("原密码错误")

    new_hash = bcrypt_hash(body.new_password)
    await db.execute(update(User).where(User.id == user.id).values(password_hash=new_hash))

    return {"message": "密码修改成功"}
