# ============================================================
#  项目支出管理接口
# ============================================================
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.mysql import get_db
from app.models.project import Project
from app.models.project_expense import ProjectExpense
from app.schemas.expenses import ExpenseCreate, ExpenseOut
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.get("/{project_id}/expenses")
async def list_expenses(
    project_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取项目支出列表。"""
    result = await db.execute(
        select(ProjectExpense).where(ProjectExpense.project_id == project_id)
        .order_by(ProjectExpense.expense_date.desc())
    )
    expenses = result.scalars().all()
    total = sum(float(e.amount) for e in expenses)
    return {"items": [ExpenseOut.model_validate(e) for e in expenses], "total": total}


@router.post("/{project_id}/expenses", response_model=ExpenseOut)
async def create_expense(
    project_id: int,
    body: ExpenseCreate,
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """添加支出项。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status not in ("draft", "rejected"):
        raise ValidationError("只有草稿或已驳回的项目可以添加支出")

    expense = ProjectExpense(
        project_id=project_id,
        description=body.description,
        amount=body.amount,
        expense_date=body.expense_date,
        created_by=user.id,
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return ExpenseOut.model_validate(expense)


@router.delete("/{project_id}/expenses/{expense_id}")
async def delete_expense(
    project_id: int,
    expense_id: int,
    user: User = Depends(require_role("business", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """删除支出项。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("项目不存在")
    if project.status not in ("draft", "rejected"):
        raise ValidationError("只有草稿或已驳回的项目可以删除支出")

    exp = (await db.execute(
        select(ProjectExpense).where(
            ProjectExpense.id == expense_id,
            ProjectExpense.project_id == project_id,
        )
    )).scalar_one_or_none()
    if not exp:
        raise NotFoundError("支出记录不存在")

    await db.delete(exp)
    return {"message": "删除成功"}
