# ============================================================
#  项目管理接口 - 登记/维护/校验/审核
# ============================================================
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date

from app.db.mysql import get_db
from app.models.project import Project
from app.models.contract import Contract
from app.models.contract_diff import ContractDiff
from app.schemas.projects import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    ProjectAuditRequest,
)
from app.dependencies import get_current_user, require_admin, require_role
from app.models.user import User
from app.utils.pagination import paginate, PageResponse
from app.utils.file_utils import validate_file_type, validate_file_size, generate_safe_filename, get_upload_path
from app.exceptions import NotFoundError, ValidationError
from app.core.contract_parser import parse_word_contract, parse_pdf_contract
from app.core.contract_verifier import verifier

router = APIRouter()


@router.get("", response_model=PageResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """项目列表（分页 + 筛选）。"""
    query = select(Project)
    count_query = select(func.count(Project.id))

    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)
    if keyword:
        query = query.where(Project.project_name.contains(keyword) | Project.customer_name.contains(keyword))
        count_query = count_query.where(Project.project_name.contains(keyword) | Project.customer_name.contains(keyword))

    if user.role not in ("admin",):
        query = query.where(Project.created_by == user.id)
        count_query = count_query.where(Project.created_by == user.id)

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Project.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    projects = result.scalars().all()

    return paginate([ProjectOut.model_validate(p) for p in projects], total, page, size)


