# ============================================================
#  全局成功响应信封中间件
#  对所有 /api/* 的成功 JSON 响应统一套 {code, message, data}。
# ============================================================
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.schemas.common import is_envelope

# 不套信封的路径前缀（基础设施探针，保持原始形状）
_SKIP_PREFIXES = ("/api/health",)


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """统一成功响应契约。

    - 仅处理 application/json 的成功响应（status < 400）；
    - 文件下载等非 JSON 响应（如 FileResponse）按 content-type 跳过，**不消费其 body**；
    - 错误响应（status >= 400）已由全局异常处理器套信封，原样透传；
    - 已是信封形状的响应不二次包裹（便于路由按需直接 return ok(...)）。
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if not path.startswith("/api/") or path.startswith(_SKIP_PREFIXES):
            return response
        if response.status_code >= 400:
            return response
        if "application/json" not in response.headers.get("content-type", ""):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return JSONResponse(
                {"code": 200, "message": "success", "data": None},
                status_code=response.status_code,
            )
        try:
            payload = json.loads(body)
        except Exception:
            # 非法 JSON：原样重建，绝不破坏
            return Response(content=body, status_code=response.status_code,
                            media_type=response.headers.get("content-type"))

        wrapped = payload if is_envelope(payload) else {
            "code": 200, "message": "success", "data": payload,
        }
        return JSONResponse(wrapped, status_code=response.status_code)
