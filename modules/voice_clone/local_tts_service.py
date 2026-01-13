"""
本地 TTS 服务 - 使用 edge-tts (微软免费TTS)
用于测试业务流程，无需 GPU，无需 API key

注意：edge-tts 不支持真正的声音克隆，但提供多种预设声音
"""
import asyncio
import edge_tts
from pathlib import Path
from typing import Optional, List, Dict
import uuid


# 预设英文声音列表
ENGLISH_VOICES = {
    "male_1": "en-US-GuyNeural",      # 男声1
    "male_2": "en-US-ChristopherNeural",  # 男声2
    "female_1": "en-US-AriaNeural",    # 女声1
    "female_2": "en-US-JennyNeural",   # 女声2
    "child": "en-US-AnaNeural",        # 童声
}

# 默认声音映射（模拟声音克隆）
DEFAULT_VOICE_MAP = {
    "SPEAKER_00": "en-US-GuyNeural",      # 说话人1 用男声
    "SPEAKER_01": "en-US-AriaNeural",     # 说话人2 用女声
}


class LocalTTSService:
    """本地 TTS 服务"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path("uploads/local_tts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voice_profiles: Dict[str, str] = {}  # profile_id -> voice_name

    async def list_voices(self) -> List[dict]:
        """列出所有可用声音"""
        voices = await edge_tts.list_voices()
        # 只返回英文声音
        en_voices = [v for v in voices if v["Locale"].startswith("en-")]
        return en_voices

    async def synthesize(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        output_path: str = None
    ) -> str:
        """
        文字转语音

        Args:
            text: 要转换的文本
            voice: 声音名称
            output_path: 输出路径（可选）

        Returns:
            输出文件路径
        """
        if not output_path:
            output_path = self.output_dir / f"{uuid.uuid4().hex[:8]}.mp3"
        else:
            output_path = Path(output_path)

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))

        return str(output_path)

    async def synthesize_with_subtitles(
        self,
        text: str,
        voice: str = "en-US-AriaNeural",
        output_audio: str = None,
        output_srt: str = None
    ) -> dict:
        """
        文字转语音，同时生成字幕

        Returns:
            {"audio": audio_path, "srt": srt_path}
        """
        if not output_audio:
            base = uuid.uuid4().hex[:8]
            output_audio = self.output_dir / f"{base}.mp3"
            output_srt = self.output_dir / f"{base}.srt"

        communicate = edge_tts.Communicate(text, voice)

        # 收集字幕
        subtitles = []

        with open(output_srt, "w", encoding="utf-8") as srt_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    # 音频数据
                    pass
                elif chunk["type"] == "WordBoundary":
                    subtitles.append({
                        "offset": chunk["offset"],
                        "duration": chunk["duration"],
                        "text": chunk["text"]
                    })

        # 保存音频
        await communicate.save(str(output_audio))

        return {
            "audio": str(output_audio),
            "srt": str(output_srt),
            "subtitles": subtitles
        }

    def create_voice_profile(self, profile_id: str, voice_name: str = None) -> str:
        """
        创建声音档案（模拟声音克隆）

        实际上只是保存一个预设声音的映射
        """
        if not voice_name:
            voice_name = "en-US-AriaNeural"
        self.voice_profiles[profile_id] = voice_name
        return profile_id

    def get_voice_for_speaker(self, speaker_id: str) -> str:
        """
        获取说话人对应的声音

        Args:
            speaker_id: 说话人ID（如 SPEAKER_00）

        Returns:
            声音名称
        """
        # 优先使用自定义映射
        if speaker_id in self.voice_profiles:
            return self.voice_profiles[speaker_id]

        # 使用默认映射
        return DEFAULT_VOICE_MAP.get(speaker_id, "en-US-AriaNeural")

    async def clone_voice_from_audio(
        self,
        reference_audio: str,
        speaker_id: str = None
    ) -> str:
        """
        模拟声音克隆（实际上是根据音频特征选择最接近的预设声音）

        对于测试流程，直接返回一个预设声音
        """
        # 简单的模拟：根据 speaker_id 分配声音
        if speaker_id:
            if "00" in speaker_id:
                voice = "en-US-GuyNeural"  # 男声
            else:
                voice = "en-US-AriaNeural"  # 女声
        else:
            voice = "en-US-AriaNeural"

        profile_id = f"local_{uuid.uuid4().hex[:8]}"
        self.voice_profiles[profile_id] = voice

        return profile_id


# 全局实例
local_tts_service = LocalTTSService()


async def test():
    """测试函数"""
    service = LocalTTSService(output_dir="E:/工作代码/73_web_human/video_tests")

    # 测试基本 TTS
    print("Testing basic TTS...")
    audio_path = await service.synthesize(
        "Hello! This is a test of the local text to speech service.",
        voice="en-US-AriaNeural",
        output_path="E:/工作代码/73_web_human/video_tests/local_tts_test.mp3"
    )
    print(f"Generated: {audio_path}")

    # 测试多说话人
    print("\nTesting multi-speaker...")

    speakers = ["SPEAKER_00", "SPEAKER_01"]
    texts = [
        "Hi there! My name is John and I will be your narrator today.",
        "Hello everyone! I'm Sarah, and I'm excited to tell you this story."
    ]

    for speaker, text in zip(speakers, texts):
        voice = service.get_voice_for_speaker(speaker)
        output = f"E:/工作代码/73_web_human/video_tests/{speaker}_test.mp3"
        await service.synthesize(text, voice, output)
        print(f"{speaker} ({voice}): {output}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(test())
