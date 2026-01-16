"""
只重新生成男声部分（SPEAKER_00）
- 使用新的 trimmed 参考音频
- 使用新的男头像
- 女声和背景音保持不变
"""
import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from modules.voice_clone.local_service import LocalVoiceCloneService
from modules.digital_human.local_service import LocalDigitalHumanService

# 配置
JOB_ID = "696600258dbaae1ff9d72c83"
STORY_ID = "6960c86ebb273d8a0dcfafea"
BASE_DIR = Path("E:/工作代码/73_web_human")
UPLOAD_DIR = BASE_DIR / "uploads" / "story_generation"
VIDEO_PATH = BASE_DIR / "uploads" / "videos" / "20260109172045_f573db.mp4"

# 新的参考音频和头像
MALE_REF_AUDIO = BASE_DIR / "uploads/voice_separation/6960c86ebb273d8a0dcfafea/dual/speakers/SPEAKER_00_trimmed.wav"
MALE_AVATAR = BASE_DIR / "uploads/digital_human/images/male_avatar.png"


async def main():
    print("=" * 60)
    print("重新生成男声完整版本")
    print("=" * 60)

    # 1. 获取转录文本和说话人分段
    print("\n[1/5] 获取转录和分段数据...")
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.echobot

    story = await db.stories.find_one({'_id': ObjectId(STORY_ID)})
    diarization_segs = story.get('dual_speaker_analysis', {}).get('diarization_segments', [])

    # 读取转录
    with open(UPLOAD_DIR / f"{JOB_ID}_transcription.json", 'r', encoding='utf-8') as f:
        transcription = json.load(f)

    words = transcription.get('words', [])
    print(f"  Diarization段数: {len(diarization_segs)}")
    print(f"  转录词数: {len(words)}")

    # 2. 将转录词语分配给说话人
    print("\n[2/5] 分配词语给说话人...")
    speaker_texts = {'SPEAKER_00': [], 'SPEAKER_01': []}

    for word in words:
        word_mid = (word['start'] + word['end']) / 2
        # 找到对应的说话人段
        speaker = None
        for seg in diarization_segs:
            if seg['start'] <= word_mid <= seg['end']:
                speaker = seg['speaker']
                break
        if speaker in speaker_texts:
            speaker_texts[speaker].append(word['word'])

    speaker_00_text = ' '.join(speaker_texts['SPEAKER_00'])
    speaker_01_text = ' '.join(speaker_texts['SPEAKER_01'])

    print(f"  SPEAKER_00 文本长度: {len(speaker_00_text)} 字符")
    print(f"  SPEAKER_01 文本长度: {len(speaker_01_text)} 字符")

    # 3. 生成男声克隆
    print("\n[3/5] 生成男声克隆...")
    vc_service = LocalVoiceCloneService()

    # 分段生成（每段约500字符，避免TTS一次处理太长文本）
    chunk_size = 500
    chunks = [speaker_00_text[i:i+chunk_size] for i in range(0, len(speaker_00_text), chunk_size)]
    print(f"  分成 {len(chunks)} 段")

    chunk_audios = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        output = UPLOAD_DIR / f"{JOB_ID}_SPEAKER_00_chunk{i}.wav"
        print(f"  生成第 {i+1}/{len(chunks)} 段...", end=" ", flush=True)

        result = await vc_service.clone_audio_with_text(
            reference_audio_path=str(MALE_REF_AUDIO),
            text=chunk,
            output_path=str(output)
        )

        if result:
            chunk_audios.append(str(output))
            print("OK")
        else:
            print("FAILED")

    # 合并音频块
    if chunk_audios:
        print(f"\n  合并 {len(chunk_audios)} 个音频块...")
        concat_file = UPLOAD_DIR / f"{JOB_ID}_male_concat.txt"
        with open(concat_file, 'w') as f:
            for audio in chunk_audios:
                f.write(f"file '{audio}'\n")

        male_cloned = UPLOAD_DIR / f"{JOB_ID}_SPEAKER_00_cloned_full.mp3"
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
               '-c:a', 'libmp3lame', '-b:a', '192k', str(male_cloned)]
        subprocess.run(cmd, capture_output=True)

        duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                       '-of', 'default=noprint_wrappers=1', str(male_cloned)]
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        print(f"  男声克隆完成: {result.stdout.strip()}")

    # 4. 生成男声数字人视频
    print("\n[4/5] 生成男声数字人视频...")
    dh_service = LocalDigitalHumanService()

    # 分段生成数字人（每段45秒）
    male_audio_duration = float(result.stdout.split('=')[1].strip())
    segment_duration = 45.0
    num_segments = int(male_audio_duration / segment_duration) + 1
    print(f"  数字人分段数: {num_segments}")

    dh_segments = []
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, male_audio_duration)

        # 提取音频段
        seg_audio = UPLOAD_DIR / f"{JOB_ID}_SPEAKER_00_dh_seg{i}.mp3"
        cmd = ['ffmpeg', '-y', '-i', str(male_cloned), '-ss', str(start_time),
               '-t', str(segment_duration), '-c:a', 'libmp3lame', str(seg_audio)]
        subprocess.run(cmd, capture_output=True)

        # 生成数字人
        print(f"  生成数字人段 {i+1}/{num_segments}...", end=" ", flush=True)

        task_id = f"{JOB_ID}_male_dh_seg{i}"
        emo_result = await dh_service.create_emo_task(
            task_id=task_id,
            image_url=str(MALE_AVATAR),
            audio_url=str(seg_audio)
        )

        if emo_result:
            video_url = await dh_service.wait_for_emo_task(task_id)
            if video_url:
                dh_segments.append(video_url)
                print("OK")
            else:
                print("WAIT FAILED")
        else:
            print("CREATE FAILED")

    # 合并数字人视频段
    if dh_segments:
        print(f"\n  合并 {len(dh_segments)} 个数字人视频段...")
        concat_file = UPLOAD_DIR / f"{JOB_ID}_male_dh_concat.txt"
        with open(concat_file, 'w') as f:
            for seg in dh_segments:
                # 处理路径
                seg_path = seg.lstrip('/')
                if not os.path.isabs(seg_path):
                    seg_path = str(BASE_DIR / seg_path)
                f.write(f"file '{seg_path}'\n")

        male_dh = UPLOAD_DIR / f"{JOB_ID}_SPEAKER_00_dh_full_new.mp4"
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
               '-c:v', 'libx264', '-preset', 'fast', str(male_dh)]
        subprocess.run(cmd, capture_output=True)
        print(f"  男声数字人完成: {male_dh}")

    # 5. 合成最终视频
    print("\n[5/5] 合成最终视频...")

    # 使用已有的女声和背景音
    female_cloned = UPLOAD_DIR / f"{JOB_ID}_SPEAKER_01_cloned.mp3"
    female_dh = UPLOAD_DIR / f"{JOB_ID}_SPEAKER_01_dh_full.mp4"
    background = UPLOAD_DIR / f"{JOB_ID}_background.wav"

    # 检查文件
    files = {
        'video': VIDEO_PATH,
        'male_cloned': male_cloned,
        'female_cloned': female_cloned,
        'male_dh': male_dh,
        'female_dh': female_dh,
        'background': background
    }

    for name, path in files.items():
        exists = Path(path).exists()
        print(f"  {name}: {'OK' if exists else 'MISSING'}")
        if not exists:
            print(f"    路径: {path}")

    # 获取视频尺寸
    probe_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(VIDEO_PATH)]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    width, height = map(int, result.stdout.strip().split(','))

    pip_w = int(width * 0.2)
    pip_h = int(height * 0.2)
    pip_margin = 20

    output = UPLOAD_DIR / f"{JOB_ID}_final_new.mp4"

    filter_complex = (
        f"[1:v]scale={pip_w}:{pip_h}[pip1];"
        f"[2:v]scale={pip_w}:{pip_h}[pip2];"
        f"[0:v][pip1]overlay=x={pip_margin}:y=H-h-{pip_margin}[tmp];"
        f"[tmp][pip2]overlay=x=W-w-{pip_margin}:y=H-h-{pip_margin}[vout];"
        "[3:a][4:a][5:a]amix=inputs=3:duration=longest:normalize=0[aout]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-i', str(VIDEO_PATH),
        '-i', str(female_dh),
        '-i', str(male_dh),
        '-i', str(female_cloned),
        '-i', str(male_cloned),
        '-i', str(background),
        '-filter_complex', filter_complex,
        '-map', '[vout]',
        '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '192k',
        str(output)
    ]

    print("\n  运行 FFmpeg 合成...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size = output.stat().st_size / 1024 / 1024
        print(f"\n{'='*60}")
        print(f"完成! 输出: {output}")
        print(f"大小: {size:.1f}MB")
    else:
        print(f"\n合成失败: {result.stderr[-500:]}")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