@router.post("/register", response_model=ProjectOut)
async def register_project(
    body: ProjectCreate,
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """立项登记（手动填写表单）。"""
    project = Project(
        project_name=body.project_name,
        contract_no=body.contract_no,
        contract_amount=body.contract_amount,
        customer_name=body.customer_name,
        project_type=body.project_type,
        pm_id=body.pm_id,
        sign_date=body.sign_date,
        expected_start_date=body.expected_start_date,
        expected_end_date=body.expected_end_date,
        description=body.description,
        status="draft",
        created_by=user.id,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return ProjectOut.model_validate(project)


@router.post("/{project_id}/upload-word")
async def upload_word_contract(
    project_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """上传 Word 合同 → python-docx 提取文本 → NLP 实体提取 → 自动回填项目信息。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")

    validate_file_type(file.filename, "word")
    content = await file.read()
    validate_file_size(len(content))

    # 保存文件
    safe_name = generate_safe_filename(file.filename)
    file_path = get_upload_path("contracts", safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # 记录合同文件
    contract = Contract(
        project_id=project_id,
        file_type="word",
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        uploaded_by=user.id,
    )
    db.add(contract)

    # 调用 python-docx + NLP 提取
    try:
        ocr_result = parse_word_contract(file_path)
        extracted = ocr_result["extracted"]

        # 自动回填项目信息（仅当项目字段为空时）
        if extracted.get("project_name") and not project.project_name:
            project.project_name = extracted["project_name"]
        if extracted.get("contract_amount") and not project.contract_amount:
            try:
                project.contract_amount = Decimal(extracted["contract_amount"])
            except Exception:
                pass
        if extracted.get("contract_no") and not project.contract_no:
            project.contract_no = extracted["contract_no"]
        if extracted.get("customer_name") and not project.customer_name:
            project.customer_name = extracted["customer_name"]
        if extracted.get("sign_date") and not project.sign_date:
            try:
                project.sign_date = date.fromisoformat(extracted["sign_date"])
            except Exception:
                pass

        contract.ocr_result = ocr_result
    except Exception as e:
        ocr_result = {"error": str(e), "source": "python-docx"}
        contract.ocr_result = ocr_result

    await db.flush()
    return {
        "message": "Word 合同上传成功",
        "contract_id": contract.id,
        "ocr_result": contract.ocr_result,
        "project": ProjectOut.model_validate(project).model_dump(),
    }


@router.post("/{project_id}/upload-pdf")
async def upload_pdf_contract(
    project_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """上传盖章 PDF → OCR 识别文字 → NLP 提取关键字段。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")

    validate_file_type(file.filename, "pdf")
    content = await file.read()
    validate_file_size(len(content))

    safe_name = generate_safe_filename(file.filename)
    file_path = get_upload_path("contracts", safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # 查询当前版本号
    max_ver = (await db.execute(
        select(func.max(Contract.version)).where(
            Contract.project_id == project_id, Contract.file_type == "pdf"
        )
    )).scalar() or 0

    contract = Contract(
        project_id=project_id,
        file_type="pdf",
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        version=max_ver + 1,
        uploaded_by=user.id,
    )
    db.add(contract)

    # 调用 OCR + NLP 提取
    try:
        ocr_result = parse_pdf_contract(file_path)
        contract.ocr_result = ocr_result
    except Exception as e:
        ocr_result = {"error": str(e), "source": "paddleocr"}
        contract.ocr_result = ocr_result

    await db.flush()
    return {
        "message": "PDF 合同上传成功",
        "contract_id": contract.id,
        "version": contract.version,
        "ocr_result": contract.ocr_result,
    }


@router.post("/{project_id}/verify")
async def verify_contract(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """合同校验：比对 PDF OCR 结果与项目录入信息。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")

    # 获取最新的 PDF 合同 OCR 结果（limit(1) 避免多条记录崩溃）
    pdf_contract = (await db.execute(
        select(Contract).where(
            Contract.project_id == project_id,
            Contract.file_type == "pdf",
        ).order_by(Contract.version.desc()).limit(1)
    )).scalar_one_or_none()

    if not pdf_contract or not pdf_contract.ocr_result:
        raise ValidationError("请先上传 PDF 合同")

    # 从 OCR 结果中提取字段
    ocr_data = pdf_contract.ocr_result.get("extracted", {})

    # 项目录入信息
    input_data = {
        "project_name": project.project_name or "",
        "contract_amount": str(project.contract_amount) if project.contract_amount else "",
        "contract_no": project.contract_no or "",
        "sign_date": str(project.sign_date) if project.sign_date else "",
    }

    # 调用校验引擎
    diffs = verifier.verify(ocr_data, input_data)

    # 保存差异记录到数据库
    # 先清除旧的差异记录
    old_diffs = (await db.execute(
        select(ContractDiff).where(ContractDiff.project_id == project_id)
    )).scalars().all()
    for d in old_diffs:
        await db.delete(d)

    for diff in diffs:
        db.add(ContractDiff(
            project_id=project_id,
            field_name=diff["field_name"],
            ocr_value=diff["ocr_value"],
            input_value=diff["input_value"],
            diff_type=diff["diff_type"],
        ))

    await db.flush()
    return {"diffs": diffs, "ocr_raw": ocr_data}


@router.post("/{project_id}/submit")
async def submit_project(
    project_id: int,
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """提交立项申请。"""
    from app.models.activity_log import ActivityLog

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status != "draft":
        raise ValidationError("只有草稿状态的项目可以提交")

    project.status = "pending_audit"

    db.add(ActivityLog(
        action="project_submit",
        detail=f"项目「{project.project_name}」提交立项申请",
        user_id=user.id,
        project_id=project_id,
    ))

    await db.flush()
    return {"message": "提交成功", "status": project.status}


@router.post("/{project_id}/audit")
async def audit_project(
    project_id: int,
    body: ProjectAuditRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """审核立项。"""
    from datetime import datetime, timezone
    from app.models.audit_log import AuditLog
    from app.models.activity_log import ActivityLog

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status != "pending_audit":
        raise ValidationError("项目不在待审核状态")

    project.status = body.result
    project.audit_by = admin.id
    project.audit_time = datetime.now(timezone.utc)
    project.audit_reason = body.reason

    # 写入审核日志
    db.add(AuditLog(
        project_id=project_id,
        action="project_audit",
        result=body.result,
        reason=body.reason,
        reviewer_id=admin.id,
    ))

    # 写入活动日志
    action_label = "审核通过" if body.result == "approved" else "审核驳回"
    db.add(ActivityLog(
        action=f"audit_{body.result}",
        detail=f"项目「{project.project_name}」{action_label}",
        user_id=admin.id,
        project_id=project_id,
    ))

    await db.flush()
    return {"message": f"审核完成: {body.result}", "status": project.status}


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目详情。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    return ProjectOut.model_validate(project)


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """更新项目信息。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status not in ("draft", "rejected"):
        raise ValidationError("只有草稿或已驳回的项目可以修改")

    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(project, k, v)

    await db.flush()
    await db.refresh(project)
    return ProjectOut.model_validate(project)
