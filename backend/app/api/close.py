# ============================================================
#  结项管理接口
# ============================================================
from datetime import datetime, timezone, date

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.project import Project
from app.models.project_close import ProjectClose
from app.models.audit_log import AuditLog
from app.schemas.close import CloseAuditRequest
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.utils.file_utils import validate_file_type, validate_file_size, generate_safe_filename, get_upload_path
from app.exceptions import NotFoundError, ValidationError
from app.services.close import ensure_closeable, audit_close as audit_close_service

router = APIRouter()


@router.post("/{project_id}/close")
async def request_close(
    project_id: int,
    close_date: date = Form(...),
    close_reason: str = Form(None),
    file: UploadFile = File(None),
    user: User = Depends(require_role("pm", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """提交结项申请（不改项目状态，等审核通过后再改）。"""
    # 结项申请前置校验（服务层）：项目已立项且尚无结项申请
    await ensure_closeable(db, project_id)

    report_path = None
    if file:
        validate_file_type(file.filename, "all")
        content = await file.read()
        validate_file_size(len(content))
        safe_name = generate_safe_filename(file.filename)
        report_path = get_upload_path("reports", safe_name)
        try:
            with open(report_path, "wb") as f:
                f.write(content)
        except OSError as e:
            raise ValidationError(f"文件保存失败: {e}")

    close_record = ProjectClose(
        project_id=project_id,
        close_date=close_date,
        close_reason=close_reason,
        acceptance_report_path=report_path,
        status="pending",
        created_by=user.id,
    )
    db.add(close_record)
    await db.flush()
    return {"message": "结项申请提交成功", "status": "pending"}


@router.post("/{project_id}/close/audit")
async def audit_close(
    project_id: int,
    body: CloseAuditRequest,
    user: User = Depends(require_role("finance", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """审核结项：通过→项目状态变 closed，驳回→恢复 approved。"""
    await audit_close_service(db, project_id, body.result, body.reason, user)
    await db.flush()
    return {"message": f"结项审核完成: {body.result}"}
