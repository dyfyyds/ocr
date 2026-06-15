# ============================================================
#  统一响应信封 {code, message, data}
#  采纳 OCR-IPMS 的响应契约模式：成功 code=200。
#  说明：全局成功信封由 ResponseEnvelopeMiddleware 自动套用，
#  路由通常**直接返回业务数据/Pydantic 模型即可**；当需要自定义
#  message（或显式构造信封）时使用 ok()/paginated()。
# ============================================================
from typing import Any


def ok(data: Any = None, message: str = "success") -> dict:
    """构造成功信封。"""
    return {"code": 200, "message": message, "data": data}


def paginated(items: list, total: int, page: int, size: int, message: str = "success") -> dict:
    """构造分页信封（data 内沿用既有 PageResponse 形状）。"""
    return ok(
        {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if size > 0 else 0,
        },
        message,
    )


def is_envelope(payload: Any) -> bool:
    """判断 payload 是否已是信封形状（供中间件避免二次包裹）。"""
    return isinstance(payload, dict) and {"code", "message", "data"} <= payload.keys()
