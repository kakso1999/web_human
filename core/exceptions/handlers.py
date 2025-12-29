"""
异常处理模块
统一异常定义和处理
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from core.schemas.base import ErrorCode, ERROR_MESSAGES, error_response


class AppException(Exception):
    """应用异常基类"""

    def __init__(
        self,
        code: int,
        message: str = None,
        data: any = None,
        status_code: int = 400
    ):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "未知错误")
        self.data = data
        self.status_code = status_code
        super().__init__(self.message)


class UnauthorizedException(AppException):
    """未授权异常"""

    def __init__(self, message: str = None):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401
        )


class TokenExpiredException(AppException):
    """令牌过期异常"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.TOKEN_EXPIRED,
            status_code=401
        )


class TokenInvalidException(AppException):
    """令牌无效异常"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.TOKEN_INVALID,
            status_code=401
        )


class PermissionDeniedException(AppException):
    """权限不足异常"""

    def __init__(self, message: str = None):
        super().__init__(
            code=ErrorCode.PERMISSION_DENIED,
            message=message,
            status_code=403
        )


class NotFoundException(AppException):
    """资源不存在异常"""

    def __init__(self, message: str = None):
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=404
        )


class RateLimitedException(AppException):
    """限流异常"""

    def __init__(self):
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            status_code=429
        )


class ValidationException(AppException):
    """验证异常"""

    def __init__(self, message: str, data: any = None):
        super().__init__(
            code=ErrorCode.INVALID_PARAMS,
            message=message,
            data=data,
            status_code=422
        )


# 异常处理器
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """应用异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.code, exc.message, exc.data)
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """请求验证异常处理器"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"]
        })

    return JSONResponse(
        status_code=422,
        content=error_response(
            ErrorCode.INVALID_PARAMS,
            "参数验证失败",
            errors
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            exc.status_code * 100,  # 简单的错误码映射
            exc.detail
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    # 生产环境不暴露详细错误信息
    from core.config.settings import get_settings
    settings = get_settings()

    # 调试：记录异常详情
    import traceback
    with open("debug_exception.log", "a") as f:
        f.write(f"\n\n{'='*50}\n")
        f.write(f"[Exception] {type(exc).__name__}: {exc}\n")
        f.write(f"URL: {request.url}\n")
        f.write(f"Method: {request.method}\n")
        f.write(f"Traceback:\n{traceback.format_exc()}\n")

    message = str(exc) if settings.DEBUG else "服务器内部错误"

    return JSONResponse(
        status_code=500,
        content=error_response(
            ErrorCode.UNKNOWN_ERROR,
            message
        )
    )


def register_exception_handlers(app):
    """注册所有异常处理器"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
