"""
APICore 服务
提供语音转文字、AI 文本生成等功能
"""
import httpx
import os
from typing import Optional, Dict, Any
from core.config.settings import get_settings

settings = get_settings()


class APICoreService:
    """APICore API 服务"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.APICORE_API_KEY
        self.base_url = settings.APICORE_BASE_URL

    async def transcribe_audio(self, audio_path: str, response_format: str = "verbose_json") -> Dict[str, Any]:
        """
        语音转文字（使用 Whisper 模型）

        Args:
            audio_path: 音频文件路径
            response_format: 响应格式 (json, text, srt, verbose_json, vtt)

        Returns:
            转写结果
        """
        url = f"{self.base_url}/v1/audio/transcriptions"

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
                }
                data = {
                    "model": "whisper-1",
                    "response_format": response_format,
                    "temperature": 0
                }

                response = await client.post(
                    url,
                    files=files,
                    data=data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )

                if response.status_code != 200:
                    raise Exception(f"Transcription failed: {response.status_code} - {response.text}")

                return response.json()

    async def generate_title(self, subtitle_text: str) -> str:
        """
        使用 Gemini 2.5 Flash 生成英文标题

        Args:
            subtitle_text: 字幕文本（故事内容）

        Returns:
            生成的英文标题
        """
        url = f"{self.base_url}/v1/chat/completions"

        prompt = f"""Based on the following story content (subtitles), generate a short, catchy English title for this children's story.
The title should be:
- Short (2-6 words)
- Child-friendly
- Descriptive of the main theme or character
- Engaging and memorable

Story content:
{subtitle_text[:3000]}

Respond with ONLY the title, nothing else."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 50
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Title generation failed: {response.status_code} - {response.text}")

            result = response.json()
            # 提取生成的标题
            title = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return title.strip().strip('"\'')

    async def generate_chinese_title(self, subtitle_text: str) -> str:
        """
        使用 Gemini 2.5 Flash 生成中文标题

        Args:
            subtitle_text: 字幕文本（故事内容）

        Returns:
            生成的中文标题
        """
        url = f"{self.base_url}/v1/chat/completions"

        prompt = f"""根据以下故事内容（字幕），为这个儿童故事生成一个简短、吸引人的中文标题。
标题要求：
- 简短（3-10个字）
- 适合儿童
- 描述主题或主角
- 吸引人、好记

故事内容：
{subtitle_text[:3000]}

只回复标题本身，不要加任何其他内容。"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 50
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Chinese title generation failed: {response.status_code} - {response.text}")

            result = response.json()
            # 提取生成的标题
            title = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return title.strip().strip('"\'《》')

    async def generate_description(self, subtitle_text: str) -> str:
        """
        使用 Gemini 2.5 Flash 生成英文描述

        Args:
            subtitle_text: 字幕文本（故事内容）

        Returns:
            生成的英文描述
        """
        url = f"{self.base_url}/v1/chat/completions"

        prompt = f"""Based on the following story content (subtitles), generate a brief English description for this children's story.
The description should be:
- 1-2 sentences (50-100 words)
- Child-friendly and engaging
- Summarize the main plot or theme
- Appeal to parents looking for stories for their children

Story content:
{subtitle_text[:3000]}

Respond with ONLY the description, nothing else."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Description generation failed: {response.status_code} - {response.text}")

            result = response.json()
            # 提取生成的描述
            desc = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return desc.strip().strip('"\'')


# 服务单例
_apicore_service: Optional[APICoreService] = None


def get_apicore_service(api_key: Optional[str] = None) -> APICoreService:
    """获取 APICore 服务实例"""
    global _apicore_service
    if _apicore_service is None or api_key:
        _apicore_service = APICoreService(api_key)
    return _apicore_service
