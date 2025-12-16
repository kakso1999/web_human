"""
Auth 模块 - 业务逻辑层
登录、注册、Token 刷新等业务逻辑
"""
from typing import Optional, Tuple
import httpx

from core.config.settings import get_settings
from core.security.jwt import create_token_pair, verify_refresh_token, TokenPair
from core.security.password import verify_password
from core.exceptions.handlers import (
    AppException,
    UnauthorizedException,
    ValidationException
)
from core.schemas.base import ErrorCode

from modules.auth.repository import UserRepository
from modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    GoogleUserInfo
)

settings = get_settings()


class AuthService:
    """认证服务"""

    def __init__(self):
        self.user_repo = UserRepository()

    async def register(self, data: RegisterRequest) -> Tuple[UserResponse, TokenPair]:
        """
        用户注册

        Args:
            data: 注册请求数据

        Returns:
            (用户信息, Token 对)

        Raises:
            ValidationException: 邮箱已存在
        """
        # 检查邮箱是否已存在
        if await self.user_repo.email_exists(data.email):
            raise AppException(
                code=ErrorCode.USER_ALREADY_EXISTS,
                message="该邮箱已被注册"
            )

        # 创建用户
        user_id = await self.user_repo.create_user(
            email=data.email,
            password=data.password,
            nickname=data.nickname
        )

        # 获取用户信息
        user = await self.user_repo.get_by_id(user_id)

        # 生成 Token
        tokens = create_token_pair(user_id, user["role"])

        # 更新最后登录时间
        await self.user_repo.update_last_login(user_id)

        return self._to_user_response(user), tokens

    async def login(self, data: LoginRequest) -> Tuple[UserResponse, TokenPair]:
        """
        用户登录

        Args:
            data: 登录请求数据

        Returns:
            (用户信息, Token 对)

        Raises:
            UnauthorizedException: 用户不存在或密码错误
        """
        # 查找用户
        user = await self.user_repo.get_by_email(data.email)

        if not user:
            raise AppException(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在"
            )

        # 验证密码
        if not user.get("password_hash"):
            raise AppException(
                code=ErrorCode.INVALID_PASSWORD,
                message="该账号使用第三方登录，请使用 Google 登录"
            )

        if not verify_password(data.password, user["password_hash"]):
            raise AppException(
                code=ErrorCode.INVALID_PASSWORD,
                message="密码错误"
            )

        # 检查用户状态
        if not user.get("is_active", True):
            raise AppException(
                code=ErrorCode.USER_DISABLED,
                message="账号已被禁用"
            )

        # 生成 Token
        tokens = create_token_pair(user["id"], user["role"])

        # 更新最后登录时间
        await self.user_repo.update_last_login(user["id"])

        return self._to_user_response(user), tokens

    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """
        刷新 Token

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 Token 对

        Raises:
            UnauthorizedException: Token 无效或过期
        """
        # 验证 refresh token
        payload = verify_refresh_token(refresh_token)

        if not payload:
            raise AppException(
                code=ErrorCode.REFRESH_TOKEN_EXPIRED,
                message="刷新令牌无效或已过期，请重新登录"
            )

        # 检查用户是否存在
        user = await self.user_repo.get_by_id(payload.sub)

        if not user:
            raise AppException(
                code=ErrorCode.USER_NOT_FOUND,
                message="用户不存在"
            )

        if not user.get("is_active", True):
            raise AppException(
                code=ErrorCode.USER_DISABLED,
                message="账号已被禁用"
            )

        # 生成新的 Token 对
        return create_token_pair(user["id"], user["role"])

    async def google_login(self, code: str) -> Tuple[UserResponse, TokenPair]:
        """
        Google 登录

        Args:
            code: Google 授权码

        Returns:
            (用户信息, Token 对)
        """
        # 获取 Google 用户信息
        google_user = await self._get_google_user_info(code)

        # 查找是否已有关联账号
        user = await self.user_repo.get_by_google_id(google_user.id)

        if not user:
            # 检查邮箱是否已注册
            user = await self.user_repo.get_by_email(google_user.email)

            if user:
                # 关联已有账号
                await self.user_repo.link_google_account(
                    user["id"],
                    google_user.id,
                    google_user.picture
                )
            else:
                # 创建新用户
                user_id = await self.user_repo.create_user(
                    email=google_user.email,
                    password="",  # Google 登录无密码
                    nickname=google_user.name or google_user.email.split("@")[0],
                    google_id=google_user.id,
                    avatar_url=google_user.picture
                )
                user = await self.user_repo.get_by_id(user_id)

        # 检查用户状态
        if not user.get("is_active", True):
            raise AppException(
                code=ErrorCode.USER_DISABLED,
                message="账号已被禁用"
            )

        # 生成 Token
        tokens = create_token_pair(user["id"], user["role"])

        # 更新最后登录时间
        await self.user_repo.update_last_login(user["id"])

        return self._to_user_response(user), tokens

    async def _get_google_user_info(self, code: str) -> GoogleUserInfo:
        """
        通过授权码获取 Google 用户信息

        Args:
            code: Google 授权码

        Returns:
            Google 用户信息
        """
        async with httpx.AsyncClient() as client:
            # 1. 用授权码换取 access_token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )

            if token_response.status_code != 200:
                raise AppException(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Google 认证失败"
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            # 2. 获取用户信息
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if user_response.status_code != 200:
                raise AppException(
                    code=ErrorCode.UNAUTHORIZED,
                    message="获取 Google 用户信息失败"
                )

            user_data = user_response.json()

            return GoogleUserInfo(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name"),
                picture=user_data.get("picture"),
                verified_email=user_data.get("verified_email", False)
            )

    def _to_user_response(self, user: dict) -> UserResponse:
        """转换为用户响应"""
        return UserResponse(
            id=user["id"],
            email=user["email"],
            nickname=user["nickname"],
            avatar_url=user.get("avatar_url"),
            role=user["role"],
            is_active=user.get("is_active", True),
            created_at=user["created_at"]
        )


# 服务单例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
