"""
基础响应模型
统一 API 响应格式
"""
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')


class ResponseBase(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int
    message: str
    data: Optional[Any] = None


# 常用响应工厂函数
def success_response(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {
        "code": 0,
        "message": message,
        "data": data
    }


def error_response(code: int, message: str, data: Any = None) -> dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


# 常用错误码
class ErrorCode:
    """错误码定义"""

    # 通用错误 (1xxxx)
    UNKNOWN_ERROR = 10000
    INVALID_PARAMS = 10001
    NOT_FOUND = 10002
    PERMISSION_DENIED = 10003

    # 认证错误 (2xxxx)
    UNAUTHORIZED = 20001
    TOKEN_EXPIRED = 20002
    TOKEN_INVALID = 20003
    REFRESH_TOKEN_EXPIRED = 20004

    # 用户错误 (3xxxx)
    USER_NOT_FOUND = 30001
    USER_ALREADY_EXISTS = 30002
    INVALID_PASSWORD = 30003
    USER_DISABLED = 30004
    EMAIL_NOT_VERIFIED = 30005

    # 业务错误 (4xxxx)
    STORY_NOT_FOUND = 40001
    ORDER_NOT_FOUND = 40002
    SUBSCRIPTION_EXPIRED = 40003

    # 限流错误 (5xxxx)
    RATE_LIMITED = 50001


# 错误消息映射
ERROR_MESSAGES = {
    ErrorCode.UNKNOWN_ERROR: "未知错误",
    ErrorCode.INVALID_PARAMS: "参数验证失败",
    ErrorCode.NOT_FOUND: "资源不存在",
    ErrorCode.PERMISSION_DENIED: "权限不足",
    ErrorCode.UNAUTHORIZED: "未授权，请登录",
    ErrorCode.TOKEN_EXPIRED: "令牌已过期",
    ErrorCode.TOKEN_INVALID: "无效的令牌",
    ErrorCode.REFRESH_TOKEN_EXPIRED: "刷新令牌已过期，请重新登录",
    ErrorCode.USER_NOT_FOUND: "用户不存在",
    ErrorCode.USER_ALREADY_EXISTS: "用户已存在",
    ErrorCode.INVALID_PASSWORD: "密码错误",
    ErrorCode.USER_DISABLED: "用户已被禁用",
    ErrorCode.EMAIL_NOT_VERIFIED: "邮箱未验证",
    ErrorCode.STORY_NOT_FOUND: "故事不存在",
    ErrorCode.ORDER_NOT_FOUND: "订单不存在",
    ErrorCode.SUBSCRIPTION_EXPIRED: "订阅已过期",
    ErrorCode.RATE_LIMITED: "请求过于频繁，请稍后再试",
}
