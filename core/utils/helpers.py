"""
工具函数
提供各种常用工具函数
"""
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Any
from pathlib import Path


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
