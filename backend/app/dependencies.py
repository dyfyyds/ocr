# ============================================================
#  FastAPI 依赖注入 - JWT 解析、角色鉴权
# ============================================================
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.user import User
from app.exceptions import AuthError, PermissionError
from app.utils.security import decode_jwt

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 Authorization header 解析 JWT，返回当前用户。"""
    if not credentials:
        raise AuthError("缺少认证凭据")

    try:
        payload = decode_jwt(credentials.credentials)
    except Exception:
        raise AuthError("Token 无效或已过期")

    if payload.get("type") != "access":
        raise AuthError("Token 类型错误")

    user_id = payload.get("user_id")
    if not user_id:
        raise AuthError("Token 缺少用户信息")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthError("用户不存在")
    if user.status != 1:
        raise PermissionError("账号已被禁用")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求管理员角色。"""
    if user.role != "admin":
        raise PermissionError("需要管理员权限")
    return user


def require_role(*roles: str):
    """要求指定角色之一。"""
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise PermissionError(f"需要以下角色之一: {', '.join(roles)}")
        return user
    return _check
