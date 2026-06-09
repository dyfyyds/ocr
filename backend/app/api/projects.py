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
from app.models.project_close import ProjectClose
from app.schemas.projects import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    ProjectAuditRequest,
)
from app.dependencies import get_current_user, require_admin, require_role
from app.models.user import User
from app.utils.pagination import paginate, PageResponse
from app.utils.file_utils import validate_file_type, validate_file_size, generate_safe_filename, get_upload_path
from app.exceptions import NotFoundError, ValidationError
from app.core.contract_parser import (
    parse_word_contract, parse_pdf_contract,
    parse_word_contract_with_llm, parse_pdf_contract_with_llm,
)
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

    # 角色感知可见性：
    # - admin：全部项目
    # - business：仅自己创建的（草稿/审核中/驳回等全生命周期都看自己的）
    # - finance / pm：需要对「已立项 / 已结项」项目开票、回款、结项，
    #   这些项目并非他们创建，故放开 approved/closed 状态的可见性，
    #   否则财务/项目经理看不到任何可操作项目（历史 BUG）。
    if user.role == "business":
        query = query.where(Project.created_by == user.id)
        count_query = count_query.where(Project.created_by == user.id)
    elif user.role in ("finance", "pm"):
        visible = Project.status.in_(("approved", "closed"))
        query = query.where(visible)
        count_query = count_query.where(visible)
    # admin：不加额外过滤

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Project.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    projects = result.scalars().all()

    # 附加展示字段：创建人姓名 + 结项申请状态（一次性批量查询，避免 N+1）
    creators: dict[int, str] = {}
    creator_ids = {p.created_by for p in projects if p.created_by}
    if creator_ids:
        rows = (await db.execute(
            select(User.id, User.real_name, User.username).where(User.id.in_(creator_ids))
        )).all()
        creators = {r[0]: (r[1] or r[2]) for r in rows}

    closes: dict[int, ProjectClose] = {}
    proj_ids = [p.id for p in projects]
    if proj_ids:
        crows = (await db.execute(
            select(ProjectClose).where(ProjectClose.project_id.in_(proj_ids))
        )).scalars().all()
        closes = {c.project_id: c for c in crows}

    items = []
    for p in projects:
        out = ProjectOut.model_validate(p)
        out.created_by_name = creators.get(p.created_by)
        c = closes.get(p.id)
        if c:
            out.close_status = c.status
            out.acceptance_report = c.acceptance_report_path
            out.close_date = c.close_date
        items.append(out)

    return paginate(items, total, page, size)


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
    user: User = Depends(require_role("business", "admin", "pm")),
    db: AsyncSession = Depends(get_db),
):
    """上传 Word 合同 → python-docx 提取文本 → NLP 实体提取 → 自动回填项目信息。

    允许的角色与项目详情页（admin/business/pm）保持一致，避免项目经理
    打开详情页却因鉴权被拒（403）。
    """
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

    # 调用 python-docx + 正则 + LLM 综合提取
    try:
        ocr_result = await parse_word_contract_with_llm(file_path)
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
    user: User = Depends(require_role("business", "admin", "pm")),
    db: AsyncSession = Depends(get_db),
):
    """上传盖章 PDF → OCR 识别文字 → NLP 提取关键字段。

    角色与项目详情页保持一致（admin/business/pm）。
    """
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

    # 调用 OCR + 正则 + LLM 综合提取
    try:
        ocr_result = await parse_pdf_contract_with_llm(file_path)
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

    # OCR 字段名 → Project 模型属性名映射
    FIELD_TO_ATTR = {
        "project_name": "project_name",
        "contract_amount": "contract_amount",
        "contract_no": "contract_no",
        "sign_date": "sign_date",
        "customer_name": "customer_name",
    }

    # 动态构建录入信息：遍历 OCR 提取的字段，从项目记录中取对应值
    input_data = {}
    for field in ocr_data:
        attr = FIELD_TO_ATTR.get(field, field)
        val = getattr(project, attr, None)
        if isinstance(val, Decimal):
            input_data[field] = str(val)
        elif isinstance(val, date):
            input_data[field] = str(val)
        else:
            input_data[field] = val or ""

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


@router.get("/{project_id}/contracts")
async def list_contracts(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目所有合同文件列表（含 OCR 结果）。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("项目不存在")

    contracts = (await db.execute(
        select(Contract).where(Contract.project_id == project_id)
        .order_by(Contract.file_type, Contract.version.desc())
    )).scalars().all()

    items = []
    for c in contracts:
        ocr = c.ocr_result or {}
        items.append({
            "id": c.id,
            "file_type": c.file_type,
            "file_name": c.file_name,
            "version": c.version,
            "extracted": ocr.get("extracted", {}),
            "extracted_by": ocr.get("extracted_by", {}),
            "raw_text": ocr.get("raw_text", ""),
            "source": ocr.get("source", ""),
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"contracts": items}


@router.post("/{project_id}/analyze-versions")
async def analyze_versions(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """多版本 OCR 分析：用 LLM 对比分析该项目所有 PDF 版本的 OCR 结果差异。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")

    # 获取所有 PDF 合同版本
    contracts = (await db.execute(
        select(Contract).where(
            Contract.project_id == project_id,
            Contract.file_type == "pdf",
        ).order_by(Contract.version.asc())
    )).scalars().all()

    if len(contracts) < 2:
        raise ValidationError("至少需要上传 2 个 PDF 版本才能进行版本分析")

    # 收集各版本的 OCR 结果
    versions = []
    for c in contracts:
        if c.ocr_result and c.ocr_result.get("extracted"):
            versions.append({
                "version": c.version,
                "file_name": c.file_name,
                "raw_text": c.ocr_result.get("raw_text", ""),
                "extracted": c.ocr_result["extracted"],
            })

    if len(versions) < 2:
        raise ValidationError("至少需要 2 个有效 OCR 结果才能进行版本分析")

    # 调用 LLM 分析版本差异
    from app.core.llm_extractor import llm_extractor
    analysis = await llm_extractor.analyze_versions(versions)

    return {
        "versions": versions,
        "analysis": analysis,
    }


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
    # 草稿或已驳回的项目都可提交立项（支持驳回后修改再提交）
    if project.status not in ("draft", "rejected"):
        raise ValidationError("只有草稿或已驳回的项目可以提交立项")

    project.status = "pending_audit"
    # 重新提交时清除上一次的审核意见
    project.audit_reason = None

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
