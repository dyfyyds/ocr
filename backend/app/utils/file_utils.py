# ============================================================
#  文件工具 - 类型校验、大小校验、安全文件名
# ============================================================
import os
import uuid
from pathlib import Path

from app.config import settings
from app.exceptions import ValidationError

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    "word": {".docx"},
    "pdf": {".pdf"},
    "image": {".jpg", ".jpeg", ".png", ".bmp", ".tiff"},
    "all": {".docx", ".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"},
}


def validate_file_type(filename: str, allowed_type: str = "all") -> str:
    """校验文件类型，返回小写扩展名。"""
    ext = Path(filename).suffix.lower()
    allowed = ALLOWED_EXTENSIONS.get(allowed_type, ALLOWED_EXTENSIONS["all"])
    if ext not in allowed:
        raise ValidationError(f"不支持的文件类型: {ext}，允许: {', '.join(allowed)}")
    return ext


def validate_file_size(size: int) -> None:
    """校验文件大小。"""
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size > max_size:
        raise ValidationError(f"文件大小超过限制: {size / 1024 / 1024:.1f}MB > {settings.MAX_FILE_SIZE_MB}MB")


def generate_safe_filename(original_filename: str) -> str:
    """生成安全的唯一文件名，保留原始扩展名。"""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def get_upload_path(category: str, filename: str) -> str:
    """获取上传文件的完整路径。"""
    upload_dir = os.path.join(settings.UPLOAD_DIR, category)
    os.makedirs(upload_dir, exist_ok=True)
    return os.path.join(upload_dir, filename)
