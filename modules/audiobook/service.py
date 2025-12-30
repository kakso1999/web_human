"""
有声书模块 - 服务层

核心功能：
- 使用 CosyVoice TTS 生成有声书
- 可选与背景音乐混合
"""

import os
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

from core.config.settings import get_settings
from .repository import (
    audiobook_story_repository,
    audiobook_job_repository,
    AudiobookStoryRepository,
    AudiobookJobRepository
)

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_ffmpeg_command(cmd: List[str]) -> tuple[int, bytes, bytes]:
    """
    Windows 兼容的 FFmpeg 命令执行
    """
    def _run():
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode, result.stdout, result.stderr

    return await asyncio.to_thread(_run)


class AudiobookService:
    """有声书生成服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.story_repo = audiobook_story_repository
        self.job_repo = audiobook_job_repository
        self.upload_dir = Path(settings.UPLOAD_DIR) / "audiobook"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.media_bed_url = settings.MEDIA_BED_URL

    # ==================== 故事管理 ====================

    async def create_story(self, story_data: dict) -> str:
        """创建故事"""
        # 估算时长（基于内容长度，假设每分钟约 150 词/300 字）
        content = story_data.get("content", "")
        word_count = len(content.split()) if story_data.get("language") == "en" else len(content)
        estimated_duration = max(60, int(word_count / 2.5))  # 至少 1 分钟
        story_data["estimated_duration"] = estimated_duration

        return await self.story_repo.create(story_data)

    async def get_story(self, story_id: str) -> Optional[dict]:
        """获取故事详情"""
        return await self.story_repo.get_by_id(story_id)

    async def list_stories(
        self,
        page: int = 1,
        page_size: int = 20,
        language: Optional[str] = None,
        category: Optional[str] = None,
        age_group: Optional[str] = None,
        published_only: bool = True
    ) -> Dict[str, Any]:
        """获取故事列表"""
        if published_only:
            stories, total = await self.story_repo.list_published(
                page=page,
                page_size=page_size,
                language=language,
                category=category,
                age_group=age_group
            )
        else:
            stories, total = await self.story_repo.list_all(
                page=page,
                page_size=page_size,
                language=language,
                category=category
            )

        return {
            "items": stories,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def update_story(self, story_id: str, update_data: dict) -> bool:
        """更新故事"""
        # 如果更新了内容，重新估算时长
        if "content" in update_data:
            content = update_data["content"]
            language = update_data.get("language", "en")
            word_count = len(content.split()) if language == "en" else len(content)
            update_data["estimated_duration"] = max(60, int(word_count / 2.5))

        return await self.story_repo.update(story_id, update_data)

    async def delete_story(self, story_id: str) -> bool:
        """删除故事"""
        return await self.story_repo.delete(story_id)

    # ==================== 任务管理 ====================

    async def create_job(
        self,
        user_id: str,
        story_id: str,
        voice_profile_id: str
    ) -> Dict[str, Any]:
        """创建有声书生成任务"""
        # 获取故事信息
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise ValueError(f"Story not found: {story_id}")

        # 获取声音档案信息
        from modules.voice_clone.repository import voice_profile_repository
        voice_profile = await voice_profile_repository.get_by_id(voice_profile_id)
        if not voice_profile:
            raise ValueError(f"Voice profile not found: {voice_profile_id}")

        # 创建任务
        job_id = await self.job_repo.create(
            user_id=user_id,
            story_id=story_id,
            voice_profile_id=voice_profile_id,
            story_title=story.get("title_en") or story.get("title", ""),
            voice_name=voice_profile.get("name", "")
        )

        # 启动异步处理
        asyncio.create_task(self._process_job(job_id))

        return {"job_id": job_id, "status": "pending"}

    async def get_job(self, user_id: str, job_id: str) -> Optional[dict]:
        """获取用户的任务详情"""
        return await self.job_repo.get_by_user(user_id, job_id)

    async def list_jobs(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户的任务列表"""
        jobs, total = await self.job_repo.list_by_user(user_id, page, page_size)
        return {
            "items": jobs,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def list_all_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取所有任务（管理端）"""
        jobs, total = await self.job_repo.list_all(
            page=page,
            page_size=page_size,
            status=status,
            user_id=user_id
        )
        return {
            "items": jobs,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    # ==================== 任务处理 ====================

    async def _process_job(self, job_id: str):
        """
        处理有声书生成任务

        流程：
        1. 获取故事内容和声音档案
        2. 使用 CosyVoice TTS 生成语音
        3. (可选) 与背景音乐混合
        4. 上传到图床
        5. 更新任务状态
        """
        logger.info(f"[{job_id}] Starting audiobook generation")

        try:
            # 更新状态为处理中
            await self.job_repo.update_status(job_id, "processing", 5, "init")

            # 获取任务信息
            job = await self.job_repo.get_by_id(job_id)
            if not job:
                raise Exception("Job not found")

            story_id = job.get("story_id")
            voice_profile_id = job.get("voice_profile_id")

            # 获取故事内容
            story = await self.story_repo.get_by_id(story_id)
            if not story:
                raise Exception("Story not found")

            content = story.get("content", "")
            background_music_url = story.get("background_music_url")

            # 获取声音档案
            from modules.voice_clone.repository import voice_profile_repository
            voice_profile = await voice_profile_repository.get_by_id(voice_profile_id)
            if not voice_profile:
                raise Exception("Voice profile not found")

            voice_id = voice_profile.get("voice_id")
            if not voice_id:
                raise Exception("No voice_id in profile")

            logger.info(f"[{job_id}] Using voice_id: {voice_id}")
            await self.job_repo.update_status(job_id, "processing", 20, "tts")

            # 生成 TTS 语音
            audio_path = await self._generate_tts(job_id, voice_id, content)
            if not audio_path:
                raise Exception("TTS generation failed")

            await self.job_repo.update_status(job_id, "processing", 70, "mixing")

            # 获取音频时长
            duration = await self._get_audio_duration(audio_path)

            # 如果有背景音乐，进行混合
            final_audio_path = audio_path
            if background_music_url:
                logger.info(f"[{job_id}] Mixing with background music...")
                mixed_path = await self._mix_with_bgm(job_id, audio_path, background_music_url)
                if mixed_path:
                    final_audio_path = mixed_path

            await self.job_repo.update_status(job_id, "processing", 90, "mixing")

            # 上传到图床
            audio_url = await self._upload_to_media_bed(final_audio_path)
            if not audio_url:
                raise Exception("Failed to upload audio")

            # 更新任务完成
            await self.job_repo.update_fields(job_id, {
                "status": "completed",
                "progress": 100,
                "current_step": "completed",
                "audio_url": audio_url,
                "duration": int(duration),
                "completed_at": datetime.utcnow()
            })

            logger.info(f"[{job_id}] Audiobook generation completed: {audio_url}")

        except Exception as e:
            logger.error(f"[{job_id}] Audiobook generation failed: {e}")
            import traceback
            traceback.print_exc()

            await self.job_repo.update_status(
                job_id, "failed", 0, "init", error=str(e)
            )

    async def _generate_tts(
        self,
        job_id: str,
        voice_id: str,
        text: str
    ) -> Optional[str]:
        """
        使用 CosyVoice TTS 生成语音

        对于长文本，分段生成然后拼接
        """
        logger.info(f"[{job_id}] Generating TTS for {len(text)} characters")

        try:
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            # 分段处理（每段最多 2000 字符）
            MAX_CHUNK_SIZE = 2000
            chunks = self._split_text(text, MAX_CHUNK_SIZE)

            logger.info(f"[{job_id}] Split into {len(chunks)} chunks")

            segment_files = []
            for i, chunk in enumerate(chunks):
                logger.info(f"[{job_id}] Processing chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

                # 调用 TTS
                def synthesize_sync():
                    synthesizer = SpeechSynthesizer(
                        model='cosyvoice-v2',
                        voice=voice_id
                    )
                    return synthesizer.call(chunk)

                audio_data = await asyncio.to_thread(synthesize_sync)

                if not audio_data:
                    logger.warning(f"[{job_id}] Chunk {i+1} TTS failed")
                    continue

                # 保存临时文件
                chunk_path = self.upload_dir / f"{job_id}_chunk_{i}.mp3"
                with open(chunk_path, 'wb') as f:
                    f.write(audio_data)

                segment_files.append(str(chunk_path))

            if not segment_files:
                logger.error(f"[{job_id}] No audio chunks generated")
                return None

            # 如果只有一个片段，直接返回
            if len(segment_files) == 1:
                final_path = self.upload_dir / f"{job_id}_audio.mp3"
                Path(segment_files[0]).rename(final_path)
                return str(final_path)

            # 多个片段，使用 FFmpeg 拼接
            final_path = await self._concat_audio_files(job_id, segment_files)

            # 清理临时文件
            for f in segment_files:
                try:
                    Path(f).unlink()
                except:
                    pass

            return final_path

        except Exception as e:
            logger.error(f"[{job_id}] TTS generation error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _split_text(self, text: str, max_size: int) -> List[str]:
        """
        智能分割文本

        在句子边界分割，避免中断句子
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        current_chunk = ""

        # 按段落分割
        paragraphs = text.split('\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前段落太长，按句子分割
            if len(para) > max_size:
                sentences = self._split_into_sentences(para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > max_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                if len(current_chunk) + len(para) + 2 > max_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    current_chunk += "\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """按句子分割"""
        import re
        # 英文句子分割
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    async def _concat_audio_files(
        self,
        job_id: str,
        file_paths: List[str]
    ) -> Optional[str]:
        """使用 FFmpeg 拼接音频文件"""
        logger.info(f"[{job_id}] Concatenating {len(file_paths)} audio files")

        try:
            # 创建拼接列表文件
            concat_list_path = self.upload_dir / f"{job_id}_concat.txt"
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for path in file_paths:
                    abs_path = str(Path(path).resolve()).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")

            output_path = self.upload_dir / f"{job_id}_audio.mp3"

            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list_path),
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            # 清理列表文件
            concat_list_path.unlink(missing_ok=True)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg concat error: {stderr.decode()[:300]}")
                return None

            if not output_path.exists():
                return None

            return str(output_path)

        except Exception as e:
            logger.error(f"[{job_id}] Concat audio error: {e}")
            return None

    async def _mix_with_bgm(
        self,
        job_id: str,
        voice_path: str,
        bgm_url: str,
        bgm_volume: float = 0.2
    ) -> Optional[str]:
        """将语音与背景音乐混合"""
        logger.info(f"[{job_id}] Mixing with background music")

        try:
            # 下载背景音乐
            bgm_path = self.upload_dir / f"{job_id}_bgm.mp3"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(bgm_url)
                if response.status_code != 200:
                    logger.warning(f"[{job_id}] Failed to download BGM")
                    return None
                with open(bgm_path, 'wb') as f:
                    f.write(response.content)

            output_path = self.upload_dir / f"{job_id}_mixed.mp3"

            # FFmpeg 混音命令
            cmd = [
                'ffmpeg', '-y',
                '-i', voice_path,
                '-i', str(bgm_path),
                '-filter_complex',
                f'[0:a]volume=1.0[voice];[1:a]volume={bgm_volume},aloop=loop=-1:size=2e+09[bgm];'
                f'[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[out]',
                '-map', '[out]',
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            # 清理背景音乐文件
            bgm_path.unlink(missing_ok=True)

            if returncode != 0:
                logger.warning(f"[{job_id}] BGM mix failed: {stderr.decode()[:200]}")
                return None

            if not output_path.exists():
                return None

            return str(output_path)

        except Exception as e:
            logger.error(f"[{job_id}] Mix BGM error: {e}")
            return None

    async def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]

        returncode, stdout, stderr = await run_ffmpeg_command(cmd)

        try:
            return float(stdout.decode().strip())
        except:
            return 0.0

    async def _upload_to_media_bed(self, file_path: str) -> Optional[str]:
        """上传文件到图床"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return None

            with open(file_path, 'rb') as f:
                file_content = f.read()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.media_bed_url}/upload",
                    files={"file": (file_path.name, file_content, "audio/mpeg")}
                )

                if response.status_code == 200:
                    result = response.json()
                    relative_url = result.get("url")
                    if relative_url:
                        return f"{self.media_bed_url}{relative_url}"

            return None

        except Exception as e:
            logger.error(f"Upload to media bed error: {e}")
            return None


# 全局服务实例
_service: Optional[AudiobookService] = None


def get_audiobook_service() -> AudiobookService:
    """获取服务单例"""
    global _service
    if _service is None:
        _service = AudiobookService()
    return _service
