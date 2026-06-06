# ============================================================
#  结项管理 Schema
# ============================================================
from datetime import date, datetime
from pydantic import BaseModel, Field


class CloseRequest(BaseModel):
    close_date: date
    close_reason: str | None = None


class CloseAuditRequest(BaseModel):
    result: str = Field(..., pattern="^(approved|rejected)$")
    reason: str | None = None


class CloseOut(BaseModel):
    id: int
    project_id: int
    close_date: date
    close_reason: str | None
    acceptance_report_path: str | None
    status: str
    reviewer_id: int | None
    review_time: datetime | None
    review_reason: str | None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
