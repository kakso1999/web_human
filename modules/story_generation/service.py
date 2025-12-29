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

import subprocess
import httpx

from core.config.settings import get_settings
from .repository import get_story_generation_repository, StoryGenerationRepository
from .apicore_client import get_apicore_client, APICoreClient
from .schemas import StoryJobStatus, StoryJobStep

settings = get_settings()
logger = logging.getLogger(__name__)


async def run_ffmpeg_command(cmd: List[str]) -> tuple[int, bytes, bytes]:
    """
    Windows 兼容的 FFmpeg 命令执行

    Windows 的默认 asyncio 事件循环不支持 subprocess，
    所以使用 asyncio.to_thread 在线程池中运行同步的 subprocess.run
    """
    def _run():
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode, result.stdout, result.stderr

    return await asyncio.to_thread(_run)


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
        """
        处理任务 - 主流程（分段处理版本）

        流程：
        1. 提取音频
        2. 分离人声（可选）
        3. 语音识别获取词级时间戳
        4. 智能切割为最大30秒的片段（在句子边界切割）
        5. 测试阶段：只处理前2个片段
        6. 每个片段单独生成克隆语音和数字人
        7. 拼接所有片段
        """
        logger.info(f"[{job_id}] Starting story generation job (segmented mode)")

        try:
            # 更新状态为处理中
            await self._update_progress(job_id, StoryJobStep.INIT, 0)

            # Step 1: 提取音频
            await self._update_progress(job_id, StoryJobStep.EXTRACTING_AUDIO, 5)
            audio_url = await self._extract_audio(job_id)
            if not audio_url:
                raise Exception("Failed to extract audio from video")

            # Step 2: 尝试分离人声（可选，失败则跳过）
            await self._update_progress(job_id, StoryJobStep.SEPARATING_VOCALS, 10)
            vocals_url, instrumental_url = await self._separate_vocals(job_id, audio_url)

            # 如果分离失败，使用原始音频
            if not vocals_url:
                logger.warning(f"[{job_id}] Vocal separation failed, using original audio")
                vocals_url = audio_url
                instrumental_url = None

            # Step 3: 语音识别生成字幕（使用词级时间戳）
            await self._update_progress(job_id, StoryJobStep.TRANSCRIBING, 15)
            transcription = await self._transcribe_audio(job_id, vocals_url)
            if not transcription:
                raise Exception("Failed to transcribe audio")

            # Step 4: 智能切割为片段（最大30秒，在句子边界切割）
            words = transcription.get("words", [])
            if words:
                subtitles = self._words_to_segments(words, max_gap=0.7, max_segment_duration=10.0)
            else:
                segments = transcription.get("segments", [])
                subtitles = [
                    {
                        "index": i + 1,
                        "start_time": seg.get("start", 0),
                        "end_time": seg.get("end", 0),
                        "text": seg.get("text", "").strip()
                    }
                    for i, seg in enumerate(segments)
                ]

            await self.repository.save_subtitles(job_id, subtitles)
            await self.repository.update_job_field(job_id, "transcription_text", transcription.get("text", ""))

            # 将字幕切割为最大30秒的片段
            video_segments = self._split_into_chunks(subtitles, max_duration=30.0)
            logger.info(f"[{job_id}] Split into {len(video_segments)} video segments")

            # 测试阶段：只处理前2个片段
            MAX_SEGMENTS_FOR_TEST = 2
            segments_to_process = video_segments[:MAX_SEGMENTS_FOR_TEST]
            logger.info(f"[{job_id}] Processing first {len(segments_to_process)} segments for testing")

            # Step 5-6: 对每个片段生成克隆语音和数字人
            await self._update_progress(job_id, StoryJobStep.GENERATING_VOICE, 20)

            segment_results = []
            for i, segment in enumerate(segments_to_process):
                seg_start = segment["start_time"]
                seg_end = segment["end_time"]
                seg_subtitles = segment["subtitles"]

                logger.info(f"[{job_id}] Processing segment {i+1}/{len(segments_to_process)}: {seg_start:.2f}s - {seg_end:.2f}s")

                # 更新进度
                progress = 20 + int((i / len(segments_to_process)) * 60)
                await self._update_progress(job_id, StoryJobStep.GENERATING_VOICE, progress)

                # 为此片段生成克隆语音
                cloned_audio_url = await self._generate_cloned_voice_for_segment(
                    job_id, i, seg_subtitles
                )
                if not cloned_audio_url:
                    logger.error(f"[{job_id}] Failed to generate cloned voice for segment {i+1}")
                    continue

                # 为此片段生成数字人视频
                digital_human_url = await self._generate_digital_human_for_segment(
                    job_id, i, cloned_audio_url
                )

                # 截取原视频对应片段
                video_segment_path = await self._extract_video_segment(
                    job_id, i, seg_start, seg_end
                )

                segment_results.append({
                    "index": i,
                    "start_time": seg_start,
                    "end_time": seg_end,
                    "cloned_audio_url": cloned_audio_url,
                    "digital_human_url": digital_human_url,
                    "video_segment_path": video_segment_path
                })

            if not segment_results:
                raise Exception("No segments processed successfully")

            # Step 7: 合成每个片段的视频（画中画）
            await self._update_progress(job_id, StoryJobStep.COMPOSITING_VIDEO, 85)

            composited_segments = []
            for seg_result in segment_results:
                if seg_result["digital_human_url"] and seg_result["video_segment_path"]:
                    # 有数字人：画中画合成
                    composited_path = await self._composite_segment_pip(
                        job_id,
                        seg_result["index"],
                        seg_result["video_segment_path"],
                        seg_result["digital_human_url"],
                        seg_result["cloned_audio_url"]
                    )
                else:
                    # 无数字人：仅替换音频
                    composited_path = await self._composite_segment_audio_only(
                        job_id,
                        seg_result["index"],
                        seg_result["video_segment_path"],
                        seg_result["cloned_audio_url"]
                    )

                if composited_path:
                    composited_segments.append(composited_path)

            if not composited_segments:
                raise Exception("No segments composited successfully")

            # Step 8: 拼接所有片段
            await self._update_progress(job_id, StoryJobStep.COMPOSITING_VIDEO, 95)
            final_video_url = await self._concat_video_segments(job_id, composited_segments)

            if not final_video_url:
                raise Exception("Failed to concatenate video segments")

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

    # ===================== 分段处理辅助函数 =====================

    def _split_into_chunks(
        self,
        subtitles: List[dict],
        max_duration: float = 30.0
    ) -> List[dict]:
        """
        将字幕智能切割为最大 max_duration 秒的片段

        策略：在句子边界切割，避免音频中断
        每个片段包含：start_time, end_time, subtitles
        """
        if not subtitles:
            return []

        chunks = []
        current_chunk_subtitles = []
        chunk_start = subtitles[0]["start_time"]

        for sub in subtitles:
            sub_duration = sub["end_time"] - chunk_start

            # 如果加上这个字幕会超过最大时长，先保存当前片段
            if sub_duration > max_duration and current_chunk_subtitles:
                # 保存当前片段
                chunks.append({
                    "start_time": chunk_start,
                    "end_time": current_chunk_subtitles[-1]["end_time"],
                    "subtitles": current_chunk_subtitles
                })
                # 开始新片段
                current_chunk_subtitles = [sub]
                chunk_start = sub["start_time"]
            else:
                current_chunk_subtitles.append(sub)

        # 保存最后一个片段
        if current_chunk_subtitles:
            chunks.append({
                "start_time": chunk_start,
                "end_time": current_chunk_subtitles[-1]["end_time"],
                "subtitles": current_chunk_subtitles
            })

        return chunks

    async def _generate_cloned_voice_for_segment(
        self,
        job_id: str,
        segment_index: int,
        subtitles: List[dict]
    ) -> Optional[str]:
        """为单个片段生成克隆语音"""
        logger.info(f"[{job_id}] Generating cloned voice for segment {segment_index}, {len(subtitles)} subtitles")

        try:
            job = await self.repository.get_job(job_id)
            voice_profile_id = job.get("voice_profile_id")

            # 获取声音档案
            from modules.voice_clone.repository import voice_profile_repository
            profile = await voice_profile_repository.get_by_id(voice_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Voice profile not found")
                return None

            voice_id = profile.get("voice_id")  # 数据库字段名是 voice_id
            if not voice_id:
                logger.error(f"[{job_id}] No voice_id in profile")
                return None

            logger.info(f"[{job_id}] Using voice_id: {voice_id}")

            # 计算片段的基准时间（用于转换为相对时间）
            segment_base_time = subtitles[0]["start_time"] if subtitles else 0

            # 生成每个字幕的语音
            segment_files = []
            for i, sub in enumerate(subtitles):
                text = sub.get("text", "").strip()
                if not text:
                    continue

                # 转换为相对于片段开头的时间
                abs_start_time = sub.get("start_time", 0)
                relative_start_time = abs_start_time - segment_base_time
                duration = sub.get("end_time", 0) - abs_start_time

                logger.info(f"[{job_id}] Seg{segment_index} Sub{i}: '{text[:20]}...' at {relative_start_time:.2f}s")

                # 调用 TTS
                audio_content = await self._call_cosyvoice_tts(voice_id, text)
                if not audio_content:
                    logger.warning(f"[{job_id}] TTS failed for subtitle {i}")
                    continue

                # 保存临时文件
                temp_file = self.upload_dir / f"{job_id}_seg{segment_index}_sub{i}.mp3"
                with open(temp_file, 'wb') as f:
                    f.write(audio_content)

                segment_files.append({
                    "path": str(temp_file),
                    "start_time": relative_start_time,  # 使用相对时间
                    "target_duration": duration
                })

            if not segment_files:
                logger.error(f"[{job_id}] No audio segments generated for segment {segment_index}")
                return None

            logger.info(f"[{job_id}] Generated {len(segment_files)} audio files for segment {segment_index}")

            # 计算片段总时长
            total_duration = subtitles[-1]["end_time"] - subtitles[0]["start_time"]

            # 拼接所有字幕音频
            final_audio_path = self.upload_dir / f"{job_id}_seg{segment_index}_cloned.mp3"
            success = await self._concat_audio_segments(
                job_id,
                segment_files,
                str(final_audio_path),
                total_duration
            )

            if not success:
                logger.error(f"[{job_id}] Failed to concat audio segments for segment {segment_index}")
                return None

            # 上传到图床
            audio_url = await self._upload_to_media_bed(str(final_audio_path))
            logger.info(f"[{job_id}] Segment {segment_index} cloned voice uploaded: {audio_url}")

            return audio_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate cloned voice for segment {segment_index} error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_digital_human_for_segment(
        self,
        job_id: str,
        segment_index: int,
        audio_url: str
    ) -> Optional[str]:
        """为单个片段生成数字人视频"""
        logger.info(f"[{job_id}] Generating digital human for segment {segment_index}")

        try:
            job = await self.repository.get_job(job_id)
            avatar_profile_id = job.get("avatar_profile_id")

            # 获取头像档案
            from modules.digital_human.repository import avatar_profile_repository
            profile = await avatar_profile_repository.get_by_id(avatar_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Avatar profile not found")
                return None

            image_url = profile.get("image_url")
            face_bbox = profile.get("face_bbox")
            ext_bbox = profile.get("ext_bbox")

            if not image_url or not face_bbox or not ext_bbox:
                logger.error(f"[{job_id}] Invalid avatar profile")
                return None

            # 调用 EMO API
            from modules.digital_human.service import DigitalHumanService
            dh_service = DigitalHumanService()

            emo_task_id = await dh_service._create_emo_task(
                task_id=f"{job_id}_seg{segment_index}",
                image_url=image_url,
                audio_url=audio_url,
                face_bbox=face_bbox,
                ext_bbox=ext_bbox
            )

            if not emo_task_id:
                logger.error(f"[{job_id}] Failed to create EMO task for segment {segment_index}")
                return None

            # 等待任务完成
            video_url = await dh_service._wait_for_emo_task(
                task_id=f"{job_id}_seg{segment_index}",
                emo_task_id=emo_task_id,
                max_attempts=180,
                poll_interval=5
            )

            logger.info(f"[{job_id}] Segment {segment_index} digital human: {video_url}")
            return video_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate digital human for segment {segment_index} error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _extract_video_segment(
        self,
        job_id: str,
        segment_index: int,
        start_time: float,
        end_time: float
    ) -> Optional[str]:
        """截取原视频的指定时间段"""
        logger.info(f"[{job_id}] Extracting video segment {segment_index}: {start_time:.2f}s - {end_time:.2f}s")

        try:
            video_path = self.upload_dir / f"{job_id}_video.mp4"
            if not video_path.exists():
                logger.error(f"[{job_id}] Source video not found")
                return None

            output_path = self.upload_dir / f"{job_id}_seg{segment_index}_video.mp4"
            duration = end_time - start_time

            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', str(video_path),
                '-t', str(duration),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-an',  # 去掉音频
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg extract segment error: {stderr.decode()[:300]}")
                return None

            if not output_path.exists():
                return None

            return str(output_path)

        except Exception as e:
            logger.error(f"[{job_id}] Extract video segment error: {e}")
            return None

    async def _composite_segment_pip(
        self,
        job_id: str,
        segment_index: int,
        video_path: str,
        digital_human_url: str,
        audio_url: str
    ) -> Optional[str]:
        """单个片段的画中画合成"""
        logger.info(f"[{job_id}] Compositing segment {segment_index} with PIP")

        try:
            import httpx

            # 下载数字人视频
            dh_video_path = self.upload_dir / f"{job_id}_seg{segment_index}_dh.mp4"
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(digital_human_url)
                if response.status_code != 200:
                    logger.error(f"[{job_id}] Failed to download digital human video")
                    return None
                with open(dh_video_path, 'wb') as f:
                    f.write(response.content)

            # 下载克隆语音
            audio_path = self.upload_dir / f"{job_id}_seg{segment_index}_audio.mp3"
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(audio_url)
                if response.status_code != 200:
                    logger.error(f"[{job_id}] Failed to download audio")
                    return None
                with open(audio_path, 'wb') as f:
                    f.write(response.content)

            output_path = self.upload_dir / f"{job_id}_seg{segment_index}_composited.mp4"

            # 获取原视频尺寸
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                video_path
            ]
            returncode, stdout, stderr = await run_ffmpeg_command(probe_cmd)

            try:
                width, height = map(int, stdout.decode().strip().split(','))
            except:
                width, height = 1920, 1080

            # 获取数字人视频尺寸（保持原比例）
            probe_dh_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(dh_video_path)
            ]
            returncode, stdout, stderr = await run_ffmpeg_command(probe_dh_cmd)

            try:
                dh_width, dh_height = map(int, stdout.decode().strip().split(','))
            except:
                dh_width, dh_height = 512, 512  # EMO 默认输出

            logger.info(f"[{job_id}] Original video: {width}x{height}, Digital human: {dh_width}x{dh_height}")

            # 计算画中画尺寸（保持数字人原比例）
            pip_width = width // 4
            pip_height = int(pip_width * dh_height / dh_width)  # 保持原比例
            pip_x = width - pip_width - 20
            pip_y = 20

            # 画中画合成（使用 -1 保持比例）
            filter_complex = (
                f"[1:v]scale={pip_width}:-1[pip];"
                f"[0:v][pip]overlay={pip_x}:{pip_y}:shortest=1[outv]"
            )

            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', str(dh_video_path),
                '-i', str(audio_path),
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', '2:a',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg PIP composite error: {stderr.decode()[:300]}")
                return None

            if not output_path.exists():
                return None

            return str(output_path)

        except Exception as e:
            logger.error(f"[{job_id}] Composite segment PIP error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _composite_segment_audio_only(
        self,
        job_id: str,
        segment_index: int,
        video_path: str,
        audio_url: str
    ) -> Optional[str]:
        """单个片段仅替换音频"""
        logger.info(f"[{job_id}] Compositing segment {segment_index} audio only")

        try:
            import httpx

            # 下载克隆语音
            audio_path = self.upload_dir / f"{job_id}_seg{segment_index}_audio.mp3"
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(audio_url)
                if response.status_code != 200:
                    return None
                with open(audio_path, 'wb') as f:
                    f.write(response.content)

            output_path = self.upload_dir / f"{job_id}_seg{segment_index}_composited.mp4"

            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-map', '0:v',
                '-map', '1:a',
                '-c:a', 'aac',
                '-shortest',
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg audio composite error: {stderr.decode()[:300]}")
                return None

            return str(output_path) if output_path.exists() else None

        except Exception as e:
            logger.error(f"[{job_id}] Composite segment audio error: {e}")
            return None

    async def _concat_video_segments(
        self,
        job_id: str,
        segment_paths: List[str]
    ) -> Optional[str]:
        """拼接所有视频片段"""
        logger.info(f"[{job_id}] Concatenating {len(segment_paths)} video segments")

        try:
            if len(segment_paths) == 1:
                # 只有一个片段，直接上传
                return await self._upload_to_media_bed(segment_paths[0])

            # 创建拼接列表文件
            concat_list_path = self.upload_dir / f"{job_id}_concat_list.txt"
            with open(concat_list_path, 'w') as f:
                for path in segment_paths:
                    f.write(f"file '{path}'\n")

            output_path = self.upload_dir / f"{job_id}_final.mp4"

            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list_path),
                '-c', 'copy',
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg concat error: {stderr.decode()[:300]}")
                return None

            if not output_path.exists():
                return None

            # 上传最终视频
            final_url = await self._upload_to_media_bed(str(output_path))
            logger.info(f"[{job_id}] Final video uploaded: {final_url}")

            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] Concat video segments error: {e}")
            import traceback
            traceback.print_exc()
            return None

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
            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
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
    ) -> Optional[Dict[str, Any]]:
        """
        语音识别 - 使用词级时间戳获取精确时间

        对于长音频，会自动分块处理，每块最大 3 分钟

        Returns:
            {
                "text": "完整文本",
                "words": [{"word": "Hi", "start": 12.1, "end": 12.3}, ...],
                "segments": [{"start": 12.1, "end": 17.3, "text": "..."}, ...]
            }
        """
        logger.info(f"[{job_id}] Transcribing audio with word timestamps")

        try:
            import json

            # 获取音频文件路径
            audio_path = self.upload_dir / f"{job_id}_audio.mp3"

            if not audio_path.exists():
                if audio_url.startswith("http"):
                    # 下载音频
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.get(audio_url)
                        if response.status_code != 200:
                            logger.error(f"[{job_id}] Failed to download audio: {response.status_code}")
                            return None
                        with open(audio_path, 'wb') as f:
                            f.write(response.content)
                else:
                    logger.error(f"[{job_id}] Invalid audio source")
                    return None

            # 获取音频时长
            audio_duration = await self._get_audio_duration(str(audio_path))
            logger.info(f"[{job_id}] Audio duration: {audio_duration:.2f}s")

            # 分块阈值：3 分钟
            CHUNK_MAX_DURATION = 180  # 秒

            if audio_duration <= CHUNK_MAX_DURATION:
                # 短音频，直接转写
                result = await self._transcribe_audio_chunk(job_id, str(audio_path), 0)
            else:
                # 长音频，分块转写
                logger.info(f"[{job_id}] Audio too long ({audio_duration:.0f}s), splitting into chunks")
                result = await self._transcribe_audio_chunked(job_id, str(audio_path), audio_duration, CHUNK_MAX_DURATION)

            if not result:
                return None

            # 保存原始结果
            json_path = self.upload_dir / f"{job_id}_transcription.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            logger.info(f"[{job_id}] Transcription completed: {len(result.get('words', []))} words")
            return result

        except Exception as e:
            logger.error(f"[{job_id}] Transcribe error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _transcribe_audio_chunked(
        self,
        job_id: str,
        audio_path: str,
        total_duration: float,
        chunk_duration: float
    ) -> Optional[Dict[str, Any]]:
        """
        分块转写长音频

        1. 将音频分割成多个块
        2. 分别转写每个块
        3. 合并结果，调整时间戳
        """
        import math

        chunks_dir = self.upload_dir / f"{job_id}_chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)

        # 计算需要多少块
        num_chunks = math.ceil(total_duration / chunk_duration)
        logger.info(f"[{job_id}] Splitting audio into {num_chunks} chunks")

        # 分割音频
        chunk_files = []
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = chunks_dir / f"chunk_{i:03d}.mp3"

            # 使用 FFmpeg 分割
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'libmp3lame',
                '-ar', '16000',  # 降采样以减小文件大小
                '-ac', '1',      # 单声道
                '-b:a', '64k',   # 降低比特率
                str(chunk_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)
            if returncode != 0:
                logger.error(f"[{job_id}] Failed to split chunk {i}: {stderr.decode()[:200]}")
                continue

            if chunk_path.exists() and chunk_path.stat().st_size > 0:
                chunk_files.append({
                    "path": str(chunk_path),
                    "start_time": start_time,
                    "index": i
                })

        if not chunk_files:
            logger.error(f"[{job_id}] No chunks created")
            return None

        logger.info(f"[{job_id}] Created {len(chunk_files)} chunks, starting transcription")

        # 逐个转写
        all_words = []
        all_segments = []
        all_text_parts = []

        for chunk_info in chunk_files:
            chunk_idx = chunk_info["index"]
            chunk_start = chunk_info["start_time"]
            chunk_path = chunk_info["path"]

            logger.info(f"[{job_id}] Transcribing chunk {chunk_idx + 1}/{len(chunk_files)} (starts at {chunk_start:.1f}s)")

            chunk_result = await self._transcribe_audio_chunk(job_id, chunk_path, chunk_idx)

            if chunk_result:
                # 调整时间戳并合并
                chunk_text = chunk_result.get("text", "")
                all_text_parts.append(chunk_text)

                # 调整 words 的时间戳
                for word in chunk_result.get("words", []):
                    adjusted_word = {
                        "word": word.get("word", ""),
                        "start": word.get("start", 0) + chunk_start,
                        "end": word.get("end", 0) + chunk_start
                    }
                    all_words.append(adjusted_word)

                # 调整 segments 的时间戳
                for seg in chunk_result.get("segments", []):
                    adjusted_seg = {
                        "start": seg.get("start", 0) + chunk_start,
                        "end": seg.get("end", 0) + chunk_start,
                        "text": seg.get("text", "")
                    }
                    all_segments.append(adjusted_seg)
            else:
                logger.warning(f"[{job_id}] Chunk {chunk_idx} transcription failed, skipping")

        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(chunks_dir)
        except:
            pass

        if not all_words and not all_segments:
            logger.error(f"[{job_id}] All chunks failed to transcribe")
            return None

        # 合并结果
        result = {
            "text": " ".join(all_text_parts),
            "words": all_words,
            "segments": all_segments
        }

        logger.info(f"[{job_id}] Merged transcription: {len(all_words)} words from {len(chunk_files)} chunks")
        return result

    async def _transcribe_audio_chunk(
        self,
        job_id: str,
        audio_path: str,
        chunk_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        转写单个音频块

        包含重试逻辑
        """
        try:
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()

            logger.info(f"[{job_id}] Chunk {chunk_index} size: {len(audio_bytes)} bytes")

            headers = {
                "Authorization": f"Bearer {settings.APICORE_API_KEY}"
            }

            max_retries = 3
            result = None

            for attempt in range(max_retries):
                try:
                    timeout = httpx.Timeout(300.0, connect=60.0)  # 每块 5 分钟超时
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        logger.info(f"[{job_id}] Whisper API chunk {chunk_index} (attempt {attempt + 1}/{max_retries})")
                        response = await client.post(
                            f"{settings.APICORE_BASE_URL}/v1/audio/transcriptions",
                            headers=headers,
                            files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
                            data={
                                "model": "whisper-1",
                                "response_format": "verbose_json",
                                "timestamp_granularities[]": "word",
                                "language": "en"
                            }
                        )

                        if response.status_code != 200:
                            logger.error(f"[{job_id}] Whisper API error: {response.status_code}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep((attempt + 1) * 10)
                                continue
                            return None

                        result = response.json()
                        break

                except httpx.ReadTimeout as e:
                    logger.warning(f"[{job_id}] Chunk {chunk_index} timeout (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep((attempt + 1) * 15)
                        continue
                    return None

                except httpx.HTTPError as e:
                    logger.warning(f"[{job_id}] Chunk {chunk_index} HTTP error (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep((attempt + 1) * 10)
                        continue
                    return None

            return result

        except Exception as e:
            logger.error(f"[{job_id}] Transcribe chunk {chunk_index} error: {e}")
            return None

    def _words_to_segments(
        self,
        words: List[Dict[str, Any]],
        max_gap: float = 0.7,
        max_segment_duration: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        将词级时间戳转换为句子段落

        根据词之间的停顿来分割段落：
        - 停顿 > max_gap 秒则分割
        - 段落超过 max_segment_duration 秒也分割

        Args:
            words: Whisper 返回的词列表 [{"word": "Hi", "start": 0.5, "end": 0.8}, ...]
            max_gap: 最大词间隔（秒），超过此值则分割
            max_segment_duration: 最大段落时长（秒）

        Returns:
            段落列表: [{"index": 1, "start_time": 0.5, "end_time": 3.2, "text": "Hi welcome"}, ...]
        """
        if not words:
            return []

        segments = []
        current_segment = {
            "words": [words[0]],
            "start": words[0].get("start", 0),
            "end": words[0].get("end", 0)
        }

        for word in words[1:]:
            word_start = word.get("start", 0)
            word_end = word.get("end", 0)
            gap = word_start - current_segment["end"]
            segment_duration = word_end - current_segment["start"]

            # 检查是否需要分割
            should_split = (
                gap > max_gap or  # 停顿过长
                segment_duration > max_segment_duration  # 段落过长
            )

            if should_split:
                # 保存当前段落
                segments.append(current_segment)
                # 开始新段落
                current_segment = {
                    "words": [word],
                    "start": word_start,
                    "end": word_end
                }
            else:
                # 继续当前段落
                current_segment["words"].append(word)
                current_segment["end"] = word_end

        # 保存最后一个段落
        if current_segment["words"]:
            segments.append(current_segment)

        # 转换为最终格式
        result = []
        for i, seg in enumerate(segments):
            text = " ".join(w.get("word", "").strip() for w in seg["words"])
            result.append({
                "index": i + 1,
                "start_time": seg["start"],
                "end_time": seg["end"],
                "text": text.strip(),
                "word_count": len(seg["words"])
            })

        return result

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

    # ===================== Step 4: 生成克隆语音 (SSML 方案) =====================

    def _subtitles_to_ssml(self, subtitles: List[Dict[str, Any]]) -> str:
        """
        将字幕转换为 SSML 格式

        通过 <break> 标签精确控制每句之间的停顿时间，实现音频同步

        Args:
            subtitles: 字幕列表，每项包含 start_time, end_time, text

        Returns:
            SSML 格式的文本
        """
        if not subtitles:
            return "<speak></speak>"

        ssml_parts = ['<speak>']

        # 开头的静音（如果第一句不是从 0 开始）
        first_start = subtitles[0].get("start_time", 0)
        if first_start > 0.1:  # 超过 100ms 才添加
            ssml_parts.append(f'<break time="{int(first_start * 1000)}ms"/>')

        for i, sub in enumerate(subtitles):
            text = sub.get("text", "").strip()
            if not text:
                continue

            # 转义 XML 特殊字符
            text = text.replace("&", "&amp;")
            text = text.replace("<", "&lt;")
            text = text.replace(">", "&gt;")
            text = text.replace('"', "&quot;")
            text = text.replace("'", "&apos;")

            # 添加文本
            ssml_parts.append(text)

            # 计算到下一句的间隔时间
            if i < len(subtitles) - 1:
                current_end = sub.get("end_time", 0)
                next_start = subtitles[i + 1].get("start_time", 0)
                gap_ms = int((next_start - current_end) * 1000)

                # 只有间隔大于 50ms 才添加 break
                if gap_ms > 50:
                    # 限制最大停顿为 5 秒
                    gap_ms = min(gap_ms, 5000)
                    ssml_parts.append(f'<break time="{gap_ms}ms"/>')

        ssml_parts.append('</speak>')
        return ''.join(ssml_parts)

    async def _generate_cloned_voice(
        self,
        job_id: str,
        subtitles: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        生成克隆语音 - 使用分段生成 + FFmpeg adelay 精确定位

        重要：SSML 方案无法保证精确同步，因为 TTS 语速与原始音频不同，
        会导致累积时间偏移。必须使用分段方案确保每段音频在正确的时间点开始。

        流程：
        1. 创建声音克隆
        2. 对每段字幕分别生成语音
        3. 使用 FFmpeg adelay 将每段音频放置在精确的时间点
        4. 混合所有音轨生成最终音频
        """
        logger.info(f"[{job_id}] Generating cloned voice using segment-based approach for {len(subtitles)} subtitles")

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

            # 创建 voice（声音复刻）
            voice_id = await self._create_voice_from_url(job_id, reference_audio_url)
            if not voice_id:
                return None

            # 等待 voice 就绪
            voice_ready = await self._wait_for_voice_ready(job_id, voice_id)
            if not voice_ready:
                return None

            # 使用分段方案生成精确同步的音频
            return await self._generate_cloned_voice_segments(job_id, subtitles, voice_id)

        except Exception as e:
            logger.error(f"[{job_id}] Generate cloned voice error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_cloned_voice_segments(
        self,
        job_id: str,
        subtitles: List[Dict[str, Any]],
        voice_id: str
    ) -> Optional[str]:
        """
        降级方案：分段生成语音（当文本超过 2000 字符时使用）

        流程：
        1. 对每段字幕生成克隆语音
        2. 使用 FFmpeg adelay 按时间轴拼接
        """
        logger.info(f"[{job_id}] Using segment-based approach (fallback)")

        try:
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            segments_dir = self.upload_dir / f"{job_id}_segments"
            segments_dir.mkdir(parents=True, exist_ok=True)

            total_duration = max(sub["end_time"] for sub in subtitles) if subtitles else 0
            segment_files = []

            for i, sub in enumerate(subtitles):
                text = sub["text"]
                start_time = sub["start_time"]

                logger.info(f"[{job_id}] Segment {i+1}/{len(subtitles)}: '{text[:30]}...'")

                segment_path = segments_dir / f"segment_{i:03d}.mp3"

                def synthesize_segment(txt, vid):
                    synthesizer = SpeechSynthesizer(
                        model='cosyvoice-v2',
                        voice=vid
                    )
                    return synthesizer.call(txt)

                audio_data = await asyncio.to_thread(synthesize_segment, text, voice_id)

                if audio_data:
                    with open(segment_path, 'wb') as f:
                        f.write(audio_data)

                    duration = await self._get_audio_duration(str(segment_path))
                    segment_files.append({
                        "path": str(segment_path),
                        "start_time": start_time,
                        "end_time": start_time + duration
                    })

            if not segment_files:
                logger.error(f"[{job_id}] No segments generated")
                return None

            # 拼接所有片段
            final_audio_path = self.upload_dir / f"{job_id}_cloned_audio.mp3"
            success = await self._concat_audio_segments(
                job_id,
                segment_files,
                str(final_audio_path),
                total_duration
            )

            if not success:
                return None

            audio_url = await self._upload_to_media_bed(str(final_audio_path))
            await self.repository.update_job_field(job_id, "cloned_audio_url", audio_url)

            logger.info(f"[{job_id}] Cloned voice (segments) generated: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate segments error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _call_cosyvoice_tts(self, voice_id: str, text: str) -> Optional[bytes]:
        """
        调用 CosyVoice TTS 生成克隆语音

        Args:
            voice_id: 声音克隆ID
            text: 要合成的文本

        Returns:
            音频字节数据，失败返回 None
        """
        try:
            from dashscope.audio.tts_v2 import SpeechSynthesizer

            def synthesize_sync():
                synthesizer = SpeechSynthesizer(
                    model='cosyvoice-v2',
                    voice=voice_id
                )
                return synthesizer.call(text)

            audio_data = await asyncio.to_thread(synthesize_sync)

            if audio_data:
                logger.info(f"TTS generated {len(audio_data)} bytes for text: '{text[:30]}...'")
                return audio_data
            else:
                logger.error(f"TTS returned empty data for text: '{text[:30]}...'")
                return None

        except Exception as e:
            logger.error(f"CosyVoice TTS error: {e}")
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

        returncode, stdout, stderr = await run_ffmpeg_command(cmd)

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

        returncode, stdout, stderr = await run_ffmpeg_command(cmd)

        return returncode == 0

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

        returncode, stdout, stderr = await run_ffmpeg_command(cmd)

        return returncode == 0

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
        重要：使用 normalize=0 防止 amix 降低音量
        """
        if not segments:
            return False

        logger.info(f"[{job_id}] Concatenating {len(segments)} segments, total duration: {total_duration:.2f}s")

        # 打印前几个段的时间信息用于调试
        for i, seg in enumerate(segments[:5]):
            logger.info(f"[{job_id}] Segment {i}: start={seg['start_time']:.2f}s, path={seg['path'][-30:]}")

        # 构建 FFmpeg 复杂滤镜
        # 方案：为每个片段添加延迟，然后混合
        inputs = []
        filter_parts = []
        mix_inputs = []

        for i, seg in enumerate(segments):
            inputs.extend(['-i', seg["path"]])
            delay_ms = int(seg["start_time"] * 1000)
            # adelay 为音频添加延迟，使用 all=1 确保所有通道都延迟
            filter_parts.append(f"[{i}:a]adelay={delay_ms}:all=1[a{i}]")
            mix_inputs.append(f"[a{i}]")

        # 混合所有音轨
        # normalize=0 防止音量降低，dropout_transition=0 防止音量渐变
        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(segments)}:duration=longest:dropout_transition=0:normalize=0[out]"
        full_filter = ";".join(filter_parts) + ";" + mix_filter

        cmd = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', full_filter,
            '-map', '[out]',
            '-t', str(total_duration + 1),  # 多加1秒确保不截断
            '-ac', '2',
            '-ar', '44100',
            '-b:a', '192k',
            output_path
        ]

        logger.info(f"[{job_id}] Running FFmpeg with {len(segments)} inputs...")

        returncode, stdout, stderr = await run_ffmpeg_command(cmd)

        if returncode != 0:
            logger.error(f"[{job_id}] FFmpeg concat error: {stderr.decode()[:500]}")
            return False

        # 验证输出文件
        if Path(output_path).exists():
            output_duration = await self._get_audio_duration(output_path)
            logger.info(f"[{job_id}] Concat successful: output duration={output_duration:.2f}s")

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
        """
        生成数字人视频

        注意: EMO API 限制音频长度不能超过60秒，因此需要截取前60秒
        """
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

            # EMO API 限制音频不能超过60秒，截取前60秒
            truncated_audio_url = await self._truncate_audio_for_emo(job_id, audio_url, max_duration=55)
            if not truncated_audio_url:
                logger.error(f"[{job_id}] Failed to truncate audio for EMO")
                return None

            logger.info(f"[{job_id}] Using truncated audio for EMO: {truncated_audio_url}")

            # 调用 EMO API 生成数字人视频
            from modules.digital_human.service import DigitalHumanService
            dh_service = DigitalHumanService()

            # 创建 EMO 任务
            emo_task_id = await dh_service._create_emo_task(
                task_id=job_id,
                image_url=image_url,
                audio_url=truncated_audio_url,
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

    async def _truncate_audio_for_emo(
        self,
        job_id: str,
        audio_url: str,
        max_duration: int = 55
    ) -> Optional[str]:
        """
        截取音频前N秒用于EMO数字人生成

        EMO API限制音频不能超过60秒，为了安全起见截取55秒
        """
        logger.info(f"[{job_id}] Truncating audio to {max_duration}s for EMO")

        try:
            import httpx

            # 下载音频
            audio_path = self.upload_dir / f"{job_id}_emo_source.mp3"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(audio_url)
                if response.status_code != 200:
                    logger.error(f"[{job_id}] Failed to download audio: {response.status_code}")
                    return None

                with open(audio_path, 'wb') as f:
                    f.write(response.content)

            # 使用FFmpeg截取前N秒
            truncated_path = self.upload_dir / f"{job_id}_emo_truncated.mp3"

            cmd = [
                'ffmpeg', '-y',
                '-i', str(audio_path),
                '-t', str(max_duration),
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                str(truncated_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg truncate failed: {stderr.decode()}")
                return None

            if not truncated_path.exists():
                logger.error(f"[{job_id}] Truncated audio file not created")
                return None

            # 上传到图床
            truncated_url = await self._upload_to_media_bed(str(truncated_path))

            # 清理临时文件
            audio_path.unlink(missing_ok=True)
            truncated_path.unlink(missing_ok=True)

            logger.info(f"[{job_id}] Truncated audio uploaded: {truncated_url}")
            return truncated_url

        except Exception as e:
            logger.error(f"[{job_id}] Truncate audio error: {e}")
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

                        returncode, stdout, stderr = await run_ffmpeg_command(mix_cmd)

                        if returncode == 0:
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

            returncode, stdout, stderr = await run_ffmpeg_command(composite_cmd)

            if returncode != 0:
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

        returncode, stdout, stderr = await run_ffmpeg_command(cmd)

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
        """合成最终视频（带数字人画中画）- 旧方法，保留兼容"""
        return await self._composite_video_pip(job_id, digital_human_url, instrumental_url)

    async def _composite_video_pip(
        self,
        job_id: str,
        digital_human_url: str,
        instrumental_url: Optional[str]
    ) -> Optional[str]:
        """
        画中画合成：数字人视频叠加在原视频右上角

        流程：
        1. 下载数字人视频
        2. 获取原视频和数字人视频的尺寸
        3. 使用 FFmpeg overlay 滤镜将数字人放在右上角
        4. 混合克隆语音和背景音乐（如果有）
        5. 合成最终视频
        """
        logger.info(f"[{job_id}] Compositing video with digital human PIP")

        try:
            import httpx
            import shutil

            job = await self.repository.get_job(job_id)
            cloned_audio_url = job.get("cloned_audio_url")

            if not cloned_audio_url:
                logger.error(f"[{job_id}] No cloned audio available")
                return None

            # 准备文件路径
            video_path = self.upload_dir / f"{job_id}_video.mp4"
            dh_video_path = self.upload_dir / f"{job_id}_digital_human.mp4"
            cloned_audio_path = self.upload_dir / f"{job_id}_cloned.mp3"
            output_path = self.upload_dir / f"{job_id}_final.mp4"

            # 检查原视频文件
            if not video_path.exists():
                logger.error(f"[{job_id}] Original video not found: {video_path}")
                return None

            # 下载数字人视频
            logger.info(f"[{job_id}] Downloading digital human video: {digital_human_url}")
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(digital_human_url)
                if response.status_code != 200:
                    logger.error(f"[{job_id}] Failed to download digital human video: {response.status_code}")
                    return None
                with open(dh_video_path, 'wb') as f:
                    f.write(response.content)

            # 获取克隆语音
            local_cloned_audio = self.upload_dir / f"{job_id}_cloned_audio.mp3"
            if local_cloned_audio.exists():
                shutil.copy(str(local_cloned_audio), str(cloned_audio_path))
            elif cloned_audio_url.startswith("http"):
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(cloned_audio_url)
                    if response.status_code != 200:
                        logger.error(f"[{job_id}] Failed to download cloned audio")
                        return None
                    with open(cloned_audio_path, 'wb') as f:
                        f.write(response.content)

            # 获取原视频尺寸
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(video_path)
            ]
            returncode, stdout, stderr = await run_ffmpeg_command(probe_cmd)
            if returncode != 0:
                logger.error(f"[{job_id}] Failed to probe video: {stderr.decode()}")
                return None

            try:
                width, height = map(int, stdout.decode().strip().split(','))
                logger.info(f"[{job_id}] Original video size: {width}x{height}")
            except:
                width, height = 1920, 1080
                logger.warning(f"[{job_id}] Using default video size: {width}x{height}")

            # 获取数字人视频尺寸（保持原比例）
            probe_dh_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(dh_video_path)
            ]
            returncode, stdout, stderr = await run_ffmpeg_command(probe_dh_cmd)

            try:
                dh_width, dh_height = map(int, stdout.decode().strip().split(','))
                logger.info(f"[{job_id}] Digital human video size: {dh_width}x{dh_height}")
            except:
                dh_width, dh_height = 512, 512

            # 计算数字人视频大小和位置（保持原比例）
            pip_width = width // 4
            pip_height = int(pip_width * dh_height / dh_width)  # 保持原比例
            pip_x = width - pip_width - 20  # 右边距 20px
            pip_y = 20  # 上边距 20px

            # 准备最终音频
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

                        # 混合：克隆语音 + 背景音乐（音量降低）
                        mix_cmd = [
                            'ffmpeg', '-y',
                            '-i', str(cloned_audio_path),
                            '-i', str(instrumental_path),
                            '-filter_complex',
                            '[0:a]volume=1.0[voice];[1:a]volume=0.3[bgm];[voice][bgm]amix=inputs=2:duration=longest[out]',
                            '-map', '[out]',
                            '-ac', '2', '-ar', '44100',
                            str(mixed_audio_path)
                        ]
                        returncode, _, stderr = await run_ffmpeg_command(mix_cmd)
                        if returncode == 0:
                            final_audio_path = mixed_audio_path

            # 画中画合成
            # 滤镜：将数字人视频缩放并叠加到原视频右上角
            logger.info(f"[{job_id}] Creating PIP composite (digital human at {pip_x},{pip_y}, size {pip_width}x{pip_height})")

            filter_complex = (
                f"[1:v]scale={pip_width}:{pip_height}[pip];"
                f"[0:v][pip]overlay={pip_x}:{pip_y}:shortest=1[outv]"
            )

            composite_cmd = [
                'ffmpeg', '-y',
                '-i', str(video_path),        # 原视频
                '-i', str(dh_video_path),     # 数字人视频
                '-i', str(final_audio_path),  # 克隆语音（或混合音频）
                '-filter_complex', filter_complex,
                '-map', '[outv]',             # 使用合成后的视频
                '-map', '2:a',                # 使用克隆语音
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                str(output_path)
            ]

            logger.info(f"[{job_id}] Running FFmpeg PIP composite...")
            returncode, stdout, stderr = await run_ffmpeg_command(composite_cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg PIP error: {stderr.decode()[:500]}")
                return None

            if not output_path.exists():
                logger.error(f"[{job_id}] Output file not created")
                return None

            logger.info(f"[{job_id}] PIP video created: {output_path}, size: {output_path.stat().st_size} bytes")

            # 上传到媒体床
            final_url = await self._upload_to_media_bed(str(output_path))
            logger.info(f"[{job_id}] Final video uploaded: {final_url}")

            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] PIP composite error: {e}")
            import traceback
            traceback.print_exc()
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
                    relative_url = result.get("url")
                    if relative_url:
                        # 返回完整URL，确保前端可以直接使用
                        return f"{self.media_bed_url}{relative_url}"
                    return None

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
