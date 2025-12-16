"""
数据验证器
提供各种数据验证函数
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, list]:
    """
    验证密码强度

    Args:
        password: 密码

    Returns:
        (是否有效, 问题列表)
    """
    issues = []

    if len(password) < 8:
        issues.append("密码长度至少8位")

    if len(password) > 128:
        issues.append("密码长度不能超过128位")

    if not any(c.isdigit() for c in password):
        issues.append("密码需包含数字")

    if not any(c.islower() for c in password):
        issues.append("密码需包含小写字母")

    if not any(c.isupper() for c in password):
        issues.append("密码需包含大写字母")

    return len(issues) == 0, issues


def validate_nickname(nickname: str) -> tuple[bool, Optional[str]]:
    """
    验证昵称

    Args:
        nickname: 昵称

    Returns:
        (是否有效, 错误消息)
    """
    if len(nickname) < 2:
        return False, "昵称至少2个字符"

    if len(nickname) > 50:
        return False, "昵称最多50个字符"

    # 只允许字母、数字、中文、下划线
    pattern = r'^[\w\u4e00-\u9fa5]+$'
    if not re.match(pattern, nickname):
        return False, "昵称只能包含字母、数字、中文和下划线"

    return True, None


def sanitize_string(value: str) -> str:
    """
    清理字符串，防止 XSS

    Args:
        value: 原始字符串

    Returns:
        清理后的字符串
    """
    # 转义 HTML 特殊字符
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }

    for char, replacement in replacements.items():
        value = value.replace(char, replacement)

    return value


def validate_object_id(id: str) -> bool:
    """
    验证 MongoDB ObjectId 格式

    Args:
        id: ID 字符串

    Returns:
        是否有效
    """
    if not id or len(id) != 24:
        return False

    try:
        int(id, 16)
        return True
    except ValueError:
        return False


def validate_url(url: str) -> bool:
    """
    验证 URL 格式

    Args:
        url: URL 字符串

    Returns:
        是否有效
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    验证文件扩展名

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名列表

    Returns:
        是否有效
    """
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in [e.lower().lstrip('.') for e in allowed_extensions]
