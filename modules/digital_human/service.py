"""
Digital Human Service - 阿里云 EMO 数字人生成服务
使用 DashScope API 实现数字人头像动态视频生成
"""

import os
import asyncio
import time
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import uuid
import io

from PIL import Image

from core.config.settings import get_settings

settings = get_settings()

# 任务状态存储（内存中，生产环境可改用 Redis）
digital_human_tasks: Dict[str, dict] = {}

# EMO API 端点
EMO_DETECT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/face-detect"
EMO_GENERATE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis"
EMO_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"


class DigitalHumanService:
    """数字人服务 - 使用阿里云 EMO API"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.media_bed_url = settings.MEDIA_BED_URL
        self.upload_dir = Path(settings.UPLOAD_DIR) / "digital_human"
        self.images_dir = self.upload_dir / "images"
        self.previews_dir = self.upload_dir / "previews"

        # 确保目录存在
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)

    def compress_image(self, file_path: str, max_size: int = 800, quality: int = 85) -> bytes:
        """
        压缩图片以减少文件大小，加快阿里云下载速度

        Args:
            file_path: 原始图片路径
            max_size: 最大边长（像素）
            quality: JPEG 压缩质量（1-100）

        Returns:
            压缩后的图片字节数据
        """
        with Image.open(file_path) as img:
            # 转换为 RGB（处理 PNG 透明通道）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 计算新尺寸，保持宽高比
            width, height = img.size
            if max(width, height) > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * max_size / width)
                else:
                    new_height = max_size
                    new_width = int(width * max_size / height)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 压缩为 JPEG
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_data = buffer.getvalue()

            original_size = os.path.getsize(file_path)
            print(f"Image compressed: {original_size / 1024:.1f}KB -> {len(compressed_data) / 1024:.1f}KB")

            return compressed_data

    async def upload_to_media_bed(self, file_path: str, compress_images: bool = True) -> Optional[str]:
        """上传文件到图床服务"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return None

            # 根据文件类型设置 content-type
            suffix = file_path.suffix.lower()
            content_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.mp4': 'video/mp4'
            }
            content_type = content_types.get(suffix, 'application/octet-stream')

            # 对图片进行压缩以加快阿里云下载
            is_image = suffix in ['.jpg', '.jpeg', '.png', '.webp']
            if is_image and compress_images:
                file_data = self.compress_image(str(file_path))
                content_type = 'image/jpeg'
                upload_filename = file_path.stem + '.jpg'
            else:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                upload_filename = file_path.name

            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {'file': (upload_filename, file_data, content_type)}
                response = await client.post(
                    f"{self.media_bed_url}/upload",
                    files=files
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        file_url = result.get('url', '')
                        full_url = f"{self.media_bed_url}{file_url}"
                        print(f"Uploaded to media bed: {full_url}")
                        return full_url

                print(f"Media bed upload failed: {response.text}")
                return None

        except Exception as e:
            print(f"Media bed upload error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_audio(self, user_id: str, file_content: bytes, filename: str) -> str:
        """保存用户上传的音频文件"""
        ext = Path(filename).suffix or ".wav"
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.previews_dir / new_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    async def generate_preview(
        self,
        task_id: str,
        image_path: str,
        audio_source: 'AudioSourceType' = None,
        audio_path: str = None,
        voice_profile_id: str = None,
        preview_text: str = "Hello, I am your digital avatar. Nice to meet you!"
    ):
        """
        使用阿里云 EMO 生成数字人预览视频

        流程:
        1. 上传图片到图床获取公网 URL
        2. 调用 EMO 图像检测 API 获取人脸区域
        3. 获取音频 (上传的音频 / 克隆声音合成 / 默认音色)
        4. 调用 EMO 视频生成 API 生成动态视频
        5. 下载并保存预览视频

        Args:
            task_id: 任务ID
            image_path: 头像图片路径
            audio_source: 音频来源类型
            audio_path: 上传的音频文件路径 (如果有)
            voice_profile_id: 声音档案ID (如果使用克隆声音)
            preview_text: 预览文本
        """
        from .schemas import AudioSourceType

        if audio_source is None:
            audio_source = AudioSourceType.DEFAULT

        try:
            # 更新任务状态
            digital_human_tasks[task_id]["status"] = "processing"
            digital_human_tasks[task_id]["progress"] = 5

            # 检查配置
            if not self.api_key:
                raise Exception("DASHSCOPE_API_KEY not configured in .env")

            digital_human_tasks[task_id]["progress"] = 10

            # Step 1: 上传图片到图床
            print(f"[{task_id}] Uploading image to media bed...")
            image_url = await self.upload_to_media_bed(image_path)

            if not image_url:
                raise Exception("Failed to upload image to media bed service")

            print(f"[{task_id}] Image URL: {image_url}")
            digital_human_tasks[task_id]["image_url"] = image_url
            digital_human_tasks[task_id]["progress"] = 20

            # Step 2: 图像检测获取人脸区域
            print(f"[{task_id}] Detecting face in image...")
            digital_human_tasks[task_id]["status"] = "detecting"

            face_bbox, ext_bbox = await self._detect_face(task_id, image_url)

            if not face_bbox or not ext_bbox:
                raise Exception("Face detection failed - please use a clear portrait photo")

            print(f"[{task_id}] Face detected: face_bbox={face_bbox}, ext_bbox={ext_bbox}")
            digital_human_tasks[task_id]["face_bbox"] = face_bbox
            digital_human_tasks[task_id]["ext_bbox"] = ext_bbox
            digital_human_tasks[task_id]["progress"] = 35

            # Step 3: 获取音频 URL
            print(f"[{task_id}] Preparing audio (source: {audio_source.value})...")
            audio_url = await self._get_audio_url(
                task_id=task_id,
                audio_source=audio_source,
                audio_path=audio_path,
                voice_profile_id=voice_profile_id,
                preview_text=preview_text
            )

            if not audio_url:
                raise Exception("Failed to prepare audio")

            print(f"[{task_id}] Audio URL: {audio_url}")
            digital_human_tasks[task_id]["progress"] = 50

            # Step 4: 创建 EMO 视频生成任务
            print(f"[{task_id}] Creating EMO video task...")
            digital_human_tasks[task_id]["status"] = "generating"

            emo_task_id = await self._create_emo_task(
                task_id, image_url, audio_url, face_bbox, ext_bbox
            )

            if not emo_task_id:
                raise Exception("Failed to create EMO video task")

            print(f"[{task_id}] EMO task created: {emo_task_id}")
            digital_human_tasks[task_id]["progress"] = 60

            # Step 5: 等待 EMO 任务完成
            print(f"[{task_id}] Waiting for EMO task to complete...")
            video_url = await self._wait_for_emo_task(task_id, emo_task_id)

            if not video_url:
                raise Exception("EMO video generation failed or timed out")

            digital_human_tasks[task_id]["progress"] = 90

            # Step 6: 下载并保存视频
            print(f"[{task_id}] Downloading video...")
            output_filename = f"{task_id}.mp4"
            output_path = self.previews_dir / output_filename

            await self._download_video(video_url, str(output_path))

            # 更新任务状态为完成
            digital_human_tasks[task_id]["status"] = "completed"
            digital_human_tasks[task_id]["progress"] = 100
            digital_human_tasks[task_id]["video_url"] = f"/uploads/digital_human/previews/{output_filename}"
            digital_human_tasks[task_id]["completed_at"] = datetime.utcnow()

            print(f"[{task_id}] Digital human preview completed successfully")

        except Exception as e:
            print(f"[{task_id}] Digital human generation failed: {e}")
            import traceback
            traceback.print_exc()

            digital_human_tasks[task_id]["status"] = "failed"
            digital_human_tasks[task_id]["error"] = str(e)
            digital_human_tasks[task_id]["progress"] = 0

    async def _detect_face(self, task_id: str, image_url: str) -> Tuple[Optional[List[int]], Optional[List[int]]]:
        """
        调用 EMO 图像检测 API

        Returns:
            (face_bbox, ext_bbox) 或 (None, None)
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "emo-detect-v1",
                "input": {
                    "image_url": image_url
                },
                "parameters": {
                    "ratio": "1:1"  # 使用 1:1 头像比例
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(EMO_DETECT_URL, headers=headers, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    output = result.get("output", {})

                    if output.get("check_pass"):
                        face_bbox = output.get("face_bbox")
                        ext_bbox = output.get("ext_bbox")
                        return face_bbox, ext_bbox
                    else:
                        print(f"[{task_id}] Face detection check failed")
                        return None, None
                else:
                    print(f"[{task_id}] Face detection API error: {response.text}")
                    return None, None

        except Exception as e:
            print(f"[{task_id}] Face detection error: {e}")
            return None, None

    async def _get_audio_url(
        self,
        task_id: str,
        audio_source: 'AudioSourceType',
        audio_path: str = None,
        voice_profile_id: str = None,
        preview_text: str = None
    ) -> Optional[str]:
        """
        根据音频来源获取音频 URL

        Args:
            task_id: 任务ID
            audio_source: 音频来源类型
            audio_path: 上传的音频文件路径
            voice_profile_id: 声音档案ID
            preview_text: 预览文本

        Returns:
            音频的公网 URL
        """
        from .schemas import AudioSourceType

        if audio_source == AudioSourceType.UPLOAD:
            # 直接上传用户提供的音频
            print(f"[{task_id}] Using uploaded audio file...")
            if not audio_path:
                return None
            return await self.upload_to_media_bed(audio_path, compress_images=False)

        elif audio_source == AudioSourceType.VOICE_PROFILE:
            # 使用克隆声音合成
            print(f"[{task_id}] Using cloned voice profile: {voice_profile_id}...")
            return await self._synthesize_with_voice_profile(
                task_id, voice_profile_id, preview_text
            )

        else:
            # 使用默认音色
            print(f"[{task_id}] Using default voice...")
            return await self._generate_preview_audio(task_id, preview_text)

    async def _synthesize_with_voice_profile(
        self,
        task_id: str,
        voice_profile_id: str,
        text: str
    ) -> Optional[str]:
        """
        使用已保存的声音档案合成音频

        注意：阿里云 CosyVoice 的 voice_id 是临时的，会过期。
        因此每次使用时需要从存储的参考音频重新创建 voice。

        Args:
            task_id: 任务ID
            voice_profile_id: 声音档案ID
            text: 要合成的文本
        """
        try:
            # 获取声音档案信息
            from modules.voice_clone.repository import voice_profile_repository

            profile = await voice_profile_repository.get_by_id(voice_profile_id)
            if not profile:
                print(f"[{task_id}] Voice profile not found: {voice_profile_id}")
                return None

            # 获取参考音频 URL（优先使用已上传的 URL，否则重新上传本地文件）
            reference_audio_url = profile.get("reference_audio_url")
            reference_audio_local = profile.get("reference_audio_local")

            if not reference_audio_url and reference_audio_local:
                # 重新上传本地音频到图床
                print(f"[{task_id}] Re-uploading reference audio to media bed...")
                reference_audio_url = await self.upload_to_media_bed(
                    reference_audio_local, compress_images=False
                )

            if not reference_audio_url:
                print(f"[{task_id}] No reference audio available for voice profile")
                return None

            print(f"[{task_id}] Reference audio URL: {reference_audio_url}")

            # Step 1: 创建新的 voice（因为旧的 voice_id 已过期）
            print(f"[{task_id}] Creating voice from reference audio...")
            voice_id = await self._create_voice_from_url(task_id, reference_audio_url)

            if not voice_id:
                print(f"[{task_id}] Failed to create voice from reference audio")
                return None

            print(f"[{task_id}] Voice created: {voice_id}")

            # Step 2: 等待 voice 就绪
            print(f"[{task_id}] Waiting for voice to be ready...")
            voice_ready = await self._wait_for_voice_ready(task_id, voice_id)

            if not voice_ready:
                print(f"[{task_id}] Voice enrollment failed or timed out")
                return None

            # Step 3: 使用新的 voice 合成语音
            print(f"[{task_id}] Synthesizing with voice: {voice_id}")

            from dashscope.audio.tts_v2 import SpeechSynthesizer

            def synthesize_sync():
                synthesizer = SpeechSynthesizer(
                    model='cosyvoice-v2',
                    voice=voice_id
                )
                return synthesizer.call(text)

            audio_data = await asyncio.to_thread(synthesize_sync)

            if not audio_data:
                print(f"[{task_id}] Voice synthesis returned no data")
                return None

            # 保存音频文件
            audio_filename = f"{task_id}_cloned_audio.mp3"
            audio_path = self.previews_dir / audio_filename

            with open(audio_path, 'wb') as f:
                f.write(audio_data)

            print(f"[{task_id}] Cloned audio saved: {audio_path}, size: {len(audio_data)} bytes")

            # 上传到图床
            return await self.upload_to_media_bed(str(audio_path), compress_images=False)

        except Exception as e:
            print(f"[{task_id}] Voice profile synthesis error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _create_voice_from_url(self, task_id: str, audio_url: str) -> Optional[str]:
        """
        从音频 URL 创建新的 voice

        Args:
            task_id: 任务ID
            audio_url: 音频公网 URL

        Returns:
            voice_id 或 None
        """
        try:
            from dashscope.audio.tts_v2 import VoiceEnrollmentService

            service = VoiceEnrollmentService()

            # 生成唯一的音色前缀（仅数字和小写字母，<10字符）
            voice_prefix = f"dh{uuid.uuid4().hex[:6]}"

            def create_voice_sync():
                return service.create_voice(
                    target_model='cosyvoice-v2',
                    prefix=voice_prefix,
                    url=audio_url
                )

            voice_id = await asyncio.to_thread(create_voice_sync)

            if voice_id:
                print(f"[{task_id}] Voice created: {voice_id}")
                return voice_id
            else:
                print(f"[{task_id}] Failed to create voice")
                return None

        except Exception as e:
            print(f"[{task_id}] Create voice error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _wait_for_voice_ready(
        self,
        task_id: str,
        voice_id: str,
        max_attempts: int = 30,
        poll_interval: int = 3
    ) -> bool:
        """
        轮询等待音色就绪

        Args:
            task_id: 任务ID
            voice_id: 音色ID
            max_attempts: 最大尝试次数
            poll_interval: 轮询间隔（秒）

        Returns:
            是否就绪
        """
        try:
            from dashscope.audio.tts_v2 import VoiceEnrollmentService

            service = VoiceEnrollmentService()

            for attempt in range(max_attempts):
                try:
                    voice_info = await asyncio.to_thread(
                        service.query_voice, voice_id=voice_id
                    )
                    status = voice_info.get("status")
                    print(f"[{task_id}] Voice status (attempt {attempt + 1}/{max_attempts}): {status}")

                    if status == "OK":
                        return True
                    elif status in ["UNDEPLOYED", "FAILED"]:
                        print(f"[{task_id}] Voice enrollment failed: {status}")
                        return False

                except Exception as e:
                    print(f"[{task_id}] Query voice error: {e}")

                await asyncio.sleep(poll_interval)

            print(f"[{task_id}] Voice enrollment timed out")
            return False

        except Exception as e:
            print(f"[{task_id}] Wait for voice error: {e}")
            return False

    async def _generate_preview_audio(self, task_id: str, text: str) -> Optional[str]:
        """
        使用 CosyVoice 生成预览音频

        使用默认音色生成简短的预览音频
        """
        try:
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            def synthesize_sync():
                synthesizer = SpeechSynthesizer(
                    model='cosyvoice-v1',
                    voice='longxiaochun'  # 使用默认音色
                )
                return synthesizer.call(text)

            audio_data = await asyncio.to_thread(synthesize_sync)

            if not audio_data:
                return None

            # 保存音频文件
            audio_filename = f"{task_id}_audio.mp3"
            audio_path = self.previews_dir / audio_filename

            with open(audio_path, 'wb') as f:
                f.write(audio_data)

            # 上传到图床
            audio_url = await self.upload_to_media_bed(str(audio_path))
            return audio_url

        except Exception as e:
            print(f"[{task_id}] Generate preview audio error: {e}")
            return None

    async def _create_emo_task(
        self,
        task_id: str,
        image_url: str,
        audio_url: str,
        face_bbox: List[int],
        ext_bbox: List[int]
    ) -> Optional[str]:
        """创建 EMO 视频生成任务"""
        try:
            print(f"[{task_id}] Creating EMO task...")
            print(f"[{task_id}]   image_url: {image_url[:80]}...")
            print(f"[{task_id}]   audio_url: {audio_url[:80]}...")
            print(f"[{task_id}]   face_bbox: {face_bbox}")
            print(f"[{task_id}]   ext_bbox: {ext_bbox}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"  # 异步任务
            }
            payload = {
                "model": "emo-v1",
                "input": {
                    "image_url": image_url,
                    "audio_url": audio_url,
                    "face_bbox": face_bbox,
                    "ext_bbox": ext_bbox
                },
                "parameters": {
                    "style_level": "normal"  # 动作风格：calm/normal/active
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(EMO_GENERATE_URL, headers=headers, json=payload)

                print(f"[{task_id}] EMO create response status: {response.status_code}")
                print(f"[{task_id}] EMO create response: {response.text[:500]}")

                if response.status_code == 200:
                    result = response.json()
                    output = result.get("output", {})
                    emo_task_id = output.get("task_id")
                    print(f"[{task_id}] EMO task_id from response: {emo_task_id}")
                    return emo_task_id
                else:
                    print(f"[{task_id}] EMO create task error: {response.text}")
                    return None

        except Exception as e:
            print(f"[{task_id}] EMO create task error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _wait_for_emo_task(
        self,
        task_id: str,
        emo_task_id: str,
        max_attempts: int = 120,
        poll_interval: int = 5
    ) -> Optional[str]:
        """
        等待 EMO 任务完成 (支持从 story_generation 调用)

        注意: task_id 可能不在 digital_human_tasks 中 (当从 story_generation 调用时)
        """
        print(f"[{task_id}] _wait_for_emo_task started, emo_task_id={emo_task_id}")

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        task_url = f"{EMO_TASK_URL}/{emo_task_id}"

        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(task_url, headers=headers)

                    if response.status_code == 200:
                        result = response.json()
                        output = result.get("output", {})
                        task_status = output.get("task_status")

                        print(f"[{task_id}] EMO task status (attempt {attempt + 1}): {task_status}")

                        if task_status == "SUCCEEDED":
                            # video_url 在 results 字段中
                            results = output.get("results", {})
                            video_url = results.get("video_url") if isinstance(results, dict) else None
                            if not video_url:
                                # 尝试直接从 output 获取
                                video_url = output.get("video_url")
                            print(f"[{task_id}] EMO task succeeded, video_url={video_url}")
                            return video_url
                        elif task_status == "FAILED":
                            error_msg = output.get("message", "Unknown error")
                            print(f"[{task_id}] EMO task failed: {error_msg}")
                            return None

                        # 更新进度 (仅当 task_id 在 digital_human_tasks 字典中时)
                        # 从 story_generation 调用时，task_id 不在此字典中，跳过进度更新
                        if task_id in digital_human_tasks:
                            progress = 60 + int((attempt / max_attempts) * 30)
                            digital_human_tasks[task_id]["progress"] = min(progress, 85)
                    else:
                        print(f"[{task_id}] EMO API returned status {response.status_code}: {response.text[:200]}")

            except httpx.TimeoutException as te:
                print(f"[{task_id}] EMO poll timeout (attempt {attempt + 1}): {te}")
            except httpx.HTTPError as he:
                print(f"[{task_id}] EMO HTTP error (attempt {attempt + 1}): {he}")
            except KeyError as ke:
                # 明确捕获 KeyError 以便调试
                print(f"[{task_id}] EMO poll KeyError (attempt {attempt + 1}): key={ke}")
                import traceback
                traceback.print_exc()
            except Exception as inner_e:
                print(f"[{task_id}] EMO poll error (attempt {attempt + 1}): {type(inner_e).__name__}: {inner_e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(poll_interval)

        print(f"[{task_id}] EMO task timed out after {max_attempts} attempts")
        return None

    async def _download_video(self, video_url: str, output_path: str):
        """下载视频文件"""
        print(f"Downloading video from: {video_url[:50]}...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(video_url)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"Video downloaded to: {output_path}")
            else:
                raise Exception(f"Failed to download video: {response.status_code}")

    def create_task(self, user_id: str) -> str:
        """创建新的数字人任务"""
        task_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

        digital_human_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "video_url": None,
            "image_url": None,
            "face_bbox": None,
            "ext_bbox": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None
        }

        return task_id

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        return digital_human_tasks.get(task_id)

    def save_image(self, user_id: str, file_content: bytes, filename: str) -> str:
        """保存用户上传的头像图片"""
        ext = Path(filename).suffix or ".jpg"
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.images_dir / new_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    async def save_avatar_profile(self, user_id: str, task_id: str, name: str) -> Optional[dict]:
        """保存头像档案到数据库"""
        from .repository import avatar_profile_repository

        task = digital_human_tasks.get(task_id)
        if not task:
            return None

        if task.get("status") != "completed":
            return None

        if not task_id.startswith(user_id):
            return None

        profile_data = {
            "user_id": user_id,
            "name": name,
            "image_url": task.get("image_url"),
            "image_local": task.get("image_local", ""),
            "face_bbox": task.get("face_bbox", []),
            "ext_bbox": task.get("ext_bbox", []),
            "preview_video_url": task.get("video_url"),
            "status": "active"
        }

        profile_id = await avatar_profile_repository.create(profile_data)
        profile_data["id"] = profile_id

        return profile_data

    async def get_user_avatar_profiles(self, user_id: str) -> list:
        """获取用户的所有头像档案"""
        from .repository import avatar_profile_repository
        return await avatar_profile_repository.get_by_user_id(user_id)

    async def get_avatar_profile(self, profile_id: str, user_id: str) -> Optional[dict]:
        """获取单个头像档案"""
        from .repository import avatar_profile_repository
        profile = await avatar_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return profile
        return None

    async def update_avatar_profile(self, profile_id: str, user_id: str, name: str) -> bool:
        """更新头像档案名称"""
        from .repository import avatar_profile_repository
        profile = await avatar_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await avatar_profile_repository.update(profile_id, {"name": name})
        return False

    async def delete_avatar_profile(self, profile_id: str, user_id: str) -> bool:
        """删除头像档案"""
        from .repository import avatar_profile_repository
        profile = await avatar_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await avatar_profile_repository.delete(profile_id)
        return False


# 全局服务实例
digital_human_service = DigitalHumanService()
