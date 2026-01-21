"""
工具函数
提供各种常用工具函数
"""
import os
import uuid
import hashlib
import subprocess
import json
from datetime import datetime
from typing import Optional, Any, Tuple
from pathlib import Path


def get_ffmpeg_path() -> str:
    """获取 FFmpeg 可执行文件路径"""
    # 首先检查系统 PATH
    import shutil
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # 检查常见安装位置
    possible_paths = [
        r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # 如果都找不到，返回默认值（让系统报错）
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """获取 FFprobe 可执行文件路径"""
    import shutil
    ffprobe_in_path = shutil.which('ffprobe')
    if ffprobe_in_path:
        return ffprobe_in_path

    possible_paths = [
        r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffprobe.exe",
        r"C:\ffmpeg\bin\ffprobe.exe",
        r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
        "/usr/bin/ffprobe",
        "/usr/local/bin/ffprobe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return "ffprobe"


def generate_id() -> str:
    """生成唯一 ID"""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """生成短 ID"""
    return str(uuid.uuid4())[:length]


def generate_filename(original_name: str) -> str:
    """
    生成唯一文件名

    Args:
        original_name: 原始文件名

    Returns:
        新文件名
    """
    ext = Path(original_name).suffix
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_short_id(6)
    return f"{timestamp}_{random_part}{ext}"


def ensure_dir(path: str) -> None:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        return ""
    return dt.strftime(format)


def parse_datetime(dt_str: str, format: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """解析日期时间字符串"""
    try:
        return datetime.strptime(dt_str, format)
    except (ValueError, TypeError):
        return None


def mask_email(email: str) -> str:
    """
    隐藏邮箱中间部分

    Args:
        email: 邮箱地址

    Returns:
        隐藏后的邮箱，如 t***@example.com
    """
    if '@' not in email:
        return email

    local, domain = email.split('@')
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '***' + local[-1]

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    隐藏手机号中间部分

    Args:
        phone: 手机号

    Returns:
        隐藏后的手机号，如 138****8888
    """
    if len(phone) < 7:
        return phone

    return phone[:3] + '****' + phone[-4:]


def calculate_file_hash(file_content: bytes) -> str:
    """
    计算文件 MD5 哈希

    Args:
        file_content: 文件内容

    Returns:
        MD5 哈希值
    """
    return hashlib.md5(file_content).hexdigest()


def format_file_size(size: int) -> str:
    """
    格式化文件大小

    Args:
        size: 文件大小（字节）

    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def format_duration(seconds: int) -> str:
    """
    格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串，如 "2:30" 或 "1:02:30"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def safe_get(obj: Any, *keys, default: Any = None) -> Any:
    """
    安全获取嵌套字典值

    Args:
        obj: 字典对象
        keys: 键路径
        default: 默认值

    Returns:
        值或默认值
    """
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return default
        if obj is None:
            return default
    return obj


def get_video_duration(video_path: str) -> int:
    """
    获取视频时长（秒）

    Args:
        video_path: 视频文件路径

    Returns:
        视频时长（秒），失败返回0
    """
    try:
        ffprobe_path = get_ffprobe_path()
        result = subprocess.run(
            [
                ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            return int(duration)
    except Exception as e:
        print(f"Error getting video duration: {e}")

    return 0


def extract_video_thumbnail(video_path: str, output_path: str, time_seconds: int = 20) -> bool:
    """
    从视频中提取缩略图

    Args:
        video_path: 视频文件路径
        output_path: 输出图片路径
        time_seconds: 截取时间点（秒），默认第20秒

    Returns:
        是否成功
    """
    try:
        # 先获取视频时长
        duration = get_video_duration(video_path)

        # 如果视频时长小于指定时间，则取中间时间点
        if duration > 0 and duration < time_seconds:
            time_seconds = duration // 2

        # 确保至少从第1秒开始
        if time_seconds < 1:
            time_seconds = 1

        ffmpeg_path = get_ffmpeg_path()
        result = subprocess.run(
            [
                ffmpeg_path,
                '-y',  # 覆盖输出文件
                '-i', video_path,
                '-ss', str(time_seconds),  # 跳转到指定时间
                '-vframes', '1',  # 只提取1帧
                '-q:v', '2',  # 图片质量
                output_path
            ],
            capture_output=True,
            text=True
        )

        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"Error extracting thumbnail: {e}")
        return False


def extract_audio_from_video(video_path: str, output_path: str) -> bool:
    """
    从视频中提取音频

    Args:
        video_path: 视频文件路径
        output_path: 输出音频路径 (.mp3)

    Returns:
        是否成功
    """
    try:
        ffmpeg_path = get_ffmpeg_path()
        result = subprocess.run(
            [
                ffmpeg_path,
                '-y',  # 覆盖输出文件
                '-i', video_path,
                '-vn',  # 不处理视频
                '-acodec', 'libmp3lame',  # 使用 MP3 编码
                '-ab', '128k',  # 比特率
                '-ar', '16000',  # 采样率 16kHz（适合语音识别）
                '-ac', '1',  # 单声道
                output_path
            ],
            capture_output=True,
            text=True
        )

        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return False
