"""
数据加密模块
使用 AES 加密敏感数据
"""
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config.settings import get_settings

settings = get_settings()


class AESCipher:
    """AES 加密器 - 用于加密敏感数据"""

    def __init__(self, key: Optional[str] = None):
        """
        初始化加密器

        Args:
            key: 加密密钥，默认使用配置中的 AES_KEY
        """
        key = key or settings.AES_KEY

        # 使用 PBKDF2 从密钥派生加密密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'echobot_salt_v1',  # 固定 salt，生产环境可改为动态
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        self.fernet = Fernet(derived_key)

    def encrypt(self, data: str) -> str:
        """
        加密数据

        Args:
            data: 明文数据

        Returns:
            加密后的数据（Base64 编码）
        """
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据

        Args:
            encrypted_data: 加密的数据

        Returns:
            解密后的明文
        """
        return self.fernet.decrypt(encrypted_data.encode()).decode()


# 全局加密器实例
_cipher: Optional[AESCipher] = None


def get_cipher() -> AESCipher:
    """获取加密器单例"""
    global _cipher
    if _cipher is None:
        _cipher = AESCipher()
    return _cipher


def encrypt_data(data: str) -> str:
    """加密数据的便捷函数"""
    return get_cipher().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """解密数据的便捷函数"""
    return get_cipher().decrypt(encrypted_data)


def hash_data(data: str) -> str:
    """
    对数据进行 SHA256 哈希（不可逆）

    Args:
        data: 原始数据

    Returns:
        哈希值（十六进制）
    """
    return hashlib.sha256(data.encode()).hexdigest()
