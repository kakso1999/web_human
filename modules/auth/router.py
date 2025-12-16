"""
Auth 模块 - API 路由
登录、注册、Token 刷新等接口
"""
from fastapi import APIRouter, Depends, Response

from core.schemas.base import success_response
from core.middleware.auth import get_current_user_id
from core.config.settings import get_settings

from modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    GoogleAuthRequest,
    ChangePasswordRequest
)
from modules.auth.service import get_auth_service, AuthService

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户注册

    - **email**: 邮箱地址
    - **password**: 密码（至少8位，包含大小写字母和数字）
    - **nickname**: 昵称（2-50个字符）
    """
    user, tokens = await auth_service.register(data)

    return success_response({
        "user": user.model_dump(),
        "tokens": tokens.model_dump()
    })


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录

    - **email**: 邮箱地址
    - **password**: 密码
    """
    user, tokens = await auth_service.login(data)

    # 将 refresh_token 设置到 HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,  # 生产环境启用 HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return success_response({
        "user": user.model_dump(),
        "tokens": {
            "access_token": tokens.access_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in
        }
    })


@router.post("/refresh")
async def refresh_token(
    data: RefreshTokenRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新 Token

    - **refresh_token**: 刷新令牌
    """
    tokens = await auth_service.refresh_token(data.refresh_token)

    # 更新 Cookie 中的 refresh_token
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return success_response({
        "access_token": tokens.access_token,
        "token_type": tokens.token_type,
        "expires_in": tokens.expires_in
    })


@router.post("/logout")
async def logout(
    response: Response,
    user_id: str = Depends(get_current_user_id)
):
    """
    用户登出

    清除 Cookie 中的 refresh_token
    """
    response.delete_cookie("refresh_token")

    # TODO: 将当前 token 加入黑名单

    return success_response(message="登出成功")


@router.post("/google")
async def google_auth(
    data: GoogleAuthRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Google 账号登录

    - **code**: Google 授权码
    """
    user, tokens = await auth_service.google_login(data.code)

    # 将 refresh_token 设置到 HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return success_response({
        "user": user.model_dump(),
        "tokens": {
            "access_token": tokens.access_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in
        }
    })


@router.get("/google/url")
async def get_google_auth_url():
    """
    获取 Google 登录 URL

    前端重定向到此 URL 进行 Google 授权
    """
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
    )

    return success_response({"url": google_auth_url})
