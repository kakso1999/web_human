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

# DNS 补丁：解决本地 DNS 服务器无法解析阿里云域名的问题
try:
    from core.utils.dns_patch import patch_dns
    # patch_dns() 在导入时自动执行
except ImportError:
    pass  # DNS 补丁可选

from core.config.settings import get_settings
from .repository import get_story_generation_repository, StoryGenerationRepository
from .apicore_client import get_apicore_client, APICoreClient
from .schemas import StoryJobStatus, StoryJobStep

settings = get_settings()
logger = logging.getLogger(__name__)

# 配置代理绕过：阿里云域名不走代理
# 解决代理开启时无法访问 dashscope.aliyuncs.com 的问题
_no_proxy_domains = "aliyuncs.com,dashscope.aliyuncs.com,alibabacloud.com"
_existing_no_proxy = os.environ.get("NO_PROXY", os.environ.get("no_proxy", ""))
if _existing_no_proxy:
    os.environ["NO_PROXY"] = f"{_existing_no_proxy},{_no_proxy_domains}"
else:
    os.environ["NO_PROXY"] = _no_proxy_domains
os.environ["no_proxy"] = os.environ["NO_PROXY"]  # 兼容小写
logger.info(f"NO_PROXY configured: {os.environ['NO_PROXY']}")


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
        mode: str = "single",
        voice_profile_id: Optional[str] = None,
        avatar_profile_id: Optional[str] = None,
        speaker_configs: Optional[List[Dict[str, Any]]] = None,
        replace_all_voice: bool = True,
        full_video: bool = False
    ) -> Dict[str, Any]:
        """
        创建故事生成任务

        支持两种模式：
        1. 单人模式 (single)：使用 voice_profile_id 和 avatar_profile_id，一个声音一个数字人
        2. 双人模式 (dual)：使用 speaker_configs 数组，为每个说话人配置声音和头像

        Args:
            user_id: 用户ID
            story_id: 故事ID
            mode: 生成模式 - 'single' 或 'dual'
            voice_profile_id: 声音档案ID（单人模式）
            avatar_profile_id: 头像档案ID（单人模式）
            speaker_configs: 说话人配置列表（双人模式）
            replace_all_voice: 是否替换全部人声
            full_video: 是否生成完整视频
        """
        # 获取故事信息
        from modules.story.repository import StoryRepository
        story_repo = StoryRepository()
        story = await story_repo.get_by_id(story_id)

        if not story:
            raise ValueError(f"Story not found: {story_id}")

        video_url = story.get("video_url")
        if not video_url:
            raise ValueError(f"Story has no video: {story_id}")

        # 根据模式验证参数
        if mode == "single":
            # 单人模式：需要 voice_profile_id 和 avatar_profile_id
            if not voice_profile_id:
                raise ValueError("voice_profile_id is required for single mode")
            if not avatar_profile_id:
                raise ValueError("avatar_profile_id is required for single mode")
            # 验证单人模式分析是否完成
            single_analysis = story.get("single_speaker_analysis")
            if not single_analysis or not single_analysis.get("is_analyzed"):
                raise ValueError("Story single speaker analysis is not completed")
        elif mode == "dual":
            # 双人模式：需要 speaker_configs
            if not speaker_configs or len(speaker_configs) == 0:
                raise ValueError("speaker_configs is required for dual mode")
            # 验证双人模式分析是否完成
            dual_analysis = story.get("dual_speaker_analysis")
            if not dual_analysis or not dual_analysis.get("is_analyzed"):
                raise ValueError("Story dual speaker analysis is not completed")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'single' or 'dual'")

        # 创建任务
        job_id = await self.repository.create_job(
            user_id=user_id,
            story_id=story_id,
            mode=mode,
            voice_profile_id=voice_profile_id,
            avatar_profile_id=avatar_profile_id,
            speaker_configs=speaker_configs,
            original_video_url=video_url,
            replace_all_voice=replace_all_voice,
            full_video=full_video
        )

        # 根据模式启动对应的处理流程
        if mode == "dual":
            asyncio.create_task(self._process_job_multi_speaker(job_id))
        else:
            asyncio.create_task(self._process_job(job_id))

        logger.info(f"[{job_id}] Job created: mode={mode}, full_video={full_video}")
        return {"id": job_id, "status": "pending"}

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

    # ===================== 说话人分析 =====================

    async def analyze_story_audio_task(
        self,
        story_id: str,
        video_path: str,
        num_speakers: Optional[int] = None
    ):
        """
        后台任务：分析故事音频

        同时执行两种分析模式：
        1. 单人模式：人声整体 + 背景音（不进行说话人分割）
        2. 双人模式：说话人1 + 说话人2 + 背景音（最多2个说话人）

        管理员上传故事后自动调用，准备好两种模式的数据。
        用户生成时可以选择使用哪种模式。
        """
        from modules.story.repository import StoryRepository
        from modules.voice_separation import get_voice_separation_service

        story_repo = StoryRepository()

        try:
            logger.info(f"[{story_id}] Starting both-modes speaker analysis")

            # 获取语音分离服务
            voice_service = get_voice_separation_service()

            # 执行两种模式的分析
            result = await voice_service.analyze_both_modes(
                story_id=story_id,
                video_path=video_path
            )

            single_analysis = result.get("single_speaker_analysis")
            dual_analysis = result.get("dual_speaker_analysis")

            # 构建更新数据
            update_data = {
                "is_analyzed": True,
                "analysis_error": None
            }

            # 单人模式分析结果
            if single_analysis:
                update_data["single_speaker_analysis"] = single_analysis

            # 双人模式分析结果
            if dual_analysis:
                update_data["dual_speaker_analysis"] = dual_analysis
                # 保持旧字段兼容性
                update_data["speaker_count"] = len(dual_analysis.get("speakers", []))
                update_data["speakers"] = dual_analysis.get("speakers", [])
                update_data["background_audio_url"] = dual_analysis.get("background_url")
                update_data["diarization_segments"] = dual_analysis.get("diarization_segments", [])

            # 如果两种分析都失败，记录错误
            errors = result.get("errors")
            if errors and not single_analysis and not dual_analysis:
                update_data["is_analyzed"] = False
                update_data["analysis_error"] = "; ".join(errors)

            await story_repo.update(story_id, update_data)

            single_ok = "OK" if single_analysis else "FAILED"
            dual_ok = "OK" if dual_analysis else "FAILED"
            logger.info(f"[{story_id}] Both-modes analysis completed. Single: {single_ok}, Dual: {dual_ok}")

        except Exception as e:
            logger.error(f"[{story_id}] Speaker analysis failed: {e}")
            import traceback
            traceback.print_exc()

            # 记录错误
            await story_repo.update(story_id, {
                "is_analyzed": False,
                "analysis_error": str(e)
            })

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

            # 获取任务和故事信息
            job = await self.repository.get_job(job_id)
            story_id = job.get("story_id")

            from modules.story.repository import StoryRepository
            story_repo = StoryRepository()
            story = await story_repo.get_by_id(story_id)

            # Step 1: 提取音频（用于保存本地视频文件）
            await self._update_progress(job_id, StoryJobStep.EXTRACTING_AUDIO, 5)
            audio_url = await self._extract_audio(job_id)
            if not audio_url:
                raise Exception("Failed to extract audio from video")

            # Step 2: 使用故事分析结果中已有的分离音频（无需再次分离）
            await self._update_progress(job_id, StoryJobStep.SEPARATING_VOCALS, 10)

            # 从故事分析结果获取已分离的人声和背景音
            single_analysis = story.get("single_speaker_analysis", {}) if story else {}
            vocals_url = single_analysis.get("vocals_url")
            instrumental_url = single_analysis.get("background_url")

            if vocals_url:
                logger.info(f"[{job_id}] Using pre-analyzed vocals: {vocals_url}")
                logger.info(f"[{job_id}] Using pre-analyzed background: {instrumental_url}")
            else:
                # 如果没有分析结果，使用原始音频
                logger.warning(f"[{job_id}] No pre-analyzed vocals found, using original audio")
                vocals_url = audio_url
                instrumental_url = None

            # Step 3: 语音识别生成字幕（使用词级时间戳）
            # 注意：转录使用原始音频（audio_url），而不是分离后的 vocals
            # 因为分离后的 vocals 可能有质量问题，VAD 检测不到语音
            await self._update_progress(job_id, StoryJobStep.TRANSCRIBING, 15)
            transcription = await self._transcribe_audio(job_id, audio_url)
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

            # 获取任务配置，检查是否生成完整视频
            job = await self.repository.get_job(job_id)
            full_video = job.get("full_video", False) if job else False

            if full_video:
                # 生成完整视频：处理所有片段
                segments_to_process = video_segments
                logger.info(f"[{job_id}] Full video mode: processing all {len(segments_to_process)} segments")
            else:
                # 默认模式：只处理前2个片段
                MAX_SEGMENTS_DEFAULT = 2
                segments_to_process = video_segments[:MAX_SEGMENTS_DEFAULT]
                logger.info(f"[{job_id}] Preview mode: processing first {len(segments_to_process)} segments")

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

            # 检查服务模式
            from core.config.settings import get_settings
            settings = get_settings()
            service_mode = getattr(settings, 'AI_SERVICE_MODE', 'cloud').lower()

            reference_audio_path = None
            voice_id = profile.get("voice_id")

            if service_mode == "local":
                # 本地模式：需要下载参考音频
                reference_audio_url = profile.get("reference_audio_url")
                if not reference_audio_url:
                    logger.error(f"[{job_id}] No reference audio URL in profile")
                    return None

                # 下载参考音频到本地
                import httpx
                import tempfile

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(reference_audio_url)
                    if response.status_code != 200:
                        logger.error(f"[{job_id}] Failed to download reference audio: {response.status_code}")
                        return None

                # 保存到临时文件
                ref_audio_dir = self.upload_dir / f"{job_id}_ref"
                ref_audio_dir.mkdir(parents=True, exist_ok=True)
                reference_audio_path = str(ref_audio_dir / "reference.wav")

                with open(reference_audio_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"[{job_id}] Downloaded reference audio to: {reference_audio_path}")

                # 创建本地 voice_id
                from modules.voice_clone.factory import get_voice_clone_service
                vc_service = get_voice_clone_service()
                voice_id = await vc_service._create_voice(f"{job_id}_seg{segment_index}", reference_audio_url)

                if not voice_id:
                    logger.error(f"[{job_id}] Failed to create local voice")
                    return None

            else:
                # 云端模式
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
                audio_content = await self._call_cosyvoice_tts(voice_id, text, reference_audio_path)
                if not audio_content:
                    logger.warning(f"[{job_id}] TTS failed for subtitle {i}")
                    continue

                # 保存 TTS 原始输出
                raw_file = self.upload_dir / f"{job_id}_seg{segment_index}_sub{i}_raw.mp3"
                with open(raw_file, 'wb') as f:
                    f.write(audio_content)

                # 获取 TTS 生成的实际时长
                actual_duration = await self._get_audio_duration(str(raw_file))
                target_duration = duration  # 原始字幕时长

                # 音轨对齐：调整 TTS 音频时长以匹配原始字幕时长
                aligned_file = self.upload_dir / f"{job_id}_seg{segment_index}_sub{i}.mp3"

                if actual_duration > 0 and target_duration > 0 and abs(actual_duration - target_duration) > 0.1:
                    # 时长差异超过 0.1 秒才进行调整
                    logger.info(f"[{job_id}] Seg{segment_index} Sub{i}: Aligning audio {actual_duration:.2f}s -> {target_duration:.2f}s")
                    success = await self._adjust_audio_duration(
                        str(raw_file), str(aligned_file),
                        actual_duration, target_duration
                    )
                    if not success:
                        logger.warning(f"[{job_id}] Audio alignment failed, using original")
                        aligned_file = raw_file
                else:
                    # 时长接近，直接使用原始文件
                    aligned_file = raw_file

                segment_files.append({
                    "path": str(aligned_file),
                    "start_time": relative_start_time,  # 使用相对时间
                    "target_duration": target_duration
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
            from modules.digital_human.factory import get_digital_human_service
            dh_service = get_digital_human_service()

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

            return str(output_path.resolve())

        except Exception as e:
            logger.error(f"[{job_id}] Extract video segment error: {e}")
            return None

    async def _get_local_file_path(self, url_or_path: str, target_path: Path) -> Optional[Path]:
        """
        获取本地文件路径，支持：
        - 本地相对路径 (/uploads/...)
        - HTTP URL
        - 已存在的本地绝对路径
        """
        import shutil

        # 如果是本地相对路径
        if url_or_path.startswith('/uploads/'):
            # 使用 removeprefix 而不是 lstrip（lstrip 是逐字符删除的）
            rel_path = url_or_path[len('/uploads/'):]
            uploads_absolute = Path(settings.UPLOAD_DIR).resolve()
            local_path = uploads_absolute / rel_path

            logger.info(f"Local path resolution: {url_or_path} -> {local_path}")

            if local_path.exists():
                shutil.copy(str(local_path), str(target_path))
                return target_path
            else:
                logger.error(f"Local file not found: {local_path}")
                return None

        elif url_or_path.startswith('uploads/'):
            # 相对路径（不带前导斜杠）
            rel_path = url_or_path[len('uploads/'):]
            uploads_absolute = Path(settings.UPLOAD_DIR).resolve()
            local_path = uploads_absolute / rel_path

            if local_path.exists():
                shutil.copy(str(local_path), str(target_path))
                return target_path
            else:
                logger.error(f"Local file not found: {local_path}")
                return None

        # 如果已经是本地绝对路径
        elif Path(url_or_path).exists():
            shutil.copy(url_or_path, str(target_path))
            return target_path

        # HTTP URL - 下载
        elif url_or_path.startswith('http'):
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.get(url_or_path)
                if response.status_code != 200:
                    logger.error(f"Failed to download: {url_or_path}")
                    return None
                with open(target_path, 'wb') as f:
                    f.write(response.content)
                return target_path

        else:
            logger.error(f"Unknown URL format: {url_or_path}")
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

            # 获取数字人视频（支持本地路径和 HTTP URL）
            dh_video_path = self.upload_dir / f"{job_id}_seg{segment_index}_dh.mp4"
            result = await self._get_local_file_path(digital_human_url, dh_video_path)
            if not result:
                logger.error(f"[{job_id}] Failed to get digital human video")
                return None

            # 获取克隆语音（支持本地路径和 HTTP URL）
            audio_path = self.upload_dir / f"{job_id}_seg{segment_index}_audio.mp3"
            result = await self._get_local_file_path(audio_url, audio_path)
            if not result:
                logger.error(f"[{job_id}] Failed to get audio")
                return None

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

            return str(output_path.resolve())

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
            # 获取克隆语音（支持本地路径和 HTTP URL）
            audio_path = self.upload_dir / f"{job_id}_seg{segment_index}_audio.mp3"
            result = await self._get_local_file_path(audio_url, audio_path)
            if not result:
                logger.error(f"[{job_id}] Failed to get audio")
                return None

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

            return str(output_path.resolve()) if output_path.exists() else None

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

            # 创建拼接列表文件（使用绝对路径，正斜杠）
            concat_list_path = self.upload_dir / f"{job_id}_concat_list.txt"
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for path in segment_paths:
                    # 转换为绝对路径，使用正斜杠（FFmpeg 兼容）
                    abs_path = str(Path(path).resolve()).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")

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
                # 获取 /uploads/ 之后的相对路径
                rel_path = video_url[len("/uploads/"):]
                # 使用 resolve() 获取 uploads 目录的绝对路径
                uploads_absolute = Path(settings.UPLOAD_DIR).resolve()
                local_video_path = uploads_absolute / rel_path
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
        print(f"[DEBUG] Starting transcription for {job_id}", flush=True)

        # 写入调试日志（使用固定绝对路径）
        try:
            debug_path = r"E:\工作代码\73_web_human\uploads\transcribe_debug.log"
            with open(debug_path, "a", encoding="utf-8") as f:
                f.write(f"[{job_id}] _transcribe_audio START, audio_url={audio_url}\n")
                f.flush()
        except Exception as debug_err:
            logger.error(f"[{job_id}] Debug log write failed: {debug_err}")

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
            print(f"[DEBUG] Audio duration: {audio_duration:.2f}s")

            # 分块阈值：3 分钟 (临时禁用分块)
            CHUNK_MAX_DURATION = 180  # 秒

            # 临时：跳过分块，直接转写整个音频
            if True:  # audio_duration <= CHUNK_MAX_DURATION:
                # 短音频，直接转写
                print(f"[DEBUG] Direct transcription (no chunking)")
                result = await self._transcribe_audio_chunk(job_id, str(audio_path), 0)
            else:
                # 长音频，分块转写
                logger.info(f"[{job_id}] Audio too long ({audio_duration:.0f}s), splitting into chunks")
                print(f"[DEBUG] Long audio path, chunking ({audio_duration:.0f}s)")
                result = await self._transcribe_audio_chunked(job_id, str(audio_path), audio_duration, CHUNK_MAX_DURATION)

            print(f"[DEBUG] Transcription result: {result is not None}")
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

        优先使用本地 faster-whisper，失败时回退到 APICORE API
        """
        # Debug logging
        try:
            with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{job_id}] _transcribe_audio_chunk START, chunk={chunk_index}, path={audio_path}\n")
                f.flush()
        except:
            pass

        # 只使用本地 faster-whisper（不再回退到 APICORE API）
        try:
            with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{job_id}] About to call _transcribe_with_local_whisper...\n")
                f.flush()
        except:
            pass
        result = await self._transcribe_with_local_whisper(job_id, audio_path, chunk_index)
        if result:
            return result

        # 本地 Whisper 失败，记录错误但不使用 API
        logger.error(f"[{job_id}] Local Whisper failed, no API fallback available")
        return None

    async def _transcribe_with_local_whisper(
        self,
        job_id: str,
        audio_path: str,
        chunk_index: int
    ) -> Optional[Dict[str, Any]]:
        """使用本地 faster-whisper 进行转写（简化版，移除冗余调试代码）"""
        # Debug entry
        try:
            with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{job_id}] _transcribe_with_local_whisper ENTERED\n")
                f.flush()
        except:
            pass

        try:
            logger.info(f"[{job_id}] Chunk {chunk_index}: Using local faster-whisper, audio={audio_path}")

            def transcribe_sync():
                import os
                # 完全禁用所有 HuggingFace 网络请求
                os.environ['HF_HUB_OFFLINE'] = '1'
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
                os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
                os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
                os.environ['DO_NOT_TRACK'] = '1'
                os.environ['HF_HOME'] = r'E:\huggingface_cache'
                os.environ['HF_HUB_CACHE'] = r'E:\huggingface_cache\hub'

                # Debug: function started
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] transcribe_sync STARTED\n")
                    f.flush()

                # 直接使用 CTranslate2 避免 HuggingFace 依赖
                import ctranslate2
                import soundfile as sf
                import numpy as np

                # Debug: imports done
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] imports done (ctranslate2 direct)\n")
                    f.flush()

                # 使用本地缓存的模型 - base 模型适合 2核4G 服务器
                model_path = r'E:\huggingface_cache\hub\models--Systran--faster-whisper-base\snapshots\ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66'

                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] model_path={model_path}\n")
                    f.flush()

                # 使用 faster_whisper 但指定完整本地路径
                from faster_whisper import WhisperModel

                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Creating WhisperModel...\n")
                    f.flush()

                # 强制使用 CPU 避免 CUDA 上下文清理问题（CUDA 版本在线程池中会卡死）
                model = WhisperModel(model_path, device="cpu", compute_type="int8", local_files_only=True)
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Model loaded (CPU - forced to avoid CUDA hang)\n")
                    f.flush()

                # 加载音频
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Loading audio from {audio_path}...\n")
                    f.flush()

                audio, sr = sf.read(audio_path)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                audio = audio.astype(np.float32)

                # Whisper 期望 16kHz 采样率，如果不是则需要重采样
                TARGET_SR = 16000
                if sr != TARGET_SR:
                    import librosa
                    with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"[{job_id}] Resampling from {sr}Hz to {TARGET_SR}Hz...\n")
                        f.flush()
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)
                    sr = TARGET_SR

                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Audio loaded: shape={audio.shape}, sr={sr}\n")
                    f.flush()

                # 转写
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Starting transcription...\n")
                    f.flush()

                segments, info = model.transcribe(
                    audio,
                    language="en",
                    word_timestamps=True,
                    vad_filter=False,  # 禁用 VAD，因为可能误过滤整个音频
                    condition_on_previous_text=False,  # 减少幻觉
                    no_speech_threshold=0.6,  # 静音检测阈值
                    compression_ratio_threshold=2.4  # 压缩比阈值，检测重复
                )

                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Transcription complete, collecting results...\n")
                    f.flush()

                # 收集结果
                all_text = []
                all_words = []
                all_segments = []

                seg_count = 0
                for seg in segments:
                    seg_count += 1
                    all_text.append(seg.text)
                    all_segments.append({
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text.strip()
                    })
                    if seg.words:
                        for word in seg.words:
                            all_words.append({
                                "word": word.word,
                                "start": word.start,
                                "end": word.end
                            })

                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Collected {seg_count} segments, {len(all_words)} words\n")
                    f.flush()

                # 幻觉检测：检查转录结果是否合理
                audio_duration = len(audio) / sr
                is_hallucination = False
                hallucination_reason = ""

                if all_words:
                    first_word_start = all_words[0]["start"]
                    last_word_end = all_words[-1]["end"]

                    # 检查1: 第一个词的时间戳是否异常（超过10秒才开始说话很可疑）
                    if first_word_start > 30:
                        is_hallucination = True
                        hallucination_reason = f"First word starts at {first_word_start:.1f}s (too late)"

                    # 检查2: 最后一个词的时间戳是否超过音频时长
                    if last_word_end > audio_duration + 5:  # 允许5秒误差
                        is_hallucination = True
                        hallucination_reason = f"Last word at {last_word_end:.1f}s exceeds audio duration {audio_duration:.1f}s"

                    # 检查3: 文本重复率过高（幻觉常见模式）
                    if len(all_text) > 5:
                        unique_texts = set(t.strip().lower() for t in all_text)
                        repetition_ratio = 1 - (len(unique_texts) / len(all_text))
                        if repetition_ratio > 0.8:  # 超过80%重复
                            is_hallucination = True
                            hallucination_reason = f"High text repetition: {repetition_ratio:.1%}"

                if is_hallucination:
                    with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"[{job_id}] HALLUCINATION DETECTED: {hallucination_reason}\n")
                        f.flush()
                    # 返回 None 表示转录失败，让上层处理
                    return None

                # 构建结果
                result_dict = {
                    "text": " ".join(all_text),
                    "words": all_words,
                    "segments": all_segments
                }

                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Result created with {len(all_words)} words, returning...\n")
                    f.flush()

                # CPU 模式下不需要显式清理，直接返回
                return result_dict

            # 在线程池中执行同步转写
            loop = asyncio.get_running_loop()

            try:
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] About to run transcribe_sync in executor...\n")
                    f.flush()
            except:
                pass

            result = await loop.run_in_executor(None, transcribe_sync)

            try:
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] Executor returned, result={result is not None}\n")
                    f.flush()
            except:
                pass

            if result:
                logger.info(f"[{job_id}] Chunk {chunk_index}: Local Whisper success, {len(result.get('words', []))} words")
            return result

        except Exception as e:
            logger.error(f"[{job_id}] Chunk {chunk_index}: Local Whisper error: {e}")
            import traceback
            traceback.print_exc()
            # Write error to debug file
            try:
                with open(r"E:\工作代码\73_web_human\uploads\transcribe_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"[{job_id}] LOCAL WHISPER ERROR: {e}\n")
                    f.write(traceback.format_exc())
                    f.flush()
            except:
                pass
            traceback.print_exc()
            return None

    async def _transcribe_with_api(
        self,
        job_id: str,
        audio_path: str,
        chunk_index: int
    ) -> Optional[Dict[str, Any]]:
        """使用 APICORE API 进行转写"""
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
            logger.error(f"[{job_id}] Transcribe chunk {chunk_index} API error: {e}")
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

    async def _call_cosyvoice_tts(self, voice_id: str, text: str, reference_audio_path: str = None) -> Optional[bytes]:
        """
        调用 TTS 生成克隆语音

        根据 AI_SERVICE_MODE 选择：
        - local: 使用本地 SpeechT5 模型
        - cloud: 使用阿里云 CosyVoice API

        Args:
            voice_id: 声音克隆ID (cloud) 或本地 voice_id (local)
            text: 要合成的文本
            reference_audio_path: 参考音频路径 (仅 local 模式需要)

        Returns:
            音频字节数据，失败返回 None
        """
        from core.config.settings import get_settings
        settings = get_settings()
        service_mode = getattr(settings, 'AI_SERVICE_MODE', 'cloud').lower()

        if service_mode == "local":
            # 本地模式：使用 SpeechT5
            return await self._call_local_tts(voice_id, text, reference_audio_path)
        else:
            # 云端模式：使用 CosyVoice
            return await self._call_cloud_tts(voice_id, text)

    async def _call_cloud_tts(self, voice_id: str, text: str) -> Optional[bytes]:
        """云端 TTS (CosyVoice)"""
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

    async def _call_local_tts(self, voice_id: str, text: str, reference_audio_path: str = None) -> Optional[bytes]:
        """本地 TTS (SpeechT5)"""
        try:
            from modules.voice_clone.factory import get_voice_clone_service
            import tempfile
            import os

            vc_service = get_voice_clone_service()

            # 如果没有 reference_audio_path，尝试从本地 voice 缓存获取
            if not reference_audio_path:
                local_voices = getattr(vc_service, '_local_voices', {})
                reference_audio_path = local_voices.get(voice_id)

            if not reference_audio_path or not os.path.exists(reference_audio_path):
                logger.error(f"[LocalTTS] Reference audio not found for voice_id: {voice_id}")
                return None

            # 生成临时输出文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                output_path = f.name

            # 使用本地服务合成
            result = await vc_service.clone_audio_with_text(
                reference_audio_path=reference_audio_path,
                text=text,
                output_path=output_path
            )

            if result and os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    audio_data = f.read()
                os.unlink(output_path)
                logger.info(f"[LocalTTS] Generated {len(audio_data)} bytes for text: '{text[:30]}...'")
                return audio_data
            else:
                logger.error(f"[LocalTTS] Failed to generate audio")
                return None

        except Exception as e:
            logger.error(f"[LocalTTS] Error: {e}")
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

        # 混合所有音轨，然后用 apad 填充到目标时长
        # normalize=0 防止音量降低，dropout_transition=0 防止音量渐变
        # apad=whole_dur 确保输出音频达到完整视频时长（amix duration=longest 只取最长输入，不够目标时长）
        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(segments)}:duration=longest:dropout_transition=0:normalize=0,apad=whole_dur={total_duration}[out]"
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
            from modules.digital_human.factory import get_digital_human_service
            dh_service = get_digital_human_service()

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

    # ===================== 多说话人任务处理 =====================

    async def _process_job_multi_speaker(self, job_id: str):
        """
        处理任务 - 多说话人版本

        流程：
        1. 获取故事的说话人信息
        2. 提取音频、分离人声
        3. 语音识别获取字幕（带说话人标签）
        4. 对每个启用的说话人：
           - 获取该说话人的音频片段
           - 生成克隆语音
           - 生成数字人视频
        5. 合成最终视频：
           - 双数字人画中画（左上角 + 右上角）
           - 混合所有克隆语音 + 背景音
        """
        logger.info(f"[{job_id}] Starting multi-speaker story generation job")

        try:
            # 更新状态为处理中
            await self._update_progress(job_id, StoryJobStep.INIT, 0)

            # 获取任务信息
            job = await self.repository.get_job(job_id)
            if not job:
                raise Exception("Job not found")

            story_id = job.get("story_id")
            speaker_configs = job.get("speaker_configs", [])

            # 获取故事信息（包含说话人分析结果）
            from modules.story.repository import StoryRepository
            story_repo = StoryRepository()
            story = await story_repo.get_by_id(story_id)

            if not story:
                raise Exception(f"Story not found: {story_id}")

            if not story.get("is_analyzed"):
                raise Exception("Story has not been analyzed for speakers")

            # 获取说话人信息和分割片段
            speakers = story.get("speakers", [])
            diarization_segments = story.get("diarization_segments", [])
            background_audio_url = story.get("background_audio_url")

            logger.info(f"[{job_id}] Story has {len(speakers)} speakers, {len(diarization_segments)} segments")

            # Step 1: 提取音频
            await self._update_progress(job_id, StoryJobStep.EXTRACTING_AUDIO, 5)
            audio_url = await self._extract_audio(job_id)
            if not audio_url:
                raise Exception("Failed to extract audio from video")

            # 获取原视频时长（用于后续音频对齐）
            video_path = self.upload_dir / f"{job_id}_video.mp4"
            video_duration = await self._get_video_duration(str(video_path))
            logger.info(f"[{job_id}] Original video duration: {video_duration:.2f}s")

            # Step 2: 语音识别（获取完整字幕）
            await self._update_progress(job_id, StoryJobStep.TRANSCRIBING, 15)
            transcription = await self._transcribe_audio(job_id, audio_url)
            if not transcription:
                raise Exception("Failed to transcribe audio")

            # 保存字幕
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

            # 为字幕分配说话人标签
            subtitles = self._assign_speaker_to_subtitles(subtitles, diarization_segments)
            await self.repository.save_subtitles(job_id, subtitles)

            logger.info(f"[{job_id}] Subtitles with speakers: {len(subtitles)} items")

            # Step 3: 为每个说话人生成克隆语音（顺序执行）
            await self._update_progress(job_id, StoryJobStep.GENERATING_VOICE, 25)

            # 过滤启用的说话人配置
            enabled_configs = [cfg for cfg in speaker_configs if cfg.get("enabled", True)]
            logger.info(f"[{job_id}] Processing {len(enabled_configs)} enabled speakers")

            # Phase 1: 生成所有克隆语音
            speaker_results = {}
            for i, config in enumerate(enabled_configs):
                speaker_id = config.get("speaker_id")
                voice_profile_id = config.get("voice_profile_id")

                logger.info(f"[{job_id}] Phase 1 - Voice cloning for speaker {speaker_id}")

                # 更新进度
                progress = 25 + int((i / len(enabled_configs)) * 25)
                await self._update_progress(job_id, StoryJobStep.GENERATING_VOICE, progress)

                # 获取该说话人的字幕片段
                speaker_subtitles = [s for s in subtitles if s.get("speaker") == speaker_id]
                if not speaker_subtitles:
                    logger.warning(f"[{job_id}] No subtitles found for speaker {speaker_id}")
                    continue

                logger.info(f"[{job_id}] Speaker {speaker_id} has {len(speaker_subtitles)} subtitle segments")

                result = {"speaker_id": speaker_id}

                # 生成克隆语音（如果指定了声音档案）
                if voice_profile_id:
                    cloned_audio_url = await self._generate_cloned_voice_for_speaker(
                        job_id, speaker_id, speaker_subtitles, voice_profile_id, video_duration
                    )
                    result["cloned_audio_url"] = cloned_audio_url
                    logger.info(f"[{job_id}] Speaker {speaker_id} cloned audio: {cloned_audio_url}")

                speaker_results[speaker_id] = result

            # Phase 2: 分段生成数字人视频（最大45秒/段，最多5并发）
            await self._update_progress(job_id, StoryJobStep.GENERATING_DIGITAL_HUMAN, 50)
            logger.info(f"[{job_id}] Phase 2 - Creating segmented EMO tasks")

            MAX_SEGMENT_DURATION = 45  # 每段最大 45 秒
            MAX_CONCURRENT_EMO = 5     # 最大并发 5 个

            configs_by_speaker = {cfg.get("speaker_id"): cfg for cfg in enabled_configs}
            all_emo_tasks = []  # [(speaker_id, segment_index, emo_task_id), ...]

            for speaker_id, result in speaker_results.items():
                config = configs_by_speaker.get(speaker_id, {})
                avatar_profile_id = config.get("avatar_profile_id")
                cloned_audio_url = result.get("cloned_audio_url")

                if not avatar_profile_id or not cloned_audio_url:
                    continue

                # 下载克隆语音并获取时长
                audio_path = await self._download_audio_for_segmentation(
                    job_id, speaker_id, cloned_audio_url
                )
                if not audio_path:
                    continue

                audio_duration = await self._get_audio_duration(audio_path)
                logger.info(f"[{job_id}] Speaker {speaker_id} audio duration: {audio_duration:.2f}s")

                # 计算需要多少个片段
                import math
                num_segments = math.ceil(audio_duration / MAX_SEGMENT_DURATION)
                logger.info(f"[{job_id}] Speaker {speaker_id} will have {num_segments} segments")

                # 分割音频并创建 EMO 任务
                for seg_idx in range(num_segments):
                    start_time = seg_idx * MAX_SEGMENT_DURATION
                    duration = min(MAX_SEGMENT_DURATION, audio_duration - start_time)

                    # 提取音频片段
                    segment_audio_path = await self._extract_audio_segment_for_emo(
                        job_id, speaker_id, seg_idx, audio_path, start_time, duration
                    )
                    if not segment_audio_path:
                        continue

                    # 上传音频片段
                    segment_audio_url = await self._upload_to_media_bed(segment_audio_path)
                    if not segment_audio_url:
                        continue

                    # 创建 EMO 任务
                    emo_task_id = await self._create_emo_task_for_segment(
                        job_id, speaker_id, seg_idx, segment_audio_url, avatar_profile_id
                    )
                    if emo_task_id:
                        all_emo_tasks.append((speaker_id, seg_idx, emo_task_id))
                        logger.info(f"[{job_id}] EMO task created: {speaker_id}_seg{seg_idx} -> {emo_task_id}")

                    # 控制并发：每 5 个任务暂停一下让 API 处理
                    if len(all_emo_tasks) % MAX_CONCURRENT_EMO == 0:
                        await asyncio.sleep(2)

            # 持久化 EMO 任务列表到数据库（用于断点恢复）
            emo_tasks_data = [
                {"speaker_id": spk, "seg_idx": idx, "task_id": tid, "status": "pending"}
                for spk, idx, tid in all_emo_tasks
            ]
            await self.repository.update_job_field(job_id, "emo_tasks", emo_tasks_data)
            logger.info(f"[{job_id}] Saved {len(emo_tasks_data)} EMO tasks to database")

            # Phase 3: 等待所有 EMO 任务完成（每 60 秒轮询一次）
            if all_emo_tasks:
                logger.info(f"[{job_id}] Phase 3 - Waiting for {len(all_emo_tasks)} EMO tasks (poll every 60s)")
                emo_results = await self._wait_for_segmented_emo_tasks(job_id, all_emo_tasks, poll_interval=60)

                # Phase 4: 为每个说话人拼接数字人视频片段
                for speaker_id in speaker_results:
                    # 收集该说话人的所有片段
                    speaker_segments = [
                        (seg_idx, video_url)
                        for (spk_id, seg_idx, video_url) in emo_results
                        if spk_id == speaker_id and video_url
                    ]
                    speaker_segments.sort(key=lambda x: x[0])  # 按片段索引排序

                    if speaker_segments:
                        logger.info(f"[{job_id}] Concatenating {len(speaker_segments)} segments for {speaker_id}")
                        concat_video_url = await self._concat_digital_human_segments(
                            job_id, speaker_id, [url for _, url in speaker_segments]
                        )
                        speaker_results[speaker_id]["digital_human_video_url"] = concat_video_url
                        logger.info(f"[{job_id}] Speaker {speaker_id} digital human: {concat_video_url}")

            # 保存说话人结果
            await self.repository.update_job_field(job_id, "speaker_results", speaker_results)

            # Step 4: 合成最终视频
            await self._update_progress(job_id, StoryJobStep.COMPOSITING_VIDEO, 85)

            # 收集所有克隆语音和数字人视频
            cloned_audios = []
            digital_humans = []
            for speaker_id, result in speaker_results.items():
                if result.get("cloned_audio_url"):
                    cloned_audios.append({
                        "speaker_id": speaker_id,
                        "audio_url": result["cloned_audio_url"]
                    })
                if result.get("digital_human_video_url"):
                    digital_humans.append({
                        "speaker_id": speaker_id,
                        "video_url": result["digital_human_video_url"]
                    })

            logger.info(f"[{job_id}] Compositing: {len(cloned_audios)} audios, {len(digital_humans)} digital humans")

            # 合成最终视频
            final_video_url = await self._composite_multi_speaker_video(
                job_id,
                digital_humans,
                cloned_audios,
                background_audio_url
            )

            if not final_video_url:
                raise Exception("Failed to composite final video")

            # 完成
            await self.repository.update_job_status(
                job_id,
                StoryJobStatus.COMPLETED,
                progress=100,
                current_step=StoryJobStep.COMPLETED
            )
            await self.repository.update_job_field(job_id, "final_video_url", final_video_url)

            logger.info(f"[{job_id}] Multi-speaker story generation completed!")

        except Exception as e:
            logger.error(f"[{job_id}] Multi-speaker story generation failed: {e}")
            import traceback
            traceback.print_exc()

            await self.repository.update_job_status(
                job_id,
                StoryJobStatus.FAILED,
                error=str(e)
            )

    def _assign_speaker_to_subtitles(
        self,
        subtitles: List[Dict[str, Any]],
        diarization_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为字幕分配说话人标签

        根据时间重叠来匹配字幕和说话人分割片段
        """
        if not diarization_segments:
            return subtitles

        for subtitle in subtitles:
            sub_start = subtitle.get("start_time", 0)
            sub_end = subtitle.get("end_time", 0)
            sub_mid = (sub_start + sub_end) / 2

            # 找到与字幕中点时间重叠的说话人片段
            best_speaker = None
            for seg in diarization_segments:
                seg_start = seg.get("start", 0)
                seg_end = seg.get("end", 0)
                if seg_start <= sub_mid <= seg_end:
                    best_speaker = seg.get("speaker")
                    break

            if best_speaker:
                subtitle["speaker"] = best_speaker

        return subtitles

    async def _generate_cloned_voice_for_speaker(
        self,
        job_id: str,
        speaker_id: str,
        subtitles: List[Dict[str, Any]],
        voice_profile_id: str,
        video_duration: float = 0
    ) -> Optional[str]:
        """
        为指定说话人生成克隆语音

        只处理属于该说话人的字幕片段
        重要：使用原视频时长确保音轨对齐
        重要：每次都从 reference_audio_url 创建新的临时 voice_id（因为 CosyVoice 的 voice_id 会过期）
        """
        logger.info(f"[{job_id}] Generating cloned voice for speaker {speaker_id}, {len(subtitles)} subtitles")

        try:
            # 获取声音档案
            from modules.voice_clone.repository import voice_profile_repository
            profile = await voice_profile_repository.get_by_id(voice_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Voice profile not found: {voice_profile_id}")
                return None

            # 使用 reference_audio_url 创建新的临时 voice_id（而不是使用存储的 voice_id）
            reference_audio_url = profile.get("reference_audio_url")
            if not reference_audio_url:
                logger.error(f"[{job_id}] No reference_audio_url in profile")
                return None

            logger.info(f"[{job_id}] Creating fresh voice from reference: {reference_audio_url}")

            # 调用 VoiceCloneService 创建新的 voice
            from modules.voice_clone.factory import get_voice_clone_service
            vc_service = get_voice_clone_service()

            voice_id = await vc_service._create_voice(f"{job_id}_{speaker_id}", reference_audio_url)
            if not voice_id:
                logger.error(f"[{job_id}] Failed to create voice for speaker {speaker_id}")
                return None

            # 等待 voice 就绪
            is_ready = await vc_service._wait_for_voice_ready(f"{job_id}_{speaker_id}", voice_id, max_attempts=30, poll_interval=3)
            if not is_ready:
                logger.error(f"[{job_id}] Voice not ready for speaker {speaker_id}")
                return None

            logger.info(f"[{job_id}] Using fresh voice_id: {voice_id} for speaker {speaker_id}")

            # 使用原视频时长，如果未提供则从字幕计算
            if not subtitles:
                return None

            if video_duration <= 0:
                # 后备方案：从字幕计算（但这不是理想的）
                video_duration = subtitles[-1]["end_time"]
                logger.warning(f"[{job_id}] No video_duration provided, using subtitle end time: {video_duration}")

            total_duration = video_duration
            logger.info(f"[{job_id}] Speaker {speaker_id} audio will be {total_duration:.2f}s (full video length)")

            # 生成每个字幕的语音，使用绝对时间位置
            segment_files = []
            for i, sub in enumerate(subtitles):
                text = sub.get("text", "").strip()
                if not text:
                    continue

                # 使用绝对时间（相对于视频开始）
                abs_start_time = sub.get("start_time", 0)
                abs_end_time = sub.get("end_time", 0)
                target_duration = abs_end_time - abs_start_time  # 原始字幕时长

                logger.info(f"[{job_id}] Speaker {speaker_id} Sub{i}: '{text[:20]}...' at {abs_start_time:.2f}s (dur: {target_duration:.2f}s)")

                # 调用 TTS
                audio_content = await self._call_cosyvoice_tts(voice_id, text)
                if not audio_content:
                    logger.warning(f"[{job_id}] TTS failed for subtitle {i}")
                    continue

                # 保存 TTS 原始输出
                raw_file = self.upload_dir / f"{job_id}_{speaker_id}_sub{i}_raw.mp3"
                with open(raw_file, 'wb') as f:
                    f.write(audio_content)

                # 获取 TTS 生成的实际时长
                actual_duration = await self._get_audio_duration(str(raw_file))

                # 音轨对齐：调整 TTS 音频时长以匹配原始字幕时长
                aligned_file = self.upload_dir / f"{job_id}_{speaker_id}_sub{i}.mp3"

                if actual_duration > 0 and target_duration > 0 and abs(actual_duration - target_duration) > 0.1:
                    # 时长差异超过 0.1 秒才进行调整
                    logger.info(f"[{job_id}] Speaker {speaker_id} Sub{i}: Aligning audio {actual_duration:.2f}s -> {target_duration:.2f}s")
                    success = await self._adjust_audio_duration(
                        str(raw_file), str(aligned_file),
                        actual_duration, target_duration
                    )
                    if not success:
                        logger.warning(f"[{job_id}] Audio alignment failed, using original")
                        aligned_file = raw_file
                else:
                    # 时长接近，直接使用原始文件
                    aligned_file = raw_file

                segment_files.append({
                    "path": str(aligned_file),
                    "start_time": abs_start_time,  # 使用绝对时间
                    "target_duration": target_duration
                })

            if not segment_files:
                logger.error(f"[{job_id}] No audio segments generated for speaker {speaker_id}")
                return None

            # 拼接所有字幕音频
            final_audio_path = self.upload_dir / f"{job_id}_{speaker_id}_cloned.mp3"
            success = await self._concat_audio_segments(
                job_id,
                segment_files,
                str(final_audio_path),
                total_duration
            )

            if not success:
                logger.error(f"[{job_id}] Failed to concat audio for speaker {speaker_id}")
                return None

            # 上传到图床
            audio_url = await self._upload_to_media_bed(str(final_audio_path))
            logger.info(f"[{job_id}] Speaker {speaker_id} cloned voice uploaded: {audio_url}")

            return audio_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate cloned voice for speaker {speaker_id} error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _generate_digital_human_for_speaker(
        self,
        job_id: str,
        speaker_id: str,
        audio_url: str,
        avatar_profile_id: str
    ) -> Optional[str]:
        """为指定说话人生成数字人视频"""
        logger.info(f"[{job_id}] Generating digital human for speaker {speaker_id}")

        try:
            # 获取头像档案
            from modules.digital_human.repository import avatar_profile_repository
            profile = await avatar_profile_repository.get_by_id(avatar_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Avatar profile not found: {avatar_profile_id}")
                return None

            image_url = profile.get("image_url")
            face_bbox = profile.get("face_bbox")
            ext_bbox = profile.get("ext_bbox")

            if not image_url or not face_bbox or not ext_bbox:
                logger.error(f"[{job_id}] Invalid avatar profile for speaker {speaker_id}")
                return None

            # 截取音频前55秒（EMO限制）
            truncated_audio_url = await self._truncate_audio_for_emo(
                job_id, audio_url, max_duration=55
            )
            if not truncated_audio_url:
                truncated_audio_url = audio_url

            # 调用 EMO API
            from modules.digital_human.factory import get_digital_human_service
            dh_service = get_digital_human_service()

            emo_task_id = await dh_service._create_emo_task(
                task_id=f"{job_id}_{speaker_id}",
                image_url=image_url,
                audio_url=truncated_audio_url,
                face_bbox=face_bbox,
                ext_bbox=ext_bbox
            )

            if not emo_task_id:
                logger.error(f"[{job_id}] Failed to create EMO task for speaker {speaker_id}")
                return None

            # 等待任务完成
            video_url = await dh_service._wait_for_emo_task(
                task_id=f"{job_id}_{speaker_id}",
                emo_task_id=emo_task_id,
                max_attempts=180,
                poll_interval=5
            )

            logger.info(f"[{job_id}] Speaker {speaker_id} digital human: {video_url}")
            return video_url

        except Exception as e:
            logger.error(f"[{job_id}] Generate digital human for speaker {speaker_id} error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _create_emo_task_for_speaker(
        self,
        job_id: str,
        speaker_id: str,
        audio_url: str,
        avatar_profile_id: str
    ) -> Optional[str]:
        """
        为指定说话人创建 EMO 任务（不等待完成）

        返回 emo_task_id，用于后续轮询状态
        """
        logger.info(f"[{job_id}] Creating EMO task for speaker {speaker_id}")

        try:
            # 获取头像档案
            from modules.digital_human.repository import avatar_profile_repository
            profile = await avatar_profile_repository.get_by_id(avatar_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Avatar profile not found: {avatar_profile_id}")
                return None

            image_url = profile.get("image_url")
            face_bbox = profile.get("face_bbox")
            ext_bbox = profile.get("ext_bbox")

            if not image_url or not face_bbox or not ext_bbox:
                logger.error(f"[{job_id}] Invalid avatar profile for speaker {speaker_id}")
                return None

            # 截取音频前55秒（EMO限制）
            truncated_audio_url = await self._truncate_audio_for_emo(
                job_id, audio_url, max_duration=55
            )
            if not truncated_audio_url:
                truncated_audio_url = audio_url

            # 调用 EMO API 创建任务
            from modules.digital_human.factory import get_digital_human_service
            dh_service = get_digital_human_service()

            emo_task_id = await dh_service._create_emo_task(
                task_id=f"{job_id}_{speaker_id}",
                image_url=image_url,
                audio_url=truncated_audio_url,
                face_bbox=face_bbox,
                ext_bbox=ext_bbox
            )

            if not emo_task_id:
                logger.error(f"[{job_id}] Failed to create EMO task for speaker {speaker_id}")
                return None

            logger.info(f"[{job_id}] EMO task created for {speaker_id}: {emo_task_id}")
            return emo_task_id

        except Exception as e:
            logger.error(f"[{job_id}] Create EMO task for speaker {speaker_id} error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _wait_for_all_emo_tasks(
        self,
        job_id: str,
        emo_tasks: List[tuple],
        poll_interval: int = 60,
        max_attempts: int = 30
    ) -> Dict[str, Optional[str]]:
        """
        并行等待所有 EMO 任务完成

        Args:
            job_id: 任务ID
            emo_tasks: [(speaker_id, emo_task_id), ...]
            poll_interval: 轮询间隔（秒），默认 60 秒
            max_attempts: 最大轮询次数，默认 30 次（30分钟）

        Returns:
            {speaker_id: video_url or None, ...}
        """
        from modules.digital_human.factory import get_digital_human_service
        import requests
        import os

        logger.info(f"[{job_id}] Waiting for {len(emo_tasks)} EMO tasks, poll every {poll_interval}s")

        results = {speaker_id: None for speaker_id, _ in emo_tasks}
        pending_tasks = list(emo_tasks)  # [(speaker_id, emo_task_id), ...]

        api_key = os.getenv("DASHSCOPE_API_KEY")

        for attempt in range(max_attempts):
            if not pending_tasks:
                break

            logger.info(f"[{job_id}] EMO poll attempt {attempt + 1}/{max_attempts}, {len(pending_tasks)} pending")

            still_pending = []
            for i, (speaker_id, emo_task_id) in enumerate(pending_tasks):
                try:
                    # 添加小延迟避免并发请求过多
                    if i > 0:
                        await asyncio.sleep(0.5)  # 每个请求间隔 0.5 秒

                    # 查询 EMO 任务状态（带重试）
                    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{emo_task_id}"
                    headers = {"Authorization": f"Bearer {api_key}"}

                    # 简单重试机制
                    response = None
                    for retry in range(3):
                        try:
                            # proxies={"http": None, "https": None} 绕过系统代理
                            response = requests.get(url, headers=headers, timeout=60, proxies={"http": None, "https": None})
                            break
                        except Exception as retry_error:
                            if retry < 2:
                                logger.warning(f"[{job_id}] {speaker_id} retry {retry + 1}: {retry_error}")
                                await asyncio.sleep(2)
                            else:
                                raise retry_error

                    data = response.json()
                    output = data.get("output", {})
                    status = output.get("task_status")

                    logger.info(f"[{job_id}] {speaker_id} EMO status: {status}")

                    if status == "SUCCEEDED":
                        video_url = output.get("results", {}).get("video_url")
                        results[speaker_id] = video_url
                        logger.info(f"[{job_id}] {speaker_id} EMO completed: {video_url[:60]}...")
                    elif status == "FAILED":
                        error_msg = output.get("message", "Unknown error")
                        logger.error(f"[{job_id}] {speaker_id} EMO failed: {error_msg}")
                        results[speaker_id] = None
                    else:
                        # PENDING 或 RUNNING，继续等待
                        still_pending.append((speaker_id, emo_task_id))

                except Exception as e:
                    logger.warning(f"[{job_id}] Error checking {speaker_id} EMO: {e}")
                    still_pending.append((speaker_id, emo_task_id))

            pending_tasks = still_pending

            if pending_tasks and attempt < max_attempts - 1:
                logger.info(f"[{job_id}] Waiting {poll_interval}s before next poll...")
                await asyncio.sleep(poll_interval)

        # 超时的任务
        for speaker_id, emo_task_id in pending_tasks:
            logger.error(f"[{job_id}] {speaker_id} EMO timeout after {max_attempts * poll_interval}s")
            results[speaker_id] = None

        return results

    async def _composite_multi_speaker_video(
        self,
        job_id: str,
        digital_humans: List[Dict[str, Any]],
        cloned_audios: List[Dict[str, Any]],
        background_audio_url: Optional[str]
    ) -> Optional[str]:
        """
        合成多说话人最终视频

        双数字人画中画布局：
        - 第一个数字人：左上角
        - 第二个数字人：右上角

        音频混合：
        - 所有克隆语音混合
        - 添加背景音（如果有）
        """
        logger.info(f"[{job_id}] Compositing multi-speaker video: {len(digital_humans)} digital humans")

        try:
            import httpx

            # 准备文件路径
            video_path = self.upload_dir / f"{job_id}_video.mp4"
            output_path = self.upload_dir / f"{job_id}_final_multi.mp4"

            if not video_path.exists():
                logger.error(f"[{job_id}] Original video not found")
                return None

            # 下载数字人视频
            dh_video_paths = []
            for i, dh in enumerate(digital_humans[:2]):  # 最多处理2个数字人
                dh_video_path = self.upload_dir / f"{job_id}_dh_{dh['speaker_id']}.mp4"
                video_url = dh["video_url"]

                # 处理本地路径
                if video_url.startswith('/uploads') or video_url.startswith('uploads'):
                    # 本地路径处理
                    rel_path = video_url.lstrip('/').replace('\\', '/')
                    if rel_path.startswith('uploads/'):
                        rel_path = rel_path[8:]  # 去掉 uploads/
                    elif rel_path.startswith('uploads\\'):
                        rel_path = rel_path[8:]
                    uploads_absolute = Path(settings.UPLOAD_DIR).resolve()
                    local_video_path = uploads_absolute / rel_path

                    if local_video_path.exists():
                        import shutil
                        shutil.copy(str(local_video_path), str(dh_video_path))
                        dh_video_paths.append(str(dh_video_path))
                        logger.info(f"[{job_id}] Copied local digital human video: {local_video_path}")
                    else:
                        logger.warning(f"[{job_id}] Local digital human video not found: {local_video_path}")
                elif video_url.startswith('http'):
                    # HTTP URL，下载
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        response = await client.get(video_url)
                        if response.status_code == 200:
                            with open(dh_video_path, 'wb') as f:
                                f.write(response.content)
                            dh_video_paths.append(str(dh_video_path))
                        else:
                            logger.warning(f"[{job_id}] Failed to download digital human video for {dh['speaker_id']}")

            # 下载克隆语音
            audio_paths = []
            for audio in cloned_audios:
                audio_path = self.upload_dir / f"{job_id}_audio_{audio['speaker_id']}.mp3"
                audio_url = audio["audio_url"]

                # 统一路径分隔符
                audio_url_normalized = audio_url.replace('\\', '/')

                # 处理本地路径
                if audio_url_normalized.startswith('/uploads/') or audio_url_normalized.startswith('uploads/'):
                    # 获取相对于 uploads 目录的路径（使用 removeprefix 而不是 lstrip）
                    rel_path = audio_url_normalized.removeprefix('/').removeprefix('uploads/')
                    uploads_absolute = Path(settings.UPLOAD_DIR).resolve()
                    local_audio_path = uploads_absolute / rel_path

                    if local_audio_path.exists():
                        import shutil
                        shutil.copy(str(local_audio_path), str(audio_path))
                        audio_paths.append(str(audio_path))
                        logger.info(f"[{job_id}] Copied local audio: {local_audio_path}")
                    else:
                        logger.warning(f"[{job_id}] Local audio not found: {local_audio_path}")
                elif audio_url.startswith('http'):
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.get(audio_url)
                        if response.status_code == 200:
                            with open(audio_path, 'wb') as f:
                                f.write(response.content)
                            audio_paths.append(str(audio_path))

            # 下载背景音（如果有）
            bg_audio_path = None
            if background_audio_url:
                bg_audio_path = self.upload_dir / f"{job_id}_background.wav"

                # 统一路径分隔符
                bg_url_normalized = background_audio_url.replace('\\', '/')

                # 处理本地路径（/uploads/... 或相对路径）
                if bg_url_normalized.startswith('/uploads/') or bg_url_normalized.startswith('uploads/'):
                    # 获取相对于 uploads 目录的路径（使用 removeprefix 而不是 lstrip）
                    rel_path = bg_url_normalized.removeprefix('/').removeprefix('uploads/')
                    uploads_absolute = Path(settings.UPLOAD_DIR).resolve()
                    local_bg_path = uploads_absolute / rel_path

                    if local_bg_path.exists():
                        import shutil
                        shutil.copy(str(local_bg_path), str(bg_audio_path))
                        logger.info(f"[{job_id}] Copied local background audio: {local_bg_path}")
                    else:
                        logger.warning(f"[{job_id}] Local background audio not found: {local_bg_path}")
                        bg_audio_path = None
                elif background_audio_url.startswith('http'):
                    # HTTP URL，下载
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.get(background_audio_url)
                        if response.status_code == 200:
                            with open(bg_audio_path, 'wb') as f:
                                f.write(response.content)
                        else:
                            logger.warning(f"[{job_id}] Failed to download background audio")
                            bg_audio_path = None
                else:
                    logger.warning(f"[{job_id}] Unknown background audio URL format: {background_audio_url}")
                    bg_audio_path = None

            # 获取原视频尺寸
            probe_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height',
                '-of', 'csv=p=0',
                str(video_path)
            ]
            returncode, stdout, stderr = await run_ffmpeg_command(probe_cmd)

            try:
                width, height = map(int, stdout.decode().strip().split(','))
            except:
                width, height = 1920, 1080

            logger.info(f"[{job_id}] Original video: {width}x{height}")

            # Debug: 显示音频文件列表
            logger.info(f"[{job_id}] Audio files for compositing: {audio_paths}")
            logger.info(f"[{job_id}] Digital human videos: {dh_video_paths}")

            # 计算数字人画中画尺寸和位置
            pip_width = width // 5  # 占 1/5 宽度
            pip_margin = 20

            # 构建 FFmpeg 命令
            if len(dh_video_paths) == 0:
                # 无数字人，仅替换音频
                final_video_url = await self._composite_audio_only_multi(
                    job_id, str(video_path), audio_paths, bg_audio_path, str(output_path)
                )
            elif len(dh_video_paths) == 1:
                # 单数字人（左上角）
                final_video_url = await self._composite_single_pip_multi(
                    job_id, str(video_path), dh_video_paths[0],
                    audio_paths, bg_audio_path, str(output_path),
                    pip_width, pip_margin, "left"
                )
            else:
                # 双数字人（左上角 + 右上角）
                final_video_url = await self._composite_dual_pip(
                    job_id, str(video_path), dh_video_paths[0], dh_video_paths[1],
                    audio_paths, bg_audio_path, str(output_path),
                    width, height, pip_width, pip_margin
                )

            return final_video_url

        except Exception as e:
            logger.error(f"[{job_id}] Multi-speaker composite error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _composite_dual_pip(
        self,
        job_id: str,
        video_path: str,
        dh_video_path1: str,
        dh_video_path2: str,
        audio_paths: List[str],
        bg_audio_path: Optional[str],
        output_path: str,
        width: int,
        height: int,
        pip_width: int,
        pip_margin: int
    ) -> Optional[str]:
        """
        双数字人画中画合成

        布局：
        - 数字人1：左上角
        - 数字人2：右上角
        """
        logger.info(f"[{job_id}] Creating dual PIP composite")

        try:
            # 计算位置
            pip1_x = pip_margin  # 左上角
            pip1_y = pip_margin
            pip2_x = width - pip_width - pip_margin  # 右上角
            pip2_y = pip_margin

            # 构建输入列表
            inputs = [
                '-i', video_path,
                '-i', dh_video_path1,
                '-i', dh_video_path2
            ]

            # 添加音频输入
            audio_input_start = 3
            for audio_path in audio_paths:
                inputs.extend(['-i', audio_path])

            if bg_audio_path:
                inputs.extend(['-i', str(bg_audio_path)])

            # 构建视频滤镜：双数字人叠加
            video_filter = (
                f"[1:v]scale={pip_width}:-1[pip1];"
                f"[2:v]scale={pip_width}:-1[pip2];"
                f"[0:v][pip1]overlay={pip1_x}:{pip1_y}:shortest=1[tmp];"
                f"[tmp][pip2]overlay={pip2_x}:{pip2_y}:shortest=1[outv]"
            )

            # 构建音频滤镜：混合所有克隆语音
            audio_inputs = []
            for i in range(len(audio_paths)):
                audio_inputs.append(f"[{audio_input_start + i}:a]")

            if len(audio_inputs) == 1:
                audio_filter = f"{audio_inputs[0]}aresample=44100[voices]"
            else:
                audio_filter = (
                    f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}:"
                    f"duration=longest:dropout_transition=0:normalize=0[voices]"
                )

            # 添加背景音（如果有）
            if bg_audio_path:
                bg_input_idx = audio_input_start + len(audio_paths)
                audio_filter += (
                    f";[voices][{bg_input_idx}:a]amix=inputs=2:"
                    f"duration=longest:weights=1 0.3:normalize=0[outa]"
                )
                final_audio = "[outa]"
            else:
                final_audio = "[voices]"

            # 完整滤镜
            filter_complex = f"{video_filter};{audio_filter}"

            cmd = [
                'ffmpeg', '-y',
                *inputs,
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', final_audio,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_path
            ]

            logger.info(f"[{job_id}] Running FFmpeg dual PIP...")
            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg dual PIP error: {stderr.decode()[-2000:]}")
                return None

            if not Path(output_path).exists():
                return None

            # 上传最终视频
            final_url = await self._upload_to_media_bed(output_path)
            logger.info(f"[{job_id}] Dual PIP video uploaded: {final_url}")

            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] Dual PIP composite error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _composite_single_pip_multi(
        self,
        job_id: str,
        video_path: str,
        dh_video_path: str,
        audio_paths: List[str],
        bg_audio_path: Optional[str],
        output_path: str,
        pip_width: int,
        pip_margin: int,
        position: str = "left"
    ) -> Optional[str]:
        """单数字人画中画合成（多说话人模式）"""
        logger.info(f"[{job_id}] Creating single PIP composite (multi-speaker)")

        try:
            # 计算位置
            if position == "left":
                pip_x = pip_margin
            else:
                # 需要获取视频宽度
                probe_cmd = [
                    'ffprobe', '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_path
                ]
                returncode, stdout, stderr = await run_ffmpeg_command(probe_cmd)
                width = int(stdout.decode().strip()) if returncode == 0 else 1920
                pip_x = width - pip_width - pip_margin

            pip_y = pip_margin

            # 构建输入
            inputs = [
                '-i', video_path,
                '-i', dh_video_path
            ]

            audio_input_start = 2
            for audio_path in audio_paths:
                inputs.extend(['-i', audio_path])

            if bg_audio_path:
                inputs.extend(['-i', str(bg_audio_path)])

            # 视频滤镜
            video_filter = (
                f"[1:v]scale={pip_width}:-1[pip];"
                f"[0:v][pip]overlay={pip_x}:{pip_y}:shortest=1[outv]"
            )

            # 音频滤镜
            audio_inputs = [f"[{audio_input_start + i}:a]" for i in range(len(audio_paths))]

            if len(audio_inputs) == 1:
                audio_filter = f"{audio_inputs[0]}aresample=44100[voices]"
            else:
                audio_filter = (
                    f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}:"
                    f"duration=longest:dropout_transition=0:normalize=0[voices]"
                )

            if bg_audio_path:
                bg_input_idx = audio_input_start + len(audio_paths)
                audio_filter += (
                    f";[voices][{bg_input_idx}:a]amix=inputs=2:"
                    f"duration=longest:weights=1 0.3:normalize=0[outa]"
                )
                final_audio = "[outa]"
            else:
                final_audio = "[voices]"

            filter_complex = f"{video_filter};{audio_filter}"

            cmd = [
                'ffmpeg', '-y',
                *inputs,
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', final_audio,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                output_path
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] FFmpeg single PIP error: {stderr.decode()[:300]}")
                return None

            if not Path(output_path).exists():
                return None

            final_url = await self._upload_to_media_bed(output_path)
            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] Single PIP composite error: {e}")
            return None

    async def _composite_audio_only_multi(
        self,
        job_id: str,
        video_path: str,
        audio_paths: List[str],
        bg_audio_path: Optional[str],
        output_path: str
    ) -> Optional[str]:
        """仅替换音频（多说话人模式，无数字人）"""
        logger.info(f"[{job_id}] Creating audio-only composite (multi-speaker)")

        try:
            # 先混合所有音频
            mixed_audio_path = self.upload_dir / f"{job_id}_mixed_audio.mp3"

            # 构建音频混合命令
            inputs = []
            for audio_path in audio_paths:
                inputs.extend(['-i', audio_path])

            if bg_audio_path:
                inputs.extend(['-i', str(bg_audio_path)])

            audio_inputs = [f"[{i}:a]" for i in range(len(audio_paths))]

            if len(audio_inputs) == 1:
                audio_filter = f"{audio_inputs[0]}aresample=44100[voices]"
            else:
                audio_filter = (
                    f"{''.join(audio_inputs)}amix=inputs={len(audio_inputs)}:"
                    f"duration=longest:dropout_transition=0:normalize=0[voices]"
                )

            if bg_audio_path:
                bg_idx = len(audio_paths)
                audio_filter += (
                    f";[voices][{bg_idx}:a]amix=inputs=2:"
                    f"duration=longest:weights=1 0.3:normalize=0[outa]"
                )
                final_audio = "[outa]"
            else:
                final_audio = "[voices]"

            mix_cmd = [
                'ffmpeg', '-y',
                *inputs,
                '-filter_complex', audio_filter,
                '-map', final_audio,
                '-ac', '2', '-ar', '44100',
                str(mixed_audio_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(mix_cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] Audio mix failed: {stderr.decode()[:300]}")
                return None

            # 合成视频 + 混合音频
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', str(mixed_audio_path),
                '-c:v', 'copy',
                '-map', '0:v',
                '-map', '1:a',
                '-c:a', 'aac',
                '-shortest',
                output_path
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] Video composite failed: {stderr.decode()[:300]}")
                return None

            if not Path(output_path).exists():
                return None

            final_url = await self._upload_to_media_bed(output_path)
            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] Audio-only composite error: {e}")
            return None

    # ===================== 分段数字人生成方法 =====================

    async def _download_audio_for_segmentation(
        self,
        job_id: str,
        speaker_id: str,
        audio_url: str
    ) -> Optional[str]:
        """下载音频文件用于分段"""
        try:
            import httpx

            audio_path = self.upload_dir / f"{job_id}_{speaker_id}_full_audio.mp3"

            # 检查本地文件是否存在
            local_path = self.upload_dir / f"{job_id}_{speaker_id}_cloned.mp3"
            if local_path.exists():
                return str(local_path)

            # 下载音频
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(audio_url)
                if response.status_code == 200:
                    with open(audio_path, 'wb') as f:
                        f.write(response.content)
                    return str(audio_path)
                else:
                    logger.error(f"[{job_id}] Failed to download audio: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"[{job_id}] Download audio error: {e}")
            return None

    async def _extract_audio_segment_for_emo(
        self,
        job_id: str,
        speaker_id: str,
        segment_index: int,
        audio_path: str,
        start_time: float,
        duration: float
    ) -> Optional[str]:
        """提取音频片段用于 EMO"""
        try:
            output_path = self.upload_dir / f"{job_id}_{speaker_id}_emo_seg{segment_index}.mp3"

            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                str(output_path)
            ]

            returncode, stdout, stderr = await run_ffmpeg_command(cmd)

            if returncode != 0:
                logger.error(f"[{job_id}] Extract audio segment error: {stderr.decode()[:200]}")
                return None

            if output_path.exists():
                return str(output_path)
            return None

        except Exception as e:
            logger.error(f"[{job_id}] Extract audio segment error: {e}")
            return None

    async def _create_emo_task_for_segment(
        self,
        job_id: str,
        speaker_id: str,
        segment_index: int,
        audio_url: str,
        avatar_profile_id: str
    ) -> Optional[str]:
        """为音频片段创建 EMO 任务"""
        try:
            # 获取头像档案
            from modules.digital_human.repository import avatar_profile_repository
            profile = await avatar_profile_repository.get_by_id(avatar_profile_id)

            if not profile:
                logger.error(f"[{job_id}] Avatar profile not found: {avatar_profile_id}")
                return None

            image_url = profile.get("image_url")
            face_bbox = profile.get("face_bbox")
            ext_bbox = profile.get("ext_bbox")

            if not image_url or not face_bbox or not ext_bbox:
                logger.error(f"[{job_id}] Invalid avatar profile")
                return None

            # 调用 EMO API 创建任务
            from modules.digital_human.factory import get_digital_human_service
            dh_service = get_digital_human_service()

            emo_task_id = await dh_service._create_emo_task(
                task_id=f"{job_id}_{speaker_id}_seg{segment_index}",
                image_url=image_url,
                audio_url=audio_url,
                face_bbox=face_bbox,
                ext_bbox=ext_bbox
            )

            return emo_task_id

        except Exception as e:
            logger.error(f"[{job_id}] Create EMO task for segment error: {e}")
            return None

    async def _wait_for_segmented_emo_tasks(
        self,
        job_id: str,
        emo_tasks: List[tuple],
        poll_interval: int = 60,
        max_attempts: int = 60
    ) -> List[tuple]:
        """
        等待所有分段 EMO 任务完成

        使用工厂模式的 digital human 服务，支持本地和云端模式

        Args:
            emo_tasks: [(speaker_id, segment_index, emo_task_id), ...]

        Returns:
            [(speaker_id, segment_index, video_url or None), ...]
        """
        from modules.digital_human.factory import get_digital_human_service

        logger.info(f"[{job_id}] Processing {len(emo_tasks)} segmented EMO tasks")

        dh_service = get_digital_human_service()
        results = []

        # 逐个处理每个任务（使用工厂模式的服务）
        for i, (speaker_id, seg_idx, emo_task_id) in enumerate(emo_tasks):
            try:
                logger.info(f"[{job_id}] Processing EMO task {i+1}/{len(emo_tasks)}: {speaker_id}_seg{seg_idx}")

                # 使用工厂模式的服务等待/处理任务
                # 本地模式：直接调用 FFmpeg 生成视频
                # 云端模式：轮询阿里云 API
                video_url = await dh_service._wait_for_emo_task(
                    task_id=emo_task_id,
                    emo_task_id=emo_task_id,
                    max_attempts=max_attempts,
                    poll_interval=poll_interval
                )

                if video_url:
                    results.append((speaker_id, seg_idx, video_url))
                    logger.info(f"[{job_id}] {speaker_id}_seg{seg_idx} completed: {video_url[:50] if video_url else 'None'}...")
                else:
                    results.append((speaker_id, seg_idx, None))
                    logger.error(f"[{job_id}] {speaker_id}_seg{seg_idx} failed")

            except Exception as e:
                logger.error(f"[{job_id}] Error processing {speaker_id}_seg{seg_idx}: {e}")
                import traceback
                traceback.print_exc()
                results.append((speaker_id, seg_idx, None))

        return results

    async def _concat_digital_human_segments(
        self,
        job_id: str,
        speaker_id: str,
        video_urls: List[str]
    ) -> Optional[str]:
        """拼接数字人视频片段"""
        try:
            import httpx
            from core.config.settings import get_settings
            settings = get_settings()

            if not video_urls:
                return None

            if len(video_urls) == 1:
                # 只有一个片段，直接返回
                return video_urls[0]

            # 下载所有视频片段（支持本地路径和远程URL）
            segment_paths = []
            for i, url in enumerate(video_urls):
                segment_path = self.upload_dir / f"{job_id}_{speaker_id}_dh_seg{i}.mp4"

                # 判断是本地路径还是远程URL
                if url.startswith('/uploads/') or url.startswith('uploads/'):
                    # 本地相对路径，直接转为绝对路径
                    local_path = url.lstrip('/')
                    local_abs_path = Path(settings.BASE_DIR) / local_path if hasattr(settings, 'BASE_DIR') else Path(local_path)
                    if not local_abs_path.exists():
                        # 尝试当前目录
                        local_abs_path = Path(local_path)
                    if local_abs_path.exists():
                        segment_paths.append(str(local_abs_path))
                        logger.info(f"[{job_id}] Using local segment {i}: {local_abs_path}")
                    else:
                        logger.warning(f"[{job_id}] Local segment not found: {local_path}")
                elif url.startswith('http://') or url.startswith('https://'):
                    # 远程URL，下载
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        response = await client.get(url)
                        if response.status_code == 200:
                            with open(segment_path, 'wb') as f:
                                f.write(response.content)
                            segment_paths.append(str(segment_path))
                        else:
                            logger.warning(f"[{job_id}] Failed to download segment {i}")
                else:
                    # 可能是绝对路径
                    if Path(url).exists():
                        segment_paths.append(url)
                    else:
                        logger.warning(f"[{job_id}] Unknown URL format for segment {i}: {url}")

            if not segment_paths:
                return None

            # 创建拼接列表文件
            concat_list_path = self.upload_dir / f"{job_id}_{speaker_id}_dh_concat.txt"
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for path in segment_paths:
                    abs_path = str(Path(path).resolve()).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")

            output_path = self.upload_dir / f"{job_id}_{speaker_id}_dh_full.mp4"

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
                logger.error(f"[{job_id}] Concat digital human segments error: {stderr.decode()[:300]}")
                return None

            if not output_path.exists():
                return None

            # 上传拼接后的视频
            final_url = await self._upload_to_media_bed(str(output_path))
            logger.info(f"[{job_id}] {speaker_id} concatenated digital human: {final_url}")

            return final_url

        except Exception as e:
            logger.error(f"[{job_id}] Concat digital human segments error: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ===================== 工具方法 =====================

    async def _upload_to_media_bed(self, file_path: str) -> Optional[str]:
        """上传文件到图床，如果失败则返回本地路径"""
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

            # 上传失败，返回本地路径
            logger.warning(f"Media bed upload failed, using local path: {file_path}")
            return f"/{file_path}"

        except Exception as e:
            logger.error(f"Upload to media bed error: {e}")
            # 失败时返回本地路径作为后备
            try:
                if Path(file_path).exists():
                    logger.info(f"Falling back to local path: {file_path}")
                    return f"/{file_path}"
            except:
                pass
            return None


# 单例
_service: Optional[StoryGenerationService] = None


def get_story_generation_service() -> StoryGenerationService:
    """获取服务单例"""
    global _service
    if _service is None:
        _service = StoryGenerationService()
    return _service
