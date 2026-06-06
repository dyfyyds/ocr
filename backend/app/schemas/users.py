# ============================================================
#  用户管理 Schema
# ============================================================
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    real_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str = Field(..., pattern="^(admin|business|finance|pm)$")


class UserUpdate(BaseModel):
    real_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = Field(None, pattern="^(admin|business|finance|pm)$")


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str | None
    email: str | None
    phone: str | None
    role: str
    status: int
    last_login: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListQuery(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    keyword: str | None = None
    role: str | None = None
