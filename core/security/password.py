"""
密码处理模块
使用 bcrypt 进行密码哈希
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    对密码进行哈希

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    # 将密码编码为 bytes，bcrypt 需要 bytes 输入
    password_bytes = password.encode('utf-8')
    # 生成盐并哈希
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        密码是否匹配
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def check_password_strength(password: str) -> dict:
    """
    检查密码强度

    Args:
        password: 密码

    Returns:
        包含强度信息的字典
    """
    issues = []
    score = 0

    # 长度检查
    if len(password) >= 8:
        score += 1
    else:
        issues.append("密码长度至少8位")

    if len(password) >= 12:
        score += 1

    # 包含数字
    if any(c.isdigit() for c in password):
        score += 1
    else:
        issues.append("密码需包含数字")

    # 包含小写字母
    if any(c.islower() for c in password):
        score += 1
    else:
        issues.append("密码需包含小写字母")

    # 包含大写字母
    if any(c.isupper() for c in password):
        score += 1
    else:
        issues.append("密码需包含大写字母")

    # 包含特殊字符
    special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/"
    if any(c in special_chars for c in password):
        score += 1

    # 评级
    if score >= 5:
        strength = "strong"
    elif score >= 3:
        strength = "medium"
    else:
        strength = "weak"

    return {
        "score": score,
        "strength": strength,
        "issues": issues,
        "is_valid": len(issues) == 0
    }
