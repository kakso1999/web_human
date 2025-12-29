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

    # 端口配置
    BACKEND_PORT: int = 8000

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    AES_KEY: str = "your-aes-key-change-in-production-32b"

    # JWT 配置
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2小时，适应长时间任务
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

    # APICore 配置 (Suno Stems, Whisper, etc.)
    APICORE_API_KEY: str = ""
    APICORE_BASE_URL: str = "https://ismaque.org"

    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    # 语音克隆服务配置
    VOICE_CLONE_SERVICE_URL: str = "http://localhost:3002"

    # 阿里云百炼 DashScope API 配置
    DASHSCOPE_API_KEY: Optional[str] = None

    # 后端公网访问 URL（用于阿里云 API 访问本地文件）
    # 开发环境可使用 ngrok 等工具暴露本地服务
    BACKEND_PUBLIC_URL: Optional[str] = None

    # 图床服务配置（用于托管音频文件供阿里云 API 访问）
    # 比 ngrok 更稳定可靠
    MEDIA_BED_URL: str = "http://112.124.70.81"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
