"""
Admin 模块 - API 路由
管理后台接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, BackgroundTasks, HTTPException
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.schemas.base import success_response
from core.schemas.pagination import paginate
from core.middleware.auth import require_admin
from core.config.settings import get_settings
from core.utils.helpers import generate_filename, ensure_dir, get_video_duration, extract_video_thumbnail, extract_audio_from_video

from modules.user.repository import UserRepository
from modules.story.service import get_story_service, StoryService
from modules.story.schemas import StoryCreate, StoryUpdate, CategoryCreate, SubtitleSegment
from modules.voice_clone.repository import voice_profile_repository
from modules.digital_human.repository import avatar_profile_repository

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["管理后台"])

# 批量处理线程池（最大5线程）
batch_executor = ThreadPoolExecutor(max_workers=5)
# 用于追踪批量上传任务的状态
batch_upload_tasks = {}


# ========== 数据统计 ==========

@router.get("/dashboard", summary="获取数据概览")
async def get_dashboard(
    _=Depends(require_admin)
):
    """
    获取管理后台数据概览

    返回平台核心统计数据，包括用户、故事、订阅等信息。
    用于管理后台首页展示。

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "total_users": 1500,
            "total_stories": 120,
            "published_stories": 100,
            "active_subscribers": 50,
            "monthly_revenue": 0,
            "recent_users": [...],
            "recent_stories": [...]
        }
    }
    ```
    """
    user_repo = UserRepository()
    story_service = get_story_service()

    # 统计数据
    total_users = await user_repo.count()
    total_stories = await story_service.story_repo.count()
    published_stories = await story_service.story_repo.count({"is_published": True})

    # 获取最近注册的用户
    recent_users_raw = await user_repo.list_users(skip=0, limit=5)
    recent_users = []
    for u in recent_users_raw:
        recent_users.append({
            "id": u["id"],
            "email": u["email"],
            "nickname": u.get("nickname"),
            "role": u["role"],
            "created_at": u["created_at"].isoformat() if u.get("created_at") else None
        })

    # 获取最近上传的故事
    recent_stories_raw = await story_service.story_repo.get_many(
        filter={},
        skip=0,
        limit=5,
        sort=[("created_at", -1)]
    )
    recent_stories = []
    for s in recent_stories_raw:
        recent_stories.append({
            "id": s["id"],
            "title": s["title"],
            "duration": s.get("duration", 0),
            "status": "active" if s.get("is_published") else "inactive",
            "created_at": s["created_at"].isoformat() if s.get("created_at") else None
        })

    # 订阅用户数（订阅计划不为free的用户）
    active_subscribers = await user_repo.count({"subscription.plan": {"$ne": "free"}})

    return success_response({
        "total_users": total_users,
        "total_stories": total_stories,
        "published_stories": published_stories,
        "active_subscribers": active_subscribers,
        "monthly_revenue": 0,  # TODO: 从订单模块获取
        "recent_users": recent_users,
        "recent_stories": recent_stories
    })


# ========== 用户管理 ==========

@router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量，最大100"),
    role: Optional[str] = Query(None, description="角色筛选：user | subscriber | admin"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    search: Optional[str] = Query(None, description="搜索关键词，匹配邮箱或昵称"),
    _=Depends(require_admin)
):
    """
    获取用户列表

    支持分页、角色筛选、状态筛选和关键词搜索。

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": "6948bda91fd873cf81f5addd",
                    "email": "user@example.com",
                    "nickname": "小明",
                    "role": "user",
                    "subscription_plan": "free",
                    "is_active": true,
                    "created_at": "2025-01-01T12:00:00"
                }
            ],
            "total": 100,
            "page": 1,
            "page_size": 20
        }
    }
    ```
    """
    user_repo = UserRepository()

    skip = (page - 1) * page_size
    users = await user_repo.list_users(
        skip=skip,
        limit=page_size,
        role=role,
        is_active=is_active,
        search=search
    )
    total = await user_repo.count_users(
        role=role,
        is_active=is_active,
        search=search
    )

    # 转换响应格式
    items = []
    for u in users:
        items.append({
            "id": u["id"],
            "email": u["email"],
            "nickname": u["nickname"],
            "avatar_url": u.get("avatar_url"),
            "role": u["role"],
            "subscription_plan": u.get("subscription", {}).get("plan", "free"),
            "is_active": u.get("is_active", True),
            "created_at": u["created_at"].isoformat() if u.get("created_at") else None,
            "last_login_at": u.get("last_login_at").isoformat() if u.get("last_login_at") else None
        })

    return paginate(items, total, page, page_size)


@router.put("/users/{user_id}/status", summary="启用/禁用用户")
async def update_user_status(
    user_id: str,
    is_active: bool,
    _=Depends(require_admin)
):
    """
    启用或禁用用户账号

    **路径参数:**
    - **user_id**: 用户ID

    **查询参数:**
    - **is_active**: true=启用, false=禁用
    """
    user_repo = UserRepository()
    await user_repo.update(user_id, {"is_active": is_active})
    return success_response(message="更新成功")


@router.put("/users/{user_id}/role", summary="修改用户角色")
async def update_user_role(
    user_id: str,
    role: str,
    _=Depends(require_admin)
):
    """
    修改用户角色

    **路径参数:**
    - **user_id**: 用户ID

    **查询参数:**
    - **role**: 新角色，可选值：user | subscriber | admin
    """
    if role not in ["user", "subscriber", "admin"]:
        return {"code": 10001, "message": "无效的角色", "data": None}

    user_repo = UserRepository()
    await user_repo.update(user_id, {"role": role})
    return success_response(message="更新成功")


@router.get("/users/{user_id}", summary="获取用户详细信息")
async def get_user_detail(
    user_id: str,
    _=Depends(require_admin)
):
    """
    获取用户详细信息

    返回用户的完整信息，包括基本资料、档案统计和最近活动。

    **路径参数:**
    - **user_id**: 用户ID

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "id": "6948bda91fd873cf81f5addd",
            "email": "user@example.com",
            "nickname": "小明",
            "role": "user",
            "subscription": {"plan": "free"},
            "is_active": true,
            "stats": {
                "voice_profiles": 2,
                "avatar_profiles": 1,
                "story_jobs": 5
            }
        }
    }
    ```
    """
    user_repo = UserRepository()
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取声音档案数量
    voice_count = await voice_profile_repository.count_by_user(user_id)

    # 获取头像档案数量
    avatar_count = await avatar_profile_repository.count_by_user(user_id)

    # 获取故事生成任务数量
    from modules.story_generation.repository import get_story_generation_repository
    story_gen_repo = get_story_generation_repository()
    story_jobs = await story_gen_repo.list_jobs_by_user(user_id, page=1, page_size=1)
    story_job_count = story_jobs[1] if story_jobs else 0

    return success_response({
        "id": user["id"],
        "email": user["email"],
        "nickname": user.get("nickname"),
        "avatar_url": user.get("avatar_url"),
        "role": user["role"],
        "subscription": user.get("subscription", {"plan": "free"}),
        "is_active": user.get("is_active", True),
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "last_login_at": user.get("last_login_at").isoformat() if user.get("last_login_at") else None,
        "stats": {
            "voice_profiles": voice_count,
            "avatar_profiles": avatar_count,
            "story_jobs": story_job_count
        }
    })


@router.get("/users/{user_id}/voice-profiles", summary="获取用户声音档案")
async def get_user_voice_profiles(
    user_id: str,
    include_deleted: bool = Query(False, description="是否包含已删除的档案"),
    _=Depends(require_admin)
):
    """获取指定用户的所有声音档案"""
    profiles = await voice_profile_repository.get_by_user_id(user_id, include_deleted=include_deleted)

    items = []
    for p in profiles:
        items.append({
            "id": p.get("_id") or p.get("id"),
            "name": p.get("name"),
            "description": p.get("description"),
            "reference_audio_url": p.get("reference_audio_url"),
            "voice_id": p.get("voice_id"),
            "status": p.get("status", "active"),
            "created_at": p["created_at"].isoformat() if p.get("created_at") else None
        })

    return success_response({
        "items": items,
        "total": len(items)
    })


@router.delete("/users/{user_id}/voice-profiles/{profile_id}", summary="删除用户声音档案")
async def delete_user_voice_profile(
    user_id: str,
    profile_id: str,
    _=Depends(require_admin)
):
    """管理员删除指定用户的声音档案"""
    # 验证档案属于该用户
    profile = await voice_profile_repository.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="声音档案不存在")
    if profile.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权删除此档案")

    await voice_profile_repository.delete(profile_id)
    return success_response(message="删除成功")


@router.get("/users/{user_id}/avatar-profiles", summary="获取用户头像档案")
async def get_user_avatar_profiles(
    user_id: str,
    include_deleted: bool = Query(False, description="是否包含已删除的档案"),
    _=Depends(require_admin)
):
    """获取指定用户的所有头像档案"""
    profiles = await avatar_profile_repository.get_by_user_id(user_id, include_deleted=include_deleted)

    items = []
    for p in profiles:
        items.append({
            "id": p.get("_id") or p.get("id"),
            "name": p.get("name"),
            "description": p.get("description"),
            "image_url": p.get("image_url"),
            "face_bbox": p.get("face_bbox"),
            "status": p.get("status", "active"),
            "created_at": p["created_at"].isoformat() if p.get("created_at") else None
        })

    return success_response({
        "items": items,
        "total": len(items)
    })


@router.delete("/users/{user_id}/avatar-profiles/{profile_id}", summary="删除用户头像档案")
async def delete_user_avatar_profile(
    user_id: str,
    profile_id: str,
    _=Depends(require_admin)
):
    """删除用户的头像档案"""
    # 验证档案属于该用户
    profile = await avatar_profile_repository.get_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="头像档案不存在")
    if profile.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权删除此档案")

    await avatar_profile_repository.delete(profile_id)
    return success_response(message="删除成功")


@router.get("/users/{user_id}/story-jobs", summary="获取用户故事生成任务")
async def get_user_story_jobs(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _=Depends(require_admin)
):
    """获取用户的故事生成任务记录"""
    from modules.story_generation.repository import get_story_generation_repository

    repo = get_story_generation_repository()
    jobs, total = await repo.list_jobs_by_user(user_id, page=page, page_size=page_size)

    items = []
    for job in jobs:
        items.append({
            "id": job.get("job_id"),
            "story_id": job.get("story_id"),
            "status": job.get("status"),
            "progress": job.get("progress", 0),
            "current_step": job.get("current_step"),
            "final_video_url": job.get("final_video_url"),
            "error": job.get("error"),
            "created_at": job["created_at"].isoformat() if job.get("created_at") else None,
            "completed_at": job["completed_at"].isoformat() if job.get("completed_at") else None
        })

    return paginate(items, total, page, page_size)


# ========== 分类管理 ==========

@router.post("/categories", summary="创建故事分类")
async def create_category(
    data: CategoryCreate,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """创建分类"""
    category = await story_service.create_category(data)
    return success_response(category.model_dump())


@router.put("/categories/{category_id}", summary="更新故事分类")
async def update_category(
    category_id: str,
    data: CategoryCreate,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """更新分类"""
    await story_service.category_repo.update(category_id, data.model_dump())
    category = await story_service.category_repo.get_by_id(category_id)
    return success_response(category)


@router.delete("/categories/{category_id}", summary="删除故事分类")
async def delete_category(
    category_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """删除分类"""
    await story_service.category_repo.delete(category_id)
    return success_response(message="删除成功")


# ========== 故事管理 - 辅助函数 ==========


async def transcribe_with_local_whisper(audio_path: str) -> dict:
    """
    使用本地 faster-whisper 进行语音识别

    Returns:
        dict: {"text": "...", "segments": [...]}
    """
    import concurrent.futures

    def _run_whisper():
        from faster_whisper import WhisperModel
        from core.config.settings import HF_CACHE_DIR
        import os

        # 设置 HuggingFace 缓存目录为项目内
        os.environ['HF_HOME'] = str(HF_CACHE_DIR)
        os.environ['HF_HUB_CACHE'] = str(HF_CACHE_DIR / 'hub')
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

        # 尝试使用本地缓存的模型
        model_path = HF_CACHE_DIR / 'hub' / 'models--Systran--faster-whisper-base' / 'snapshots'
        local_files_only = False

        if model_path.exists():
            snapshot_dirs = list(model_path.glob('*'))
            if snapshot_dirs:
                model_name = str(snapshot_dirs[0])
                local_files_only = True
                print(f"[Local Whisper] Using cached model: {model_name}")
            else:
                model_name = "Systran/faster-whisper-base"
                print(f"[Local Whisper] Downloading model: {model_name}")
        else:
            model_name = "Systran/faster-whisper-base"
            print(f"[Local Whisper] Downloading model: {model_name}")

        model = WhisperModel(model_name, device="cpu", compute_type="int8", local_files_only=local_files_only)

        # 转写
        print(f"[Local Whisper] Transcribing: {audio_path}")
        segments_gen, info = model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            language=None,  # 自动检测
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        # 收集结果
        all_text = []
        all_segments = []

        for seg in segments_gen:
            all_text.append(seg.text.strip())
            all_segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })

        return {
            "text": " ".join(all_text),
            "segments": all_segments,
            "language": info.language
        }

    # 在线程池中运行（避免阻塞事件循环）
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, _run_whisper)

    return result


def generate_title_from_text(text: str) -> str:
    """从文本中提取标题（本地模式，无需 AI）"""
    if not text:
        return "Untitled Story"

    # 取前 100 个字符作为标题基础
    title_base = text[:100].strip()

    # 在句子边界截断
    for punct in ['.', '!', '?', '。', '！', '？']:
        if punct in title_base:
            title_base = title_base.split(punct)[0] + punct
            break

    # 如果太长，进一步截断
    if len(title_base) > 60:
        title_base = title_base[:57] + "..."

    return title_base if title_base else "Untitled Story"


async def process_video_ai(story_id: str, video_path: str, api_key: str):
    """
    后台处理视频：提取音频，然后加入 APIMart 分析队列

    Args:
        story_id: 故事ID
        video_path: 视频文件路径
        api_key: API Key (未使用，保留兼容)
    """
    story_service = get_story_service()

    try:
        # 1. 提取音频
        audio_filename = os.path.basename(video_path).rsplit('.', 1)[0] + '.mp3'
        audio_dir = os.path.join(settings.UPLOAD_DIR, "audio")
        ensure_dir(audio_dir)
        audio_path = os.path.join(audio_dir, audio_filename)

        print(f"[AI Processing] Extracting audio from {video_path}...")
        if not extract_audio_from_video(video_path, audio_path):
            print(f"[AI Processing] Failed to extract audio")
            await story_service.story_repo.update(story_id, {
                "is_processing": False,
                "analysis_error": "Failed to extract audio"
            })
            return

        audio_url = f"/uploads/audio/{audio_filename}"

        # 更新音频 URL
        await story_service.story_repo.update(story_id, {"audio_url": audio_url})

        # 2. 加入 APIMart 分析队列
        print(f"[AI Processing] Adding story {story_id} to analysis queue...")
        from modules.story.analysis_queue import add_story_to_analysis_queue

        queue_size = await add_story_to_analysis_queue(story_id, video_path)
        print(f"[AI Processing] Story {story_id} added to queue. Queue size: {queue_size}")

    except Exception as e:
        print(f"[AI Processing] Error: {e}")
        import traceback
        traceback.print_exc()
        await story_service.story_repo.update(story_id, {
            "is_processing": False,
            "analysis_error": str(e)
        })


async def process_single_video(
    video_content: bytes,
    video_filename: str,
    category_id: str,
    api_key: str,
    batch_id: str,
    index: int
):
    """
    处理单个视频（用于批量上传）

    Args:
        video_content: 视频文件内容
        video_filename: 原始文件名
        category_id: 分类ID
        api_key: APICore API Key
        batch_id: 批量任务ID
        index: 在批次中的索引
    """
    story_service = get_story_service()

    try:
        # 更新任务状态
        if batch_id in batch_upload_tasks:
            batch_upload_tasks[batch_id]["items"][index]["status"] = "uploading"

        # 保存视频文件
        new_filename = generate_filename(video_filename)
        video_dir = os.path.join(settings.UPLOAD_DIR, "videos")
        ensure_dir(video_dir)

        video_path = os.path.join(video_dir, new_filename)
        with open(video_path, "wb") as f:
            f.write(video_content)

        video_url = f"/uploads/videos/{new_filename}"

        # 获取视频时长
        duration = get_video_duration(video_path)

        # 自动生成缩略图（从第10秒提取）
        thumbnail_filename = new_filename.rsplit('.', 1)[0] + '.jpg'
        thumbnail_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
        ensure_dir(thumbnail_dir)

        thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
        thumbnail_url = None

        if extract_video_thumbnail(video_path, thumbnail_path, time_seconds=20):
            thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"

        # 创建故事数据
        story_data = StoryCreate(
            title="",  # AI会生成
            category_id=category_id or "",
            description=None,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            duration=duration,
            is_published=False,
            is_processing=True
        )

        story = await story_service.create_story(story_data)

        # 更新任务状态为处理中
        if batch_id in batch_upload_tasks:
            batch_upload_tasks[batch_id]["items"][index]["status"] = "processing"
            batch_upload_tasks[batch_id]["items"][index]["story_id"] = story.id

        # 执行 AI 处理
        await process_video_ai(story.id, video_path, api_key)

        # 更新任务状态为完成
        if batch_id in batch_upload_tasks:
            batch_upload_tasks[batch_id]["items"][index]["status"] = "completed"
            batch_upload_tasks[batch_id]["completed"] += 1

        return {"success": True, "story_id": story.id}

    except Exception as e:
        print(f"[Batch Upload] Error processing {video_filename}: {e}")
        import traceback
        traceback.print_exc()

        if batch_id in batch_upload_tasks:
            batch_upload_tasks[batch_id]["items"][index]["status"] = "failed"
            batch_upload_tasks[batch_id]["items"][index]["error"] = str(e)
            batch_upload_tasks[batch_id]["failed"] += 1

        return {"success": False, "error": str(e)}


async def run_batch_upload(
    videos_data: List[dict],
    category_id: str,
    api_key: str,
    batch_id: str
):
    """
    运行批量上传任务（串行处理，避免资源竞争）

    Args:
        videos_data: 视频数据列表 [{"content": bytes, "filename": str}, ...]
        category_id: 分类ID
        api_key: APICore API Key
        batch_id: 批量任务ID
    """
    # 串行处理每个视频，避免 Whisper 并行加载导致卡死
    for i, video_data in enumerate(videos_data):
        try:
            print(f"[Batch Upload] Processing video {i+1}/{len(videos_data)}: {video_data['filename']}")
            await process_single_video(
                video_content=video_data["content"],
                video_filename=video_data["filename"],
                category_id=category_id,
                api_key=api_key,
                batch_id=batch_id,
                index=i
            )
            print(f"[Batch Upload] Completed video {i+1}/{len(videos_data)}")
        except Exception as e:
            print(f"[Batch Upload] Failed video {i+1}/{len(videos_data)}: {e}")

    # 标记批量任务完成
    if batch_id in batch_upload_tasks:
        batch_upload_tasks[batch_id]["status"] = "completed"


# ========== 故事管理 - 批量操作（必须在 {story_id} 路由之前） ==========

@router.post("/stories/batch", summary="批量上传视频创建故事")
async def batch_create_stories(
    background_tasks: BackgroundTasks,
    videos: List[UploadFile] = File(...),
    category_id: Optional[str] = Form(None),
    _=Depends(require_admin)
):
    """
    批量上传视频创建故事

    - 支持同时上传多个视频文件
    - 所有视频将被分配到同一分类
    - AI处理最多5个并发执行
    """
    import uuid

    # 验证视频格式
    for video in videos:
        if video.content_type not in settings.ALLOWED_VIDEO_TYPES:
            return {"code": 10001, "message": f"不支持的视频格式: {video.filename}", "data": None}

    # 生成批量任务ID
    batch_id = str(uuid.uuid4())

    # 初始化任务状态
    batch_upload_tasks[batch_id] = {
        "status": "processing",
        "total": len(videos),
        "completed": 0,
        "failed": 0,
        "items": [
            {"filename": v.filename, "status": "pending", "story_id": None, "error": None}
            for v in videos
        ]
    }

    # 读取所有视频内容
    videos_data = []
    for video in videos:
        content = await video.read()
        videos_data.append({
            "content": content,
            "filename": video.filename
        })

    # 获取 API Key
    api_key = settings.APIMART_API_KEY

    # 在后台执行批量上传
    background_tasks.add_task(
        run_batch_upload,
        videos_data,
        category_id or "",
        api_key,
        batch_id
    )

    return success_response({
        "batch_id": batch_id,
        "total": len(videos),
        "message": f"已开始批量上传 {len(videos)} 个视频"
    })


@router.get("/stories/batch/{batch_id}", summary="获取批量上传任务状态")
async def get_batch_status(
    batch_id: str,
    _=Depends(require_admin)
):
    """获取批量上传任务状态"""
    if batch_id not in batch_upload_tasks:
        return {"code": 10001, "message": "任务不存在", "data": None}

    return success_response(batch_upload_tasks[batch_id])


@router.post("/stories/batch-publish", summary="批量上架故事")
async def batch_publish_stories(
    story_ids: List[str],
    _=Depends(require_admin)
):
    """
    批量上架故事

    Args:
        story_ids: 要上架的故事ID列表

    注意：处理中的故事会被跳过
    """
    story_service = get_story_service()

    success_count = 0
    skipped_count = 0
    for story_id in story_ids:
        try:
            # 检查故事是否正在处理中
            story = await story_service.story_repo.get_by_id(story_id)
            if story and story.get("is_processing"):
                skipped_count += 1
                continue

            await story_service.story_repo.update(story_id, {"is_published": True})
            success_count += 1
        except Exception as e:
            print(f"Failed to publish story {story_id}: {e}")

    message = f"成功上架 {success_count} 个故事"
    if skipped_count > 0:
        message += f"，跳过 {skipped_count} 个处理中的故事"

    return success_response({
        "total": len(story_ids),
        "success": success_count,
        "skipped": skipped_count,
        "message": message
    })


@router.post("/stories/batch-unpublish", summary="批量下架故事")
async def batch_unpublish_stories(
    story_ids: List[str],
    _=Depends(require_admin)
):
    """
    批量下架故事

    Args:
        story_ids: 要下架的故事ID列表
    """
    story_service = get_story_service()

    success_count = 0
    for story_id in story_ids:
        try:
            await story_service.story_repo.update(story_id, {"is_published": False})
            success_count += 1
        except Exception as e:
            print(f"Failed to unpublish story {story_id}: {e}")

    return success_response({
        "total": len(story_ids),
        "success": success_count,
        "message": f"成功下架 {success_count} 个故事"
    })


@router.delete("/stories/batch", summary="批量删除故事")
async def batch_delete_stories(
    story_ids: List[str],
    _=Depends(require_admin)
):
    """
    批量删除故事

    Args:
        story_ids: 要删除的故事ID列表
    """
    story_service = get_story_service()

    success_count = 0
    for story_id in story_ids:
        try:
            await story_service.delete_story(story_id)
            success_count += 1
        except Exception as e:
            print(f"Failed to delete story {story_id}: {e}")

    return success_response({
        "total": len(story_ids),
        "success": success_count,
        "message": f"成功删除 {success_count} 个故事"
    })


# ========== 故事管理 - 基本操作 ==========

@router.get("/stories", summary="获取故事列表（管理端）")
async def list_stories_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    is_published: Optional[bool] = None,
    search: Optional[str] = None,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """获取故事列表（包含未发布的）"""
    result = await story_service.list_stories(
        page=page,
        page_size=page_size,
        category_id=category_id,
        is_published=is_published,
        search=search
    )

    # 获取所有分类信息
    categories = await story_service.category_repo.list_all()
    cat_map = {c["id"]: c["name"] for c in categories}

    # 为每个故事添加分类信息
    for item in result["data"]["items"]:
        cat_id = item.get("category_id")
        if cat_id and cat_id in cat_map:
            item["category"] = {"id": cat_id, "name": cat_map[cat_id]}
        else:
            item["category"] = None
        # 添加状态字段（优先检查处理中状态）
        if item.get("is_processing"):
            item["status"] = "processing"
        elif item.get("is_published"):
            item["status"] = "active"
        else:
            item["status"] = "inactive"

    return result


@router.post("/stories", summary="上传视频创建故事")
async def create_story(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    category_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    _=Depends(require_admin)
):
    """
    创建故事 - 支持直接上传视频文件

    上传视频后会自动：
    1. 从视频第10秒提取缩略图
    2. 获取视频时长
    3. 提取音频并生成字幕
    4. 使用 AI 生成标题和英文标题
    """
    story_service = get_story_service()

    # 验证视频格式
    if video.content_type not in settings.ALLOWED_VIDEO_TYPES:
        return {"code": 10001, "message": "Unsupported video format", "data": None}

    # 保存视频文件
    video_filename = generate_filename(video.filename)
    video_dir = os.path.join(settings.UPLOAD_DIR, "videos")
    ensure_dir(video_dir)

    video_path = os.path.join(video_dir, video_filename)
    content = await video.read()
    with open(video_path, "wb") as f:
        f.write(content)

    video_url = f"/uploads/videos/{video_filename}"

    # 获取视频时长
    duration = get_video_duration(video_path)

    # 自动生成缩略图（从第10秒提取）
    thumbnail_filename = video_filename.rsplit('.', 1)[0] + '.jpg'
    thumbnail_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
    ensure_dir(thumbnail_dir)

    thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
    thumbnail_url = None

    if extract_video_thumbnail(video_path, thumbnail_path, time_seconds=20):
        thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"

    # 使用提供的标题或空字符串（AI会生成）
    effective_title = title or ""

    # 检查是否需要AI处理
    effective_api_key = api_key or getattr(settings, 'APIMART_API_KEY', None)
    is_processing = bool(effective_api_key and not title)

    # 创建故事数据
    story_data = StoryCreate(
        title=effective_title,
        category_id=category_id or "",
        description=description,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        duration=duration,
        is_published=False,
        is_processing=is_processing
    )

    story = await story_service.create_story(story_data)

    if effective_api_key:
        # 使用队列处理 AI 分析任务（串行处理，避免 API 限流）
        from modules.story.analysis_queue import add_story_to_analysis_queue
        queue_size = await add_story_to_analysis_queue(story.id, video_path, effective_api_key)
        print(f"[Story Upload] Added to analysis queue. Story: {story.id}, Queue size: {queue_size}")

    return success_response(story.model_dump())


@router.get("/analysis-queue/status", summary="获取分析队列状态")
async def get_analysis_queue_status(_=Depends(require_admin)):
    """获取故事分析队列状态"""
    from modules.story.analysis_queue import get_analysis_queue

    queue = get_analysis_queue()
    return success_response({
        "queue_size": queue.get_queue_size(),
        "current_processing": queue.get_current_task(),
        "is_running": queue._is_running
    })


# ========== 故事管理 - 单个操作（带 {story_id} 的路由必须在 batch 路由之后） ==========

@router.get("/stories/{story_id}", summary="获取故事详情")
async def get_story_detail(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """获取故事详情（包含字幕和说话人信息）"""
    story = await story_service.get_story(story_id)

    # 获取分类信息
    category = None
    if story.category_id:
        cat_data = await story_service.category_repo.get_by_id(story.category_id)
        if cat_data:
            category = {"id": cat_data["id"], "name": cat_data["name"]}

    return success_response({
        "id": story.id,
        "title": story.title,
        "title_en": story.title_en,
        "description": story.description,
        "video_url": story.video_url,
        "audio_url": story.audio_url,
        "thumbnail_url": story.thumbnail_url,
        "duration": story.duration,
        "status": "active" if story.is_published else "inactive",
        "category": category,
        "subtitles": story.subtitles,
        "subtitle_text": story.subtitle_text,
        "speakers": story.speakers,
        "speaker_count": story.speaker_count,
        "is_analyzed": story.is_analyzed,
        "background_audio_url": story.background_audio_url,
        "created_at": story.created_at.isoformat() if story.created_at else None
    })


@router.put("/stories/{story_id}", summary="更新故事信息")
async def update_story(
    story_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """更新故事（支持更新缩略图和视频）"""
    update_data = {}
    if title:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if category_id:
        update_data["category_id"] = category_id
    if status:
        update_data["is_published"] = (status == "active")

    # 处理缩略图上传
    if thumbnail and thumbnail.filename:
        if thumbnail.content_type not in settings.ALLOWED_IMAGE_TYPES:
            return {"code": 10001, "message": "不支持的图片格式", "data": None}

        thumb_filename = generate_filename(thumbnail.filename)
        thumb_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
        ensure_dir(thumb_dir)

        thumb_path = os.path.join(thumb_dir, thumb_filename)
        content = await thumbnail.read()
        with open(thumb_path, "wb") as f:
            f.write(content)

        update_data["thumbnail_url"] = f"/uploads/thumbnails/{thumb_filename}"

    # 处理视频上传
    if video and video.filename:
        if video.content_type not in settings.ALLOWED_VIDEO_TYPES:
            return {"code": 10001, "message": "不支持的视频格式", "data": None}

        video_filename = generate_filename(video.filename)
        video_dir = os.path.join(settings.UPLOAD_DIR, "videos")
        ensure_dir(video_dir)

        video_path = os.path.join(video_dir, video_filename)
        content = await video.read()
        with open(video_path, "wb") as f:
            f.write(content)

        video_url = f"/uploads/videos/{video_filename}"
        update_data["video_url"] = video_url

        # 获取视频时长
        duration = get_video_duration(video_path)
        if duration:
            update_data["duration"] = duration

        # 自动生成新缩略图（如果没有单独上传）
        if "thumbnail_url" not in update_data:
            new_thumb_filename = video_filename.rsplit('.', 1)[0] + '.jpg'
            new_thumb_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
            ensure_dir(new_thumb_dir)
            new_thumb_path = os.path.join(new_thumb_dir, new_thumb_filename)
            if extract_video_thumbnail(video_path, new_thumb_path, time_seconds=20):
                update_data["thumbnail_url"] = f"/uploads/thumbnails/{new_thumb_filename}"

    if not update_data:
        return {"code": 10001, "message": "没有要更新的数据", "data": None}

    data = StoryUpdate(**update_data)
    story = await story_service.update_story(story_id, data)
    return success_response(story.model_dump())


@router.delete("/stories/{story_id}", summary="删除故事")
async def delete_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """删除故事"""
    await story_service.delete_story(story_id)
    return success_response(message="删除成功")


@router.post("/stories/{story_id}/publish", summary="发布故事")
async def publish_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """发布故事"""
    await story_service.story_repo.update(story_id, {"is_published": True})
    return success_response(message="发布成功")


@router.post("/stories/{story_id}/unpublish", summary="下架故事")
async def unpublish_story(
    story_id: str,
    story_service: StoryService = Depends(get_story_service),
    _=Depends(require_admin)
):
    """下架故事"""
    await story_service.story_repo.update(story_id, {"is_published": False})
    return success_response(message="下架成功")


# ========== 文件上传 ==========

@router.post("/upload/thumbnail", summary="上传故事缩略图")
async def upload_thumbnail(
    file: UploadFile = File(...),
    _=Depends(require_admin)
):
    """上传故事缩略图"""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        return {"code": 10001, "message": "不支持的图片格式", "data": None}

    filename = generate_filename(file.filename)
    upload_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
    ensure_dir(upload_dir)

    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    url = f"/uploads/thumbnails/{filename}"
    return success_response({"url": url})


@router.post("/upload/video", summary="上传故事视频")
async def upload_video(
    file: UploadFile = File(...),
    _=Depends(require_admin)
):
    """上传故事视频"""
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
        return {"code": 10001, "message": "不支持的视频格式", "data": None}

    filename = generate_filename(file.filename)
    upload_dir = os.path.join(settings.UPLOAD_DIR, "videos")
    ensure_dir(upload_dir)

    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    url = f"/uploads/videos/{filename}"
    return success_response({"url": url})


# ========== 有声书管理 ==========

@router.get("/audiobook/stories", summary="获取有声书故事列表（管理端）")
async def list_audiobook_stories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: Optional[str] = None,
    category: Optional[str] = None,
    is_published: Optional[bool] = None,
    _=Depends(require_admin)
):
    """获取有声书故事列表（管理端）"""
    from modules.audiobook.service import get_audiobook_service
    from modules.audiobook.schemas import AudiobookStoryResponse

    service = get_audiobook_service()
    result = await service.list_stories(
        page=page,
        page_size=page_size,
        language=language,
        category=category,
        published_only=False
    )

    return success_response({
        "items": [
            AudiobookStoryResponse(**story).model_dump()
            for story in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    })


@router.post("/audiobook/stories", summary="创建有声书故事")
async def create_audiobook_story(
    title: str = Form(...),
    title_en: str = Form(...),
    content: str = Form(...),
    language: str = Form("en"),
    category: str = Form("fairy_tale"),
    age_group: str = Form("5-8"),
    thumbnail_url: Optional[str] = Form(None),
    background_music_url: Optional[str] = Form(None),
    is_published: bool = Form(True),
    sort_order: int = Form(0),
    _=Depends(require_admin)
):
    """创建有声书故事"""
    from modules.audiobook.service import get_audiobook_service
    from modules.audiobook.schemas import AudiobookStoryResponse

    service = get_audiobook_service()
    story_id = await service.create_story({
        "title": title,
        "title_en": title_en,
        "content": content,
        "language": language,
        "category": category,
        "age_group": age_group,
        "thumbnail_url": thumbnail_url,
        "background_music_url": background_music_url,
        "is_published": is_published,
        "sort_order": sort_order
    })

    story = await service.get_story(story_id)
    return success_response(AudiobookStoryResponse(**story).model_dump())


@router.get("/audiobook/stories/{story_id}", summary="获取有声书故事详情")
async def get_audiobook_story(
    story_id: str,
    _=Depends(require_admin)
):
    """获取有声书故事详情"""
    from modules.audiobook.service import get_audiobook_service
    from modules.audiobook.schemas import AudiobookStoryResponse
    from fastapi import HTTPException

    service = get_audiobook_service()
    story = await service.get_story(story_id)

    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    return success_response(AudiobookStoryResponse(**story).model_dump())


@router.put("/audiobook/stories/{story_id}", summary="更新有声书故事")
async def update_audiobook_story(
    story_id: str,
    title: Optional[str] = Form(None),
    title_en: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    age_group: Optional[str] = Form(None),
    thumbnail_url: Optional[str] = Form(None),
    background_music_url: Optional[str] = Form(None),
    is_published: Optional[bool] = Form(None),
    sort_order: Optional[int] = Form(None),
    _=Depends(require_admin)
):
    """更新有声书故事"""
    from modules.audiobook.service import get_audiobook_service
    from modules.audiobook.schemas import AudiobookStoryResponse
    from fastapi import HTTPException

    service = get_audiobook_service()

    update_data = {}
    if title is not None:
        update_data["title"] = title
    if title_en is not None:
        update_data["title_en"] = title_en
    if content is not None:
        update_data["content"] = content
    if language is not None:
        update_data["language"] = language
    if category is not None:
        update_data["category"] = category
    if age_group is not None:
        update_data["age_group"] = age_group
    if thumbnail_url is not None:
        update_data["thumbnail_url"] = thumbnail_url
    if background_music_url is not None:
        update_data["background_music_url"] = background_music_url
    if is_published is not None:
        update_data["is_published"] = is_published
    if sort_order is not None:
        update_data["sort_order"] = sort_order

    if not update_data:
        raise HTTPException(status_code=400, detail="没有要更新的数据")

    success = await service.update_story(story_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="故事不存在")

    story = await service.get_story(story_id)
    return success_response(AudiobookStoryResponse(**story).model_dump())


@router.delete("/audiobook/stories/{story_id}", summary="删除有声书故事")
async def delete_audiobook_story(
    story_id: str,
    _=Depends(require_admin)
):
    """删除有声书故事"""
    from modules.audiobook.service import get_audiobook_service
    from fastapi import HTTPException

    service = get_audiobook_service()
    success = await service.delete_story(story_id)

    if not success:
        raise HTTPException(status_code=404, detail="故事不存在")

    return success_response(message="删除成功")


# ========== 费用统计 ==========

@router.get("/cost-statistics", summary="获取费用统计")
async def get_cost_statistics(
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    _=Depends(require_admin)
):
    """
    获取 AI 服务费用统计

    统计 CosyVoice TTS 和 EMO 数字人视频的费用明细。

    **查询参数:**
    - **start_date**: 开始日期 (可选)
    - **end_date**: 结束日期 (可选)

    **返回示例:**
    ```json
    {
        "code": 0,
        "message": "success",
        "data": {
            "total_cost": 123.45,
            "tts_cost": 23.45,
            "emo_cost": 100.00,
            "job_count": 50,
            "tts_chars_total": 50000,
            "emo_seconds_total": 1200.5,
            "daily_stats": [...]
        }
    }
    ```
    """
    from modules.story_generation.repository import get_story_generation_repository
    from datetime import datetime, timedelta

    repo = get_story_generation_repository()

    # 构建查询条件
    query = {"status": "completed"}

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query["created_at"] = {"$gte": start_dt}
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            if "created_at" in query:
                query["created_at"]["$lt"] = end_dt
            else:
                query["created_at"] = {"$lt": end_dt}
        except ValueError:
            pass

    # 聚合费用统计
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": None,
                "total_cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                "tts_cost": {"$sum": {"$ifNull": ["$cost_details.tts_cost", 0]}},
                "tts_chars": {"$sum": {"$ifNull": ["$cost_details.tts_chars", 0]}},
                "emo_detect_cost": {"$sum": {"$ifNull": ["$cost_details.emo_detect_cost", 0]}},
                "emo_detect_count": {"$sum": {"$ifNull": ["$cost_details.emo_detect_count", 0]}},
                "emo_video_cost": {"$sum": {"$ifNull": ["$cost_details.emo_video_cost", 0]}},
                "emo_video_seconds": {"$sum": {"$ifNull": ["$cost_details.emo_video_seconds", 0]}},
                "job_count": {"$sum": 1}
            }
        }
    ]

    cursor = repo.jobs_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if result:
        stats = result[0]
        stats.pop("_id", None)
    else:
        stats = {
            "total_cost": 0,
            "tts_cost": 0,
            "tts_chars": 0,
            "emo_detect_cost": 0,
            "emo_detect_count": 0,
            "emo_video_cost": 0,
            "emo_video_seconds": 0,
            "job_count": 0
        }

    # 计算 EMO 总费用
    stats["emo_cost"] = stats.get("emo_detect_cost", 0) + stats.get("emo_video_cost", 0)

    # 获取每日统计（最近30天）
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_pipeline = [
        {"$match": {"status": "completed", "created_at": {"$gte": thirty_days_ago}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "cost": {"$sum": {"$ifNull": ["$total_cost", 0]}},
                "jobs": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]

    daily_cursor = repo.jobs_collection.aggregate(daily_pipeline)
    daily_stats = await daily_cursor.to_list(length=30)
    stats["daily_stats"] = [
        {"date": d["_id"], "cost": d["cost"], "jobs": d["jobs"]}
        for d in daily_stats
    ]

    return success_response(stats)


@router.get("/cost-statistics/jobs", summary="获取费用详情任务列表")
async def get_cost_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    _=Depends(require_admin)
):
    """
    获取有费用记录的任务列表

    显示每个任务的费用明细，按完成时间倒序排列。
    """
    from modules.story_generation.repository import get_story_generation_repository
    from datetime import datetime, timedelta

    repo = get_story_generation_repository()

    # 构建查询条件
    query = {"status": "completed", "total_cost": {"$gt": 0}}

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query["created_at"] = {"$gte": start_dt}
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            if "created_at" in query:
                query["created_at"]["$lt"] = end_dt
            else:
                query["created_at"] = {"$lt": end_dt}
        except ValueError:
            pass

    # 计算总数
    total = await repo.jobs_collection.count_documents(query)

    # 获取分页数据
    skip = (page - 1) * page_size
    cursor = repo.jobs_collection.find(query).sort(
        "completed_at", -1
    ).skip(skip).limit(page_size)

    jobs = []
    user_repo = UserRepository()
    story_service = get_story_service()

    async for doc in cursor:
        # 获取用户信息
        user_info = None
        if doc.get("user_id"):
            user = await user_repo.get_by_id(str(doc["user_id"]))
            if user:
                user_info = {
                    "id": user["id"],
                    "email": user["email"],
                    "nickname": user.get("nickname")
                }

        # 获取故事信息
        story_info = None
        if doc.get("story_id"):
            try:
                story = await story_service.get_story(str(doc["story_id"]))
                if story:
                    story_info = {
                        "id": story.id,
                        "title": story.title
                    }
            except:
                pass

        cost_details = doc.get("cost_details", {})
        jobs.append({
            "id": str(doc["_id"]),
            "user": user_info,
            "story": story_info,
            "mode": doc.get("mode", "single"),
            "total_cost": doc.get("total_cost", 0),
            "tts_cost": cost_details.get("tts_cost", 0),
            "tts_chars": cost_details.get("tts_chars", 0),
            "emo_detect_cost": cost_details.get("emo_detect_cost", 0),
            "emo_video_cost": cost_details.get("emo_video_cost", 0),
            "emo_video_seconds": cost_details.get("emo_video_seconds", 0),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "completed_at": doc["completed_at"].isoformat() if doc.get("completed_at") else None
        })

    return paginate(jobs, total, page, page_size)


@router.get("/audiobook/jobs", summary="获取有声书任务列表（管理端）")
async def list_audiobook_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    _=Depends(require_admin)
):
    """获取有声书生成任务列表（管理端）"""
    from modules.audiobook.service import get_audiobook_service
    from modules.audiobook.schemas import AdminAudiobookJobResponse

    service = get_audiobook_service()
    result = await service.list_all_jobs(
        page=page,
        page_size=page_size,
        status=status,
        user_id=user_id
    )

    user_repo = UserRepository()
    items = []
    for job in result["items"]:
        job_data = AdminAudiobookJobResponse(**job).model_dump()
        user = await user_repo.get_by_id(job.get("user_id"))
        if user:
            job_data["user_email"] = user.get("email")
            job_data["user_nickname"] = user.get("nickname")
        items.append(job_data)

    return success_response({
        "items": items,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    })
