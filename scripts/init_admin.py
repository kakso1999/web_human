"""
初始化管理员账号脚本
运行: python scripts/init_admin.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from core.config.database import Database
from core.security.password import hash_password
from datetime import datetime


async def create_admin():
    """创建超级管理员账号"""
    # 连接数据库
    await Database.connect()
    db = Database.get_db()
    users_collection = db["users"]

    admin_email = "admin@echobot.com"
    admin_password = "Admin123456"

    # 检查是否已存在
    existing = await users_collection.find_one({"email": admin_email})
    if existing:
        # 更新为管理员角色
        await users_collection.update_one(
            {"email": admin_email},
            {"$set": {"role": "super", "is_active": True}}
        )
        print(f"管理员账号已存在，已更新角色为 super")
    else:
        # 创建新管理员
        admin_data = {
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "nickname": "超级管理员",
            "role": "super",
            "avatar_url": None,
            "google_id": None,
            "subscription": {
                "plan": "free",
                "expires_at": None
            },
            "is_active": True,
            "email_verified": True,
            "last_login_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        result = await users_collection.insert_one(admin_data)
        print(f"管理员账号创建成功！")

    print(f"\n{'='*40}")
    print(f"管理员登录信息:")
    print(f"{'='*40}")
    print(f"邮箱: {admin_email}")
    print(f"密码: {admin_password}")
    print(f"{'='*40}")
    print(f"\n请访问 http://localhost:3001 登录管理后台")

    # 断开数据库连接
    await Database.disconnect()


if __name__ == "__main__":
    asyncio.run(create_admin())
