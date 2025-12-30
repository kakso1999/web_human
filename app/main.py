"""
Echobot API 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.config.settings import get_settings
from core.config.database import Database
from core.middleware.security_headers import SecurityHeadersMiddleware
from core.middleware.logging import RequestLoggingMiddleware
from core.exceptions.handlers import register_exception_handlers

# 导入路由
from modules.auth.router import router as auth_router
from modules.user.router import router as user_router
from modules.story.router import router as story_router
from modules.admin.router import router as admin_router
from modules.voice_clone.router import router as voice_clone_router
from modules.digital_human.router import router as digital_human_router
from modules.story_generation.router import router as story_generation_router
from modules.audiobook.router import router as audiobook_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print(f"Starting {settings.APP_NAME}...")
    await Database.connect()

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "avatars"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "thumbnails"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "voice_clones", "references"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "voice_clones", "previews"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "digital_human", "images"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "digital_human", "previews"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "story_generation"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "audiobook"), exist_ok=True)

    # 注意：模型预加载暂时禁用，模型会在第一次使用时加载
    # 这避免了启动时长时间加载9GB模型导致服务器响应变慢的问题
    # print("预加载 Chatterbox TTS 模型...")
    # from modules.voice_clone.service import voice_clone_service
    # import asyncio
    # asyncio.create_task(voice_clone_service.preload_model())

    yield

    # 关闭时
    print(f"Shutting down {settings.APP_NAME}...")
    await Database.disconnect()


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    description="AI驱动的数字人动画平台 API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# 注册异常处理器
register_exception_handlers(app)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(user_router, prefix=settings.API_V1_PREFIX)
app.include_router(story_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(voice_clone_router, prefix=settings.API_V1_PREFIX)
app.include_router(digital_human_router, prefix=settings.API_V1_PREFIX)
app.include_router(story_generation_router, prefix=settings.API_V1_PREFIX)
app.include_router(audiobook_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "message": "AI驱动的数字人动画平台"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
