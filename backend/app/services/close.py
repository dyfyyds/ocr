# ============================================================
#  结项服务层 — 结项申请 / 结项审核 的状态流转
# ============================================================
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.project_close import ProjectClose
from app.models.audit_log import AuditLog
from app.models.enums import CLOSEABLE_STATUSES, CLOSE_PENDING, CLOSE_APPROVED, PROJECT_CLOSED
from app.exceptions import NotFoundError, ValidationError


async def ensure_closeable(db: AsyncSession, project_id: int) -> Project:
    """结项申请前置校验：项目已立项且尚无结项申请。"""
    project = (await db.execute(
        select(Project).where(Project.id == project_id)
    )).scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status not in CLOSEABLE_STATUSES:
        raise ValidationError("只有已立项的项目可以申请结项")
    exists = (await db.execute(
        select(ProjectClose).where(ProjectClose.project_id == project_id)
    )).scalar_one_or_none()
    if exists:
        raise ValidationError("该项目已有结项申请")
    return project


async def audit_close(db: AsyncSession, project_id: int, result: str, reason: str | None, reviewer) -> ProjectClose:
    """结项审核：通过 → 项目 closed；驳回 → 项目保持 approved（记审核日志）。"""
    close_record = (await db.execute(
        select(ProjectClose).where(ProjectClose.project_id == project_id)
    )).scalar_one_or_none()
    if not close_record:
        raise NotFoundError("结项记录不存在")
    if close_record.status != CLOSE_PENDING:
        raise ValidationError("该结项记录不在待审核状态")

    close_record.status = result
    close_record.reviewer_id = reviewer.id
    close_record.review_time = datetime.now(timezone.utc)
    close_record.review_reason = reason

    if result == CLOSE_APPROVED:
        project = (await db.execute(
            select(Project).where(Project.id == project_id)
        )).scalar_one_or_none()
        if project:
            project.status = PROJECT_CLOSED

    db.add(AuditLog(
        project_id=project_id, action="close_audit",
        result=result, reason=reason, reviewer_id=reviewer.id,
    ))
    return close_record
