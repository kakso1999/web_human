"""
语音分离服务

整合自 94_人声分离模型2 项目

流程：
1. 从视频提取音频 (FFmpeg)
2. 使用 Demucs (htdemucs) 分离人声/背景
3. 使用 Pyannote speaker-diarization-3.1 进行说话人识别（仅双人模式）
4. 提取各说话人独立音轨（仅双人模式）

支持两种分析模式：
- 单人模式：人声整体 + 背景音（不进行说话人分割）
- 双人模式：说话人1 + 说话人2 + 背景音（最多2个说话人）
"""
import os
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.config.settings import get_settings
from core.utils import get_ffmpeg_path

settings = get_settings()
logger = logging.getLogger(__name__)


def run_ffmpeg_sync(cmd: List[str]) -> tuple:
    """同步执行 FFmpeg 命令"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode, result.stdout, result.stderr


class VoiceSeparationService:
    """语音分离服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.hf_token = getattr(settings, 'HF_TOKEN', None)
        self.upload_dir = Path(settings.UPLOAD_DIR) / "voice_separation"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.media_bed_url = settings.MEDIA_BED_URL

    # ===================== 核心方法 =====================

    async def analyze_story_audio(
        self,
        story_id: str,
        video_path: str,
        num_speakers: int = None
    ) -> Dict[str, Any]:
        """
        分析故事音频，识别说话人

        Args:
            story_id: 故事 ID
            video_path: 视频文件路径
            num_speakers: 预设说话人数量 (None 为自动检测)

        Returns:
            {
                "speaker_count": 2,
                "speakers": [
                    {"speaker_id": "SPEAKER_00", "duration": 120.5, "audio_url": "..."},
                    {"speaker_id": "SPEAKER_01", "duration": 85.3, "audio_url": "..."}
                ],
                "background_audio_url": "...",
                "segments": [...]
            }
        """
        print(f"[{story_id}] Starting audio analysis")
        logger.info(f"[{story_id}] Starting audio analysis")

        if not self.hf_token:
            raise ValueError("HF_TOKEN not configured")

        # 创建输出目录
        output_dir = self.upload_dir / story_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: 提取音频
            logger.info(f"[{story_id}] Step 1: Extracting audio from video")
            audio_path = await self._extract_audio(video_path, output_dir / "extracted_audio.wav")

            # Step 2: 分离人声和背景
            logger.info(f"[{story_id}] Step 2: Separating vocals and background")
            separation_result = await self._separate_vocals(
                str(audio_path),
                str(output_dir / "separated")
            )

            # Step 3: 说话人分割
            logger.info(f"[{story_id}] Step 3: Speaker diarization")
            segments = await self._diarize_speakers(
                separation_result["vocals"],
                num_speakers
            )

            # 保存分割结果
            segments_path = output_dir / "diarization_segments.json"
            with open(segments_path, "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)

            # Step 3.5: 分析说话人比例，判断是否实际为单人
            # 如果主说话人占比超过80%，则判定为单人模式
            speaker_durations = {}
            for seg in segments:
                spk = seg["speaker"]
                dur = seg["end"] - seg["start"]
                speaker_durations[spk] = speaker_durations.get(spk, 0) + dur

            total_speech_duration = sum(speaker_durations.values())
            unique_speakers = list(speaker_durations.keys())

            # 检查是否应该切换到单人模式
            if len(unique_speakers) >= 2 and total_speech_duration > 0:
                # 按时长排序
                sorted_speakers = sorted(speaker_durations.items(), key=lambda x: x[1], reverse=True)
                dominant_speaker, dominant_duration = sorted_speakers[0]
                dominant_ratio = dominant_duration / total_speech_duration

                logger.info(f"[{story_id}] Speaker ratio analysis: {dict(speaker_durations)}")
                logger.info(f"[{story_id}] Dominant speaker: {dominant_speaker}, ratio: {dominant_ratio:.2%}")

                if dominant_ratio >= 0.80:
                    # 主说话人占比超过80%，切换到单人模式
                    logger.info(f"[{story_id}] Dominant speaker ratio {dominant_ratio:.2%} >= 80%, switching to single-speaker mode")

                    # 上传人声和背景音到媒体床
                    vocals_url = await self._upload_to_media_bed(separation_result["vocals"])
                    background_url = await self._upload_to_media_bed(separation_result["background"])

                    # 计算人声总时长
                    import soundfile as sf
                    audio, sr = sf.read(separation_result["vocals"])
                    vocals_duration = len(audio) / sr

                    # 返回单人模式结果结构
                    result = {
                        "speaker_count": 1,
                        "speakers": [{
                            "speaker_id": "SPEAKER_00",
                            "label": "说话人 1",
                            "gender": "unknown",
                            "audio_url": vocals_url,
                            "duration": round(vocals_duration, 2)
                        }],
                        "background_audio_url": background_url,
                        "segments": segments,  # 保留原始分割信息用于调试
                        "single_speaker_mode": True,  # 标记为自动切换的单人模式
                        "dominant_ratio": round(dominant_ratio, 4)
                    }

                    logger.info(f"[{story_id}] Auto-switched to single-speaker mode")
                    return result

            # Step 4: 提取各说话人音轨（多说话人模式）
            logger.info(f"[{story_id}] Step 4: Extracting speaker tracks")
            speaker_tracks = await self._extract_speaker_tracks(
                separation_result["vocals"],
                segments,
                str(output_dir / "speakers"),
                separation_result["sample_rate"]
            )

            # 上传到媒体床
            background_url = await self._upload_to_media_bed(separation_result["background"])

            speakers = []
            for speaker_id, audio_path in speaker_tracks.items():
                audio_url = await self._upload_to_media_bed(audio_path)
                duration = self._calculate_speaker_duration(segments, speaker_id)
                speakers.append({
                    "speaker_id": speaker_id,
                    "label": self._get_default_label(speaker_id),
                    "gender": "unknown",  # 后续可以添加性别检测
                    "audio_url": audio_url,
                    "duration": duration
                })

            # 按时长排序
            speakers.sort(key=lambda x: x["duration"], reverse=True)

            result = {
                "speaker_count": len(speakers),
                "speakers": speakers,
                "background_audio_url": background_url,
                "segments": segments
            }

            logger.info(f"[{story_id}] Analysis completed: {len(speakers)} speakers detected")
            return result

        except Exception as e:
            logger.error(f"[{story_id}] Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def analyze_single_speaker(
        self,
        story_id: str,
        video_path: str
    ) -> Dict[str, Any]:
        """
        单人模式分析：只分离人声和背景音

        不进行说话人分割，将所有人声作为一个整体。
        适用于：用同一个声音和头像替换所有人声。

        Args:
            story_id: 故事 ID
            video_path: 视频文件路径

        Returns:
            {
                "vocals_url": "...",
                "background_url": "...",
                "duration": 120.5,
                "is_analyzed": True
            }
        """
        print(f"[{story_id}] Starting single-speaker analysis")
        logger.info(f"[{story_id}] Starting single-speaker analysis")

        # 创建输出目录
        output_dir = self.upload_dir / story_id / "single"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: 提取音频
            logger.info(f"[{story_id}] Single: Extracting audio from video")
            audio_path = await self._extract_audio(video_path, output_dir / "extracted_audio.wav")

            # Step 2: 分离人声和背景
            logger.info(f"[{story_id}] Single: Separating vocals and background")
            separation_result = await self._separate_vocals(
                str(audio_path),
                str(output_dir / "separated")
            )

            # 计算人声时长
            import soundfile as sf
            audio, sr = sf.read(separation_result["vocals"])
            duration = len(audio) / sr

            # Step 3: 语音转录（词级时间戳）
            logger.info(f"[{story_id}] Single: Transcribing audio with word timestamps")
            # 使用原始提取的音频进行转录（质量更好）
            transcription = await self._transcribe_audio(story_id, str(audio_path))

            # 上传到媒体床
            vocals_url = await self._upload_to_media_bed(separation_result["vocals"])
            background_url = await self._upload_to_media_bed(separation_result["background"])

            result = {
                "vocals_url": vocals_url,
                "background_url": background_url,
                "duration": round(duration, 2),
                "transcription": transcription,  # 包含 text, words, segments
                "is_analyzed": True
            }

            logger.info(f"[{story_id}] Single-speaker analysis completed, duration: {duration:.2f}s, words: {len(transcription.get('words', [])) if transcription else 0}")
            return result

        except Exception as e:
            logger.error(f"[{story_id}] Single-speaker analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def analyze_dual_speaker(
        self,
        story_id: str,
        video_path: str,
        num_speakers: int = 2
    ) -> Dict[str, Any]:
        """
        双人模式分析：分离人声、背景音，并进行说话人分割

        最多识别2个说话人，为每个说话人分离独立音轨。
        适用于：为爸爸和妈妈分别配置不同的声音和头像。

        Args:
            story_id: 故事 ID
            video_path: 视频文件路径
            num_speakers: 说话人数量（默认2，最大2）

        Returns:
            {
                "speakers": [...],
                "background_url": "...",
                "diarization_segments": [...],
                "is_analyzed": True
            }
        """
        print(f"[{story_id}] Starting dual-speaker analysis")
        logger.info(f"[{story_id}] Starting dual-speaker analysis")

        if not self.hf_token:
            raise ValueError("HF_TOKEN not configured")

        # 创建输出目录
        output_dir = self.upload_dir / story_id / "dual"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: 提取音频
            logger.info(f"[{story_id}] Dual: Extracting audio from video")
            audio_path = await self._extract_audio(video_path, output_dir / "extracted_audio.wav")

            # Step 2: 分离人声和背景
            logger.info(f"[{story_id}] Dual: Separating vocals and background")
            separation_result = await self._separate_vocals(
                str(audio_path),
                str(output_dir / "separated")
            )

            # Step 3: 说话人分割
            logger.info(f"[{story_id}] Dual: Speaker diarization")
            segments = await self._diarize_speakers(
                separation_result["vocals"],
                min(num_speakers, 2)  # 强制最多2人
            )

            # 保存分割结果
            segments_path = output_dir / "diarization_segments.json"
            with open(segments_path, "w", encoding="utf-8") as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)

            # Step 3.5: 分析说话人比例，判断是否实际为单人
            # 如果主说话人占比超过80%，则判定为单人模式
            speaker_durations = {}
            for seg in segments:
                spk = seg["speaker"]
                dur = seg["end"] - seg["start"]
                speaker_durations[spk] = speaker_durations.get(spk, 0) + dur

            total_speech_duration = sum(speaker_durations.values())
            unique_speakers = list(speaker_durations.keys())

            # 检查是否应该切换到单人模式
            if len(unique_speakers) >= 2 and total_speech_duration > 0:
                # 按时长排序
                sorted_speakers = sorted(speaker_durations.items(), key=lambda x: x[1], reverse=True)
                dominant_speaker, dominant_duration = sorted_speakers[0]
                dominant_ratio = dominant_duration / total_speech_duration

                logger.info(f"[{story_id}] Speaker ratio analysis: {dict(speaker_durations)}")
                logger.info(f"[{story_id}] Dominant speaker: {dominant_speaker}, ratio: {dominant_ratio:.2%}")

                if dominant_ratio >= 0.80:
                    # 主说话人占比超过80%，切换到单人模式
                    logger.info(f"[{story_id}] Dominant speaker ratio {dominant_ratio:.2%} >= 80%, returning single-speaker result")

                    # 上传人声和背景音到媒体床
                    vocals_url = await self._upload_to_media_bed(separation_result["vocals"])
                    background_url = await self._upload_to_media_bed(separation_result["background"])

                    # 计算人声总时长
                    import soundfile as sf
                    audio, sr = sf.read(separation_result["vocals"])
                    vocals_duration = len(audio) / sr

                    # 返回单人模式结果结构（只有一个说话人）
                    # 前端会根据 speakers.length <= 1 判断为单人模式
                    result = {
                        "speakers": [{
                            "speaker_id": "SPEAKER_00",
                            "label": "说话人 1",
                            "gender": "unknown",
                            "audio_url": vocals_url,
                            "duration": round(vocals_duration, 2)
                        }],
                        "background_url": background_url,
                        "diarization_segments": [
                            {"start": seg["start"], "end": seg["end"], "speaker": seg["speaker"]}
                            for seg in segments
                        ],
                        "is_analyzed": True,
                        "single_speaker_mode": True,  # 标记为自动切换的单人模式
                        "dominant_ratio": round(dominant_ratio, 4)
                    }

                    logger.info(f"[{story_id}] Auto-switched to single-speaker mode (1 speaker)")
                    return result

            # Step 4: 提取各说话人音轨（多说话人模式）
            logger.info(f"[{story_id}] Dual: Extracting speaker tracks")
            speaker_tracks = await self._extract_speaker_tracks(
                separation_result["vocals"],
                segments,
                str(output_dir / "speakers"),
                separation_result["sample_rate"]
            )

            # 上传到媒体床
            background_url = await self._upload_to_media_bed(separation_result["background"])

            speakers = []
            for speaker_id, audio_path_str in speaker_tracks.items():
                audio_url = await self._upload_to_media_bed(audio_path_str)
                duration = self._calculate_speaker_duration(segments, speaker_id)
                speakers.append({
                    "speaker_id": speaker_id,
                    "label": self._get_default_label(speaker_id),
                    "gender": "unknown",
                    "audio_url": audio_url,
                    "duration": duration
                })

            # 按时长排序
            speakers.sort(key=lambda x: x["duration"], reverse=True)

            # 转换 diarization_segments 格式
            diarization_segments = [
                {"start": seg["start"], "end": seg["end"], "speaker": seg["speaker"]}
                for seg in segments
            ]

            result = {
                "speakers": speakers,
                "background_url": background_url,
                "diarization_segments": diarization_segments,
                "is_analyzed": True
            }

            logger.info(f"[{story_id}] Dual-speaker analysis completed: {len(speakers)} speakers detected")
            return result

        except Exception as e:
            logger.error(f"[{story_id}] Dual-speaker analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def analyze_both_modes(
        self,
        story_id: str,
        video_path: str
    ) -> Dict[str, Any]:
        """
        同时执行单人和双人两种模式的分析

        管理员上传故事后调用此方法，准备好两种模式的数据。
        用户生成时可以选择使用哪种模式。

        Args:
            story_id: 故事 ID
            video_path: 视频文件路径

        Returns:
            {
                "single_speaker_analysis": {...},
                "dual_speaker_analysis": {...}
            }
        """
        print(f"[{story_id}] Starting both-modes analysis")
        logger.info(f"[{story_id}] Starting both-modes analysis")

        single_result = None
        dual_result = None
        errors = []

        # 并行执行两种分析
        try:
            # 单人模式分析
            print(f"[{story_id}] Running single-speaker analysis...")
            single_result = await self.analyze_single_speaker(story_id, video_path)
        except Exception as e:
            logger.error(f"[{story_id}] Single-speaker analysis failed: {e}")
            errors.append(f"Single: {str(e)}")

        try:
            # 双人模式分析
            print(f"[{story_id}] Running dual-speaker analysis...")
            dual_result = await self.analyze_dual_speaker(story_id, video_path)
        except Exception as e:
            logger.error(f"[{story_id}] Dual-speaker analysis failed: {e}")
            errors.append(f"Dual: {str(e)}")

        result = {
            "single_speaker_analysis": single_result,
            "dual_speaker_analysis": dual_result,
            "errors": errors if errors else None
        }

        logger.info(f"[{story_id}] Both-modes analysis completed. Single: {single_result is not None}, Dual: {dual_result is not None}")
        return result

    # ===================== 私有方法 =====================

    async def _extract_audio(self, video_path: str, output_path: Path) -> Path:
        """从视频提取音频"""
        import os

        print(f"[DEBUG] video_path: {video_path}")
        print(f"[DEBUG] video_path exists: {os.path.exists(video_path)}")
        print(f"[DEBUG] output_path: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            get_ffmpeg_path(), "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(output_path)
        ]

        print(f"[DEBUG] FFmpeg command: {' '.join(cmd)}")

        returncode, stdout, stderr = await asyncio.to_thread(run_ffmpeg_sync, cmd)

        print(f"[DEBUG] FFmpeg returncode: {returncode}")
        if returncode != 0:
            print(f"[DEBUG] FFmpeg stderr: {stderr.decode()[:1000]}")

        if returncode != 0:
            raise Exception(f"FFmpeg error: {stderr.decode()[:500]}")

        logger.info(f"Audio extracted: {output_path}")
        return output_path

    async def _separate_vocals(self, audio_path: str, output_dir: str) -> Dict[str, Any]:
        """使用 Demucs 分离人声和背景"""

        def _separate_sync():
            import torch
            import soundfile as sf
            import numpy as np
            from demucs.pretrained import get_model
            from demucs.apply import apply_model

            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)

            # 加载模型
            print("加载 demucs 模型 (htdemucs)...")
            model = get_model("htdemucs")
            model.eval()

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model.to(device)
            print(f"使用设备: {device}")

            # 加载音频
            print("加载音频...")
            audio, sr = sf.read(audio_path)

            # 转换为 torch tensor
            if audio.ndim == 1:
                waveform = torch.from_numpy(audio).float().unsqueeze(0).repeat(2, 1)
            else:
                waveform = torch.from_numpy(audio.T).float()
                if waveform.shape[0] == 1:
                    waveform = waveform.repeat(2, 1)

            # 重采样
            if sr != model.samplerate:
                import torchaudio.functional as F
                waveform = F.resample(waveform, sr, model.samplerate)

            waveform = waveform.unsqueeze(0).to(device)

            # 分离
            print("正在分离音频...")
            with torch.no_grad():
                sources = apply_model(model, waveform, device=device)

            source_names = model.sources
            vocals_idx = source_names.index("vocals")

            vocals = sources[0, vocals_idx].cpu()
            background = sources[0, [i for i in range(len(source_names)) if i != vocals_idx]].sum(dim=0).cpu()

            # 保存
            vocals_path = output_dir_path / "vocals.wav"
            background_path = output_dir_path / "background.wav"

            sf.write(str(vocals_path), vocals.numpy().T, model.samplerate)
            sf.write(str(background_path), background.numpy().T, model.samplerate)

            print(f"人声已保存: {vocals_path}")
            print(f"背景音已保存: {background_path}")

            return {
                "vocals": str(vocals_path),
                "background": str(background_path),
                "sample_rate": model.samplerate
            }

        return await asyncio.to_thread(_separate_sync)

    async def _diarize_speakers(
        self,
        audio_path: str,
        num_speakers: int = None
    ) -> List[Dict[str, Any]]:
        """
        使用 Pyannote 进行说话人分割

        注意：强制限制为最多2个说话人（男声/女声）
        """

        def _diarize_sync():
            import torch
            import soundfile as sf
            from pyannote.audio import Pipeline

            print("加载 pyannote 说话人分割模型...")
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self.hf_token
            )

            if torch.cuda.is_available():
                pipeline.to(torch.device("cuda"))
                print("使用 GPU 进行说话人分割")
            else:
                print("使用 CPU 进行说话人分割")

            # 预加载音频（绕过 torchcodec 问题）
            print("加载音频...")
            audio, sr = sf.read(audio_path)

            if audio.ndim == 1:
                waveform = torch.from_numpy(audio).float().unsqueeze(0)
            else:
                waveform = torch.from_numpy(audio.T).float()

            audio_input = {"waveform": waveform, "sample_rate": sr}

            # 强制限制为最多2个说话人（男声/女声）
            # 无论传入什么参数，都使用 min(num_speakers, 2) 或默认 2
            max_speakers = 2
            if num_speakers:
                effective_speakers = min(num_speakers, max_speakers)
            else:
                effective_speakers = max_speakers

            print(f"正在进行说话人分割 (限制为 {effective_speakers} 个说话人)...")
            diarization = pipeline(audio_input, num_speakers=effective_speakers)

            # 兼容不同版本的 pyannote 返回结构
            segments = []
            try:
                # 新版格式: DiarizeOutput 直接有 itertracks 方法
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    segments.append({
                        "start": turn.start,
                        "end": turn.end,
                        "speaker": speaker
                    })
            except AttributeError:
                # 旧版格式: 需要访问 speaker_diarization 属性
                annotation = diarization.speaker_diarization
                for turn, _, speaker in annotation.itertracks(yield_label=True):
                    segments.append({
                        "start": turn.start,
                        "end": turn.end,
                        "speaker": speaker
                    })

            speaker_count = len(set(s['speaker'] for s in segments))
            print(f"检测到 {speaker_count} 个说话人 (已限制为最多2个)")
            print(f"共 {len(segments)} 个语音片段")

            return segments

        return await asyncio.to_thread(_diarize_sync)

    async def _extract_speaker_tracks(
        self,
        audio_path: str,
        segments: List[Dict],
        output_dir: str,
        sample_rate: int = 16000
    ) -> Dict[str, str]:
        """提取各说话人独立音轨"""

        def _extract_sync():
            import soundfile as sf
            import numpy as np

            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)

            audio, sr = sf.read(audio_path)

            # 按说话人分组
            speakers = {}
            for seg in segments:
                speaker = seg["speaker"]
                if speaker not in speakers:
                    speakers[speaker] = []
                speakers[speaker].append(seg)

            result = {}
            for speaker, segs in speakers.items():
                speaker_audio = np.zeros_like(audio)

                for seg in segs:
                    start_sample = int(seg["start"] * sr)
                    end_sample = int(seg["end"] * sr)
                    start_sample = max(0, start_sample)
                    end_sample = min(len(audio), end_sample)
                    speaker_audio[start_sample:end_sample] = audio[start_sample:end_sample]

                output_path = output_dir_path / f"{speaker}.wav"
                sf.write(str(output_path), speaker_audio, sr)

                result[speaker] = str(output_path)
                logger.info(f"Speaker {speaker} track saved: {output_path}")

            return result

        return await asyncio.to_thread(_extract_sync)

    def _calculate_speaker_duration(
        self,
        segments: List[Dict],
        speaker_id: str
    ) -> float:
        """计算说话人总时长"""
        total = 0.0
        for seg in segments:
            if seg["speaker"] == speaker_id:
                total += seg["end"] - seg["start"]
        return round(total, 2)

    async def generate_speaker_subtitles(
        self,
        story_id: str,
        speaker_id: str,
        audio_path: str,
        diarization_segments: List[Dict],
        model_size: str = "base",
        language: str = None  # None = 自动检测语言
    ) -> List[Dict]:
        """
        为指定说话人生成词级字幕

        使用 subprocess 运行 Whisper，避免 CUDA + asyncio.to_thread 的兼容性问题
        """
        import json
        import subprocess
        import sys
        import tempfile
        import os
        from core.config.settings import HF_CACHE_DIR

        # 准备临时文件
        segments_file = os.path.join(tempfile.gettempdir(), f"segments_{story_id}_{speaker_id}.json")
        output_file = os.path.join(tempfile.gettempdir(), f"subtitles_{story_id}_{speaker_id}.json")

        # 过滤该说话人的片段
        speaker_segments = [s for s in diarization_segments if s["speaker"] == speaker_id]
        with open(segments_file, 'w', encoding='utf-8') as f:
            json.dump(speaker_segments, f)

        print(f"[{speaker_id}] 启动 Whisper 子进程 (model: {model_size})...", flush=True)

        # 创建子进程脚本
        # language 参数: None = 自动检测, "en" = 英语, "zh" = 中文
        lang_param = f'"{language}"' if language else 'None'
        script = f'''
import sys
import os
import json
from faster_whisper import WhisperModel
import soundfile as sf
import numpy as np
import torch

speaker_id = "{speaker_id}"
audio_path = r"{audio_path}"
segments_file = r"{segments_file}"
output_file = r"{output_file}"
model_size = "{model_size}"
language = {lang_param}

# 设置 HuggingFace 缓存目录 (使用项目内缓存)
hf_cache_dir = r"{str(HF_CACHE_DIR)}"
os.environ['HF_HOME'] = hf_cache_dir
os.environ['HF_HUB_CACHE'] = os.path.join(hf_cache_dir, 'hub')
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

# 检测是否有 GPU
use_cuda = torch.cuda.is_available()
device = "cuda" if use_cuda else "cpu"
compute_type = "float16" if use_cuda else "int8"

print(f"[{{speaker_id}}] 加载 Whisper 模型 ({{model_size}}, device={{device}})...", flush=True)
# 使用完整模型名称以支持自动下载
full_model_name = f"Systran/faster-whisper-{{model_size}}"
model = WhisperModel(full_model_name, device=device, compute_type=compute_type)

print(f"[{{speaker_id}}] 加载音频: {{audio_path}}", flush=True)
audio, sr = sf.read(audio_path)
print(f"[{{speaker_id}}] 音频形状: {{audio.shape}}, 采样率: {{sr}}", flush=True)

if audio.ndim > 1:
    audio = audio.mean(axis=1)
    print(f"[{{speaker_id}}] 音频已转为单声道", flush=True)
audio = audio.astype(np.float32)

with open(segments_file, 'r') as f:
    speaker_segments = json.load(f)
print(f"[{{speaker_id}}] 共 {{len(speaker_segments)}} 个语音片段", flush=True)

subtitles = []
for i, seg in enumerate(speaker_segments):
    start_time = seg["start"]
    end_time = seg["end"]

    start_sample = int(start_time * sr)
    end_sample = int(end_time * sr)
    segment_audio = audio[start_sample:end_sample]

    if len(segment_audio) < sr * 0.1:
        continue

    segments_result, info = model.transcribe(
        segment_audio, language=language, word_timestamps=True, vad_filter=True
    )

    for segment in segments_result:
        subtitle = {{
            "index": len(subtitles),
            "speaker_id": speaker_id,
            "start_time": round(start_time + segment.start, 3),
            "end_time": round(start_time + segment.end, 3),
            "text": segment.text.strip(),
            "words": []
        }}

        if segment.words:
            for word in segment.words:
                subtitle["words"].append({{
                    "word": word.word.strip(),
                    "start": round(start_time + word.start, 3),
                    "end": round(start_time + word.end, 3)
                }})

        if subtitle["text"]:
            subtitles.append(subtitle)

    if (i + 1) % 10 == 0:
        print(f"[{{speaker_id}}] 已处理 {{i + 1}}/{{len(speaker_segments)}} 个片段", flush=True)

print(f"[{{speaker_id}}] 字幕生成完成，共 {{len(subtitles)}} 条", flush=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(subtitles, f, ensure_ascii=False)

print(f"[{{speaker_id}}] 结果已保存到: {{output_file}}", flush=True)
'''

        # 运行子进程
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-c", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        # 实时打印输出 (处理 Windows 编码问题)
        async for line in process.stdout:
            try:
                decoded = line.decode('utf-8', errors='replace').rstrip()
                # 过滤掉非 ASCII 字符避免 Windows GBK 编码问题
                ascii_safe = decoded.encode('ascii', errors='replace').decode('ascii')
                print(ascii_safe, flush=True)
            except Exception:
                pass  # 忽略打印错误

        await process.wait()

        # 即使进程崩溃，也尝试读取结果（因为结果在崩溃前已保存）
        # Windows 上 faster-whisper 在退出时可能会崩溃，但结果已保存
        if not os.path.exists(output_file):
            raise Exception(f"Whisper subprocess failed with code {process.returncode}, no output file")

        # 读取结果
        print(f"[{speaker_id}] 子进程完成 (exit: {process.returncode})，读取结果...", flush=True)
        with open(output_file, 'r', encoding='utf-8') as f:
            subtitles = json.load(f)

        # 清理临时文件
        os.remove(segments_file)
        os.remove(output_file)

        print(f"[{speaker_id}] 返回 {len(subtitles)} 条字幕", flush=True)
        return subtitles

    async def generate_all_speaker_subtitles(
        self,
        story_id: str,
        speakers: List[Dict],
        diarization_segments: List[Dict],
        base_path: str
    ) -> Dict[str, List[Dict]]:
        """
        为所有说话人生成词级字幕

        Returns:
            {
                "SPEAKER_00": [...subtitles...],
                "SPEAKER_01": [...subtitles...],
                "ALL": [...merged subtitles...]
            }
        """
        all_subtitles = {}

        for speaker in speakers:
            speaker_id = speaker["speaker_id"]
            audio_path = f"{base_path}/speakers/{speaker_id}.wav"

            print(f"[{story_id}] 为 {speaker_id} 生成字幕...", flush=True)
            try:
                subtitles = await self.generate_speaker_subtitles(
                    story_id=story_id,
                    speaker_id=speaker_id,
                    audio_path=audio_path,
                    diarization_segments=diarization_segments
                )
                print(f"[{story_id}] {speaker_id} 返回了 {len(subtitles) if subtitles else 0} 条字幕", flush=True)
                all_subtitles[speaker_id] = subtitles
                print(f"[{story_id}] {speaker_id} 已添加到结果字典", flush=True)
            except Exception as e:
                print(f"[{story_id}] {speaker_id} 错误: {type(e).__name__}: {e}", flush=True)
                import traceback
                traceback.print_exc()
                all_subtitles[speaker_id] = []

        # 合并所有字幕（按时间排序）
        print(f"[{story_id}] 开始合并字幕...", flush=True)
        merged = []
        for speaker_id, subs in all_subtitles.items():
            print(f"[{story_id}] 合并 {speaker_id}: {len(subs)} 条", flush=True)
            merged.extend(subs)

        print(f"[{story_id}] 排序 {len(merged)} 条字幕...", flush=True)
        merged.sort(key=lambda x: x["start_time"])

        # 重新编号
        for i, sub in enumerate(merged):
            sub["index"] = i

        all_subtitles["ALL"] = merged

        print(f"[{story_id}] 字幕生成完成，共 {len(merged)} 条", flush=True)
        return all_subtitles

    def _get_default_label(self, speaker_id: str) -> str:
        """获取默认标签"""
        # SPEAKER_00 -> 说话人 1 (男声)
        # SPEAKER_01 -> 说话人 2 (女声)
        try:
            num = int(speaker_id.split("_")[1])
            if num == 0:
                return "说话人 1"
            elif num == 1:
                return "说话人 2"
            else:
                return f"说话人 {num + 1}"
        except:
            return speaker_id

    async def _upload_to_media_bed(self, file_path: str) -> Optional[str]:
        """上传到媒体床，失败则返回本地路径"""
        try:
            import httpx

            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return None

            # 先尝试上传到媒体床
            suffix = file_path_obj.suffix.lower()
            content_type = "audio/wav" if suffix == ".wav" else "audio/mpeg"

            with open(file_path, 'rb') as f:
                file_content = f.read()

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.media_bed_url}/upload",
                        files={"file": (file_path_obj.name, file_content, content_type)}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        relative_url = result.get("url")
                        if relative_url:
                            return f"{self.media_bed_url}{relative_url}"
            except Exception as e:
                print(f"[WARN] Media bed upload failed: {e}, using local path")

            # 媒体床失败，返回本地相对路径
            # 将绝对路径转为相对 URL
            file_path_str = str(file_path_obj).replace("\\", "/")
            if "uploads" in file_path_str:
                # split 后可能有前导斜杠，需要去除
                relative_part = file_path_str.split("uploads", 1)[1].lstrip("/")
                return f"/uploads/{relative_part}"

            return None

        except Exception as e:
            logger.error(f"Upload error: {e}")
            return None

    async def _transcribe_audio(
        self,
        story_id: str,
        audio_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        使用 faster-whisper 进行词级转录

        Returns:
            {
                "text": "完整文本",
                "words": [{"word": "Hi", "start": 12.1, "end": 12.3}, ...],
                "segments": [{"start": 12.1, "end": 17.3, "text": "..."}, ...]
            }
        """
        logger.info(f"[{story_id}] Starting audio transcription with word timestamps")
        print(f"[{story_id}] Starting audio transcription...", flush=True)

        try:
            def transcribe_sync():
                import os
                import numpy as np
                import soundfile as sf
                from core.config.settings import HF_CACHE_DIR

                # 设置 HuggingFace 缓存目录
                os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
                os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
                os.environ['DO_NOT_TRACK'] = '1'
                os.environ['HF_HOME'] = str(HF_CACHE_DIR)
                os.environ['HF_HUB_CACHE'] = str(HF_CACHE_DIR / 'hub')

                from faster_whisper import WhisperModel

                # 尝试使用本地缓存的模型
                model_path = HF_CACHE_DIR / 'hub' / 'models--Systran--faster-whisper-base' / 'snapshots'
                local_files_only = False

                if model_path.exists():
                    snapshot_dirs = list(model_path.glob('*'))
                    if snapshot_dirs:
                        model_path = str(snapshot_dirs[0])
                        local_files_only = True
                        print(f"[{story_id}] Using cached Whisper model")
                    else:
                        model_path = "Systran/faster-whisper-base"
                        print(f"[{story_id}] Downloading Whisper model...")
                else:
                    model_path = "Systran/faster-whisper-base"
                    print(f"[{story_id}] Downloading Whisper model...")

                # 强制使用 CPU 避免 CUDA 上下文清理问题
                model = WhisperModel(model_path, device="cpu", compute_type="int8", local_files_only=local_files_only)
                print(f"[{story_id}] Whisper model loaded (CPU mode)")

                # 加载音频
                audio, sr = sf.read(audio_path)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                audio = audio.astype(np.float32)

                # Whisper 期望 16kHz 采样率
                TARGET_SR = 16000
                if sr != TARGET_SR:
                    import librosa
                    print(f"[{story_id}] Resampling from {sr}Hz to {TARGET_SR}Hz")
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=TARGET_SR)
                    sr = TARGET_SR

                print(f"[{story_id}] Audio loaded: duration={len(audio)/sr:.2f}s")

                # 转写
                segments_gen, info = model.transcribe(
                    audio,
                    language="en",
                    word_timestamps=True,
                    vad_filter=False,
                    condition_on_previous_text=False,
                    no_speech_threshold=0.6,
                    compression_ratio_threshold=2.4
                )

                # 收集结果
                all_text = []
                all_words = []
                all_segments = []

                for seg in segments_gen:
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

                print(f"[{story_id}] Transcription complete: {len(all_segments)} segments, {len(all_words)} words")

                return {
                    "text": " ".join(all_text).strip(),
                    "words": all_words,
                    "segments": all_segments
                }

            result = await asyncio.to_thread(transcribe_sync)
            logger.info(f"[{story_id}] Transcription completed successfully")
            return result

        except Exception as e:
            logger.error(f"[{story_id}] Transcription failed: {e}")
            import traceback
            traceback.print_exc()
            return None


# 单例
_service: Optional[VoiceSeparationService] = None


def get_voice_separation_service() -> VoiceSeparationService:
    """获取服务单例"""
    global _service
    if _service is None:
        _service = VoiceSeparationService()
    return _service
