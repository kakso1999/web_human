"""
APICore 客户端

封装 APICore 服务的 API 调用：
- Suno Stems: 人声/背景音分离
- Whisper: 语音识别 + SRT 字幕
- Suno Timing: 词级时间对齐
"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any, List
from core.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class APICoreSunoError(Exception):
    """APICore Suno API 错误"""
    pass


class APICoreWhisperError(Exception):
    """APICore Whisper API 错误"""
    pass


class APICoreClient:
    """APICore API 客户端"""

    def __init__(self):
        self.base_url = settings.APICORE_BASE_URL.rstrip("/")
        self.api_key = settings.APICORE_API_KEY
        self.timeout = httpx.Timeout(300.0)  # 5 分钟超时

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        # 如果有 files 参数，不设置 Content-Type，让 httpx 自动处理
        if "files" in kwargs:
            headers.pop("Content-Type", None)

        logger.info(f"APICore request: {method} {url}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )

            logger.info(f"APICore response: {response.status_code}")
            logger.debug(f"Response text: {response.text[:500] if response.text else 'empty'}")

            if response.status_code != 200:
                logger.error(f"APICore request failed: {response.status_code} - {response.text}")
                raise Exception(f"APICore request failed: {response.status_code} - {response.text}")

            return response

    # ===================== Suno APIs =====================

    async def upload_audio_url(self, audio_url: str) -> Dict[str, Any]:
        """
        上传音频 URL 获取 clip_id

        Args:
            audio_url: 音频文件 URL

        Returns:
            {"clip_id": "...", "task_id": "..."}
        """
        logger.info(f"Uploading audio URL to Suno: {audio_url}")

        response = await self._make_request(
            method="POST",
            endpoint="/suno/uploads/audio-url",
            json={"url": audio_url}
        )

        result = response.json()
        logger.info(f"Upload response: {result}")
        return result

    async def get_stems(
        self,
        clip_id: str,
        max_retries: int = 30,
        retry_interval: int = 10
    ) -> Dict[str, str]:
        """
        获取人声分离结果

        Args:
            clip_id: 音频 clip ID
            max_retries: 最大重试次数
            retry_interval: 重试间隔 (秒)

        Returns:
            {"vocals": "url", "instrumental": "url"}
        """
        logger.info(f"Getting stems for clip: {clip_id}")

        for attempt in range(max_retries):
            try:
                response = await self._make_request(
                    method="GET",
                    endpoint=f"/suno/act/stems/{clip_id}"
                )

                result = response.json()
                logger.info(f"Stems response: {result}")

                # 检查是否完成
                if result.get("vocals") and result.get("instrumental"):
                    return {
                        "vocals": result["vocals"],
                        "instrumental": result["instrumental"]
                    }

                # 如果还在处理中，等待后重试
                if result.get("status") == "processing":
                    logger.info(f"Stems still processing, retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(retry_interval)
                    continue

                # 其他情况
                logger.warning(f"Unexpected stems response: {result}")
                await asyncio.sleep(retry_interval)

            except Exception as e:
                logger.error(f"Error getting stems: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_interval)
                else:
                    raise APICoreSunoError(f"Failed to get stems after {max_retries} retries")

        raise APICoreSunoError(f"Stems processing timeout after {max_retries} retries")

    async def get_timing(self, clip_id: str) -> List[Dict[str, Any]]:
        """
        获取词级时间对齐

        Args:
            clip_id: 音频 clip ID

        Returns:
            [{"word": "...", "start_s": 0.0, "end_s": 1.0}, ...]
        """
        logger.info(f"Getting timing for clip: {clip_id}")

        response = await self._make_request(
            method="GET",
            endpoint=f"/suno/act/timing/{clip_id}"
        )

        result = response.json()
        logger.info(f"Timing response: {len(result.get('words', []))} words")
        return result.get("words", [])

    # ===================== Whisper APIs =====================

    async def transcribe_audio(
        self,
        audio_file: bytes,
        filename: str = "audio.mp3",
        response_format: str = "srt",
        language: str = "zh"
    ) -> str:
        """
        语音识别生成字幕

        Args:
            audio_file: 音频文件字节
            filename: 文件名
            response_format: 输出格式 (srt, vtt, json, text, verbose_json)
            language: 语言代码

        Returns:
            SRT/VTT 格式字幕内容 或 JSON
        """
        logger.info(f"Transcribing audio: {filename}, format: {response_format}")

        response = await self._make_request(
            method="POST",
            endpoint="/v1/audio/transcriptions",
            files={"file": (filename, audio_file)},
            data={
                "model": "whisper-1",
                "response_format": response_format,
                "language": language
            }
        )

        if response_format in ["json", "verbose_json"]:
            return response.json()
        else:
            return response.text

    async def transcribe_audio_url(
        self,
        audio_url: str,
        response_format: str = "srt",
        language: str = "zh"
    ) -> str:
        """
        从 URL 下载音频并转录

        Args:
            audio_url: 音频 URL
            response_format: 输出格式
            language: 语言

        Returns:
            字幕内容
        """
        logger.info(f"Downloading audio from URL: {audio_url}")

        # 先下载音频
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(audio_url)
            if response.status_code != 200:
                raise APICoreWhisperError(f"Failed to download audio: {response.status_code}")
            audio_bytes = response.content

        # 转录
        return await self.transcribe_audio(
            audio_file=audio_bytes,
            filename="audio.mp3",
            response_format=response_format,
            language=language
        )


# 单例
_client: Optional[APICoreClient] = None


def get_apicore_client() -> APICoreClient:
    """获取 APICore 客户端单例"""
    global _client
    if _client is None:
        _client = APICoreClient()
    return _client
