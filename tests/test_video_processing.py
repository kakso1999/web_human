"""
测试视频处理功能
使用 outside_video 目录中的示例视频进行测试
"""
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.settings import get_settings
from core.utils.helpers import extract_audio_from_video, extract_video_thumbnail, get_video_duration
from core.services.apicore import get_apicore_service

settings = get_settings()

# APICore API Key
API_KEY = "sk-2lABiLDoSOocQjuwACtRWItGEEvSHM4jt0kgCQPgEb0NPS3O"


async def test_video_processing():
    """测试视频处理流程"""

    # 使用第一个示例视频
    video_path = r"E:\工作代码\73_web_human\outside_video\睡前故事\01b0e46e57fe34607ae9e4e37e1f3a44.mp4"

    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return

    print(f"Testing with video: {video_path}")
    print("=" * 50)

    # 1. 测试获取视频时长
    print("\n[1] Getting video duration...")
    duration = get_video_duration(video_path)
    print(f"    Duration: {duration} seconds")

    # 2. ��试提取缩略图
    print("\n[2] Extracting thumbnail...")
    thumbnail_path = os.path.join(settings.UPLOAD_DIR, "test_thumbnail.jpg")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    if extract_video_thumbnail(video_path, thumbnail_path, time_seconds=10):
        print(f"    Thumbnail saved to: {thumbnail_path}")
    else:
        print("    Failed to extract thumbnail")

    # 3. 测试提取音频
    print("\n[3] Extracting audio...")
    audio_path = os.path.join(settings.UPLOAD_DIR, "test_audio.mp3")

    if extract_audio_from_video(video_path, audio_path):
        print(f"    Audio saved to: {audio_path}")
        audio_size = os.path.getsize(audio_path)
        print(f"    Audio size: {audio_size / 1024:.2f} KB")
    else:
        print("    Failed to extract audio")
        return

    # 4. 测试语音转文字
    print("\n[4] Transcribing audio with Whisper...")
    apicore = get_apicore_service(API_KEY)

    try:
        transcription = await apicore.transcribe_audio(audio_path, response_format="verbose_json")

        subtitle_text = transcription.get("text", "")
        segments = transcription.get("segments", [])

        print(f"    Transcription successful!")
        print(f"    Full text ({len(subtitle_text)} chars):")
        print(f"    {subtitle_text[:500]}...")
        print(f"\n    Segments: {len(segments)}")

        if segments:
            print("    First 3 segments:")
            for seg in segments[:3]:
                print(f"      [{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s]: {seg.get('text', '')[:50]}...")
    except Exception as e:
        print(f"    Transcription failed: {e}")
        return

    # 5. 测试生成英文标题
    print("\n[5] Generating English title with Gemini...")
    try:
        title_en = await apicore.generate_title(subtitle_text)
        print(f"    Generated title: {title_en}")
    except Exception as e:
        print(f"    Title generation failed: {e}")

    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_video_processing())
