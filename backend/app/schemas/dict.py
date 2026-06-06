# ============================================================
#  数据字典 Schema
# ============================================================
from datetime import datetime
from pydantic import BaseModel, Field


class DictTypeCreate(BaseModel):
    type_code: str = Field(..., min_length=1, max_length=50)
    type_name: str = Field(..., min_length=1, max_length=100)
    remark: str | None = None


class DictTypeOut(BaseModel):
    id: int
    type_code: str
    type_name: str
    status: int
    remark: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DictItemCreate(BaseModel):
    item_label: str = Field(..., min_length=1, max_length=100)
    item_value: str = Field(..., min_length=1, max_length=100)
    sort_order: int = 0


class DictItemOut(BaseModel):
    id: int
    type_id: int
    item_label: str
    item_value: str
    sort_order: int
    status: int
    created_at: datetime

    class Config:
        from_attributes = True
