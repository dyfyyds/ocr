"""
通用文件上传与下载接口
"""
import os

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mysql import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.file_utils import (
    validate_file_type,
    validate_file_size,
    generate_safe_filename,
    get_upload_path,
)
from app.exceptions import NotFoundError
from app.config import settings

router = APIRouter()

ALLOWED_CATEGORIES = {"contracts", "invoices", "reports", "payments"}


@router.post("/{category}")
async def upload_file(
    category: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """通用文件上传。根据 category 决定存储目录和文件类型校验。"""
    if category not in ALLOWED_CATEGORIES:
        raise NotFoundError(f"不支持的上传分类: {category}")

    # 按分类选择校验类型
    type_map = {
        "contracts": "all",
        "invoices": "image",
        "reports": "all",
        "payments": "image",
    }
    validate_file_type(file.filename, type_map.get(category, "all"))
    content = await file.read()
    validate_file_size(len(content))

    safe_name = generate_safe_filename(file.filename)
    file_path = get_upload_path(category, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "message": "上传成功",
        "category": category,
        "filename": safe_name,
        "original_name": file.filename,
        "size": len(content),
        "url": f"/api/uploads/{category}/{safe_name}",
    }


@router.get("/{category}/{filename}")
async def download_file(
    category: str,
    filename: str,
):
    """文件下载 / 预览。"""
    if category not in ALLOWED_CATEGORIES:
        raise NotFoundError(f"不支持的分类: {category}")

    file_path = os.path.join(settings.UPLOAD_DIR, category, filename)
    if not os.path.isfile(file_path):
        raise NotFoundError("文件不存在")

    return FileResponse(file_path, filename=filename)
