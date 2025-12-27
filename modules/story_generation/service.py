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
        from modules.story.repository import StoryRepository
        story_repo = StoryRepository()
        story = await story_repo.get_by_id(story_id)

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

            # Step 2: 尝试分离人声（可选，失败则跳过）
            await self._update_progress(job_id, StoryJobStep.SEPARATING_VOCALS, 15)
            vocals_url, instrumental_url = await self._separate_vocals(job_id, audio_url)

            # 如果分离失败，使用原始音频
            if not vocals_url:
                logger.warning(f"[{job_id}] Vocal separation failed, using original audio")
                vocals_url = audio_url
                instrumental_url = None  # 没有背景音乐

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
            await self._update_progress(job_id, StoryJobStep.GENERATING_VOICE, 50)
            cloned_audio_url = await self._generate_cloned_voice(job_id, subtitles)
            if not cloned_audio_url:
                raise Exception("Failed to generate cloned voice")

            # Step 5: 跳过数字人生成（太贵），直接合成视频
            # await self._update_progress(job_id, StoryJobStep.GENERATING_DIGITAL_HUMAN, 60)
            # digital_human_url = await self._generate_digital_human(job_id, cloned_audio_url)

            # Step 6: 合成最终视频（原视频 + 克隆语音 + 背景音乐）
            await self._update_progress(job_id, StoryJobStep.COMPOSITING_VIDEO, 70)
            final_video_url = await self._composite_video_with_audio(job_id, instrumental_url)

            if not final_video_url:
                raise Exception("Failed to composite video")

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

            video_path = self.upload_dir / f"{job_id}_video.mp4"

            # 检查是否是本地路径
            if video_url.startswith("/uploads/"):
                # 本地路径，直接复制
                local_video_path = Path(settings.UPLOAD_DIR).parent / video_url.lstrip("/")
                logger.info(f"[{job_id}] Using local video: {local_video_path}")
                if local_video_path.exists():
                    import shutil
                    shutil.copy(str(local_video_path), str(video_path))
                else:
                    logger.error(f"[{job_id}] Local video not found: {local_video_path}")
                    return None
            elif video_url.startswith("http"):
                # 下载视频
                logger.info(f"[{job_id}] Downloading video: {video_url}")
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(video_url)
                    if response.status_code != 200:
                        logger.error(f"[{job_id}] Failed to download video: {response.status_code}")
                        return None
                    with open(video_path, 'wb') as f:
                        f.write(response.content)
            else:
                logger.error(f"[{job_id}] Invalid video URL: {video_url}")
                return None

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
            import traceback
            traceback.print_exc()
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
            import httpx

            # 获取音频数据
            audio_path = self.upload_dir / f"{job_id}_audio.mp3"

            if audio_path.exists():
                # 使用本地文件
                with open(audio_path, 'rb') as f:
                    audio_bytes = f.read()
                logger.info(f"[{job_id}] Using local audio file: {len(audio_bytes)} bytes")
            elif audio_url.startswith("http"):
                # 下载音频
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.get(audio_url)
                    if response.status_code != 200:
                        logger.error(f"[{job_id}] Failed to download audio: {response.status_code}")
                        return None
                    audio_bytes = response.content
            else:
                logger.error(f"[{job_id}] Invalid audio source")
                return None

            # 调用 Whisper API
            headers = {
                "Authorization": f"Bearer {settings.APICORE_API_KEY}"
            }

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{settings.APICORE_BASE_URL}/v1/audio/transcriptions",
                    headers=headers,
                    files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
                    data={
                        "model": "whisper-1",
                        "response_format": "srt",
                        "language": "en"  # 自动检测语言
                    }
                )

                if response.status_code != 200:
                    logger.error(f"[{job_id}] Whisper API error: {response.status_code} - {response.text}")
                    return None

                srt_content = response.text

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
            import traceback
            traceback.print_exc()
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
        """
        生成克隆语音 - 按字幕时间轴对齐

        流程：
        1. 对每段字幕生成克隆语音
        2. 使用 FFmpeg atempo 调整每段语音时长匹配原始时间
        3. 按时间轴拼接所有片段（空白处用静音填充）
        """
        logger.info(f"[{job_id}] Generating cloned voice for {len(subtitles)} subtitles")

        try:
            job = await self.repository.get_job(job_id)
            voice_profile_id = job.get("voice_profile_id")

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

            # 创建片段目录
            segments_dir = self.upload_dir / f"{job_id}_segments"
            segments_dir.mkdir(parents=True, exist_ok=True)

            # 获取总时长（用于生成最终音频长度）
            total_duration = max(sub["end_time"] for sub in subtitles) if subtitles else 0
            logger.info(f"[{job_id}] Total duration: {total_duration:.2f}s, {len(subtitles)} segments")

            # 对每段字幕生成克隆语音
            from dashscope.audio.tts_v2 import SpeechSynthesizer
            segment_files = []

            for i, sub in enumerate(subtitles):
                text = sub["text"]
                start_time = sub["start_time"]
                end_time = sub["end_time"]
                target_duration = end_time - start_time

                logger.info(f"[{job_id}] Segment {i+1}/{len(subtitles)}: {start_time:.2f}s - {end_time:.2f}s ({target_duration:.2f}s) - '{text[:30]}...'")

                # 生成克隆语音
                segment_path = segments_dir / f"segment_{i:03d}_raw.mp3"
                adjusted_path = segments_dir / f"segment_{i:03d}_adjusted.mp3"

                def synthesize_segment(txt):
                    synthesizer = SpeechSynthesizer(
                        model='cosyvoice-v2',
                        voice=voice_id
                    )
                    return synthesizer.call(txt)

                audio_data = await asyncio.to_thread(synthesize_segment, text)

                if not audio_data:
                    logger.warning(f"[{job_id}] Failed to generate segment {i+1}")
                    continue

                # 保存原始片段
                with open(segment_path, 'wb') as f:
                    f.write(audio_data)

                # 获取生成音频的时长
                generated_duration = await self._get_audio_duration(str(segment_path))
                logger.info(f"[{job_id}] Segment {i+1} generated: {generated_duration:.2f}s (target: {target_duration:.2f}s)")

                # 智能调整时长（保持自然语速）
                if generated_duration > 0 and target_duration > 0:
                    speed_ratio = generated_duration / target_duration

                    if speed_ratio <= 1.0:
                        # 生成的比目标短或相等，不需要调整，后面会自动留空白
                        logger.info(f"[{job_id}] Segment {i+1}: shorter than target, keeping original")
                        segment_files.append({
                            "path": str(segment_path),
                            "start_time": start_time,
                            "end_time": start_time + generated_duration  # 实际结束时间
                        })
                    elif speed_ratio <= 1.3:
                        # 需要加速，但在可接受范围内（最多1.3倍）
                        logger.info(f"[{job_id}] Segment {i+1}: speeding up {speed_ratio:.2f}x")
                        success = await self._adjust_audio_duration(
                            str(segment_path),
                            str(adjusted_path),
                            generated_duration,
                            target_duration
                        )
                        if success:
                            segment_files.append({
                                "path": str(adjusted_path),
                                "start_time": start_time,
                                "end_time": end_time
                            })
                        else:
                            segment_files.append({
                                "path": str(segment_path),
                                "start_time": start_time,
                                "end_time": start_time + generated_duration
                            })
                    else:
                        # 超过1.3倍，加速到1.3倍然后截断
                        logger.info(f"[{job_id}] Segment {i+1}: too long ({speed_ratio:.2f}x), speeding up 1.3x and trimming")
                        # 先加速到 1.3 倍
                        new_duration = generated_duration / 1.3
                        success = await self._adjust_audio_duration(
                            str(segment_path),
                            str(adjusted_path),
                            generated_duration,
                            new_duration
                        )
                        if success:
                            # 如果加速后还是超过目标时长，截断
                            if new_duration > target_duration:
                                trimmed_path = segments_dir / f"segment_{i:03d}_trimmed.mp3"
                                await self._trim_audio(str(adjusted_path), str(trimmed_path), target_duration)
                                segment_files.append({
                                    "path": str(trimmed_path),
                                    "start_time": start_time,
                                    "end_time": end_time
                                })
                            else:
                                segment_files.append({
                                    "path": str(adjusted_path),
                                    "start_time": start_time,
                                    "end_time": start_time + new_duration
                                })
                        else:
                            # 调整失败，截断原始文件
                            trimmed_path = segments_dir / f"segment_{i:03d}_trimmed.mp3"
                            await self._trim_audio(str(segment_path), str(trimmed_path), target_duration)
                            segment_files.append({
                                "path": str(trimmed_path),
                                "start_time": start_time,
                                "end_time": end_time
                            })

            if not segment_files:
                logger.error(f"[{job_id}] No segments generated")
                return None

            # 按时间轴拼接所有片段
            final_audio_path = self.upload_dir / f"{job_id}_cloned_audio.mp3"
            success = await self._concat_audio_segments(
                job_id,
                segment_files,
                str(final_audio_path),
                total_duration
            )

            if not success:
                logger.error(f"[{job_id}] Failed to concat audio segments")
                return None

            # 上传到媒体床
            audio_url = await self._upload_to_media_bed(str(final_audio_path))
            await self.repository.update_job_field(job_id, "cloned_audio_url", audio_url)

            logger.info(f"[{job_id}] Cloned voice generated: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate cloned voice error: {e}")
            import traceback
            traceback.print_exc()
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

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        try:
            return float(stdout.decode().strip())
        except:
            return 0.0

    async def _adjust_audio_duration(
        self,
        input_path: str,
        output_path: str,
        current_duration: float,
        target_duration: float
    ) -> bool:
        """
        使用 FFmpeg atempo 调整音频时长

        atempo 范围是 0.5-2.0，超出范围需要链式调用
        """
        if current_duration <= 0 or target_duration <= 0:
            return False

        # 计算速度比率
        speed_ratio = current_duration / target_duration

        # atempo 只支持 0.5-2.0 范围，超出需要链式调用
        atempo_filters = []
        remaining_ratio = speed_ratio

        while remaining_ratio > 2.0:
            atempo_filters.append("atempo=2.0")
            remaining_ratio /= 2.0

        while remaining_ratio < 0.5:
            atempo_filters.append("atempo=0.5")
            remaining_ratio /= 0.5

        atempo_filters.append(f"atempo={remaining_ratio:.4f}")

        filter_str = ",".join(atempo_filters)

        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-filter:a', filter_str,
            '-vn',
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return process.returncode == 0

    async def _trim_audio(
        self,
        input_path: str,
        output_path: str,
        duration: float
    ) -> bool:
        """截断音频到指定时长"""
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-t', str(duration),
            '-acodec', 'copy',
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return process.returncode == 0

    async def _concat_audio_segments(
        self,
        job_id: str,
        segments: List[Dict[str, Any]],
        output_path: str,
        total_duration: float
    ) -> bool:
        """
        按时间轴拼接音频片段

        使用 FFmpeg 的 adelay 和 amix 滤镜
        """
        if not segments:
            return False

        # 构建 FFmpeg 复杂滤镜
        # 方案：为每个片段添加延迟，然后混合
        inputs = []
        filter_parts = []
        mix_inputs = []

        for i, seg in enumerate(segments):
            inputs.extend(['-i', seg["path"]])
            delay_ms = int(seg["start_time"] * 1000)
            # adelay 为音频添加延迟
            filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")
            mix_inputs.append(f"[a{i}]")

        # 混合所有音轨
        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(segments)}:duration=longest:dropout_transition=0[out]"
        full_filter = ";".join(filter_parts) + ";" + mix_filter

        cmd = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', full_filter,
            '-map', '[out]',
            '-t', str(total_duration),  # 限制输出时长
            '-ac', '2',
            '-ar', '44100',
            output_path
        ]

        logger.info(f"[{job_id}] Concatenating {len(segments)} segments...")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"[{job_id}] FFmpeg concat error: {stderr.decode()[:500]}")
            return False

        return True

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

    async def _composite_video_with_audio(
        self,
        job_id: str,
        instrumental_url: Optional[str]
    ) -> Optional[str]:
        """
        合成最终视频：原视频画面 + 克隆语音 (+ 背景音乐)

        使用 FFmpeg 实现:
        1. 如果有背景音乐：混合克隆语音和背景音乐
        2. 将音频替换到原视频中
        """
        logger.info(f"[{job_id}] Compositing video with cloned audio")

        try:
            job = await self.repository.get_job(job_id)
            cloned_audio_url = job.get("cloned_audio_url")

            if not cloned_audio_url:
                logger.error(f"[{job_id}] No cloned audio available")
                return None

            import httpx
            import shutil

            # 准备文件路径
            video_path = self.upload_dir / f"{job_id}_video.mp4"
            cloned_audio_path = self.upload_dir / f"{job_id}_cloned.mp3"
            output_path = self.upload_dir / f"{job_id}_final.mp4"

            # 检查视频文件
            if not video_path.exists():
                logger.error(f"[{job_id}] Video file not found: {video_path}")
                return None

            # 获取克隆语音文件
            logger.info(f"[{job_id}] Getting cloned audio from: {cloned_audio_url}")

            # 检查是否是本地生成的文件（直接使用本地文件）
            local_cloned_audio = self.upload_dir / f"{job_id}_cloned_audio.mp3"
            if local_cloned_audio.exists():
                logger.info(f"[{job_id}] Using local cloned audio file")
                shutil.copy(str(local_cloned_audio), str(cloned_audio_path))
            elif cloned_audio_url.startswith("/files/"):
                # 媒体床相对路径，需要拼接完整 URL
                full_url = f"{self.media_bed_url}{cloned_audio_url}"
                logger.info(f"[{job_id}] Downloading from media bed: {full_url}")
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(full_url)
                    if response.status_code != 200:
                        logger.error(f"[{job_id}] Failed to download cloned audio: {response.status_code}")
                        return None
                    with open(cloned_audio_path, 'wb') as f:
                        f.write(response.content)
            elif cloned_audio_url.startswith("http"):
                # 完整 URL
                logger.info(f"[{job_id}] Downloading cloned audio from URL")
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(cloned_audio_url)
                    if response.status_code != 200:
                        logger.error(f"[{job_id}] Failed to download cloned audio")
                        return None
                    with open(cloned_audio_path, 'wb') as f:
                        f.write(response.content)
            else:
                logger.error(f"[{job_id}] Invalid cloned audio URL format: {cloned_audio_url}")
                return None

            # 决定最终使用的音频
            final_audio_path = cloned_audio_path

            # 如果有背景音乐，混合音频
            if instrumental_url:
                logger.info(f"[{job_id}] Mixing with background music...")
                instrumental_path = self.upload_dir / f"{job_id}_instrumental.mp3"
                mixed_audio_path = self.upload_dir / f"{job_id}_mixed_audio.mp3"

                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(instrumental_url)
                    if response.status_code == 200:
                        with open(instrumental_path, 'wb') as f:
                            f.write(response.content)

                        # 混合音频：克隆语音 + 背景音乐（音量降低）
                        mix_cmd = [
                            'ffmpeg', '-y',
                            '-i', str(cloned_audio_path),
                            '-i', str(instrumental_path),
                            '-filter_complex',
                            '[0:a]volume=1.0[voice];[1:a]volume=0.3[bgm];[voice][bgm]amix=inputs=2:duration=longest[out]',
                            '-map', '[out]',
                            '-ac', '2',
                            '-ar', '44100',
                            str(mixed_audio_path)
                        ]

                        process = await asyncio.create_subprocess_exec(
                            *mix_cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()

                        if process.returncode == 0:
                            final_audio_path = mixed_audio_path
                        else:
                            logger.warning(f"[{job_id}] Audio mix failed, using cloned audio only")

            # 合成最终视频：原视频画面 + 音频
            logger.info(f"[{job_id}] Compositing final video...")
            composite_cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),
                '-i', str(final_audio_path),
                '-c:v', 'copy',  # 直接复制视频流
                '-c:a', 'aac',
                '-b:a', '192k',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',  # 以最短的流为准
                str(output_path)
            ]

            process = await asyncio.create_subprocess_exec(
                *composite_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"[{job_id}] Video composite error: {stderr.decode()}")
                return None

            # 检查输出文件
            if not output_path.exists():
                logger.error(f"[{job_id}] Output file not created")
                return None

            logger.info(f"[{job_id}] Final video created: {output_path}, size: {output_path.stat().st_size} bytes")

            # 上传到图床
            final_url = await self._upload_to_media_bed(str(output_path))
            logger.info(f"[{job_id}] Final video uploaded: {final_url}")

            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] Composite video error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        try:
            return float(stdout.decode().strip())
        except:
            return 0.0

    async def _composite_video(
        self,
        job_id: str,
        instrumental_url: str,
        digital_human_url: str
    ) -> Optional[str]:
        """合成最终视频（带数字人画中画）- 暂未实现"""
        logger.warning(f"[{job_id}] Digital human PIP not implemented yet")
        return digital_human_url

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
