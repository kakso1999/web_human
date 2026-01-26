"""
APIMart API 客户端
封装 Whisper-1 和 Gemini API 调用
"""
import os
import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WhisperResult:
    """Whisper 转录结果"""
    text: str
    language: str
    duration: float
    words: List[Dict[str, Any]]  # [{"word": "xxx", "start": 1.0, "end": 1.5}, ...]


@dataclass
class SpeakerSegment:
    """说话人分段"""
    start: float
    end: float
    voice: str  # VOICE_1 or VOICE_2
    text: str


@dataclass
class SpeakerAnalysisResult:
    """说话人分析结果"""
    title: str
    title_en: str
    description: str
    description_en: str
    original_speakers: List[Dict[str, str]]  # [{"id": "NARRATOR", "description": "旁白"}]
    dual_voice_assignment: Dict[str, List[str]]  # {"VOICE_1": ["NARRATOR"], "VOICE_2": [...]}
    segments: List[SpeakerSegment]


class APIMartClient:
    """APIMart API 客户端"""

    BASE_URL = "https://api.apimart.ai/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("APIMART_API_KEY")
        if not self.api_key:
            raise ValueError("APIMART_API_KEY is required")

        self.base_url = self.BASE_URL

        # 禁用代理，增加超时和重试
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(300.0, connect=60.0),  # 5分钟超时，连接60秒
            headers={"Authorization": f"Bearer {self.api_key}"},
            proxy=None,  # 禁用代理
            transport=httpx.AsyncHTTPTransport(retries=3)  # 自动重试3次
        )

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ==================== Whisper-1 API ====================

    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "en",
        response_format: str = "verbose_json"
    ) -> WhisperResult:
        """
        使用 Whisper-1 转录音频

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (en, zh, etc.)
            response_format: 响应格式 (json, text, srt, vtt, verbose_json)

        Returns:
            WhisperResult: 转录结果，包含词级时间戳
        """
        url = f"{self.base_url}/audio/transcriptions"

        with open(audio_path, 'rb') as f:
            files = {'file': (os.path.basename(audio_path), f, 'audio/mpeg')}
            data = {
                'model': 'whisper-1',
                'response_format': response_format,
                'language': language,
                'timestamp_granularities[]': 'word'
            }

            logger.info(f"Calling Whisper-1 API for: {audio_path}")
            response = await self.client.post(url, files=files, data=data)

        if response.status_code != 200:
            logger.error(f"Whisper API error: {response.text}")
            raise Exception(f"Whisper API error: {response.status_code} - {response.text}")

        result = response.json()

        return WhisperResult(
            text=result.get('text', ''),
            language=result.get('language', language),
            duration=result.get('duration', 0),
            words=result.get('words', [])
        )

    # ==================== Gemini API ====================

    async def analyze_speakers(
        self,
        transcript_with_timestamps: str,
        story_language: str = "en"
    ) -> SpeakerAnalysisResult:
        """
        使用 Gemini 分析字幕中的说话人

        Args:
            transcript_with_timestamps: 带时间戳的字幕文本
            story_language: 故事语言

        Returns:
            SpeakerAnalysisResult: 说话人分析结果
        """
        url = f"{self.base_url}/chat/completions"

        # 构建提示词
        prompt = self._build_speaker_analysis_prompt(transcript_with_timestamps, story_language)

        payload = {
            "model": "gemini-2.0-flash",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "stream": False
        }

        logger.info("Calling Gemini API for speaker analysis")
        response = await self.client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            logger.error(f"Gemini API error: {response.text}")
            raise Exception(f"Gemini API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result['choices'][0]['message']['content']
        analysis = json.loads(content)

        # 解析分段
        segments = [
            SpeakerSegment(
                start=seg['start'],
                end=seg['end'],
                voice=seg['voice'],
                text=seg['text']
            )
            for seg in analysis.get('segments', [])
        ]

        return SpeakerAnalysisResult(
            title=analysis.get('title', ''),
            title_en=analysis.get('title_en', ''),
            description=analysis.get('description', ''),
            description_en=analysis.get('description_en', ''),
            original_speakers=analysis.get('original_speakers', []),
            dual_voice_assignment=analysis.get('dual_voice_assignment', {}),
            segments=segments
        )

    def _build_speaker_analysis_prompt(self, transcript: str, language: str) -> str:
        """Build speaker analysis prompt (English output)"""

        return f"""You are a professional subtitle analysis expert. Analyze the following children's story subtitles and complete these tasks:

1. Identify all speakers in the story (narrator, characters, etc.)
2. Intelligently assign all speakers to two voice roles (for parent dubbing)
3. Generate story title and description in English

Assignment principles:
- VOICE_1: Usually assigned to narrator and main male characters
- VOICE_2: Usually assigned to main female characters and secondary characters
- If there's only one speaker, assign all to VOICE_1
- Maintain dialogue continuity as much as possible

Subtitle content:
{transcript}

Return in JSON format as follows:
{{
    "title": "Story Title in English",
    "title_en": "Story Title in English",
    "description": "Story description in English, 50-100 words",
    "description_en": "Story description in English, 50-100 words",
    "original_speakers": [
        {{"speaker_id": "NARRATOR", "description": "Narrator/Storyteller"}},
        {{"speaker_id": "CHARACTER_XXX", "description": "Character description"}}
    ],
    "dual_voice_assignment": {{
        "VOICE_1": ["NARRATOR", "CHARACTER_XXX"],
        "VOICE_2": ["CHARACTER_YYY"]
    }},
    "segments": [
        {{"start": 6.8, "end": 13.2, "voice": "VOICE_1", "text": "Text content..."}},
        {{"start": 25.0, "end": 30.5, "voice": "VOICE_2", "text": "Text content..."}}
    ]
}}

Important:
1. The start/end times in segments must match the input subtitle timestamps
2. Each segment's text is the complete text for that time period
3. Return ONLY JSON, no other explanations
4. All titles and descriptions MUST be in English"""

    # ==================== 辅助方法 ====================

    @staticmethod
    def format_words_for_analysis(words: List[Dict], max_segments: int = 100) -> str:
        """
        将词级时间戳格式化为便于 AI 分析的文本

        Args:
            words: Whisper 返回的词列表
            max_segments: 最大分段数（避免提示词过长）

        Returns:
            格式化的字幕文本
        """
        if not words:
            return ""

        # 按句子边界分组
        segments = []
        current_segment = []
        current_start = None

        for word in words:
            if current_start is None:
                current_start = word['start']
            current_segment.append(word['word'])

            # 遇到句号、问号、感叹号，结束当前片段
            if word['word'].rstrip().endswith(('.', '?', '!', '。', '？', '！')):
                segments.append({
                    'start': current_start,
                    'end': word['end'],
                    'text': ' '.join(current_segment)
                })
                current_segment = []
                current_start = None

            # 如果句子太长（超过50个词），也切分
            elif len(current_segment) >= 50:
                segments.append({
                    'start': current_start,
                    'end': word['end'],
                    'text': ' '.join(current_segment)
                })
                current_segment = []
                current_start = None

        # 处理剩余部分
        if current_segment:
            segments.append({
                'start': current_start,
                'end': words[-1]['end'],
                'text': ' '.join(current_segment)
            })

        # 限制分段数量
        if len(segments) > max_segments:
            segments = segments[:max_segments]

        # 格式化输出
        lines = []
        for seg in segments:
            lines.append(f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")

        return "\n".join(lines)


# 便捷函数
async def get_apimart_client() -> APIMartClient:
    """获取 APIMart 客户端实例"""
    return APIMartClient()
