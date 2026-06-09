# ============================================================
#  项目管理 Schema
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


def _empty_str_to_none(v: str | None) -> str | None:
    """将空字符串统一转为 None，避免前端传 "" 时 Pydantic 解析失败。"""
    if v is not None and isinstance(v, str) and v.strip() == '':
        return None
    return v


def _empty_str_to_none_any(v):
    """对任意类型字段，将空字符串转为 None（用于 date/Decimal/int 等可选字段）。"""
    if v is not None and isinstance(v, str) and v.strip() == '':
        return None
    return v


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)
    contract_no: str | None = None
    contract_amount: Decimal | None = None
    customer_name: str | None = None
    project_type: str | None = None
    pm_id: int | None = None
    sign_date: date | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    description: str | None = None

    @field_validator('contract_no', 'customer_name', 'project_type', 'description', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        return _empty_str_to_none(v)

    @field_validator('sign_date', 'expected_start_date', 'expected_end_date', 'contract_amount', 'pm_id', mode='before')
    @classmethod
    def empty_str_to_none_non_str(cls, v):
        return _empty_str_to_none_any(v)


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(None, min_length=1, max_length=200)
    contract_no: str | None = None
    contract_amount: Decimal | None = None
    customer_name: str | None = None
    project_type: str | None = None
    pm_id: int | None = None
    sign_date: date | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    description: str | None = None

    @field_validator('contract_no', 'customer_name', 'project_type', 'description', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        return _empty_str_to_none(v)

    @field_validator('sign_date', 'expected_start_date', 'expected_end_date', 'contract_amount', 'pm_id', mode='before')
    @classmethod
    def empty_str_to_none_non_str(cls, v):
        return _empty_str_to_none_any(v)


class ProjectOut(BaseModel):
    id: int
    project_name: str
    contract_no: str | None
    contract_amount: Decimal | None
    customer_name: str | None
    project_type: str | None
    pm_id: int | None
    sign_date: date | None
    status: str
    created_by: int
    created_at: datetime
    description: str | None = None         # 项目说明 + 差异核对备注，供审核人真实查看
    audit_reason: str | None = None       # 立项审核意见（驳回原因），供商务查看
    # 列表接口附加字段（其它接口默认为 None）：
    created_by_name: str | None = None    # 创建人姓名/用户名，用于前端「申请人/创建人」展示
    close_status: str | None = None       # 结项申请状态：None / pending / approved / rejected
    acceptance_report: str | None = None  # 验收报告文件路径（非空表示已上传）
    close_date: date | None = None        # 结项日期

    class Config:
        from_attributes = True


class ProjectAuditRequest(BaseModel):
    result: str = Field(..., pattern="^(approved|rejected)$")
    reason: str | None = None


class DiffItem(BaseModel):
    field_name: str
    ocr_value: str | None
    input_value: str | None
    diff_type: str | None
    confirmed: bool = False


class ConfirmDiffRequest(BaseModel):
    diffs: list[DiffItem]
