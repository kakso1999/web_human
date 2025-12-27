"""
故事生成服务

完整业务流程：
1. 从故事视频提取音频
2. 分离人声和背景音乐 (APICore Suno Stems)
3. 语音识别生成字幕 (APICore Whisper)
4. 生成克隆语音 (CosyVoice)
5. 生成数字人视频 (EMO)
6. 合成最终视频 (IMS)
"""
import os
import re
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.config.settings import get_settings
from .repository import get_story_generation_repository, StoryGenerationRepository
from .apicore_client import get_apicore_client, APICoreClient
from .schemas import StoryJobStatus, StoryJobStep

settings = get_settings()
logger = logging.getLogger(__name__)


class StoryGenerationService:
    """故事生成服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.repository = get_story_generation_repository()
        self.apicore = get_apicore_client()
        self.upload_dir = Path(settings.UPLOAD_DIR) / "story_generation"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.media_bed_url = settings.MEDIA_BED_URL

    # ===================== 任务管理 =====================

    async def create_job(
        self,
        user_id: str,
        story_id: str,
        voice_profile_id: str,
        avatar_profile_id: str,
        replace_all_voice: bool = True
    ) -> Dict[str, Any]:
        """创建故事生成任务"""
        # 获取故事信息
        from modules.story.repository import get_story_repository
        story_repo = get_story_repository()
        story = await story_repo.get_story_by_id(story_id)

        if not story:
            raise ValueError(f"Story not found: {story_id}")

        video_url = story.get("video_url")
        if not video_url:
            raise ValueError(f"Story has no video: {story_id}")

        # 创建任务
        job_id = await self.repository.create_job(
            user_id=user_id,
            story_id=story_id,
            voice_profile_id=voice_profile_id,
            avatar_profile_id=avatar_profile_id,
            original_video_url=video_url,
            replace_all_voice=replace_all_voice
        )

        # 启动异步处理
        asyncio.create_task(self._process_job(job_id))

        return {"job_id": job_id, "status": "pending"}

    async def get_job(self, user_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        return await self.repository.get_job_by_user(user_id, job_id)

    async def list_jobs(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户任务列表"""
        jobs, total = await self.repository.list_jobs_by_user(user_id, page, page_size)
        return {
            "items": jobs,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def get_subtitles(self, user_id: str, job_id: str) -> Dict[str, Any]:
        """获取字幕列表"""
        job = await self.repository.get_job_by_user(user_id, job_id)
        if not job:
            raise ValueError("Job not found")

        subtitles = await self.repository.get_subtitles(job_id)

        # 计算总时长
        total_duration = 0.0
        if subtitles:
            total_duration = max(s["end_time"] for s in subtitles)

        return {
            "subtitles": subtitles,
            "total_duration": total_duration
        }

    # ===================== 任务处理流程 =====================

    async def _process_job(self, job_id: str):
        """处理任务 - 主流程"""
        logger.info(f"[{job_id}] Starting story generation job")

        try:
            # 更新状态为处理中
            await self._update_progress(job_id, StoryJobStep.INIT, 0)

            # Step 1: 提取音频
            await self._update_progress(job_id, StoryJobStep.EXTRACTING_AUDIO, 5)
            audio_url = await self._extract_audio(job_id)
            if not audio_url:
                raise Exception("Failed to extract audio from video")

            # Step 2: 分离人声
            await self._update_progress(job_id, StoryJobStep.SEPARATING_VOCALS, 15)
            vocals_url, instrumental_url = await self._separate_vocals(job_id, audio_url)
            if not vocals_url:
                raise Exception("Failed to separate vocals")

            # Step 3: 语音识别生成字幕
            await self._update_progress(job_id, StoryJobStep.TRANSCRIBING, 30)
            srt_content = await self._transcribe_audio(job_id, vocals_url)
            if not srt_content:
                raise Exception("Failed to transcribe audio")

            # 解析字幕并保存
            subtitles = self._parse_srt(srt_content)
            await self.repository.save_subtitles(job_id, subtitles)
            await self.repository.update_job_field(job_id, "subtitle_srt_content", srt_content)

            # Step 4: 生成克隆语音
            await self._update_progress(job_id, StoryJobStep.GENERATING_VOICE, 45)
            cloned_audio_url = await self._generate_cloned_voice(job_id, subtitles)
            if not cloned_audio_url:
                raise Exception("Failed to generate cloned voice")

            # Step 5: 生成数字人视频
            await self._update_progress(job_id, StoryJobStep.GENERATING_DIGITAL_HUMAN, 60)
            digital_human_url = await self._generate_digital_human(job_id, cloned_audio_url)
            if not digital_human_url:
                raise Exception("Failed to generate digital human video")

            # Step 6: 合成最终视频
            await self._update_progress(job_id, StoryJobStep.COMPOSITING_VIDEO, 80)
            final_video_url = await self._composite_video(job_id, instrumental_url, digital_human_url)

            # 完成
            await self.repository.update_job_status(
                job_id,
                StoryJobStatus.COMPLETED,
                progress=100,
                current_step=StoryJobStep.COMPLETED
            )
            await self.repository.update_job_field(job_id, "final_video_url", final_video_url)

            logger.info(f"[{job_id}] Story generation completed!")

        except Exception as e:
            logger.error(f"[{job_id}] Story generation failed: {e}")
            import traceback
            traceback.print_exc()

            await self.repository.update_job_status(
                job_id,
                StoryJobStatus.FAILED,
                error=str(e)
            )

    async def _update_progress(
        self,
        job_id: str,
        step: StoryJobStep,
        progress: int
    ):
        """更新任务进度"""
        await self.repository.update_job_status(
            job_id,
            StoryJobStatus.PROCESSING,
            progress=progress,
            current_step=step
        )

    # ===================== Step 1: 提取音频 =====================

    async def _extract_audio(self, job_id: str) -> Optional[str]:
        """从视频提取音频"""
        logger.info(f"[{job_id}] Extracting audio from video")

        job = await self.repository.get_job(job_id)
        video_url = job.get("original_video_url")

        if not video_url:
            return None

        try:
            import httpx
            import subprocess

            # 下载视频
            logger.info(f"[{job_id}] Downloading video: {video_url}")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(video_url)
                if response.status_code != 200:
                    logger.error(f"[{job_id}] Failed to download video: {response.status_code}")
                    return None
                video_bytes = response.content

            # 保存视频
            video_path = self.upload_dir / f"{job_id}_video.mp4"
            with open(video_path, 'wb') as f:
                f.write(video_bytes)

            # 使用 FFmpeg 提取音频
            audio_path = self.upload_dir / f"{job_id}_audio.mp3"

            cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-vn',  # 无视频
                '-acodec', 'libmp3lame',
                '-ar', '44100',
                '-ac', '2',
                '-b:a', '192k',
                str(audio_path)
            ]

            logger.info(f"[{job_id}] Running FFmpeg: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"[{job_id}] FFmpeg error: {stderr.decode()}")
                return None

            # 上传到图床
            audio_url = await self._upload_to_media_bed(str(audio_path))
            await self.repository.update_job_field(job_id, "original_audio_url", audio_url)

            logger.info(f"[{job_id}] Audio extracted: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"[{job_id}] Extract audio error: {e}")
            return None

    # ===================== Step 2: 分离人声 =====================

    async def _separate_vocals(
        self,
        job_id: str,
        audio_url: str
    ) -> tuple[Optional[str], Optional[str]]:
        """分离人声和背景音乐"""
        logger.info(f"[{job_id}] Separating vocals from audio")

        try:
            # 上传音频到 Suno
            upload_result = await self.apicore.upload_audio_url(audio_url)
            clip_id = upload_result.get("clip_id") or upload_result.get("id")

            if not clip_id:
                logger.error(f"[{job_id}] Failed to get clip_id from upload")
                return None, None

            logger.info(f"[{job_id}] Audio uploaded, clip_id: {clip_id}")

            # 获取分离结果
            stems = await self.apicore.get_stems(clip_id)
            vocals_url = stems.get("vocals")
            instrumental_url = stems.get("instrumental")

            # 保存结果
            await self.repository.update_job_fields(job_id, {
                "vocals_url": vocals_url,
                "instrumental_url": instrumental_url
            })

            logger.info(f"[{job_id}] Vocals separated - vocals: {vocals_url}, instrumental: {instrumental_url}")
            return vocals_url, instrumental_url

        except Exception as e:
            logger.error(f"[{job_id}] Separate vocals error: {e}")
            return None, None

    # ===================== Step 3: 语音识别 =====================

    async def _transcribe_audio(
        self,
        job_id: str,
        audio_url: str
    ) -> Optional[str]:
        """语音识别生成 SRT 字幕"""
        logger.info(f"[{job_id}] Transcribing audio to SRT")

        try:
            srt_content = await self.apicore.transcribe_audio_url(
                audio_url=audio_url,
                response_format="srt",
                language="zh"
            )

            if not srt_content:
                return None

            # 保存 SRT 文件
            srt_path = self.upload_dir / f"{job_id}_subtitles.srt"
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)

            # 上传到图床
            srt_url = await self._upload_to_media_bed(str(srt_path))
            await self.repository.update_job_field(job_id, "subtitle_srt_url", srt_url)

            logger.info(f"[{job_id}] Transcription completed, {len(srt_content)} chars")
            return srt_content

        except Exception as e:
            logger.error(f"[{job_id}] Transcribe error: {e}")
            return None

    def _parse_srt(self, srt_content: str) -> List[Dict[str, Any]]:
        """解析 SRT 字幕内容"""
        subtitles = []
        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\n|\Z)'

        for match in re.finditer(pattern, srt_content, re.DOTALL):
            index = int(match.group(1))
            start_time = self._srt_time_to_seconds(match.group(2))
            end_time = self._srt_time_to_seconds(match.group(3))
            text = match.group(4).strip().replace('\n', ' ')

            subtitles.append({
                "index": index,
                "start_time": start_time,
                "end_time": end_time,
                "text": text
            })

        return subtitles

    def _srt_time_to_seconds(self, time_str: str) -> float:
        """SRT 时间格式转秒"""
        # 格式: 00:00:00,000
        parts = time_str.replace(',', '.').split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    # ===================== Step 4: 生成克隆语音 =====================

    async def _generate_cloned_voice(
        self,
        job_id: str,
        subtitles: List[Dict[str, Any]]
    ) -> Optional[str]:
        """生成克隆语音"""
        logger.info(f"[{job_id}] Generating cloned voice for {len(subtitles)} subtitles")

        try:
            job = await self.repository.get_job(job_id)
            voice_profile_id = job.get("voice_profile_id")

            # 合并所有字幕文本
            full_text = " ".join(sub["text"] for sub in subtitles)

            # 获取声音档案
            from modules.voice_clone.repository import voice_profile_repository
            profile = await voice_profile_repository.get_by_id(voice_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Voice profile not found: {voice_profile_id}")
                return None

            reference_audio_url = profile.get("reference_audio_url")
            if not reference_audio_url:
                logger.error(f"[{job_id}] No reference audio in voice profile")
                return None

            # 创建 voice
            voice_id = await self._create_voice_from_url(job_id, reference_audio_url)
            if not voice_id:
                return None

            # 等待 voice 就绪
            voice_ready = await self._wait_for_voice_ready(job_id, voice_id)
            if not voice_ready:
                return None

            # 合成语音
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            def synthesize_sync():
                synthesizer = SpeechSynthesizer(
                    model='cosyvoice-v2',
                    voice=voice_id
                )
                return synthesizer.call(full_text)

            audio_data = await asyncio.to_thread(synthesize_sync)

            if not audio_data:
                return None

            # 保存并上传
            audio_path = self.upload_dir / f"{job_id}_cloned_audio.mp3"
            with open(audio_path, 'wb') as f:
                f.write(audio_data)

            audio_url = await self._upload_to_media_bed(str(audio_path))
            await self.repository.update_job_field(job_id, "cloned_audio_url", audio_url)

            logger.info(f"[{job_id}] Cloned voice generated: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate cloned voice error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _create_voice_from_url(self, job_id: str, audio_url: str) -> Optional[str]:
        """从音频 URL 创建 voice"""
        try:
            from dashscope.audio.tts_v2 import VoiceEnrollmentService

            service = VoiceEnrollmentService()
            voice_prefix = f"sg{uuid.uuid4().hex[:6]}"

            def create_voice_sync():
                return service.create_voice(
                    target_model='cosyvoice-v2',
                    prefix=voice_prefix,
                    url=audio_url
                )

            voice_id = await asyncio.to_thread(create_voice_sync)
            logger.info(f"[{job_id}] Voice created: {voice_id}")
            return voice_id

        except Exception as e:
            logger.error(f"[{job_id}] Create voice error: {e}")
            return None

    async def _wait_for_voice_ready(
        self,
        job_id: str,
        voice_id: str,
        max_attempts: int = 30,
        poll_interval: int = 3
    ) -> bool:
        """等待 voice 就绪"""
        from dashscope.audio.tts_v2 import VoiceEnrollmentService

        service = VoiceEnrollmentService()

        for attempt in range(max_attempts):
            try:
                voice_info = await asyncio.to_thread(
                    service.query_voice, voice_id=voice_id
                )
                status = voice_info.get("status")
                logger.info(f"[{job_id}] Voice status ({attempt + 1}/{max_attempts}): {status}")

                if status == "OK":
                    return True
                elif status in ["UNDEPLOYED", "FAILED"]:
                    return False

                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"[{job_id}] Query voice error: {e}")
                await asyncio.sleep(poll_interval)

        return False

    # ===================== Step 5: 生成数字人视频 =====================

    async def _generate_digital_human(
        self,
        job_id: str,
        audio_url: str
    ) -> Optional[str]:
        """生成数字人视频"""
        logger.info(f"[{job_id}] Generating digital human video")

        try:
            job = await self.repository.get_job(job_id)
            avatar_profile_id = job.get("avatar_profile_id")

            # 获取头像档案
            from modules.digital_human.repository import avatar_profile_repository
            profile = await avatar_profile_repository.get_by_id(avatar_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Avatar profile not found: {avatar_profile_id}")
                return None

            image_url = profile.get("image_url")
            face_bbox = profile.get("face_bbox")
            ext_bbox = profile.get("ext_bbox")

            if not image_url:
                logger.error(f"[{job_id}] No image in avatar profile")
                return None

            if not face_bbox or not ext_bbox:
                logger.error(f"[{job_id}] No bbox info in avatar profile")
                return None

            # 调用 EMO API 生成数字人视频
            from modules.digital_human.service import DigitalHumanService
            dh_service = DigitalHumanService()

            # 创建 EMO 任务
            emo_task_id = await dh_service._create_emo_task(
                task_id=job_id,
                image_url=image_url,
                audio_url=audio_url,
                face_bbox=face_bbox,
                ext_bbox=ext_bbox
            )

            if not emo_task_id:
                logger.error(f"[{job_id}] Failed to create EMO task")
                return None

            logger.info(f"[{job_id}] EMO task created: {emo_task_id}")

            # 等待 EMO 任务完成
            video_url = await dh_service._wait_for_emo_task(
                task_id=job_id,
                emo_task_id=emo_task_id,
                max_attempts=180,  # 15分钟超时
                poll_interval=5
            )

            if video_url:
                await self.repository.update_job_field(job_id, "digital_human_video_url", video_url)

            logger.info(f"[{job_id}] Digital human video: {video_url}")
            return video_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate digital human error: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ===================== Step 6: 视频合成 =====================

    async def _composite_video(
        self,
        job_id: str,
        instrumental_url: str,
        digital_human_url: str
    ) -> Optional[str]:
        """合成最终视频"""
        logger.info(f"[{job_id}] Compositing final video")

        try:
            job = await self.repository.get_job(job_id)
            original_video_url = job.get("original_video_url")
            cloned_audio_url = job.get("cloned_audio_url")

            # TODO: 使用 IMS API 或 FFmpeg 进行视频合成
            # 目前简化处理：返回数字人视频

            # 使用 FFmpeg 合成
            # 1. 原视频（静音）
            # 2. 数字人视频（画中画，右下角）
            # 3. 克隆语音 + 背景音乐

            # 简化版本：暂时返回数字人视频
            logger.warning(f"[{job_id}] Video composition not fully implemented, returning digital human video")

            return digital_human_url

        except Exception as e:
            logger.error(f"[{job_id}] Composite video error: {e}")
            return None

    # ===================== 工具方法 =====================

    async def _upload_to_media_bed(self, file_path: str) -> Optional[str]:
        """上传文件到图床"""
        try:
            import httpx

            file_path = Path(file_path)
            if not file_path.exists():
                return None

            suffix = file_path.suffix.lower()
            content_type_map = {
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.mp4': 'video/mp4',
                '.srt': 'text/plain',
                '.jpg': 'image/jpeg',
                '.png': 'image/png',
            }
            content_type = content_type_map.get(suffix, 'application/octet-stream')

            with open(file_path, 'rb') as f:
                file_content = f.read()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.media_bed_url}/upload",
                    files={"file": (file_path.name, file_content, content_type)}
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("url")

            return None

        except Exception as e:
            logger.error(f"Upload to media bed error: {e}")
            return None


# 单例
_service: Optional[StoryGenerationService] = None


def get_story_generation_service() -> StoryGenerationService:
    """获取服务单例"""
    global _service
    if _service is None:
        _service = StoryGenerationService()
    return _service
