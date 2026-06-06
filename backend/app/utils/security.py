# ============================================================
#  安全工具 - bcrypt 哈希 / JWT 签发与验证
# ============================================================
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def bcrypt_hash(password: str) -> str:
    """生成 bcrypt 密码哈希。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配。"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_jwt(payload: dict, expires_delta: timedelta | None = None) -> str:
    """签发 JWT Token。"""
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=settings.JWT_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    """解码并验证 JWT Token。失败抛出 jwt 异常。"""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def create_access_token(user_id: int, role: str) -> str:
    """签发 access_token。"""
    return create_jwt({"user_id": user_id, "role": role, "type": "access"})


def create_refresh_token(user_id: int) -> str:
    """签发 refresh_token。"""
    return create_jwt(
        {"user_id": user_id, "type": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_EXPIRE_DAYS),
    )
