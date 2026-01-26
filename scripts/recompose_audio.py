"""
重新合成克隆音频 - 使用正确的时间戳

用现有的 TTS 片段重新构建完整时长的克隆音频
"""
import asyncio
import subprocess
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def merge_words_to_segments(words, max_gap=0.7, max_duration=10.0):
    """将词合并为句子段（与 service.py 相同的逻辑）"""
    if not words:
        return []

    segments = []
    current_segment = {
        "start_time": words[0].get("start", 0),
        "end_time": words[0].get("end", 0),
        "text": words[0].get("word", "")
    }

    for i in range(1, len(words)):
        word = words[i]
        word_start = word.get("start", 0)
        word_end = word.get("end", 0)
        word_text = word.get("word", "")

        gap = word_start - current_segment["end_time"]
        duration = word_end - current_segment["start_time"]

        if gap > max_gap or duration > max_duration:
            segments.append(current_segment)
            current_segment = {
                "start_time": word_start,
                "end_time": word_end,
                "text": word_text
            }
        else:
            current_segment["end_time"] = word_end
            current_segment["text"] += " " + word_text

    segments.append(current_segment)

    # 添加索引
    for i, seg in enumerate(segments):
        seg["index"] = i + 1

    return segments


def assign_speakers(segments, diarization_segments):
    """为每个段分配说话人"""
    for seg in segments:
        seg_mid = (seg["start_time"] + seg["end_time"]) / 2

        # 找最佳匹配的 diarization 段
        best_speaker = "SPEAKER_00"
        best_overlap = 0

        for dia in diarization_segments:
            dia_start = dia.get("start", 0)
            dia_end = dia.get("end", 0)

            # 计算重叠
            overlap_start = max(seg["start_time"], dia_start)
            overlap_end = min(seg["end_time"], dia_end)
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = dia.get("speaker", "SPEAKER_00")

        seg["speaker"] = best_speaker

    return segments


async def recompose_audio(job_id: str, story_id: str):
    """重新合成克隆音频"""
    from core.config.database import Database
    from core.database.mongodb import get_database
    from bson import ObjectId

    await Database.connect()
    db = get_database()

    try:
        # 获取故事信息
        story = await db['stories'].find_one({'_id': ObjectId(story_id)})
        if not story:
            print(f"[ERROR] Story not found: {story_id}")
            return

        # 获取视频时长
        video_url = story.get('video_url', '')
        video_path = 'uploads' + video_url.replace('/uploads', '') if video_url.startswith('/uploads') else None

        if not video_path or not os.path.exists(video_path):
            print(f"[ERROR] Video not found: {video_path}")
            return

        # 获取视频时长
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True, text=True
        )
        video_duration = float(result.stdout.strip())
        print(f"视频时长: {video_duration:.2f}s")

        # 读取转录数据
        transcription_path = f"uploads/story_generation/{job_id}_transcription.json"
        if not os.path.exists(transcription_path):
            print(f"[ERROR] Transcription not found: {transcription_path}")
            return

        with open(transcription_path, 'r', encoding='utf-8') as f:
            transcription = json.load(f)

        words = transcription.get('words', [])
        print(f"转录词数: {len(words)}")

        # 合并为段
        segments = merge_words_to_segments(words, max_gap=0.7, max_duration=10.0)
        print(f"合并后段数: {len(segments)}")

        # 获取说话人分割信息
        dual_analysis = story.get('dual_speaker_analysis', {})
        diarization_segments = dual_analysis.get('diarization_segments', [])
        print(f"说话人分割段数: {len(diarization_segments)}")

        # 分配说话人
        segments = assign_speakers(segments, diarization_segments)

        # 检查现有的 TTS 片段
        upload_dir = Path('uploads/story_generation')

        for speaker in ['SPEAKER_00', 'SPEAKER_01']:
            # 获取该说话人的段
            speaker_segments = [s for s in segments if s.get('speaker') == speaker]
            print(f"\n{speaker}: {len(speaker_segments)} 个段")

            # 找到所有该说话人的 TTS 片段
            tts_files = sorted(upload_dir.glob(f"{job_id}_{speaker}_sub*.mp3"),
                               key=lambda x: int(x.stem.split('_sub')[-1]))

            if not tts_files:
                print(f"  [WARN] No TTS files found")
                continue

            print(f"  TTS 文件: {len(tts_files)} 个")

            if len(tts_files) != len(speaker_segments):
                print(f"  [WARN] TTS 文件数 ({len(tts_files)}) != 段数 ({len(speaker_segments)})")
                # 使用较小的数量
                count = min(len(tts_files), len(speaker_segments))
            else:
                count = len(tts_files)

            # 构建带时间戳的片段列表
            segment_files = []
            for i in range(count):
                tts_file = tts_files[i]
                seg = speaker_segments[i]
                start_time = seg.get('start_time', 0)
                segment_files.append({
                    'path': str(tts_file),
                    'start_time': start_time
                })
                if i < 3:
                    print(f"    片段{i}: {start_time:.2f}s - {tts_file.name}")

            # 使用 FFmpeg 合成完整时长的音频
            output_path = upload_dir / f"{job_id}_{speaker}_cloned_fixed.mp3"
            success = await concat_audio_segments(job_id, speaker, segment_files, str(output_path), video_duration)

            if success:
                print(f"  [OK] 输出: {output_path}")

                # 验证时长
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', str(output_path)],
                    capture_output=True, text=True
                )
                output_duration = float(result.stdout.strip())
                print(f"  输出时长: {output_duration:.2f}s (目标: {video_duration:.2f}s)")
            else:
                print(f"  [ERROR] 合成失败")

    finally:
        await Database.disconnect()


async def concat_audio_segments(job_id: str, speaker: str, segments: list, output_path: str, total_duration: float) -> bool:
    """按时间轴拼接音频片段"""
    if not segments:
        return False

    print(f"  合成 {len(segments)} 个片段, 目标时长: {total_duration:.2f}s")

    # 构建 FFmpeg 复杂滤镜
    inputs = []
    filter_parts = []
    mix_inputs = []

    for i, seg in enumerate(segments):
        inputs.extend(['-i', seg["path"]])
        delay_ms = int(seg["start_time"] * 1000)
        filter_parts.append(f"[{i}:a]adelay={delay_ms}:all=1[a{i}]")
        mix_inputs.append(f"[a{i}]")

    # 混合所有音轨，然后用 apad 填充到目标时长
    mix_filter = "".join(mix_inputs) + f"amix=inputs={len(segments)}:duration=longest:dropout_transition=0:normalize=0,apad=whole_dur={total_duration}[out]"
    full_filter = ";".join(filter_parts) + ";" + mix_filter

    cmd = [
        'ffmpeg', '-y',
        *inputs,
        '-filter_complex', full_filter,
        '-map', '[out]',
        '-t', str(total_duration),
        '-ac', '2',
        '-ar', '44100',
        '-b:a', '192k',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


async def main():
    if len(sys.argv) < 3:
        print("用法: python tests/recompose_audio.py <job_id> <story_id>")
        print("示例: python tests/recompose_audio.py 6960cf070e08e5275955e8d8 6960c86fbb273d8a0dcfafeb")
        return

    job_id = sys.argv[1]
    story_id = sys.argv[2]
    await recompose_audio(job_id, story_id)


if __name__ == "__main__":
    asyncio.run(main())
