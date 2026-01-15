"""
Local Voice Clone Service - 本地声音克隆服务
使用 SpeechT5 + SpeechBrain 实现本地声音克隆
"""

import os
import asyncio
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import torch
import soundfile as sf
import numpy as np

from .base import BaseVoiceCloneService
from core.config.settings import get_settings

settings = get_settings()

# 任务状态存储
local_voice_clone_tasks: Dict[str, dict] = {}


class LocalVoiceCloneService(BaseVoiceCloneService):
    """本地声音克隆服务 - 使用 SpeechT5 + SpeechBrain"""

    _instance = None
    _models_loaded = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.upload_dir = Path(settings.UPLOAD_DIR) / "voice_clones"
        self.references_dir = self.upload_dir / "references"
        self.previews_dir = self.upload_dir / "previews"

        # 确保目录存在
        self.references_dir.mkdir(parents=True, exist_ok=True)
        self.previews_dir.mkdir(parents=True, exist_ok=True)

        # 模型相关
        self.processor = None
        self.tts_model = None
        self.vocoder = None
        self.speaker_model = None
        self.device = "cpu"

        # 缓存已提取的 speaker embeddings
        self._embedding_cache: Dict[str, torch.Tensor] = {}

    def _convert_local_path_to_url(self, local_path: str) -> str:
        """
        将本地文件路径转换为可访问的 URL 路径

        例如:
        - E:\\工作代码\\73_web_human\\uploads\\voice_clones\\references\\user_xxx.wav
        - 转换为: /uploads/voice_clones/references/user_xxx.wav
        """
        if not local_path:
            return ""

        # 统一路径分隔符
        normalized_path = local_path.replace("\\", "/")

        # 方法1: 查找 uploads 目录的位置
        if "/uploads/" in normalized_path:
            idx = normalized_path.find("/uploads/")
            return normalized_path[idx:]

        # 方法2: 查找 voice_clones 目录
        if "voice_clones" in normalized_path:
            idx = normalized_path.find("voice_clones")
            return "/uploads/" + normalized_path[idx:]

        # 方法3: 使用配置的 UPLOAD_DIR 进行替换
        from core.config.settings import get_settings
        settings = get_settings()
        upload_dir = settings.UPLOAD_DIR.replace("\\", "/")

        if normalized_path.startswith(upload_dir):
            relative_path = normalized_path[len(upload_dir):]
            if not relative_path.startswith("/"):
                relative_path = "/" + relative_path
            return "/uploads" + relative_path

        # 如果路径中包含 uploads，尝试提取
        if "uploads" in normalized_path:
            idx = normalized_path.find("uploads")
            return "/" + normalized_path[idx:]

        # 最后的回退: 返回原路径（可能无法访问，但至少有值）
        return normalized_path

    async def check_service_health(self) -> bool:
        """检查服务是否可用"""
        try:
            if not self._models_loaded:
                return True  # 模型可延迟加载
            return self.processor is not None and self.tts_model is not None
        except Exception:
            return False

    def _load_models(self):
        """加载 TTS 模型（延迟加载）"""
        if self._models_loaded:
            return

        print("[LocalVoiceClone] Loading TTS models...")
        start = time.time()

        try:
            # 设置 HuggingFace 镜像
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

            from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
            from speechbrain.inference import EncoderClassifier

            self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
            self.tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
            self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

            self.speaker_model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-xvect-voxceleb",
                savedir="pretrained_models/spkrec-xvect-voxceleb",
                run_opts={"device": self.device}
            )

            self._models_loaded = True
            print(f"[LocalVoiceClone] Models loaded in {time.time() - start:.1f}s")

        except Exception as e:
            print(f"[LocalVoiceClone] Failed to load models: {e}")
            raise

    def _extract_speaker_embedding(self, audio_path: str) -> torch.Tensor:
        """从音频提取说话人嵌入"""
        import librosa

        # 检查缓存
        cache_key = str(audio_path)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        audio, sr = sf.read(str(audio_path))

        # 转单声道
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # 重采样到 16kHz
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        # 只取前30秒
        max_samples = 16000 * 30
        if len(audio) > max_samples:
            audio = audio[:max_samples]

        # 提取嵌入
        audio_tensor = torch.tensor(audio).float().unsqueeze(0)
        embedding = self.speaker_model.encode_batch(audio_tensor).squeeze()

        # 调整到 512 维
        if embedding.shape[-1] != 512:
            if embedding.shape[-1] < 512:
                repeats = 512 // embedding.shape[-1] + 1
                embedding = embedding.repeat(repeats)[:512]
            else:
                embedding = embedding[:512]

        embedding = embedding.unsqueeze(0)

        # 缓存
        self._embedding_cache[cache_key] = embedding
        return embedding

    def _synthesize_text(self, speaker_embedding: torch.Tensor, text: str) -> Optional[np.ndarray]:
        """合成单段文本"""
        if not text or len(text.strip()) < 2:
            return None

        try:
            inputs = self.processor(text=text, return_tensors="pt")
            with torch.no_grad():
                speech = self.tts_model.generate_speech(
                    inputs["input_ids"],
                    speaker_embedding,
                    vocoder=self.vocoder
                )
            return speech.numpy()
        except Exception as e:
            print(f"[LocalVoiceClone] Synth error: {e}")
            return None

    async def generate_preview(
        self,
        task_id: str,
        reference_audio_path: str,
        text: str
    ) -> None:
        """生成语音克隆预览"""
        try:
            local_voice_clone_tasks[task_id]["status"] = "processing"
            local_voice_clone_tasks[task_id]["progress"] = 10

            # 加载模型
            await asyncio.to_thread(self._load_models)
            local_voice_clone_tasks[task_id]["progress"] = 30

            # 提取说话人嵌入
            print(f"[{task_id}] Extracting speaker embedding...")
            speaker_embedding = await asyncio.to_thread(
                self._extract_speaker_embedding, reference_audio_path
            )
            local_voice_clone_tasks[task_id]["progress"] = 50

            # 合成语音
            print(f"[{task_id}] Synthesizing speech...")
            audio = await asyncio.to_thread(
                self._synthesize_text, speaker_embedding, text
            )
            local_voice_clone_tasks[task_id]["progress"] = 80

            if audio is None:
                raise Exception("Speech synthesis failed")

            # 保存音频
            output_filename = f"{task_id}.wav"
            output_path = self.previews_dir / output_filename
            sf.write(str(output_path), audio, 16000)

            local_voice_clone_tasks[task_id]["status"] = "completed"
            local_voice_clone_tasks[task_id]["progress"] = 100
            local_voice_clone_tasks[task_id]["audio_url"] = f"/uploads/voice_clones/previews/{output_filename}"
            local_voice_clone_tasks[task_id]["completed_at"] = datetime.utcnow()
            local_voice_clone_tasks[task_id]["reference_audio_local"] = reference_audio_path

            print(f"[{task_id}] Voice clone completed: {output_path}")

        except Exception as e:
            print(f"[{task_id}] Voice clone failed: {e}")
            import traceback
            traceback.print_exc()

            local_voice_clone_tasks[task_id]["status"] = "failed"
            local_voice_clone_tasks[task_id]["error"] = str(e)
            local_voice_clone_tasks[task_id]["progress"] = 0

    def create_task(self, user_id: str) -> str:
        """创建新任务"""
        task_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

        local_voice_clone_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "audio_url": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "completed_at": None
        }

        return task_id

    def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        return local_voice_clone_tasks.get(task_id)

    def save_reference_audio(self, user_id: str, file_content: bytes, filename: str) -> str:
        """保存参考音频"""
        ext = Path(filename).suffix or ".wav"
        new_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.references_dir / new_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    async def save_voice_profile(self, user_id: str, task_id: str, name: str) -> Optional[dict]:
        """保存声音档案"""
        from .repository import voice_profile_repository

        task = local_voice_clone_tasks.get(task_id)
        if not task or task.get("status") != "completed":
            return None

        if not task_id.startswith(user_id):
            return None

        # 本地模式下，将本地路径转换为相对 URL 路径
        reference_audio_local = task.get("reference_audio_local", "")
        reference_audio_url = self._convert_local_path_to_url(reference_audio_local)

        profile_data = {
            "user_id": user_id,
            "name": name,
            "voice_id": f"local_{task_id}",  # 本地模式没有云端 voice_id
            "reference_audio_url": reference_audio_url,
            "reference_audio_local": reference_audio_local,
            "preview_audio_url": task.get("audio_url"),
            "status": "active",
            "service_mode": "local"  # 标记为本地模式
        }

        profile_id = await voice_profile_repository.create(profile_data)
        profile_data["id"] = profile_id

        return profile_data

    async def get_user_voice_profiles(self, user_id: str) -> list:
        """获取用户声音档案"""
        from .repository import voice_profile_repository
        return await voice_profile_repository.get_by_user_id(user_id)

    async def get_voice_profile(self, profile_id: str, user_id: str) -> Optional[dict]:
        """获取单个声音档案"""
        from .repository import voice_profile_repository
        profile = await voice_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return profile
        return None

    async def update_voice_profile(self, profile_id: str, user_id: str, name: str) -> bool:
        """更新声音档案"""
        from .repository import voice_profile_repository
        profile = await voice_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            return await voice_profile_repository.update(profile_id, {"name": name})
        return False

    async def delete_voice_profile(self, profile_id: str, user_id: str) -> bool:
        """删除声音档案"""
        from .repository import voice_profile_repository
        profile = await voice_profile_repository.get_by_id(profile_id)
        if profile and profile.get("user_id") == user_id:
            # 清除嵌入缓存
            ref_audio = profile.get("reference_audio_local")
            if ref_audio and ref_audio in self._embedding_cache:
                del self._embedding_cache[ref_audio]
            return await voice_profile_repository.delete(profile_id)
        return False

    async def preload_model(self) -> None:
        """预加载模型"""
        try:
            await asyncio.to_thread(self._load_models)
            print("[LocalVoiceClone] Models preloaded successfully")
        except Exception as e:
            print(f"[LocalVoiceClone] Model preload failed: {e}")

    async def synthesize_speech(
        self,
        voice_profile_id: str,
        text: str,
        output_path: str
    ) -> Optional[str]:
        """使用声音档案合成语音"""
        try:
            from .repository import voice_profile_repository

            profile = await voice_profile_repository.get_by_id(voice_profile_id)
            if not profile:
                print(f"[LocalVoiceClone] Voice profile not found: {voice_profile_id}")
                return None

            ref_audio = profile.get("reference_audio_local")
            if not ref_audio or not Path(ref_audio).exists():
                print(f"[LocalVoiceClone] Reference audio not found")
                return None

            await asyncio.to_thread(self._load_models)

            speaker_embedding = await asyncio.to_thread(
                self._extract_speaker_embedding, ref_audio
            )

            audio = await asyncio.to_thread(
                self._synthesize_text, speaker_embedding, text
            )

            if audio is None:
                return None

            sf.write(output_path, audio, 16000)
            return output_path

        except Exception as e:
            print(f"[LocalVoiceClone] Synthesize error: {e}")
            return None

    async def clone_audio_with_text(
        self,
        reference_audio_path: str,
        text: str,
        output_path: str
    ) -> Optional[str]:
        """使用参考音频克隆语音（不保存档案）"""
        try:
            await asyncio.to_thread(self._load_models)

            speaker_embedding = await asyncio.to_thread(
                self._extract_speaker_embedding, reference_audio_path
            )

            audio = await asyncio.to_thread(
                self._synthesize_text, speaker_embedding, text
            )

            if audio is None:
                return None

            sf.write(output_path, audio, 16000)
            return output_path

        except Exception as e:
            print(f"[LocalVoiceClone] Clone error: {e}")
            return None

    async def clone_full_audio(
        self,
        reference_audio_path: str,
        segments: list,
        output_path: str,
        sample_rate: int = 16000
    ) -> Optional[str]:
        """
        克隆完整音频（多段文本按时间戳合成）

        Args:
            reference_audio_path: 参考音频路径
            segments: 分段列表 [{"start": float, "end": float, "text": str}, ...]
            output_path: 输出路径
            sample_rate: 采样率

        Returns:
            输出文件路径
        """
        try:
            await asyncio.to_thread(self._load_models)

            speaker_embedding = await asyncio.to_thread(
                self._extract_speaker_embedding, reference_audio_path
            )

            # 计算总时长
            if segments:
                max_end = max(seg.get("end", 0) for seg in segments)
            else:
                max_end = 0

            total_samples = int(max_end * sample_rate) + sample_rate  # 加1秒缓冲
            output_audio = np.zeros(total_samples)

            for seg in segments:
                text = seg.get("text", "").strip()
                if not text or len(text) < 2:
                    continue

                audio = await asyncio.to_thread(
                    self._synthesize_text, speaker_embedding, text
                )

                if audio is not None:
                    start_sample = int(seg["start"] * sample_rate)
                    end_sample = start_sample + len(audio)

                    if end_sample > len(output_audio):
                        audio = audio[:len(output_audio) - start_sample]

                    if start_sample < len(output_audio):
                        output_audio[start_sample:start_sample + len(audio)] = audio

            sf.write(output_path, output_audio, sample_rate)
            return output_path

        except Exception as e:
            print(f"[LocalVoiceClone] Clone full audio error: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ==================== 兼容云端接口的方法 ====================
    # 这些方法是为了兼容 story_generation 模块调用云端 CosyVoice API 的代码
    # 本地模式下，使用 SpeechT5 进行语音合成

    async def _create_voice(self, task_id: str, audio_url: str) -> Optional[str]:
        """
        创建音色（本地兼容版）

        本地模式下，下载参考音频并存储路径，返回本地 voice_id
        后续合成时使用该 voice_id 对应的音频提取说话人特征

        Args:
            task_id: 任务ID
            audio_url: 音频 URL 或本地路径

        Returns:
            voice_id 或 None
        """
        import httpx
        import shutil

        try:
            # 初始化存储
            self._local_voices = getattr(self, '_local_voices', {})

            from core.config.settings import get_settings
            settings = get_settings()
            voice_dir = os.path.join(settings.UPLOAD_DIR, 'voice_clone', 'local_voices')
            os.makedirs(voice_dir, exist_ok=True)

            voice_id = f"local_{task_id}_{int(asyncio.get_event_loop().time())}"
            audio_path = os.path.join(voice_dir, f"{voice_id}.wav")

            # 检查是否是本地路径
            is_local_path = not audio_url.startswith(('http://', 'https://'))

            if is_local_path:
                # 本地路径处理
                local_path = audio_url
                # 处理以 / 开头的相对路径
                if local_path.startswith('/'):
                    local_path = local_path.lstrip('/')
                # 如果不是绝对路径，拼接工作目录
                if not os.path.isabs(local_path):
                    local_path = os.path.join(os.getcwd(), local_path)

                if not os.path.exists(local_path):
                    print(f"[LocalVoiceClone] Local audio file not found: {local_path}")
                    return None

                print(f"[LocalVoiceClone] Using local reference audio: {local_path}")
                # 复制文件到 voice_dir
                shutil.copy2(local_path, audio_path)

            else:
                # HTTP URL 处理
                async with httpx.AsyncClient(timeout=60.0) as client:
                    print(f"[LocalVoiceClone] Downloading reference audio: {audio_url[:80]}...")
                    response = await client.get(audio_url)
                    if response.status_code != 200:
                        print(f"[LocalVoiceClone] Failed to download audio: {response.status_code}")
                        return None

                with open(audio_path, 'wb') as f:
                    f.write(response.content)

            # 存储映射关系
            self._local_voices[voice_id] = audio_path
            print(f"[LocalVoiceClone] Created local voice: {voice_id}")

            return voice_id

        except Exception as e:
            print(f"[LocalVoiceClone] Create voice error: {e}")
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
        等待音色准备完成（本地兼容版）

        本地模式下，音色在 _create_voice 返回后立即可用，
        所以这里直接返回 True

        Args:
            task_id: 任务ID
            voice_id: voice_id
            max_attempts: 最大尝试次数（忽略）
            poll_interval: 轮询间隔（忽略）

        Returns:
            True 表示音色已准备好
        """
        # 本地模式下，音色在创建后立即可用
        self._local_voices = getattr(self, '_local_voices', {})

        if voice_id in self._local_voices:
            audio_path = self._local_voices[voice_id]
            if os.path.exists(audio_path):
                print(f"[LocalVoiceClone] Voice {voice_id} is ready")
                return True

        print(f"[LocalVoiceClone] Voice {voice_id} not found in local voices")
        return False

    async def synthesize_with_voice_id(
        self,
        voice_id: str,
        text: str,
        output_path: str
    ) -> Optional[str]:
        """
        使用 voice_id 合成语音（本地兼容版）

        Args:
            voice_id: 本地 voice_id (由 _create_voice 返回)
            text: 要合成的文本
            output_path: 输出路径

        Returns:
            输出文件路径 或 None
        """
        try:
            # 获取参考音频路径
            self._local_voices = getattr(self, '_local_voices', {})
            reference_path = self._local_voices.get(voice_id)

            if not reference_path or not os.path.exists(reference_path):
                print(f"[LocalVoiceClone] Voice not found: {voice_id}")
                return None

            # 使用已有的克隆方法
            return await self.clone_audio_with_text(
                reference_audio_path=reference_path,
                text=text,
                output_path=output_path
            )

        except Exception as e:
            print(f"[LocalVoiceClone] Synthesize with voice_id error: {e}")
            return None
