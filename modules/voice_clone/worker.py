"""
Voice Clone Worker - 独立进程执行阿里云 API 调用
避免与 FastAPI/uvicorn 事件循环的冲突
"""

import os
import sys
import json
import time
import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer


def main():
    """
    命令行参数:
    python worker.py <task_id> <audio_url> <text> <output_dir>
    """
    if len(sys.argv) != 5:
        print(json.dumps({"success": False, "error": "Invalid arguments"}))
        sys.exit(1)

    task_id = sys.argv[1]
    audio_url = sys.argv[2]
    text = sys.argv[3]
    output_dir = sys.argv[4]

    # 设置 API Key
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    if not dashscope.api_key:
        print(json.dumps({"success": False, "error": "DASHSCOPE_API_KEY not set"}))
        sys.exit(1)

    try:
        # Step 1: 创建音色
        print(f"[{task_id}] Creating voice from: {audio_url}", file=sys.stderr)
        service = VoiceEnrollmentService()

        import uuid
        voice_prefix = f"ec{uuid.uuid4().hex[:6]}"

        voice_id = service.create_voice(
            target_model='cosyvoice-v2',
            prefix=voice_prefix,
            url=audio_url
        )

        if not voice_id:
            print(json.dumps({"success": False, "error": "Failed to create voice"}))
            sys.exit(1)

        print(f"[{task_id}] Voice created: {voice_id}", file=sys.stderr)

        # Step 2: 等待音色就绪
        print(f"[{task_id}] Waiting for voice to be ready...", file=sys.stderr)
        for attempt in range(30):
            voice_info = service.query_voice(voice_id=voice_id)
            status = voice_info.get("status")
            print(f"[{task_id}] Status (attempt {attempt + 1}): {status}", file=sys.stderr)

            if status == "OK":
                break
            elif status in ["UNDEPLOYED", "FAILED"]:
                print(json.dumps({"success": False, "error": f"Voice enrollment failed: {status}"}))
                sys.exit(1)

            time.sleep(5)
        else:
            print(json.dumps({"success": False, "error": "Voice enrollment timed out"}))
            sys.exit(1)

        # Step 3: 合成语音
        print(f"[{task_id}] Synthesizing speech...", file=sys.stderr)
        synthesizer = SpeechSynthesizer(
            model='cosyvoice-v2',
            voice=voice_id
        )

        audio_data = synthesizer.call(text)

        if not audio_data:
            print(json.dumps({"success": False, "error": "Speech synthesis failed"}))
            sys.exit(1)

        # Step 4: 保存音频
        output_file = os.path.join(output_dir, f"{task_id}.mp3")
        with open(output_file, 'wb') as f:
            f.write(audio_data)

        print(f"[{task_id}] Audio saved to: {output_file}", file=sys.stderr)

        # 输出结果
        print(json.dumps({
            "success": True,
            "audio_file": output_file,
            "audio_size": len(audio_data)
        }))

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
