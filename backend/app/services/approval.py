# ============================================================
#  立项审批服务层 — 提交 / 审核 的状态流转
# ============================================================
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.audit_log import AuditLog
from app.models.activity_log import ActivityLog
from app.models.enums import (
    PROJECT_DRAFT, PROJECT_REJECTED, PROJECT_PENDING_AUDIT, PROJECT_APPROVED,
)
from app.exceptions import NotFoundError, ValidationError

# 可提交立项的状态（草稿 / 已驳回——支持驳回后修改再提交）
SUBMITTABLE_STATUSES = (PROJECT_DRAFT, PROJECT_REJECTED)


async def _get_project(db: AsyncSession, project_id: int) -> Project:
    project = (await db.execute(
        select(Project).where(Project.id == project_id)
    )).scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    return project


async def submit_for_approval(db: AsyncSession, project_id: int, user) -> Project:
    """提交立项：draft/rejected → pending_audit（并清除上次审核意见 + 记活动日志）。"""
    project = await _get_project(db, project_id)
    if project.status not in SUBMITTABLE_STATUSES:
        raise ValidationError("只有草稿或已驳回的项目可以提交立项")
    project.status = PROJECT_PENDING_AUDIT
    project.audit_reason = None
    db.add(ActivityLog(
        action="project_submit",
        detail=f"项目「{project.project_name}」提交立项申请",
        user_id=user.id,
        project_id=project_id,
    ))
    return project


async def audit_project(db: AsyncSession, project_id: int, result: str, reason: str | None, admin) -> Project:
    """立项审核：pending_audit → approved/rejected（记审核日志 + 活动日志）。"""
    project = await _get_project(db, project_id)
    if project.status != PROJECT_PENDING_AUDIT:
        raise ValidationError("项目不在待审核状态")
    project.status = result
    project.audit_by = admin.id
    project.audit_time = datetime.now(timezone.utc)
    project.audit_reason = reason
    db.add(AuditLog(
        project_id=project_id, action="project_audit",
        result=result, reason=reason, reviewer_id=admin.id,
    ))
    label = "审核通过" if result == PROJECT_APPROVED else "审核驳回"
    db.add(ActivityLog(
        action=f"audit_{result}",
        detail=f"项目「{project.project_name}」{label}",
        user_id=admin.id, project_id=project_id,
    ))
    return project
