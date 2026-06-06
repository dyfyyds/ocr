# ============================================================
#  项目管理 Schema
# ============================================================
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


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
