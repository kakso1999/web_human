"""
预设故事文本数据
用于语音克隆试听功能，每个故事约 15 秒朗读时长
"""

PRESET_STORIES = [
    {
        "id": "story_little_star",
        "title": "The Little Star",
        "title_zh": "小星星",
        "preview_text": "Once upon a time, in a sky full of stars, there lived a little star who wanted to shine the brightest. Every night, she would twinkle with all her might.",
        "estimated_duration": 12
    },
    {
        "id": "story_brave_rabbit",
        "title": "The Brave Little Rabbit",
        "title_zh": "勇敢的小兔子",
        "preview_text": "In a cozy burrow under the old oak tree, there lived a little rabbit named Benny. He was small, but his heart was full of courage and kindness.",
        "estimated_duration": 13
    },
    {
        "id": "story_magic_garden",
        "title": "The Magic Garden",
        "title_zh": "魔法花园",
        "preview_text": "Behind the cottage at the end of the lane, there was a secret garden where flowers could sing and butterflies told stories of faraway lands.",
        "estimated_duration": 12
    },
    {
        "id": "story_friendly_dragon",
        "title": "The Friendly Dragon",
        "title_zh": "友善的小龙",
        "preview_text": "High up in the misty mountains, there lived a dragon named Ember. Unlike other dragons, Ember loved making friends and baking cookies for the villagers.",
        "estimated_duration": 13
    },
    {
        "id": "story_moonlight_adventure",
        "title": "Moonlight Adventure",
        "title_zh": "月光冒险",
        "preview_text": "When the moon rose high and the world fell asleep, little Emma would dream of sailing across the silver sea on a boat made of moonbeams.",
        "estimated_duration": 12
    }
]


def get_all_stories():
    """获取所有预设故事"""
    return PRESET_STORIES


def get_story_by_id(story_id: str):
    """根据 ID 获取故事"""
    for story in PRESET_STORIES:
        if story["id"] == story_id:
            return story
    return None
