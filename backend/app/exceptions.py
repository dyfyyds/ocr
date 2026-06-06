# ============================================================
#  自定义异常类
# ============================================================


class AppError(Exception):
    """应用异常基类。"""

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    """认证异常。"""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code="AUTH_ERROR", status_code=401)


class PermissionError(AppError):
    """权限异常。"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message, code="PERMISSION_DENIED", status_code=403)


class NotFoundError(AppError):
    """资源不存在。"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ValidationError(AppError):
    """业务校验异常。"""

    def __init__(self, message: str = "数据校验失败"):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422)
