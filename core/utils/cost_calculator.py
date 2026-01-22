"""
费用计算工具
阿里云 DashScope API 费用计算
"""

from typing import Dict, Tuple
from dataclasses import dataclass


# 定价常量 (元)
class Pricing:
    """阿里云 API 定价"""
    # CosyVoice TTS 定价
    TTS_PRICE_PER_10K_CHARS = 2.0  # 2元/万字符

    # EMO 定价
    EMO_DETECT_PRICE = 0.004  # 0.004元/张
    EMO_VIDEO_1_1_PRICE = 0.08  # 0.08元/秒 (1:1)
    EMO_VIDEO_3_4_PRICE = 0.16  # 0.16元/秒 (3:4)


# 限制常量
class Limits:
    """API 限制"""
    # CosyVoice 限制
    TTS_MAX_CHARS = 2000  # 单次最大字符数
    TTS_CHINESE_CHAR_WEIGHT = 2  # 1个中文字 = 2个字符

    # EMO 限制
    EMO_MAX_DURATION = 48  # 单次最大音频时长(秒)

    # 并发限制
    MAX_CONCURRENT_TASKS = 5  # 最大并发数


@dataclass
class CostDetails:
    """费用明细"""
    tts_chars: int = 0  # TTS 字符数
    tts_cost: float = 0.0  # TTS 费用

    emo_detect_count: int = 0  # 人脸检测次数
    emo_detect_cost: float = 0.0  # 人脸检测费用

    emo_video_seconds: float = 0.0  # 视频总时长(秒)
    emo_video_ratio: str = "1:1"  # 视频比例
    emo_video_cost: float = 0.0  # 视频费用

    @property
    def total_cost(self) -> float:
        """总费用"""
        return self.tts_cost + self.emo_detect_cost + self.emo_video_cost

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "tts_chars": self.tts_chars,
            "tts_cost": round(self.tts_cost, 4),
            "emo_detect_count": self.emo_detect_count,
            "emo_detect_cost": round(self.emo_detect_cost, 4),
            "emo_video_seconds": round(self.emo_video_seconds, 2),
            "emo_video_ratio": self.emo_video_ratio,
            "emo_video_cost": round(self.emo_video_cost, 4),
        }


def count_tts_chars(text: str) -> int:
    """
    计算 TTS 字符数

    阿里云规则: 1个中文字 = 2个字符
    """
    char_count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            # 中文字符
            char_count += Limits.TTS_CHINESE_CHAR_WEIGHT
        else:
            # 英文、数字、标点等
            char_count += 1
    return char_count


def calculate_tts_cost(text: str) -> Tuple[int, float]:
    """
    计算 TTS 费用

    Returns:
        (字符数, 费用)
    """
    chars = count_tts_chars(text)
    cost = (chars / 10000) * Pricing.TTS_PRICE_PER_10K_CHARS
    return chars, cost


def calculate_emo_detect_cost(count: int = 1) -> float:
    """计算 EMO 人脸检测费用"""
    return count * Pricing.EMO_DETECT_PRICE


def calculate_emo_video_cost(duration_seconds: float, ratio: str = "1:1") -> float:
    """
    计算 EMO 视频生成费用

    Args:
        duration_seconds: 视频时长(秒)
        ratio: 视频比例 "1:1" 或 "3:4"
    """
    if ratio == "3:4":
        return duration_seconds * Pricing.EMO_VIDEO_3_4_PRICE
    else:
        return duration_seconds * Pricing.EMO_VIDEO_1_1_PRICE


def split_text_for_tts(text: str, max_chars: int = Limits.TTS_MAX_CHARS) -> list:
    """
    按 TTS 字符限制切分文本

    策略:
    1. 优先在句子边界切分（。！？.!?）
    2. 其次在逗号、分号处切分
    3. 最后在空格处切分
    4. 实在不行就硬切

    Returns:
        切分后的文本列表
    """
    if count_tts_chars(text) <= max_chars:
        return [text]

    segments = []
    current_segment = ""
    current_chars = 0

    # 先按句子分割
    sentences = []
    sentence = ""
    for char in text:
        sentence += char
        if char in '。！？.!?\n':
            sentences.append(sentence)
            sentence = ""
    if sentence:
        sentences.append(sentence)

    for sentence in sentences:
        sentence_chars = count_tts_chars(sentence)

        # 如果单个句子就超长，需要进一步切分
        if sentence_chars > max_chars:
            # 先保存当前段落
            if current_segment:
                segments.append(current_segment)
                current_segment = ""
                current_chars = 0

            # 切分超长句子
            sub_segments = _split_long_sentence(sentence, max_chars)
            segments.extend(sub_segments)
        elif current_chars + sentence_chars <= max_chars:
            current_segment += sentence
            current_chars += sentence_chars
        else:
            # 当前段落已满，开始新段落
            if current_segment:
                segments.append(current_segment)
            current_segment = sentence
            current_chars = sentence_chars

    if current_segment:
        segments.append(current_segment)

    return segments


def _split_long_sentence(sentence: str, max_chars: int) -> list:
    """切分超长句子"""
    segments = []

    # 尝试在逗号、分号处切分
    parts = []
    part = ""
    for char in sentence:
        part += char
        if char in '，,；;、':
            parts.append(part)
            part = ""
    if part:
        parts.append(part)

    current_segment = ""
    current_chars = 0

    for part in parts:
        part_chars = count_tts_chars(part)

        if part_chars > max_chars:
            # 逗号分割后还是超长，硬切
            if current_segment:
                segments.append(current_segment)
                current_segment = ""
                current_chars = 0

            # 硬切
            temp = ""
            temp_chars = 0
            for char in part:
                char_weight = Limits.TTS_CHINESE_CHAR_WEIGHT if '\u4e00' <= char <= '\u9fff' else 1
                if temp_chars + char_weight > max_chars:
                    segments.append(temp)
                    temp = char
                    temp_chars = char_weight
                else:
                    temp += char
                    temp_chars += char_weight
            if temp:
                current_segment = temp
                current_chars = temp_chars
        elif current_chars + part_chars <= max_chars:
            current_segment += part
            current_chars += part_chars
        else:
            if current_segment:
                segments.append(current_segment)
            current_segment = part
            current_chars = part_chars

    if current_segment:
        segments.append(current_segment)

    return segments


def split_audio_for_emo(duration_seconds: float, max_duration: float = Limits.EMO_MAX_DURATION) -> list:
    """
    计算音频切分点

    Returns:
        切分点列表 [(start, end), ...]
    """
    if duration_seconds <= max_duration:
        return [(0, duration_seconds)]

    segments = []
    start = 0
    while start < duration_seconds:
        end = min(start + max_duration, duration_seconds)
        segments.append((start, end))
        start = end

    return segments
