"""检查用户的头像和声音档案"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_profiles():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["echobot"]

    # 获取测试用户
    user = await db.users.find_one({"email": "2327374268@qq.com"})
    if not user:
        print("User not found")
        return

    user_id = str(user["_id"])
    print(f"User ID: {user_id}")

    # 获取头像档案
    print("\n=== Avatar Profiles ===")
    async for profile in db.avatar_profiles.find({"user_id": user_id}):
        print(f"ID: {profile['_id']}")
        print(f"  name: {profile.get('name')}")
        print(f"  image_url: {profile.get('image_url')}")
        print(f"  image_local: {profile.get('image_local')}")
        print(f"  service_mode: {profile.get('service_mode')}")
        print(f"  face_bbox: {profile.get('face_bbox')}")
        print()

    # 获取声音档案
    print("=== Voice Profiles ===")
    async for profile in db.voice_profiles.find({"user_id": user_id}):
        print(f"ID: {profile['_id']}")
        print(f"  name: {profile.get('name')}")
        print(f"  reference_audio_url: {profile.get('reference_audio_url')}")
        print(f"  service_mode: {profile.get('service_mode')}")
        print()

    # 获取最近的故事生成任务
    print("=== Recent Story Jobs ===")
    async for job in db.story_generation_jobs.find({"user_id": user_id}).sort("created_at", -1).limit(3):
        print(f"ID: {job['_id']}")
        print(f"  status: {job.get('status')}")
        print(f"  avatar_profile_id: {job.get('avatar_profile_id')}")
        print(f"  voice_profile_id: {job.get('voice_profile_id')}")
        print(f"  final_video_url: {job.get('final_video_url')}")
        print()

    client.close()

if __name__ == "__main__":
    asyncio.run(check_profiles())
