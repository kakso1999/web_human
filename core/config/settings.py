"""
配置管理模块
使用 pydantic-settings 从环境变量加载配置
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    APP_NAME: str = "Echobot"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    AES_KEY: str = "your-aes-key-change-in-production-32b"

    # JWT 配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # MongoDB 配置
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "echobot"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379"

    # 限流配置
    RATE_LIMIT_PER_MINUTE: int = 60

    # Google OAuth 配置
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_VIDEO_TYPES: list = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/avi", "video/mpeg", "application/octet-stream"]
    ALLOWED_AUDIO_TYPES: list = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/m4a"]

    # APICore 配置
    APICORE_API_KEY: str = "sk-2lABiLDoSOocQjuwACtRWItGEEvSHM4jt0kgCQPgEb0NPS3O"
    APICORE_BASE_URL: str = "https://api.apicore.ai"

    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
