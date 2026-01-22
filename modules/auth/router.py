"""
Auth 模块 - API 路由
登录、注册、Token 刷新等接口
"""
from fastapi import APIRouter, Depends, Response, Query
from fastapi.responses import RedirectResponse

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
        "tokens": tokens.model_dump()
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
        "tokens": tokens.model_dump()
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


@router.post("/admin/init")
async def init_admin(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    初始化管理员账号

    仅当数据库中不存在任何管理员时可用。
    创建默认管理员账号：admin / admin123

    **注意**: 首次部署后请立即修改密码！
    """
    from modules.auth.repository import UserRepository

    user_repo = UserRepository()

    # 检查是否已存在管理员
    admin_count = await user_repo.count({"role": {"$in": ["admin", "super"]}})
    if admin_count > 0:
        return {"code": 40003, "message": "管理员已存在，无法重复初始化", "data": None}

    # 创建默认管理员
    admin_id = await user_repo.create_user(
        email="admin@echobot.local",
        password="admin123",
        nickname="Admin",
        role="admin"
    )

    # 获取用户信息
    admin = await user_repo.get_by_id(admin_id)

    # 生成 Token
    from core.security.jwt import create_token_pair
    tokens = create_token_pair(admin_id, "admin")

    # 设置 Cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return success_response({
        "message": "管理员初始化成功",
        "email": "admin@echobot.local",
        "password": "admin123",
        "warning": "请立即修改默认密码！",
        "tokens": tokens.model_dump()
    })


@router.get("/admin/check")
async def check_admin():
    """
    检查是否存在管理员账号

    用于前端判断是否需要显示初始化管理员按钮。
    """
    from modules.auth.repository import UserRepository

    user_repo = UserRepository()
    admin_count = await user_repo.count({"role": {"$in": ["admin", "super"]}})

    return success_response({
        "has_admin": admin_count > 0
    })


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Google 授权码"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Google OAuth 回调

    Google 认证成功后重定向到此地址，携带授权码。
    处理授权码并重定向到前端。
    """
    try:
        user, tokens = await auth_service.google_login(code)

        # 重定向到前端，带上 token 信息（使用配置的 FRONTEND_URL）
        settings = get_settings()
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        redirect_url = (
            f"{frontend_url}/auth/callback"
            f"?access_token={tokens.access_token}"
            f"&user_id={user.id}"
            f"&nickname={user.nickname}"
        )

        response = RedirectResponse(url=redirect_url)

        # 设置 refresh_token 到 Cookie
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return response

    except Exception as e:
        # 认证失败，重定向到登录页并带上错误信息
        settings = get_settings()
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed")
